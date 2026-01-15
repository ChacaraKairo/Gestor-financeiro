from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from enum import Enum

# Validação para Categorias
class TransactionType(str, Enum):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"

class CategoryBase(BaseModel):
    name: str
    color_hex: Optional[str] = "#CCCCCC"
    type: TransactionType

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    class Config:
        from_attributes = True # Permite ler dados do SQLAlchemy

# Validação para Transações
class TransactionBase(BaseModel):
    description: str
    amount: float
    transaction_date: date
    category_id: int
    is_fixed: bool = False
    is_paid: bool = False
    payment_method: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    category: Optional[CategoryResponse] = None # Retorna a categoria junto
    class Config:
        from_attributes = True
        # ... (Mantenha o código anterior de Category e Transaction)

# --- SCHEMAS PARA RECORRÊNCIA (NOVO) ---
class RecurringBase(BaseModel):
    description: str
    amount: float
    category_id: int
    active: bool = True

class RecurringCreate(RecurringBase):
    pass

class RecurringResponse(RecurringBase):
    id: int
    category: Optional[CategoryResponse] = None
    class Config:
        from_attributes = True
        # ... (Mantenha o código anterior de Category e Transaction)

# --- SCHEMAS PARA RECORRÊNCIA ---
class RecurringBase(BaseModel):
    description: str
    estimated_amount: float # <--- MUDAMOS DE 'amount' PARA 'estimated_amount'
    category_id: int
    active: bool = True

class RecurringCreate(RecurringBase):
    pass

class RecurringResponse(RecurringBase):
    id: int
    category: Optional[CategoryResponse] = None
    class Config:
        from_attributes = True