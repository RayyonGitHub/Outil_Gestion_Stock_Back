from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.api.deps import get_db, require_roles
from app.models.user import Utilisateur
from app.schemas.user import UserResponse, UserUpdate, UserCreate

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    role: str = Depends(require_roles("Administrateur"))
):
    return db.query(Utilisateur).all()


@router.post("/", response_model=UserResponse)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(Utilisateur).filter(Utilisateur.identifiant == user_in.identifiant).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Cet identifiant existe déjà.")
    
    hashed_password = pwd_context.hash(user_in.mot_de_passe)
    
    new_user = Utilisateur(
        identifiant=user_in.identifiant,
        mot_de_passe=hashed_password,
        role=user_in.role,
        actif=user_in.actif
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    role: str = Depends(require_roles("Administrateur"))
):
    user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if payload.role is not None:
        user.role = payload.role

    if payload.actif is not None:
        user.actif = payload.actif
        
    if payload.mot_de_passe:
        user.mot_de_passe = pwd_context.hash(payload.mot_de_passe)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    role: str = Depends(require_roles("Administrateur"))
):
    user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé avec succès"}