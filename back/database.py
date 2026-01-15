from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
import urllib.parse 

# Carrega o .env da pasta raiz
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# --- A CORREÇÃO ESTÁ AQUI ---
# Tratamos a senha para permitir caracteres especiais como '@'
encoded_password = urllib.parse.quote_plus(DB_PASS)

# Usamos 'encoded_password' em vez de DB_PASS
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL)
    # Teste rápido de conexão ao importar
    connection = engine.connect()
    connection.close()
    print("✅ Conexão com banco de dados configurada com sucesso!")
except Exception as e:
    print(f"❌ ERRO: Não foi possível conectar ao banco. Verifique o arquivo .env.\nDetalhe: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()