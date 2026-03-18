# backend/app/services/ai_service.py
from app.utils.llm_client import OllamaClient
import re
import json
import unicodedata
from sqlalchemy import text, or_
from sqlalchemy.orm import Session
from app.models.product import Produit
from app.models.movement import MouvementStock, MouvementType


def extract_json(text_value: str) -> dict:
    if not text_value:
        return {}

    clean_text = re.sub(r"```json\s*", "", text_value)
    clean_text = re.sub(r"```\s*", "", clean_text)
    match = re.search(r"\{[\s\S]*\}", clean_text)

    if not match:
        return {}

    try:
        return json.loads(match.group())
    except Exception:
        return {}


def normalize_text(value: str) -> str:
    """
    Supprime les accents, trim, met en minuscules.
    Exemple :
    - 'Entrée' -> 'entree'
    - 'Réf-PC-01' -> 'ref-pc-01'
    """
    if not value:
        return ""

    value = value.strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value.lower().strip()


def normalize_movement_type(raw_type: str) -> str | None:
    """
    Convertit les variantes renvoyées par l'IA
    en valeurs compatibles avec MouvementType.
    """
    normalized = normalize_text(raw_type).upper()

    mapping = {
        "ENTREE": MouvementType.ENTREE.value,
        "AJOUT": MouvementType.ENTREE.value,
        "IN": MouvementType.ENTREE.value,
        "REAPPRO": MouvementType.ENTREE.value,
        "REAPPROVISIONNEMENT": MouvementType.ENTREE.value,

        "SORTIE": MouvementType.SORTIE.value,
        "RETRAIT": MouvementType.SORTIE.value,
        "VENTE": MouvementType.SORTIE.value,
        "VENDRE": MouvementType.SORTIE.value,
        "OUT": MouvementType.SORTIE.value,

        "AJUSTEMENT": MouvementType.AJUSTEMENT.value,
        "SUPPRESSION": MouvementType.SUPPRESSION.value,
    }

    if normalized in mapping:
        return mapping[normalized]

    if "ENTREE" in normalized or "AJOUT" in normalized or "REAPPRO" in normalized:
        return MouvementType.ENTREE.value

    if "SORTIE" in normalized or "RETRAIT" in normalized or "VENTE" in normalized or "VEND" in normalized:
        return MouvementType.SORTIE.value

    if "AJUST" in normalized:
        return MouvementType.AJUSTEMENT.value

    if "SUPPR" in normalized:
        return MouvementType.SUPPRESSION.value

    return None


