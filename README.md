# StockIt - API de gestion de stock

StockIt est le backend FastAPI d'une application de gestion de stock. Il permet de gerer les produits, les utilisateurs, les roles, les mouvements d'inventaire et des recommandations de stock assistees par IA via Ollama.

Le projet complet est decoupe en deux depots:

- Backend: `Outil_Gestion_Stock_Back`
- Frontend: `Outil_Gestion_Stock_Front`

Ce depot correspond a l'API. Le frontend React/Vite consomme cette API et tourne par defaut sur `http://localhost:5173`, deja autorise dans la configuration CORS.

## Fonctionnalites

- Authentification par identifiant et mot de passe.
- Gestion des roles: `Administrateur`, `Gestionnaire`, `Vendeur`.
- CRUD des produits avec reference unique, categorie, marque, quantite, seuil minimum et prix.
- Gestion des utilisateurs et activation/desactivation de comptes.
- Historique des mouvements de stock: `ENTREE`, `SORTIE`, `AJUSTEMENT`, `SUPPRESSION`.
- Alertes de stock bas et rupture via les seuils minimums.
- Assistant IA connecte aux donnees de stock avec Ollama.
- Base SQLite prete a l'emploi pour le developpement local.

## Stack technique

- Python 3.10+
- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite
- Pydantic
- Passlib + bcrypt
- HTTPX
- Ollama pour les fonctionnalites IA

## Structure du projet

```text
.
+-- app/
|   +-- api/
|   |   +-- endpoints/        # Routes FastAPI
|   |   +-- deps.py           # Authentification et roles
|   |   +-- router.py         # Routeur principal
|   +-- core/
|   |   +-- database.py       # Session SQLAlchemy et moteur SQLite
|   |   +-- exceptions.py
|   |   +-- security.py
|   +-- models/               # Modeles SQLAlchemy
|   +-- schemas/              # Schemas Pydantic
|   +-- services/             # Logique metier et IA
|   +-- utils/                # Client Ollama
|   +-- config.py
|   +-- main.py               # Point d'entree FastAPI
+-- database/
|   +-- bdd.sql               # Script SQL PostgreSQL de reference
+-- fix_db.py                 # Script de correction ponctuelle des mouvements
+-- seed.py                   # Creation des tables et comptes de demo
+-- seed_test.py              # Donnees de test produits + mouvements
+-- requirements.txt
+-- stockit.db                # Base SQLite locale
```

## Prerequis

- Python 3.10 ou plus recent
- `pip`
- Ollama, uniquement si vous utilisez les routes IA

Pour verifier Python:

```bash
python --version
```

## Installation

Clonez le projet puis installez les dependances dans un environnement virtuel.

```bash
git clone <url-du-repo>
cd Outil_Gestion_Stock_Back

python -m venv .venv
```

Sous Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Sous macOS/Linux:

```bash
source .venv/bin/activate
```

Installez les dependances:

```bash
pip install -r requirements.txt
```

## Initialisation de la base de donnees

Le backend utilise actuellement SQLite via le fichier `stockit.db`.

Pour creer les tables et ajouter les comptes de demonstration:

```bash
python seed.py
```

Pour ajouter des produits et mouvements de test:

```bash
python seed_test.py
```

Comptes crees par `seed.py`:

| Identifiant | Mot de passe | Role |
| --- | --- | --- |
| `admin` | `password123` | `Administrateur` |
| `gestionnaire` | `password123` | `Gestionnaire` |
| `vendeur` | `password123` | `Vendeur` |

## Lancement du serveur

Demarrez l'API en mode developpement:

```bash
uvicorn app.main:app --reload
```

L'API est disponible sur:

```text
http://localhost:8000
```

Documentation interactive:

```text
http://localhost:8000/docs
```

Documentation ReDoc:

```text
http://localhost:8000/redoc
```

## Lancement du projet complet

Le projet complet se lance avec deux terminaux.

Terminal 1 - backend:

```bash
cd Outil_Gestion_Stock_Back
python seed.py
uvicorn app.main:app --reload
```

Terminal 2 - frontend:

```bash
cd Outil_Gestion_Stock_Front
npm install
npm run dev
```

URLs utiles:

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:5173` |
| Backend API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |

## Configuration

Le projet contient une configuration dans `app/config.py` pour:

- `DATABASE_URL`
- `OLLAMA_HOST`
- `OLLAMA_MODEL`
- `SECRET_KEY`

Note technique: l'implementation active dans `app/core/database.py` force actuellement SQLite avec `sqlite:///./stockit.db`. Si vous souhaitez passer sur PostgreSQL ou utiliser `DATABASE_URL`, il faudra raccorder `core/database.py` a la configuration centralisee.

