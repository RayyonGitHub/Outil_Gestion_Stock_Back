from app.core.database import SessionLocal, engine, Base
from passlib.context import CryptContext
from sqlalchemy import text

# Import vital : Il faut importer les modèles pour que SQLAlchemy les "voie" et les crée
from app.models.user import Utilisateur
from app.models.product import Produit
from app.models.movement import MouvementStock

print("🛠️ Création de la base de données complète...")
# 1. Ça crée TOUTES les tables (utilisateurs, produits, mouvements_stock)
Base.metadata.create_all(bind=engine)

# 2. Création de ta VUE d'inventaire (SQLAlchemy ne le fait pas auto, on passe une vraie requête SQL)
print("👁️ Création de la vue d'inventaire...")
with engine.connect() as conn:
    conn.execute(text("""
        CREATE VIEW IF NOT EXISTS vue_inventaire_statut AS
        SELECT 
            id_produit, reference, designation, categorie, marque, quantite, seuil_min, prix_vente,
            CASE 
                WHEN quantite = 0 THEN 'RUPTURE'
                WHEN quantite <= seuil_min THEN 'BAS'
                ELSE 'OK' 
            END AS statut
        FROM produits;
    """))
    conn.commit()

# 3. Injection des utilisateurs
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

users_to_create = [
    {"identifiant": "gestionnaire", "mot_de_passe": "password123", "role": "Gestionnaire"},
    {"identifiant": "vendeur", "mot_de_passe": "password123", "role": "Vendeur"},
    {"identifiant": "admin", "mot_de_passe": "password123", "role": "Administrateur"},
]

print("⏳ Injection des utilisateurs...")
for u in users_to_create:
    existing_user = db.query(Utilisateur).filter(Utilisateur.identifiant == u["identifiant"]).first()
    if not existing_user:
        hashed_password = pwd_context.hash(u["mot_de_passe"])
        nouveau = Utilisateur(
            identifiant=u["identifiant"], 
            mot_de_passe=hashed_password, 
            role=u["role"]
        )
        db.add(nouveau)
        print(f"➕ Utilisateur {u['identifiant']} ajouté.")
    else:
        print(f"⚠️ L'utilisateur {u['identifiant']} existe déjà.")

db.commit()
db.close()
print("✅ Base de données finale prête à l'emploi !")