from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, require_roles
from app.models.product import Produit
from app.schemas.product import ProductResponse, ProductCreate

router = APIRouter()


@router.get("/", response_model=List[ProductResponse])
def get_products(
    db: Session = Depends(get_db),
    role: str = Depends(require_roles("Gestionnaire", "Vendeur", "Administrateur"))
):
    return db.query(Produit).all()


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    role: str = Depends(require_roles("Gestionnaire"))
):
    db_product = db.query(Produit).filter(Produit.reference == product.reference).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Cette référence existe déjà.")

    nouveau = Produit(**product.model_dump())
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return nouveau


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductCreate,
    db: Session = Depends(get_db),
    role: str = Depends(require_roles("Gestionnaire"))
):
    db_product = db.query(Produit).filter(Produit.id_produit == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    for key, value in product_update.model_dump().items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    role: str = Depends(require_roles("Gestionnaire"))
):
    produit = db.query(Produit).filter(Produit.id_produit == product_id).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    db.delete(produit)
    db.commit()
    return {"message": "Produit supprimé"}