class AIService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.ollama = OllamaClient()

    def _get_computed_alerts(self):
        query = text("""
            SELECT designation, quantite, seuil_min
            FROM produits
            ORDER BY designation ASC
        """)
        rows = self.db.execute(query).fetchall()

        alerts = []
        recommendations = []

        for row in rows:
            if row.quantite <= row.seuil_min:
                label = "RUPTURE" if row.quantite == 0 else "STOCK BAS"
                alerts.append(
                    f"{label} : {row.designation} ({row.quantite} restants / Seuil: {row.seuil_min})"
                )
                recommendations.append(f"Réapprovisionner {row.designation}")

        return alerts, recommendations

    def _find_product(self, target: str) -> Produit | None:
        """
        Priorité de recherche :
        1. référence exacte
        2. référence insensible à la casse
        3. référence partielle
        4. désignation / marque
        5. recherche par mots
        """
        if not target:
            return None

        target = target.strip()
        target_norm = normalize_text(target)

        # 1) Référence exacte stricte
        produit = self.db.query(Produit).filter(Produit.reference == target).first()
        if produit:
            return produit

        # 2) Référence exacte insensible à la casse
        produit = self.db.query(Produit).filter(Produit.reference.ilike(target)).first()
        if produit:
            return produit

        # 3) Référence partielle
        produits = self.db.query(Produit).filter(
            Produit.reference.ilike(f"%{target}%")
        ).all()
        if produits:
            for produit in produits:
                if normalize_text(produit.reference or "") == target_norm:
                    return produit
            return produits[0]

        # 4) Désignation ou marque partielles
        produits = self.db.query(Produit).filter(
            or_(
                Produit.designation.ilike(f"%{target}%"),
                Produit.marque.ilike(f"%{target}%")
            )
        ).all()
        if produits:
            for produit in produits:
                if normalize_text(produit.designation or "") == target_norm:
                    return produit
                if normalize_text(produit.marque or "") == target_norm:
                    return produit
            return produits[0]

        # 5) Recherche par mots
        words = [w for w in target.split() if w.strip()]
        if not words:
            return None

        filters = []
        for word in words:
            filters.append(Produit.reference.ilike(f"%{word}%"))
            filters.append(Produit.designation.ilike(f"%{word}%"))
            filters.append(Produit.marque.ilike(f"%{word}%"))

        produits = self.db.query(Produit).filter(or_(*filters)).all()
        if produits:
            return produits[0]

        return None

    def _format_product_stock_response(self, produit: Produit) -> str:
        if produit.quantite == 0:
            statut = "Le produit est en rupture."
        elif produit.quantite <= produit.seuil_min:
            statut = "Le stock est sous surveillance car il a atteint ou dépassé le seuil d'alerte."
        else:
            statut = "Le stock est actuellement au-dessus du seuil d'alerte."

        marque_info = f", marque {produit.marque}" if produit.marque else ""

        return (
            f"Il reste {produit.quantite} unité(s) de {produit.designation}"
            f" (réf: {produit.reference}{marque_info}). "
            f"Le seuil d'alerte est fixé à {produit.seuil_min}. "
            f"{statut}"
        )

    def _build_stock_analysis_response(self) -> str:
        produits = self.db.query(Produit).order_by(Produit.designation.asc()).all()

        if not produits:
            return "Aucun produit n'est enregistré dans le stock pour le moment."

        critiques = []
        vigilance = []

        for produit in produits:
            if produit.quantite == 0:
                critiques.append(
                    f"- {produit.designation} (réf: {produit.reference}) : rupture totale, seuil {produit.seuil_min}."
                )
            elif produit.quantite <= produit.seuil_min:
                vigilance.append(
                    f"- {produit.designation} (réf: {produit.reference}) : {produit.quantite} restant(s), seuil {produit.seuil_min}."
                )

        if not critiques and not vigilance:
            return (
                "Bilan critique : aucun produit n'est actuellement en rupture ou en stock bas. "
                "Aucun réapprovisionnement urgent n'est nécessaire."
            )

        response_parts = ["Bilan critique du stock :"]

        if critiques:
            response_parts.append("\nProduits en rupture :")
            response_parts.extend(critiques)

        if vigilance:
            response_parts.append("\nProduits à surveiller :")
            response_parts.extend(vigilance)

        response_parts.append(
            "\nConseil : lancer un réapprovisionnement prioritaire pour les ruptures, "
            "puis anticiper les produits proches du seuil minimum."
        )

        return "\n".join(response_parts)

    async def _detect_intent_and_action(self, user_message: str) -> dict:
        decision_prompt = f"""
Analyse le message utilisateur suivant :
"{user_message}"

Tu dois répondre uniquement en JSON.

Détermine :
- l'intention : "EXECUTE_ACTION", "QUERY_STOCK", "ANALYZE_STOCK" ou "UNKNOWN"
- si nécessaire une action avec :
  - "type" : "ENTREE", "SORTIE", "AJUSTEMENT" ou "SUPPRESSION"
  - "target" : référence, désignation ou marque du produit
  - "qty" : nombre entier si une quantité est présente

Règles :
- "vendre", "sortie", "retirer" => SORTIE
- "ajouter", "entrée", "réapprovisionner" => ENTREE
- une demande de consultation de stock ou de seuil => QUERY_STOCK
- une demande de bilan global, d'analyse, de conseil, de risque de manque => ANALYZE_STOCK

Exemples :
- "Ajoute 5 REF001" => EXECUTE_ACTION
- "Je viens de vendre 2 unités de PC Dell" => EXECUTE_ACTION
- "Dis-moi exactement ce qu'il reste en stock pour REF001 et quel est son seuil d'alerte" => QUERY_STOCK
- "Fais-moi un bilan critique du stock" => ANALYZE_STOCK

Format attendu :
{{
  "intent": "EXECUTE_ACTION" ou "QUERY_STOCK" ou "ANALYZE_STOCK" ou "UNKNOWN",
  "action": {{
    "type": "ENTREE" ou "SORTIE" ou "AJUSTEMENT" ou "SUPPRESSION",
    "target": "reference, designation ou marque du produit",
    "qty": 0
  }}
}}
"""
        resp = await self.ollama.generate(prompt=decision_prompt)
        return extract_json(resp)

    async def chat_with_data(self, user_message: str):
        try:
            decision = await self._detect_intent_and_action(user_message)
            intent = decision.get("intent", "UNKNOWN")
            action = decision.get("action", {}) if isinstance(decision.get("action"), dict) else {}

            print("--- DEBUG IA ---")
            print(f"Message: {user_message}")
            print(f"Intention détectée: {intent}")
            print(f"Action extraite: {action}")

            # =========================
            # 1) WRITE : EXECUTE_ACTION
            # =========================
            if intent == "EXECUTE_ACTION":
                target = action.get("target")
                qty = action.get("qty", 0)
                raw_type = action.get("type", "ENTREE")
                mvt_type = normalize_movement_type(raw_type)

                try:
                    qty = int(qty)
                except (TypeError, ValueError):
                    qty = 0

                if not target or qty <= 0:
                    return {
                        "reply": "ERREUR : quantité ou produit invalide."
                    }

                if not mvt_type:
                    return {
                        "reply": f"ERREUR : type de mouvement non reconnu ('{raw_type}')."
                    }

                produit = self._find_product(target)

                if not produit:
                    return {
                        "reply": f"ERREUR : produit introuvable ('{target}')."
                    }

                old_qty = produit.quantite

                if mvt_type == MouvementType.ENTREE.value:
                    produit.quantite += qty
                elif mvt_type == MouvementType.SORTIE.value:
                    produit.quantite = max(0, produit.quantite - qty)
                elif mvt_type == MouvementType.AJUSTEMENT.value:
                    produit.quantite = qty
                elif mvt_type == MouvementType.SUPPRESSION.value:
                    produit.quantite = 0

                new_mouvement = MouvementStock(
                    id_produit=produit.id_produit,
                    type=MouvementType(mvt_type),
                    quantite=qty,
                    commentaire=f"IA Order: {user_message}",
                    id_utilisateur=1
                )

                self.db.add(new_mouvement)
                self.db.commit()
                self.db.refresh(produit)
                self.db.refresh(new_mouvement)

                return {
                    "reply": (
                        f"C'est fait : le stock de {produit.designation} "
                        f"(réf: {produit.reference}) est passé de {old_qty} à {produit.quantite}. "
                        f"Le mouvement {mvt_type} de {qty} unité(s) a bien été enregistré."
                    )
                }

            # ======================
            # 2) READ : QUERY_STOCK
            # ======================
            if intent == "QUERY_STOCK":
                target = action.get("target")

                # Si l'IA n'a pas bien extrait la cible, on tente une récupération simple
                if not target:
                    # tentative basique : enlever quelques expressions communes
                    target = user_message
                    target = re.sub(
                        r"(?i)(dis-moi|dis moi|exactement|ce qu'il reste|ce qu’il reste|en stock|pour le produit|quel est|quelle est|son seuil d'alerte|son seuil d’alerte|le seuil d'alerte|le seuil d’alerte)",
                        " ",
                        target
                    )
                    target = re.sub(r"\s+", " ", target).strip(" ?.:;,")

                produit = self._find_product(target)

                if not produit:
                    return {
                        "reply": f"ERREUR : aucun produit n'a été trouvé pour '{target}'."
                    }

                return {
                    "reply": self._format_product_stock_response(produit)
                }

            # ============================
            # 3) CONSEIL : ANALYZE_STOCK
            # ============================
            if intent == "ANALYZE_STOCK":
                return {
                    "reply": self._build_stock_analysis_response()
                }

            # ============================
            # 4) FALLBACK
            # ============================
            return {
                "reply": (
                    "La demande a été reçue, mais l'intention n'a pas été reconnue clairement. "
                    "Essaie par exemple : 'Ajoute 5 REF001', "
                    "'Dis-moi le stock de REF001', "
                    "ou 'Fais-moi un bilan critique du stock'."
                )
            }

        except Exception as e:
            self.db.rollback()
            print(f"CRASH SERVICE: {str(e)}")
            return {
                "reply": "Erreur technique lors de l'action."
            }

    async def get_stock_recommendations(self, user_id: int):
        try:
            alerts, recommands = self._get_computed_alerts()
            return {
                "synthese_executive": "Analyse du stock critique.",
                "alertes_critiques": alerts,
                "plan_reapprovisionnement": recommands
            }
        except Exception as e:
            self.db.rollback()
            print(f"CRASH RECOMMENDATIONS: {str(e)}")
            return {
                "synthese_executive": "Erreur lors de l'analyse du stock.",
                "alertes_critiques": [],
                "plan_reapprovisionnement": []
            }