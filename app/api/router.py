from fastapi import APIRouter
# C'EST ICI QUE ÇA SE PASSE : on importe auth ET products
from app.api.endpoints import auth, products,ai



api_router = APIRouter()

api_router.include_router(ai.router)

api_router.include_router(auth.router, prefix="/auth", tags=["Authentification"])
api_router.include_router(products.router, prefix="/products", tags=["Produits"])