from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.models.movement import MouvementStock, MouvementType

router = APIRouter()

# Schéma Pydantic pour lire un mouvement
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

# Schéma Pydantic pour créer un mouvement
class MouvementCreate(BaseModel):
    id_produit: int
    type: str
    quantite: int
    commentaire: str | None = None

@router.get("/movements", response_model=List[MouvementResponse])
def get_movements(db: Session = Depends(get_db)):
    # On récupère tous les mouvements, du plus récent au plus ancien
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
            # Normalement on prend l'ID du token connecté, on force à 1 en dev s'il manque
            id_utilisateur=1 
        )
        db.add(new_mouvement)
        db.commit()
        db.refresh(new_mouvement)
        return new_mouvement
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))