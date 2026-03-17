# backend/app/api/endpoints/ai.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["Intelligence Artificielle"])

@router.get("/test")
async def test_ai():
    """
    Point de terminaison simple pour vérifier que le module IA est chargé.
    """
    return {"message": "Route AI OK", "status": "active"}

@router.get("/recommendations")
async def get_ai_recommendations(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Génère des recommandations de stock basées sur l'historique des 90 derniers jours.
    
    - **user_id**: ID de l'utilisateur demandant l'analyse (par défaut 1 pour le test).
    - **Retour**: Un objet JSON contenant la synthèse, les alertes critiques et le plan de réapprovisionnement.
    """
    # Initialisation du service
    service = AIService(db_session=db)
    
    # Exécution de l'analyse
    result = await service.get_stock_recommendations(user_id=user_id)
    
    # Gestion des réponses :
    # On ne lève une erreur HTTP 500 que si c'est une exception technique Python.
    # Si l'IA renvoie un champ "error" dans le JSON (ex: "JSON malformé"), 
    # on le retourne tel quel au frontend pour qu'il puisse l'afficher proprement.
    
    if isinstance(result, dict) and "error" in result and "Échec de la connexion" in result.get("details", ""):
        # C'est une vraie erreur technique (Ollama éteint, réseau, etc.)
        raise HTTPException(status_code=503, detail=result)
    
    return result