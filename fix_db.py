from sqlalchemy import text
from app.core.database import SessionLocal

def clean_database():
    db = SessionLocal()
    try:
        print("--- Début du nettoyage ---")
        
        # 1. Correction du 'É' en 'E' pour les entrées
        result = db.execute(text(
            "UPDATE mouvements_stock SET type = 'ENTREE' WHERE type = 'ENTRÉE'"
        ))
        print(f"Lignes corrigées (ENTRÉE -> ENTREE): {result.rowcount}")

        # 2. Correction pour les sorties (au cas où)
        result_out = db.execute(text(
            "UPDATE mouvements_stock SET type = 'SORTIE' WHERE type = 'SORTIE'"
        ))
        
        db.commit()
        print("✅ Base de données nettoyée avec succès !")
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors du nettoyage : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clean_database()