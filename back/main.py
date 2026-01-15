from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import calendar
from sqlalchemy import func

import models, schemas, database

app = FastAPI(title="Gestor Financeiro API")

# --- CONFIGURAÇÃO DO CORS ---
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# ROTAS DE CATEGORIAS
# ==========================================

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

@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    db.delete(category)
    db.commit()
    return {"message": "Categoria deletada com sucesso"}

# ==========================================
# ROTAS DE RECORRÊNCIA (CONTAS FIXAS)
# ==========================================

@app.post("/recurring/", response_model=schemas.RecurringResponse)
def create_recurring(recurring: schemas.RecurringCreate, db: Session = Depends(get_db)):
    db_recurring = models.RecurringTemplate(
        description=recurring.description,
        estimated_amount=recurring.estimated_amount, 
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

# ==========================================
# ROTAS DE TRANSAÇÕES (AGORA COM EDITAR/EXCLUIR)
# ==========================================

@app.post("/transactions/", response_model=schemas.TransactionResponse)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == transaction.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    db_transaction = models.Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.get("/transactions/", response_model=List[schemas.TransactionResponse])
def read_transactions(month: int = None, year: int = None, db: Session = Depends(get_db)):
    query = db.query(models.Transaction)
    if month and year:
        last_day = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        query = query.filter(models.Transaction.transaction_date >= start_date, models.Transaction.transaction_date <= end_date)
    return query.all()

# --- NOVO: ROTA DE EDITAR (PUT) ---
@app.put("/transactions/{transaction_id}", response_model=schemas.TransactionResponse)
def update_transaction(transaction_id: int, transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    # Atualiza os campos
    db_transaction.description = transaction.description
    db_transaction.amount = transaction.amount
    db_transaction.transaction_date = transaction.transaction_date
    db_transaction.category_id = transaction.category_id
    db_transaction.is_fixed = transaction.is_fixed
    db_transaction.is_paid = transaction.is_paid
    db_transaction.payment_method = transaction.payment_method
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# --- NOVO: ROTA DE EXCLUIR (DELETE) ---
@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    db.delete(db_transaction)
    db.commit()
    return {"message": "Transação deletada com sucesso"}

@app.post("/transactions/generate-fixed/{month}/{year}")
def generate_fixed_expenses(month: int, year: int, db: Session = Depends(get_db)):
    templates = db.query(models.RecurringTemplate).filter(models.RecurringTemplate.active == True).all()
    count = 0
    last_day = calendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    for template in templates:
        exists = db.query(models.Transaction).filter(
            models.Transaction.description == template.description,
            models.Transaction.category_id == template.category_id,
            models.Transaction.transaction_date >= start_date,
            models.Transaction.transaction_date <= end_date
        ).first()

        if not exists:
            dia_vencimento = min(10, last_day)
            new_trans = models.Transaction(
                description=template.description,
                amount=template.estimated_amount,
                transaction_date=date(year, month, dia_vencimento),
                category_id=template.category_id,
                is_fixed=True,
                is_paid=False,
                payment_method="Boleto"
            )
            db.add(new_trans)
            count += 1
    
    db.commit()
    return {"message": f"{count} despesas fixas geradas para {month}/{year}"}

# ==========================================
# DASHBOARD
# ==========================================

@app.get("/dashboard/summary")
def get_dashboard_summary(month: int, year: int, db: Session = Depends(get_db)):
    last_day = calendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    def get_val(tipo, pago=None):
        query = db.query(func.sum(models.Transaction.amount))\
            .join(models.Category)\
            .filter(models.Category.type == tipo)\
            .filter(models.Transaction.transaction_date >= start_date)\
            .filter(models.Transaction.transaction_date <= end_date)
        
        if pago is not None:
            query = query.filter(models.Transaction.is_paid == pago)
            
        result = query.scalar()
        return float(result) if result else 0.0

    receita = get_val("RECEITA")
    despesa = get_val("DESPESA")
    saldo = receita - despesa
    pendente = get_val("DESPESA", pago=False)

    return {
        "receita": receita,
        "despesa": despesa,
        "saldo": saldo,
        "pendente": pendente
    }