from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Numeric, Enum
from sqlalchemy.orm import relationship
import enum
from database import Base

class TransactionType(enum.Enum):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    color_hex = Column(String(7), default="#CCCCCC")
    type = Column(Enum(TransactionType), nullable=False)
    transactions = relationship("Transaction", back_populates="category")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_date = Column(Date, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    is_fixed = Column(Boolean, default=False)
    is_paid = Column(Boolean, default=False)
    payment_method = Column(String(50))
    category = relationship("Category", back_populates="transactions")

class RecurringTemplate(Base):
    __tablename__ = "recurring_templates"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    estimated_amount = Column(Numeric(10, 2))
    active = Column(Boolean, default=True)