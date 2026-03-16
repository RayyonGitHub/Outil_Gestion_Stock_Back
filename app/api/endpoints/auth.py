from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.core.database import get_db
from app.models.user import Utilisateur

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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