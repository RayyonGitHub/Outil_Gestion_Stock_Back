import enum
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.core.database import Base

class MouvementType(str, enum.Enum):
    ENTREE = "ENTREE"
    SORTIE = "SORTIE"
    AJUSTEMENT = "AJUSTEMENT"
    SUPPRESSION = "SUPPRESSION"

class MouvementStock(Base):
    __tablename__ = "mouvements_stock"

    id_mouvement = Column(Integer, primary_key=True, index=True)
    id_produit = Column(Integer, ForeignKey("produits.id_produit", ondelete="CASCADE"), nullable=False, index=True)
    id_utilisateur = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="SET NULL"), nullable=True)
    type = Column(Enum(MouvementType), nullable=False, index=True)
    quantite = Column(Integer, nullable=False)
    date_mouvement = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    commentaire = Column(Text)