Exemple de fichier `.env` possible:

```env
DATABASE_URL=sqlite:///./stockit.db
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3:latest
SECRET_KEY=change_me
```

## Routes principales

### Authentification

| Methode | Route | Description |
| --- | --- | --- |
| `POST` | `/auth/login` | Connexion utilisateur |
| `POST` | `/auth/reset-password` | Reinitialisation du mot de passe |

Exemple de connexion:

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password123"
```

### Produits

| Methode | Route | Roles | Description |
| --- | --- | --- | --- |
| `GET` | `/products/` | Tous roles connectes | Liste des produits |
| `POST` | `/products/` | Gestionnaire, Administrateur | Creation d'un produit |
| `PUT` | `/products/{product_id}` | Gestionnaire, Administrateur | Modification d'un produit |
| `DELETE` | `/products/{product_id}` | Gestionnaire, Administrateur | Suppression d'un produit |

### Utilisateurs

| Methode | Route | Roles | Description |
| --- | --- | --- | --- |
| `GET` | `/users/` | Administrateur | Liste des utilisateurs |
| `POST` | `/users/` | Public actuellement | Creation d'un utilisateur |
| `PUT` | `/users/{user_id}` | Administrateur | Modification d'un utilisateur |
| `DELETE` | `/users/{user_id}` | Administrateur | Suppression d'un utilisateur |

### Inventaire

| Methode | Route | Description |
| --- | --- | --- |
| `GET` | `/inventory/movements` | Liste des mouvements de stock |
| `POST` | `/inventory/movements` | Creation d'un mouvement |

### Intelligence artificielle

| Methode | Route | Description |
| --- | --- | --- |
| `GET` | `/ai/test` | Verification du module IA |
| `POST` | `/ai/chat` | Chat avec l'assistant stock |
| `GET` | `/ai/recommendations` | Recommandations de stock |

## Utilisation de l'IA avec Ollama

Les routes IA s'appuient sur Ollama en local. Installez Ollama, puis lancez un modele compatible:

```bash
ollama pull llama3
ollama serve
```

Exemples de demandes possibles via `/ai/chat`:

- `Ajoute 5 REF-FAST-001`
- `Je viens de vendre 2 unites de Vis M6`
- `Quel est le stock de REF-FAST-001 ?`
- `Fais-moi un bilan critique du stock`

Les roles sont pris en compte:

- `Vendeur`: consultation uniquement.
- `Gestionnaire` et `Administrateur`: consultation et actions sur le stock.

## Exemple de payload produit

```json
{
  "reference": "REF-PC-001",
  "designation": "Ordinateur portable Dell",
  "categorie": "Informatique",
  "marque": "Dell",
  "quantite": 12,
  "seuil_min": 3,
  "prix_achat": 650.0,
  "prix_vente": 899.0
}
```

## Verification rapide

Compilation Python des modules principaux:

```bash
python -m py_compile app/main.py app/api/router.py app/api/deps.py
```

Lancement manuel:

```bash
uvicorn app.main:app --reload
```

Puis ouvrez:

```text
http://localhost:8000/docs
```

## Notes de revue technique

- Le README documente le backend present dans ce depot. Le frontend est dans le depot separe `Outil_Gestion_Stock_Front`.
- `database/bdd.sql` decrit une base PostgreSQL de reference, tandis que le code lance actuellement SQLite.
- `app/config.py` prepare des variables d'environnement, mais `app/core/database.py` utilise encore une URL SQLite codee en dur.
- Les tokens d'authentification sont actuellement encodes en base64. Pour une mise en production, il est recommande de passer a de vrais JWT signes avec expiration.
- Les fichiers `product_service.py` et `inventory_service.py` sont encore des squelettes.
- La creation utilisateur via `POST /users/` n'impose pas encore de role administrateur.
- Le frontend appelle actuellement l'API avec des URLs locales codees en dur; une variable `VITE_API_URL` serait preferable pour un deploiement public.

## Roadmap suggeree

- Brancher `DATABASE_URL` dans `core/database.py`.
- Remplacer le token base64 par un JWT signe.
- Ajouter des tests automatises avec `pytest`.
- Ajouter Alembic pour les migrations de base de donnees.
- Finaliser les services metier produits et inventaire.
- Harmoniser SQLite et PostgreSQL selon la cible de deploiement.

## Licence

Projet academique / interne. Ajoutez une licence explicite (`MIT`, `Apache-2.0`, proprietaire, etc.) avant publication publique sur GitHub.
