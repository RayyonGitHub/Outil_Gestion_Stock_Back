# backend/app/models/__init__.py

# On importe les classes depuis leurs fichiers respectifs
# Assurez-vous que les noms de fichiers (product, user, movement) correspondent bien à vos fichiers .py
from .user import Utilisateur  # ou User, selon votre fichier user.py
from .product import Produit   # ou Product, selon votre fichier product.py
from .movement import MouvementStock # ou Movement, selon votre fichier movement.py

# On les expose explicitement pour pouvoir faire : from app.models import Produit
__all__ = [
    "Utilisateur",
    "Produit",
    "MouvementStock"
]