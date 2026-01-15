from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import sys
from dotenv import load_dotenv
import urllib.parse 

# --- 1. LÓGICA INTELIGENTE PARA ACHAR O .ENV ---
if getattr(sys, 'frozen', False):
    # Se estiver rodando como .exe, procura na mesma pasta do executável
    base_path = os.path.dirname(sys.executable)
else:
    # Se estiver rodando no terminal (dev), procura na pasta raiz do projeto
    base_path = os.path.join(os.path.dirname(__file__), '..')

env_path = os.path.join(base_path, '.env')

print(f"🔍 Buscando arquivo .env em: {env_path}")

# Carrega as variáveis
load_dotenv(env_path)

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# --- 2. VALIDAÇÃO ANTES DE CONECTAR ---
if not DB_USER or not DB_PASS:
    print("\n⚠️  ERRO CRÍTICO: Variáveis de ambiente (DB_USER ou DB_PASS) não encontradas!")
    print(f"👉 AÇÃO NECESSÁRIA: Copie o arquivo '.env' para dentro da pasta onde está o 'api.exe'.")
    print(f"   Pasta esperada: {base_path}")
    input("Pressione ENTER para fechar...")
    sys.exit(1) # Encerra o programa aqui para não dar erro depois

# Tratamento de senha
encoded_password = urllib.parse.quote_plus(DB_PASS)
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    # pool_recycle evita quedas de conexão com MySQL
    engine = create_engine(DATABASE_URL, pool_recycle=3600)
    
    # Teste real de conexão
    with engine.connect() as connection:
        print("✅ Conexão com banco de dados MySQL estabelecida!")
except Exception as e:
    print(f"\n❌ ERRO FATAL: Falha ao conectar no MySQL.")
    print(f"Detalhe: {e}")
    input("Pressione ENTER para fechar...")
    sys.exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()