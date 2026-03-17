# backend/app/services/ai_service.py
from app.utils.llm_client import OllamaClient
import re
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

# Import des modèles depuis le paquet global (grâce à __init__.py)
from app.models import Produit, MouvementStock


def extract_json(text: str) -> dict:
    """
    Extrait et répare le JSON même si l'IA a fait des erreurs de formatage.
    Stratégie multi-niveaux de réparation pour les LLM locaux.
    """
    if not text:
        return {"error": "Réponse vide de l'IA"}

    # 1. Nettoyer les balises markdown
    clean_text = re.sub(r"```json\s*", "", text)
    clean_text = re.sub(r"```\s*", "", clean_text)

    # 2. Extraire le bloc entre accolades (plus robuste avec [\s\S]* au lieu de .*)
    match = re.search(r"\{[\s\S]*\}", clean_text)
    if not match:
        return {
            "mode": "texte_libre",
            "message": "Aucune structure JSON trouvée.",
            "analyse_libre": text
        }
    
    json_str = match.group()

    # 3. ÉTAPE 1 : Remplacer tous les guillemets courbes/spéciaux par des guillemets droits
    # Ceci résout la plupart des erreurs de guillemets générées par les LLMs
    replacements = {
        '\u201c': '"',  # " (LEFT DOUBLE QUOTATION MARK)
        '\u201d': '"',  # " (RIGHT DOUBLE QUOTATION MARK)
        '\u2018': '"',  # ' (LEFT SINGLE QUOTATION MARK)
        '\u2019': '"',  # ' (RIGHT SINGLE QUOTATION MARK)
        '\u300c': '"',  # 「 (CJK LEFT CORNER BRACKET)
        '\u300d': '"',  # 」 (CJK RIGHT CORNER BRACKET)
        '\u00ab': '"',  # « (LEFT POINTING DOUBLE ANGLE QUOTATION MARK)
        '\u00bb': '"',  # » (RIGHT POINTING DOUBLE ANGLE QUOTATION MARK)
    }
    for special_char, normal_char in replacements.items():
        json_str = json_str.replace(special_char, normal_char)
    
    # 4. TENTATIVE DIRECTE
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # 5. ÉTAPE 2 : Fonction pour échapper les sauts de ligne dans les strings
    def fix_newlines_in_json(text):
        """Échappe les sauts de ligne non échappés à l'intérieur des strings JSON"""
        result = []
        in_string = False
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # Gérer les caractères d'échappement
            if char == '\\' and i + 1 < len(text):
                result.append(char)
                result.append(text[i + 1])
                i += 2
                continue
            
            # Détecter les limites des strings
            if char == '"':
                result.append(char)
                in_string = not in_string
                i += 1
                continue
            
            # À l'intérieur d'une string, échapper les newlines
            if in_string:
                if char == '\n':
                    result.append('\\n')
                    i += 1
                    continue
                elif char == '\r':
                    result.append('\\r')
                    i += 1
                    continue
                elif char == '\t':
                    result.append('\\t')
                    i += 1
                    continue
            
            result.append(char)
            i += 1
        
        return ''.join(result)
    
    try:
        fixed_json = fix_newlines_in_json(json_str)
        return json.loads(fixed_json)
    except json.JSONDecodeError:
        pass
    
    # 6. ÉTAPE 3 : Nettoyer les espaces inutiles autour des caractères spéciaux
    try:
        # Supprimer les espaces avant/après : et ,
        cleaned = re.sub(r'\s*:\s*', ':', json_str)
        cleaned = re.sub(r'\s*,\s*', ',', cleaned)
        
        fixed_again = fix_newlines_in_json(cleaned)
        return json.loads(fixed_again)
    except json.JSONDecodeError:
        pass
    
    # 7. ÉTAPE 4 : Approche extrême - utiliser ast.literal_eval pour Python
    try:
        python_str = json_str.replace('true', 'True').replace('false', 'False').replace('null', 'None')
        import ast
        result = ast.literal_eval(python_str)
        # Reconvertir en JSON valide
        return json.loads(json.dumps(result))
    except Exception:
        pass
    
    # 8. Échec : retourner l'erreur
    return {
        "error": "JSON malformé (même après réparation)",
        "details": "Impossible de réparer le JSON malgré plusieurs tentatives",
        "extrait_problematic": json_str[:300]
    }


