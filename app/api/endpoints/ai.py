# backend/app/api/endpoints/ai.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["Intelligence Artificielle"])

# Nouveau schéma pour la requête de chat
class ChatRequest(BaseModel):
    message: str

@router.get("/test")
async def test_ai():
    """
    Point de terminaison simple pour vérifier que le module IA est chargé.
    """
    return {"message": "Route AI OK", "status": "active"}

@router.post("/chat")
async def chat_with_ai(
    req: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat interactif avec l'IA. L'IA analyse la question et fouille dans le stock.
    """
    service = AIService(db_session=db)
    result = await service.chat_with_data(user_message=req.message)
    return result

@router.get("/recommendations")
async def get_ai_recommendations(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Génère des recommandations de stock basées sur l'historique des 90 derniers jours.
    """
    service = AIService(db_session=db)
    result = await service.get_stock_recommendations(user_id=user_id)
    
    if isinstance(result, dict) and "error" in result and "Échec de la connexion" in result.get("details", ""):
        raise HTTPException(status_code=503, detail=result)
    
    return result