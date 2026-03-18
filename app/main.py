# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.database import engine, Base

app = FastAPI(title="Projet Agile Back")

# --- Configuration CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "API running"}

# --- CORRECTION ICI : Startup Synchrone ---
@app.on_event("startup")
def on_startup():
    """
    Crée les tables de manière synchrone au démarrage.
    Compatible avec SQLite et PostgreSQL sync.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Tables de la base de données créées/vérifiées avec succès.")