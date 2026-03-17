# backend/app/api/deps.py
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db  # Importe la fonction async get_db
from app.models.user import Utilisateur # Assurez-vous que le nom de la classe est correct

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# La dépendance get_db est maintenant asynchrone, on la réexporte simplement
# Les routes l'utiliseront avec : db: AsyncSession = Depends(get_db)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Utilisateur:
    """
    Récupère l'utilisateur actuel depuis le token JWT.
    (Implémentation simplifiée pour le test - à adapter avec votre vraie logique de vérification JWT)
    """
    # TODO : Implémenter la vérification réelle du token JWT ici
    # Pour l'instant, on simule une récupération basique ou on lève une erreur si pas implémenté
    
    # Exemple de simulation pour le test (à retirer en prod) :
    # Si le token est "test", on renvoie l'user ID 1
    if token == "test_token":
        result = await db.execute(select(Utilisateur).where(Utilisateur.id_utilisateur == 1))
        user = result.scalar_one_or_none()
        if user:
            return user
            
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_roles(*allowed_roles):
    """
    Dépendance pour vérifier les rôles (à utiliser en combinaison avec get_current_user)
    """
    async def role_checker(current_user: Utilisateur = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for this role"
            )
        return current_user
    return role_checker