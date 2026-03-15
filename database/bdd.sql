-- Création de la base de données
CREATE DATABASE stockit_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'fr_FR.UTF-8'
    LC_CTYPE = 'fr_FR.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

\c stockit_db; -- Connexion à la base

-- Extension pour les UUID si nécessaire (bonne pratique, bien que le DSL demande INTEGER)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Table : Utilisateurs
-- Contraintes : Role ENUM, Mot de passe hashé, Actif par défaut
CREATE TYPE user_role AS ENUM ('Gestionnaire', 'Vendeur', 'Administrateur');

CREATE TABLE utilisateurs (
    id_utilisateur SERIAL PRIMARY KEY,
    identifiant VARCHAR(50) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL, -- Doit contenir le hash bcrypt
    role user_role NOT NULL DEFAULT 'Vendeur',
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour accélérer l'authentification
CREATE INDEX idx_utilisateurs_identifiant ON utilisateurs(identifiant);

-- 2. Table : Produits
-- Contraintes : Quantités >= 0, Prix > 0, Référence unique
CREATE TABLE produits (
    id_produit SERIAL PRIMARY KEY,
    reference VARCHAR(30) NOT NULL UNIQUE,
    designation VARCHAR(200) NOT NULL,
    categorie VARCHAR(50) NOT NULL,
    marque VARCHAR(100), -- Ajouté car mentionné dans les cas d'usage (UC-01) bien que absent du tableau 1.1
    quantite INTEGER NOT NULL DEFAULT 0 CHECK (quantite >= 0),
    seuil_min INTEGER NOT NULL DEFAULT 0 CHECK (seuil_min >= 0),
    prix_achat DECIMAL(10,2) NOT NULL CHECK (prix_achat > 0),
    prix_vente DECIMAL(10,2) NOT NULL CHECK (prix_vente > 0),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour la recherche et le tri (Section 3.2)
CREATE INDEX idx_prouits_designation ON produits(designation);
CREATE INDEX idx_prouits_categorie ON produits(categorie);
CREATE INDEX idx_prouits_reference ON produits(reference);

-- 3. Table : Mouvements de Stock
-- Contraintes : Clés étrangères, Type ENUM, Historique
CREATE TYPE mouvement_type AS ENUM ('ENTREE', 'SORTIE', 'AJUSTEMENT');

CREATE TABLE mouvements_stock (
    id_mouvement SERIAL PRIMARY KEY,
    id_produit INTEGER NOT NULL,
    id_utilisateur INTEGER NOT NULL,
    type mouvement_type NOT NULL,
    quantite INTEGER NOT NULL, -- Peut être négatif si on veut stocker le solde, mais ici c'est le "déplacement"
    date_mouvement TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    commentaire TEXT, -- Ajout pratique pour l'audit
    
    CONSTRAINT fk_mouvement_produit 
        FOREIGN KEY (id_produit) REFERENCES produits(id_produit) 
        ON DELETE CASCADE, -- Si un produit est supprimé (rare), on garde l'historique ou on supprime ? 
                           -- Le DSL dit "vérification d'intégrité" avant suppression, donc on pourrait mettre RESTRICT.
                           -- Mais pour l'historique pur, CASCADE est souvent préféré. 
                           -- Respect strict DSL UC-04 : On utilisera une logique applicative pour bloquer la suppression.
    
    CONSTRAINT fk_mouvement_utilisateur 
        FOREIGN KEY (id_utilisateur) REFERENCES utilisateurs(id_utilisateur)
        ON DELETE SET NULL -- Garder l'historique même si l'utilisateur part
);

-- Index critiques pour les performances de l'IA (requête 90 jours) et l'inventaire
CREATE INDEX idx_mouvements_date ON mouvements_stock(date_mouvement);
CREATE INDEX idx_mouvements_produit ON mouvements_stock(id_produit);
CREATE INDEX idx_mouvements_type ON mouvements_stock(type);

-- 4. Vue pour l'inventaire temps réel (Optimisation Section 1.2.3 UC-05)
CREATE VIEW vue_inventaire_statut AS
SELECT 
    p.id_produit,
    p.reference,
    p.designation,
    p.categorie,
    p.marque,
    p.quantite,
    p.seuil_min,
    p.prix_vente,
    CASE 
        WHEN p.quantite = 0 THEN 'RUPTURE'
        WHEN p.quantite <= p.seuil_min THEN 'BAS'
        ELSE 'OK' 
    END AS statut
FROM produits p;

-- 5. Trigger pour mettre à jour date_modification automatiquement
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_modification = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_produits BEFORE UPDATE ON produits FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_update_utilisateurs BEFORE UPDATE ON utilisateurs FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- NOTE SUR LA SUPPRESSION (UC-04) :
-- Le DSL exige une "vérification d'intégrité" avant suppression.
-- Il est recommandé de gérer cela au niveau de l'API (FastAPI) :
-- Avant d'exécuter DELETE FROM produits WHERE id=X, l'API doit vérifier :
-- SELECT COUNT(*) FROM mouvements_stock WHERE id_produit = X;
-- Si count > 0, l'API renvoie une erreur et n'exécute pas le DELETE.
-- Cela empêche la perte d'historique d'audit.