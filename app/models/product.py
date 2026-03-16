from sqlalchemy import Column, Integer, String, Numeric, DateTime, CheckConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class Produit(Base):
    __tablename__ = "produits"

    id_produit = Column(Integer, primary_key=True, index=True)
    reference = Column(String(30), unique=True, nullable=False, index=True)
    designation = Column(String(200), nullable=False, index=True)
    categorie = Column(String(50), nullable=False, index=True)
    marque = Column(String(100))
    quantite = Column(Integer, nullable=False, default=0)
    seuil_min = Column(Integer, nullable=False, default=0)
    prix_achat = Column(Numeric(10, 2), nullable=False)
    prix_vente = Column(Numeric(10, 2), nullable=False)

    date_creation = Column(DateTime(timezone=True), server_default=func.now())
    date_modification = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("quantite >= 0", name="check_quantite_positive"),
        CheckConstraint("prix_achat > 0", name="check_prix_achat_positif"),
        CheckConstraint("prix_vente > 0", name="check_prix_vente_positif"),
    )