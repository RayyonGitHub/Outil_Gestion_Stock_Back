from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router

app = FastAPI(title="Projet Agile Back")

# --- Configuration CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Port par défaut de Vite (à adapter si besoin)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "API running"}