from app.utils.llm_client import OllamaClient
import re
import json
from sqlalchemy import select
from app.models.product import Produit


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception as e:
            return {
                "error": "Impossible de parser le JSON extrait",
                "details": str(e)
            }
    return {"error": "Aucun JSON détecté dans la réponse"}


class AIService:
    def __init__(self, db_session):
        self.db = db_session
        self.ollama = OllamaClient()

    async def get_stock_recommendations(self, user_id: int):
        result = self.db.execute(
            select(Produit).where(Produit.quantite < Produit.seuil_min)
        )
        low_stock_products = result.scalars().all()

        data = [
            {
                "id_produit": p.id_produit,
                "reference": p.reference,
                "designation": p.designation,
                "categorie": p.categorie,
                "marque": p.marque,
                "quantite": p.quantite,
                "seuil_min": p.seuil_min,
                "prix_achat": float(p.prix_achat),
                "prix_vente": float(p.prix_vente),
            }
            for p in low_stock_products
        ]

        if not data:
            return {
                "analysis": "Tous les stocks sont suffisants",
                "recommendations": []
            }

        context_data = json.dumps(data, ensure_ascii=False)

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

        try:
            response_text = await self.ollama.generate(
                prompt=prompt,
                model="llama3:latest"
            )
        except Exception as e:
            return {
                "error": "Impossible de contacter Ollama",
                "details": str(e)
            }

        return extract_json(response_text)