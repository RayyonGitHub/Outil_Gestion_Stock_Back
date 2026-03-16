# ai_service.py
from app.utils.llm_client import OllamaClient
import re
import json
from sqlalchemy.future import select
from app.models.product import Product
from sqlalchemy.ext.asyncio import AsyncSession

# --- fonction pour extraire le JSON de la réponse IA ---
def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)  # prend tout ce qui est entre { et }
    if match:
        try:
            return json.loads(match.group())
        except Exception as e:
            return {"error": "Impossible de parser le JSON extrait", "details": str(e)}
    else:
        return {"error": "Aucun JSON détecté dans la réponse"}

# --- service IA ---
class AIService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.ollama = OllamaClient()  # wrapper HTTP vers Ollama

    async def get_stock_recommendations(self, user_id: int):
        # 1️⃣ Récupérer les produits dont le stock est inférieur au seuil
        result = await self.db.execute(select(Product).where(Product.current_stock < Product.min_threshold))
        low_stock_products = [p.__dict__ for p in result.scalars().all()]

        # Si aucun produit à faible stock, on retourne un message simple
        if not low_stock_products:
            return {"analysis": "Tous les stocks sont suffisants", "recommendations": []}

        # 2️⃣ Construction du contexte pour l'IA
        context_data = json.dumps(low_stock_products, ensure_ascii=False)

        prompt = f"""
        Tu es un expert en gestion de stock.
        Voici l'état actuel du stock (format JSON) : {context_data}

        Analyse les données et propose 3 recommandations concrètes pour réapprovisionner.
        Réponds UNIQUEMENT au format JSON suivant :
        {{
            "analysis": "Court résumé de la situation",
            "recommendations": ["Action 1", "Action 2", "Action 3"]
        }}
        """

       # 3️⃣ Appel à Ollama avec gestion des erreurs
        try:
            response_text = await self.ollama.generate(prompt=prompt, model="llama3:latest")
        except Exception as e:
            # Si Ollama n'est pas disponible ou répond mal
            return {
                "error": "Impossible de contacter Ollama",
                "details": str(e)
            }
        # 4️⃣ Extraction et parsing du JSON
        result = extract_json(response_text)
        return result