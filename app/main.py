from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(title="Projet Agile Back")

app.include_router(api_router)


@app.get("/")
def root():
    return {"message": "API running"}