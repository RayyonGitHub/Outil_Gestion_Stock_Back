import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class UserRole(str, enum.Enum):
    Gestionnaire = "Gestionnaire"
    Vendeur = "Vendeur"
    Administrateur = "Administrateur"

class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id_utilisateur = Column(Integer, primary_key=True, index=True)
    identifiant = Column(String(50), unique=True, nullable=False, index=True)
    mot_de_passe = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.Vendeur)
    actif = Column(Boolean, nullable=False, default=True)
    # Les triggers de date sont gérés automatiquement par SQLAlchemy !
    date_creation = Column(DateTime(timezone=True), server_default=func.now())
    date_modification = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())