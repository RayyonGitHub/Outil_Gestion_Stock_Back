# backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# IMPORTANT : On repasse sur un moteur synchrone classique
# car 90% des routes utilisent db.query() qui est synchrone.
SQLALCHEMY_DATABASE_URL = "sqlite:///./stockit.db"

# Création du moteur
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Mettez à False en production pour moins de logs
    connect_args={"check_same_thread": False} # Requis pour SQLite avec FastAPI
)

# Création des sessions SYNCHRONES
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Base pour les modèles
Base = declarative_base()

# Dépendance FastAPI SYNCHRONE
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()