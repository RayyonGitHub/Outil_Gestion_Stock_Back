# backend/seed_test.py
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert, select

# Imports de vos modèles (doivent correspondre à votre __init__.py)
from app.models import Produit, MouvementStock, Utilisateur
from app.core.database import Base  # Important pour créer les tables

# Configuration DB
DATABASE_URL = "sqlite+aiosqlite:///./stockit.db"

engine = create_async_engine(DATABASE_URL, echo=True) # echo=True pour voir les requêtes SQL (création des tables)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed_data():
    # 1️⃣ CRÉATION DES TABLES (ÉTAPE MANQUANTE)
    print("🏗️  Création des tables si elles n'existent pas...")
    async with engine.begin() as conn:
        # Cette ligne compare vos modèles Python (Base) avec la DB et crée ce qui manque
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables créées avec succès.")

    async with async_session() as session:
        print("🌱 Création des produits de test...")
        
        # Vérification si des produits existent déjà pour éviter les doublons
        stmt_check = select(Produit).where(Produit.reference == "REF-FAST-001")
        result_check = await session.execute(stmt_check)
        if result_check.scalar_one_or_none():
            print("⚠️  Les données de test existent déjà. Nettoyage en cours...")
            # Optionnel : Supprimer tout pour repartir à zéro
            # await session.execute(DELETE(MouvementStock))
            # await session.execute(DELETE(Produit))
            # await session.commit()
            return

        prod_a = Produit(
            reference="REF-FAST-001",
            designation="Vis M6 (Forte Rotation)",
            categorie="Quincaillerie",
            marque="FixIt",
            quantite=5,
            seuil_min=20,
            prix_achat=0.10,
            prix_vente=0.25
        )
        
        prod_b = Produit(
            reference="REF-SLOW-002",
            designation="Écrou Spécial (Faible Rotation)",
            categorie="Quincaillerie",
            marque="FixIt",
            quantite=2,
            seuil_min=10,
            prix_achat=1.50,
            prix_vente=3.00
        )

        prod_c = Produit(
            reference="REF-DEAD-003",
            designation="Adaptateur Obsolète",
            categorie="Électronique",
            marque="OldTech",
            quantite=5,
            seuil_min=15,
            prix_achat=10.00,
            prix_vente=25.00
        )

        session.add_all([prod_a, prod_b, prod_c])
        await session.commit()
        
        # Récupération des IDs
        stmt = select(Produit).where(Produit.reference.in_([
            "REF-FAST-001", "REF-SLOW-002", "REF-DEAD-003"
        ]))
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        if len(products) < 3:
            print("❌ Erreur : Impossible de récupérer les produits.")
            return

        p_fast, p_slow, p_dead = products[0], products[1], products[2]
        print(f"✅ Produits créés. IDs : {p_fast.id_produit}, {p_slow.id_produit}, {p_dead.id_produit}")

        # Création d'un utilisateur factice si nécessaire (pour les clés étrangères)
        # Vérifions si l'user ID 1 existe
        user_stmt = select(Utilisateur).where(Utilisateur.id_utilisateur == 1)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user:
            print("👤 Création d'un utilisateur de test (ID=1)...")
            fake_user = Utilisateur(
                identifiant="test_user",
                mot_de_passe="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4/62f3xYz5qZ5qZ5", # Hash factice pour test
                role="Administrateur"
            )
            session.add(fake_user)
            await session.commit()
            print("✅ Utilisateur test créé.")
        
        print("📅 Génération de l'historique des 90 derniers jours...")
        movements = []
        today = datetime.now()

        def create_move(pid, qte, days_ago, type_mov="SORTIE"):
            return {
                "id_produit": pid,
                "id_utilisateur": 1, 
                "type": type_mov,
                "quantite": qte,
                "date_mouvement": today - timedelta(days=days_ago)
            }

        # Historique Produit A (Forte vente)
        for i in range(90):
            for _ in range(5):
                movements.append(create_move(p_fast.id_produit, 1, i))

        # Historique Produit B (Vente lente)
        for i in range(0, 90, 10):
            movements.append(create_move(p_slow.id_produit, 1, i))
            
        if movements:
            try:
                await session.execute(insert(MouvementStock), movements)
                await session.commit()
                print(f"✅ {len(movements)} mouvements générés avec succès.")
            except Exception as e:
                print(f"❌ Erreur mouvements : {e}")
        else:
            print("⚠️ Aucun mouvement généré.")

if __name__ == "__main__":
    asyncio.run(seed_data())