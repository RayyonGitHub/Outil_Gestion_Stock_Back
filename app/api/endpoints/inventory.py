from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.product import Produit
from app.models.movement import MouvementStock, MouvementType
from app.schemas.movement import MovementCreate, MovementResponse

router = APIRouter()


@router.get("/movements", response_model=list[MovementResponse])
def get_movements(
    db: Session = Depends(get_db),
    role: str = Depends(require_roles("Gestionnaire", "Vendeur", "Administrateur"))
):
    return db.query(MouvementStock).order_by(MouvementStock.date_mouvement.desc()).all()


@router.post("/movements", response_model=MovementResponse)
def create_movement(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    role: str = Depends(require_roles("Gestionnaire"))
):
    produit = db.query(Produit).filter(Produit.id_produit == payload.id_produit).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    if payload.quantite <= 0:
        raise HTTPException(status_code=400, detail="La quantité doit être supérieure à 0")

    movement_type = payload.type.upper()

    if movement_type not in ["ENTREE", "SORTIE", "AJUSTEMENT"]:
        raise HTTPException(status_code=400, detail="Type invalide : ENTREE, SORTIE ou AJUSTEMENT")

    if movement_type == "ENTREE":
        produit.quantite += payload.quantite

    elif movement_type == "SORTIE":
        if produit.quantite < payload.quantite:
            raise HTTPException(status_code=400, detail="Stock insuffisant pour cette sortie")
        produit.quantite -= payload.quantite

    elif movement_type == "AJUSTEMENT":
        produit.quantite = payload.quantite

    mouvement = MouvementStock(
        id_produit=payload.id_produit,
        id_utilisateur=None,
        type=MouvementType[movement_type],
        quantite=payload.quantite,
        commentaire=payload.commentaire
    )

    db.add(mouvement)
    db.commit()
    db.refresh(mouvement)
    return mouvement