from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.database import engine, Base

app = FastAPI(title="Projet Agile Back")

# --- Configuration CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # port frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "API running"}

@app.on_event("startup")
def on_startup():
    # créer toutes les tables synchrones
    Base.metadata.create_all(bind=engine)


#uvicorn app.main:app --reload
#http://127.0.0.1:8000/ai/test