class AIService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.ollama = OllamaClient()

    async def get_stock_recommendations(self, user_id: int):
        """
        Analyse les stocks critiques et génère des recommandations basées sur l'historique des 90 derniers jours.
        """
        ninety_days_ago = datetime.now() - timedelta(days=90)

        # Requête SQL optimisée pour récupérer les produits en alerte + leur historique
        query = text("""
            SELECT 
                p.id_produit,
                p.reference,
                p.designation,
                p.categorie,
                p.quantite as stock_actuel,
                p.seuil_min,
                p.prix_achat,
                p.prix_vente,
                COALESCE(SUM(CASE 
                    WHEN m.type = 'SORTIE' AND m.date_mouvement >= :date_start THEN m.quantite 
                    ELSE 0 
                END), 0) as total_sorties_90j,
                COALESCE(SUM(CASE 
                    WHEN m.type = 'ENTREE' AND m.date_mouvement >= :date_start THEN m.quantite 
                    ELSE 0 
                END), 0) as total_entrees_90j
            FROM produits p
            LEFT JOIN mouvements_stock m ON p.id_produit = m.id_produit
            WHERE p.quantite <= p.seuil_min
            GROUP BY p.id_produit, p.reference, p.designation, p.categorie, p.quantite, p.seuil_min, p.prix_achat, p.prix_vente
            ORDER BY stock_actuel ASC;
        """)

        result = await self.db.execute(query, {"date_start": ninety_days_ago})
        rows = result.fetchall()

        # Cas où tout va bien
        if not rows:
            return {
                "status": "OK",
                "message": "Aucun produit en alerte. Tous les stocks sont au-dessus des seuils.",
                "synthese_executive": "Le stock est sain. Aucune action immédiate requise."
            }

        # Préparation des données pour le contexte de l'IA
        products_data = []
        for row in rows:
            total_sorties = row.total_sorties_90j or 0
            vitesse_vente_jour = total_sorties / 90.0 if total_sorties > 0 else 0.0
            
            # Calcul des jours avant rupture
            if vitesse_vente_jour > 0:
                jours_avant_rupture = round(row.stock_actuel / vitesse_vente_jour, 1)
                # Tendance : forte si on vend plus de 10% du seuil par jour
                tendance = "FORTE" if vitesse_vente_jour > (row.seuil_min / 10) else "FAIBLE"
            else:
                jours_avant_rupture = 999  # Stock dormant
                tendance = "NULLE"

            products_data.append({
                "reference": row.reference,
                "nom": row.designation,
                "categorie": row.categorie,
                "stock_actuel": row.stock_actuel,
                "seuil_min": row.seuil_min,
                "prix_vente": float(row.prix_vente),
                "historique_90j": {
                    "total_sorties": total_sorties,
                    "vente_moyenne_jour": round(vitesse_vente_jour, 2),
                    "jours_estimes_avant_rupture": jours_avant_rupture,
                    "tendance": tendance
                }
            })

        context_json = json.dumps(products_data, ensure_ascii=False)

        # Prompt Engineering renforcé pour obtenir du JSON pur
        prompt = f"""
        RÔLE : Tu es une API JSON stricte de Supply Chain. Tu ne dois JAMAIS parler en langage naturel.
        TÂCHE : Analyser les données de stock critiques ci-dessous et produire un JSON de recommandation.
        
        DONNÉES (Historique 90 jours) :
        {context_json}

        INSTRUCTIONS D'ANALYSE :
        1. URGENCES : Produits avec 'jours_estimes_avant_rupture' < 7 jours.
        2. QUANTITÉS : Utilise la formule : Qty = (vitesse_vente_jour * 15) - stock_actuel.
        3. ANOMALIES : Si vitesse_vente_jour == 0 mais stock bas -> Suggère un audit (produit mort).

        CONTRAINTES DE FORMAT (ABSOLU) :
        - Ta réponse doit commencer IMMÉDIATEMENT par '{{' et finir par '}}'.
        - AUCUN texte avant. AUCUN texte après.
        - AUCUNE balise markdown (pas de ```json).
        - Si erreur, renvoie {{ "error": "Description" }}.

        STRUCTURE JSON ATTENDUE :
        {{
            "synthese_executive": "Phrase d'accroche percutante sur l'état global.",
            "alertes_critiques": ["Liste des références en rupture < 3 jours"],
            "plan_reapprovisionnement": [
                {{
                    "reference": "REF...",
                    "nom": "Nom du produit",
                    "statut": "URGENT" | "STANDARD" | "SURPLUS",
                    "quantite_a_commander": 50,
                    "justification_data": "Basé sur une vente de X/jour, rupture dans Y jours.",
                    "priorite_metier": 1
                }}
            ],
            "recommandations_strategiques": ["Conseil global basé sur les tendances"]
        }}
        """

        try:
            # Appel à Ollama
            response = await self.ollama.generate(prompt=prompt, model="llama3:latest")
            
            # Extraction robuste du JSON
            return extract_json(response)
            
        except Exception as e:
            return {
                "error": "Échec de la connexion ou du traitement IA",
                "details": str(e)
            }