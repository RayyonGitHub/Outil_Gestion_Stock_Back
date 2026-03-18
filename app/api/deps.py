# backend/app/api/deps.py
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import base64

from app.core.database import get_db
from app.models.user import Utilisateur 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Utilisateur:
    """
    Récupère l'utilisateur actuel depuis le token.
    """
    try:
        # Décodage du token base64
        decoded_token = base64.b64decode(token.encode()).decode()
        user_id_str, identifiant, role = decoded_token.split(":")
        user_id = int(user_id_str)
        
        user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == user_id).first()
        if user and user.actif:
            return user
    except Exception:
        pass
            
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou token expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_roles(*allowed_roles):
    """
    Dépendance pour vérifier les rôles (à utiliser en combinaison avec get_current_user)
    """
    def role_checker(current_user: Utilisateur = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for this role"
            )
        return current_user
    return role_checker