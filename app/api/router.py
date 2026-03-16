from fastapi import APIRouter
from app.api.endpoints import auth, products, ai, users, inventory

api_router = APIRouter()

api_router.include_router(ai.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentification"])
api_router.include_router(products.router, prefix="/products", tags=["Produits"])
api_router.include_router(users.router, prefix="/users", tags=["Utilisateurs"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventaire"])