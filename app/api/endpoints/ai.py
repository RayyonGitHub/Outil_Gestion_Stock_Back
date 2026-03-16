from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["IA"])


@router.get("/test")
def test_ai():
    return {"message": "Route AI OK"}


@router.get("/recommendations")
async def get_ai_recommendations(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    service = AIService(db)
    return await service.get_stock_recommendations(user_id=user_id)