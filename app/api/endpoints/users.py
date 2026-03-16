from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import Utilisateur
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(Utilisateur).all()


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if payload.role is not None:
        user.role = payload.role

    if payload.actif is not None:
        user.actif = payload.actif

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé avec succès"}