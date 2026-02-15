import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, MetaData, Table, text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Database Connection
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define Table Schema
class TuikCalendar(Base):
    __tablename__ = 'calender'
    __table_args__ = {'schema': 'tuik'}

    id = Column(Integer, primary_key=True, index=True)
    tarih = Column(DateTime, nullable=False)
    kurum = Column(String, nullable=False)
    aciklama = Column(String, nullable=False)
    url = Column(String, nullable=True) # Link to data
    durum = Column(String, nullable=False)  # 'yayımlandı' or 'yayımlanacak'
    created_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Create tables if they don't exist"""
    try:
        # Create schema if not exists (PostgreSQL specific)
        with engine.connect() as connection:
             connection.execute(text("CREATE SCHEMA IF NOT EXISTS tuik"))
             connection.commit()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
