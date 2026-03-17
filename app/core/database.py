# backend/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# IMPORTANT : Le préfixe doit être 'sqlite+aiosqlite://' et non 'sqlite:///'
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./stockit.db"

# Création du moteur ASYNCHRONE
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Mettez à False en production pour moins de logs
    future=True
)

# Création des sessions ASYNCHRONES
async_session = sessionmaker(
    engine, 
    class_=AsyncSession,  # Crucial : force l'utilisation de AsyncSession
    expire_on_commit=False
)

# Base pour les modèles (reste identique)
Base = declarative_base()

# Dépendance FastAPI ASYNCHRONE
async def get_db():
    async with async_session() as session:
        yield session