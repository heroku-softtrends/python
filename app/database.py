from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Environment-based database configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, production

# Heroku automatically provides DATABASE_URL - use it if available
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Fix Heroku's postgres:// to postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    print("🚀 Using Heroku PostgreSQL (DATABASE_URL)")
elif ENVIRONMENT == "production":
    # Fallback to POSTGRES_URL if DATABASE_URL not set
    POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://u5hihvko57gqfc:p5ea23a8e2d8fa635303f78804905693f10fd3afd70e7ea20ceba27019e82fdf1@c57oa7dm3pc281.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d22ec8obdr7dh")
    DATABASE_URL = POSTGRES_URL
    print("🚀 Using PostgreSQL for PRODUCTION environment")
else:
    SQLITE_URL = os.getenv("SQLITE_URL", "sqlite:///./invoicereader.db")
    DATABASE_URL = SQLITE_URL
    print("🔧 Using SQLite for DEVELOPMENT environment")

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},
        echo=False  # Set to True for SQL debugging
    )
else:
    # PostgreSQL configuration with connection pooling and timeouts
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
        connect_args={
            "connect_timeout": 10,
            "application_name": "invoice_reader_app"
        }
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()