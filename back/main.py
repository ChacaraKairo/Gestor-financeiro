from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # <--- IMPORTANTE PARA O ELECTRON
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import calendar # Importamos aqui para usar nas rotas

# Importando nossos arquivos
import models, schemas, database

# Cria a aplicação
app = FastAPI(title="Gestor Financeiro API")

# --- CONFIGURAÇÃO DO CORS (LIBERA O ACESSO DO FRONTEND) ---
origins = ["*"] # Libera acesso de qualquer origem (necessário para dev local)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Libera GET, POST, PUT, DELETE
    allow_headers=["*"],
)
# ----------------------------------------------------------

# Dependência para pegar o banco de dados
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS DE CATEGORIAS ---

@app.post("/categories/", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    db_category = models.Category(
        name=category.name,
        color_hex=category.color_hex,
        type=category.type
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/categories/", response_model=List[schemas.CategoryResponse])
def read_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

# --- ROTAS DE TRANSAÇÕES ---

@app.post("/transactions/", response_model=schemas.TransactionResponse)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    # Verifica se a categoria existe
    category = db.query(models.Category).filter(models.Category.id == transaction.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    db_transaction = models.Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.get("/transactions/", response_model=List[schemas.TransactionResponse])
def read_transactions(
    month: int = None, 
    year: int = None, 
    db: Session = Depends(get_db)
):
    query = db.query(models.Transaction)
    
    # Se passar mês e ano, filtra (Ex: /transactions/?month=10&year=2025)
    if month and year:
        last_day = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        query = query.filter(models.Transaction.transaction_date >= start_date, models.Transaction.transaction_date <= end_date)
        
    return query.all()

# --- DASHBOARD (RESUMO) ---
# --- DASHBOARD (ATUALIZADO PARA REQUISITO 3.1) ---
@app.get("/dashboard/summary")
def get_dashboard_summary(month: int, year: int, db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    last_day = calendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    # 1. Receita Total (Tudo que entrou)
    receita = db.query(func.sum(models.Transaction.amount))\
        .join(models.Category).filter(models.Category.type == "RECEITA")\
        .filter(models.Transaction.transaction_date >= start_date)\
        .filter(models.Transaction.transaction_date <= end_date)\
        .scalar() or 0.0

    # 2. Despesa Total (Tudo que saiu ou vai sair - Contábil)
    despesa = db.query(func.sum(models.Transaction.amount))\
        .join(models.Category).filter(models.Category.type == "DESPESA")\
        .filter(models.Transaction.transaction_date >= start_date)\
        .filter(models.Transaction.transaction_date <= end_date)\
        .scalar() or 0.0

    # 3. Saldo Atual (O que de fato tem no bolso? Receita Paga - Despesa Paga)
    # Mas para simplificar conforme o doc, o Saldo do Mês é Receita - Despesa (Regime de Competência)
    saldo = float(receita) - float(despesa)

    # 4. Projeção (Requisito 3.1: Receita - Despesas Pagas - Despesas Fixas Pendentes)
    # Vamos adaptar para: Saldo Atual - O que falta pagar
    despesa_pendente = db.query(func.sum(models.Transaction.amount))\
        .join(models.Category).filter(models.Category.type == "DESPESA")\
        .filter(models.Transaction.is_paid == False)\
        .filter(models.Transaction.transaction_date >= start_date)\
        .filter(models.Transaction.transaction_date <= end_date)\
        .scalar() or 0.0

    # Projeção: Se eu pagar tudo o que devo este mês, quanto sobra?
    projecao = saldo # Como 'saldo' já desconta tudo (pago e não pago), ele já é a projeção final no regime de competência.
    
    # OBS: Se você quiser "Saldo de Caixa" (só o que pagou), a lógica muda. 
    # Vou manter Saldo = (Todas Receitas - Todas Despesas) conforme prática padrão.
    
    return {
        "receita": float(receita),
        "despesa": float(despesa),
        "saldo": saldo,
        "pendente": float(despesa_pendente) # Enviaremos isso para o Front mostrar alerta
    }
# ... (logo após o def read_categories)

@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    # Busca a categoria
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    # Deleta do banco
    db.delete(category)
    db.commit()
    return {"message": "Categoria deletada com sucesso"}
# ... (Mantenha imports e rotas anteriores)

# --- ROTAS DE GASTOS FIXOS (RECORRÊNCIA) ---

@app.post("/recurring/", response_model=schemas.RecurringResponse)
def create_recurring(recurring: schemas.RecurringCreate, db: Session = Depends(get_db)):
    db_recurring = models.RecurringTemplate(
        description=recurring.description,
        estimated_amount=recurring.amount, # No banco chama estimated_amount
        category_id=recurring.category_id,
        active=recurring.active
    )
    db.add(db_recurring)
    db.commit()
    db.refresh(db_recurring)
    return db_recurring

@app.get("/recurring/", response_model=List[schemas.RecurringResponse])
def read_recurring(db: Session = Depends(get_db)):
    return db.query(models.RecurringTemplate).filter(models.RecurringTemplate.active == True).all()

@app.delete("/recurring/{id}")
def delete_recurring(id: int, db: Session = Depends(get_db)):
    item = db.query(models.RecurringTemplate).filter(models.RecurringTemplate.id == id).first()
    if item:
        db.delete(item)
        db.commit()
    return {"ok": True}

# --- A MÁGICA: GERAR TRANSAÇÕES DO MÊS ---
# Requisito 3.2: "Funcionalidade Virada de Mês"
@app.post("/transactions/generate-fixed/{month}/{year}")
def generate_fixed_expenses(month: int, year: int, db: Session = Depends(get_db)):
    # 1. Busca todos os modelos ativos (Luz, Internet, Aluguel)
    templates = db.query(models.RecurringTemplate).filter(models.RecurringTemplate.active == True).all()
    
    count = 0
    
    # 2. Para cada modelo, verifica se já existe lançamento neste mês
    for template in templates:
        # Define o intervalo do mês
        last_day = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)

        # Procura duplicata (mesma descrição e categoria no mesmo mês)
        exists = db.query(models.Transaction).filter(
            models.Transaction.description == template.description,
            models.Transaction.category_id == template.category_id,
            models.Transaction.transaction_date >= start_date,
            models.Transaction.transaction_date <= end_date
        ).first()

        # 3. Se não existe, cria a transação "Pendente"
        if not exists:
            # Data padrão: Dia 05 do mês (ou dia 1 se preferir)
            # Vamos usar dia 10 como padrão de vencimento
            dia_vencimento = min(10, last_day) 
            
            new_trans = models.Transaction(
                description=template.description,
                amount=template.estimated_amount,
                transaction_date=date(year, month, dia_vencimento),
                category_id=template.category_id,
                is_fixed=True,   # Marca como fixo
                is_paid=False,   # Marca como pendente (Requisito 3.2)
                payment_method="Boleto"
            )
            db.add(new_trans)
            count += 1
    
    db.commit()
    return {"message": f"{count} despesas fixas geradas para {month}/{year}"}