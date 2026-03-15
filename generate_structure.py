import os

# Définition de la structure
base_dir = "app"
structure = {
    "": ["__init__.py", "main.py", "config.py"],
    "core": ["__init__.py", "security.py", "database.py", "exceptions.py"],
    "models": ["__init__.py", "user.py", "product.py", "movement.py"],
    "schemas": ["__init__.py", "user.py", "product.py", "ai_response.py"],
    "services": ["__init__.py", "auth_service.py", "product_service.py", "inventory_service.py", "ai_service.py"],
    "api": ["__init__.py", "deps.py", "router.py"],
    "api/endpoints": ["__init__.py", "auth.py", "products.py", "inventory.py", "ai.py"],
    "utils": ["__init__.py", "llm_client.py"]
}

def create_structure():
    print(f"🚀 Création de l'architecture StockIT dans le dossier '{base_dir}'...")
    
    for folder, files in structure.items():
        # Créer le dossier
        folder_path = os.path.join(base_dir, folder) if folder else base_dir
        os.makedirs(folder_path, exist_ok=True)
        print(f"📁 Dossier créé : {folder_path}")
        
        # Créer les fichiers
        for file in files:
            file_path = os.path.join(folder_path, file)
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    # Ajouter un commentaire par défaut
                    f.write(f"# Fichier : {file}\n# Module : {folder if folder else 'root'}\n# TODO: Implémenter la logique ici\n")
                print(f"   📄 Fichier créé : {file}")
            else:
                print(f"   ⚠️  Fichier existe déjà : {file}")

    # Création du fichier .env exemple
    with open(".env", "w") as f:
        f.write("""DATABASE_URL=postgresql://postgres:votre_mot_de_passe@localhost:5432/stockit_db
SECRET_KEY=votre_cle_secrete_tres_longue_et_aleatoire
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OLLAMA_URL=http://localhost:11434/api/generate
""")
    print("🔑 Fichier .env créé (à configurer)")
    print("✅ Structure générée avec succès !")

if __name__ == "__main__":
    create_structure()