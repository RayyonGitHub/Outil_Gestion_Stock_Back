import os
from dotenv import load_dotenv

load_dotenv()

# --- BASE DE DONNÉES (Changement ici) ---
# Pour SQLite, on pointe vers un fichier local. 
# 'file:memory:?cache=shared' permet de tester en mémoire vive (perdu au redémarrage)
# Sinon, utilisez un chemin fichier : 'sqlite+aiosqlite:///./stockit.db'
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./stockit.db")

# --- IA OLLAMA (Pas de changement logique) ---
# L'URL reste la même car Ollama tourne indépendamment de la BDD
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3") # Ou mistral, gemma, etc.

# --- SÉCURITÉ ---
SECRET_KEY = os.getenv("SECRET_KEY", "votre_cle_secrete_par_defaut_pour_dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30