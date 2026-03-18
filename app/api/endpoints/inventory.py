from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.models.movement import MouvementStock, MouvementType

router = APIRouter()

class MouvementResponse(BaseModel):
    id_mouvement: int
    id_produit: int
    id_utilisateur: int | None = None
    type: str
    quantite: int
    date_mouvement: datetime
    commentaire: str | None = None

    class Config:
        from_attributes = True

class MouvementCreate(BaseModel):
    id_produit: int
    type: str
    quantite: int
    commentaire: str | None = None

@router.get("/movements", response_model=List[MouvementResponse])
def get_movements(db: Session = Depends(get_db)):
    result = db.execute(
        select(MouvementStock).order_by(MouvementStock.date_mouvement.desc())
    )
    return result.scalars().all()

@router.post("/movements", response_model=MouvementResponse)
def create_movement(mvt: MouvementCreate, db: Session = Depends(get_db)):
    try:
        new_mouvement = MouvementStock(
            id_produit=mvt.id_produit,
            type=mvt.type,
            quantite=mvt.quantite,
            commentaire=mvt.commentaire,
            id_utilisateur=1 
        )
        db.add(new_mouvement)
        db.commit()
        db.refresh(new_mouvement)
        return new_mouvement
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))