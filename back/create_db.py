from database import engine, Base
# Importar os modelos é obrigatório para o Base reconhecê-los
from models import Category, Transaction, RecurringTemplate

def init_db():
    print("Tentando criar tabelas no MySQL local...")
    try:
        Base.metadata.create_all(bind=engine)
        print("SUCESSO: Tabelas criadas no banco 'financas_pessoais'.")
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")

if __name__ == "__main__":
    init_db()