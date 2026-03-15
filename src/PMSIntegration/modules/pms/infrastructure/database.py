from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# -----------------------------------------------------------------------
# Configuración de la base de datos del servicio PMS Integration.
# En producción/Docker: PostgreSQL usando variables de entorno PMS_DB_*.
# En desarrollo local / tests: SQLite como fallback si no hay env vars.
# -----------------------------------------------------------------------

PMS_DB_USER = os.getenv('PMS_DB_USER')
PMS_DB_PASSWORD = os.getenv('PMS_DB_PASSWORD')
PMS_DB_HOST = os.getenv('PMS_DB_HOST')
PMS_DB_PORT = os.getenv('PMS_DB_PORT', '5432')
PMS_DB_NAME = os.getenv('PMS_DB_NAME')

if all([PMS_DB_USER, PMS_DB_PASSWORD, PMS_DB_HOST, PMS_DB_NAME]):
    DATABASE_URL = f"postgresql://{PMS_DB_USER}:{PMS_DB_PASSWORD}@{PMS_DB_HOST}:{PMS_DB_PORT}/{PMS_DB_NAME}"
    print(f"[PMS DB] Connecting to PostgreSQL: {PMS_DB_HOST}:{PMS_DB_PORT}/{PMS_DB_NAME}")
else:
    # Fallback para entornos de desarrollo local sin Docker
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, '..', '..', '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, 'pms.db')
    DATABASE_URL = f"sqlite:///{db_path}"
    print(f"[PMS DB] WARNING: No PostgreSQL env vars found. Using SQLite fallback: {db_path}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()