from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    reference: str
    designation: str
    categorie: str
    marque: Optional[str] = None
    quantite: int = 0
    seuil_min: int = 0
    prix_achat: float
    prix_vente: float

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id_produit: int
    date_creation: datetime
    
    class Config:
        from_attributes = True