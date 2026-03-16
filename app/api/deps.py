from fastapi import Header, HTTPException, status
from app.core.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_roles(*allowed_roles):
    def checker(x_user_role: str = Header(default=None)):
        if x_user_role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Rôle utilisateur manquant"
            )

        if x_user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès interdit pour ce rôle"
            )

        return x_user_role

    return checker