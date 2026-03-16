from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ai_service import AIService
from app.api.deps import get_db

router = APIRouter(prefix="/ai", tags=["AI"])

@router.get("/recommendations")
async def recommendations(user_id: int, db: AsyncSession = Depends(get_db)):
    service = AIService(db)
    return await service.get_stock_recommendations(user_id)