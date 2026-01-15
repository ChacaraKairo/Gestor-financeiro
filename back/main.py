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
@app.get("/dashboard/summary")
def get_dashboard_summary(month: int, year: int, db: Session = Depends(get_db)):
    # Calcularemos o total de receitas e despesas do mês no banco
    from sqlalchemy import func
    
    # Datas de início e fim do mês
    last_day = calendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    # Função auxiliar para somar
    def get_sum(transaction_type):
        resultado = db.query(func.sum(models.Transaction.amount))\
            .join(models.Category)\
            .filter(models.Category.type == transaction_type)\
            .filter(models.Transaction.transaction_date >= start_date)\
            .filter(models.Transaction.transaction_date <= end_date)\
            .scalar()
        
        # --- A CORREÇÃO ESTÁ AQUI ---
        # Se vier None (banco vazio), retorna 0.0
        # Se vier Decimal (do MySQL), converte para float
        return float(resultado) if resultado else 0.0

    receita = get_sum("RECEITA")
    despesa = get_sum("DESPESA")
    saldo = receita - despesa

    return {
        "receita": receita,
        "despesa": despesa,
        "saldo": saldo
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