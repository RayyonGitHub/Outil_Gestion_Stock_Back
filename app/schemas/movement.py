from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MovementCreate(BaseModel):
    id_produit: int
    type: str  # ENTREE / SORTIE / AJUSTEMENT
    quantite: int
    commentaire: Optional[str] = None


class MovementResponse(BaseModel):
    id_mouvement: int
    id_produit: int
    id_utilisateur: Optional[int] = None
    type: str
    quantite: int
    date_mouvement: datetime
    commentaire: Optional[str] = None

    class Config:
        from_attributes = True