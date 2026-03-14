from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, '..', '..', '..', 'data')
os.makedirs(data_dir, exist_ok=True)
db_path = os.path.join(data_dir, 'payments.db')
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()