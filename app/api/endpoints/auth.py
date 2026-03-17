from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import Utilisateur

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ResetPasswordRequest(BaseModel):
    identifiant: str
    nouveau_mot_de_passe: str
    confirmation_mot_de_passe: str

@router.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    
    # 1. On cherche l'utilisateur dans PostgreSQL
    user = db.query(Utilisateur).filter(Utilisateur.identifiant == form_data.username).first()
    
    # 2. On vérifie qu'il existe ET que le mot de passe (hashé) correspond
    if not user or not pwd_context.verify(form_data.password, user.mot_de_passe):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
        )
        
    # 3. On vérifie s'il n'a pas été désactivé
    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé",
        )

    # 4. Succès ! On renvoie les infos (le token JWT sera implémenté plus tard)
    return {
        "access_token": f"vrai-jwt-token-pour-{user.identifiant}",
        "token_type": "bearer",
        "role": user.role
    }


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    # 1. Vérifier que les mots de passe correspondent
    if req.nouveau_mot_de_passe != req.confirmation_mot_de_passe:
        raise HTTPException(status_code=400, detail="Les mots de passe ne correspondent pas.")
        
    # 2. Chercher l'utilisateur
    user = db.query(Utilisateur).filter(Utilisateur.identifiant == req.identifiant).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Identifiant introuvable.")

    # 3. Mettre à jour avec le nouveau hash
    user.mot_de_passe = pwd_context.hash(req.nouveau_mot_de_passe)
    db.commit()
    
    return {"message": "Votre mot de passe a été mis à jour avec succès !"}