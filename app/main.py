# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.database import engine, Base  # engine est maintenant un AsyncEngine

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

# --- CORRECTION ICI : Startup Asynchrone ---
@app.on_event("startup")
async def on_startup():
    """
    Crée les tables de manière asynchrone au démarrage.
    Compatible avec SQLite (aiosqlite) et PostgreSQL async.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables de la base de données créées/vérifiées avec succès.")

# Note: Plus besoin d'appeler create_all dans seed_test.py si on le fait ici,
# mais le garder dans le seed ne fait pas de mal (c'est idempotent).