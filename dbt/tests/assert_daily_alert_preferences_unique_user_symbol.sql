-- Vérifie la contrainte UNIQUE(user_id, symbol) portée par la table
-- daily_alert_preferences (users_db/init_database.py) : un utilisateur ne
-- peut s'abonner qu'une fois aux prévisions quotidiennes d'un symbole.
--
-- Aucun test générique de dbt ne couvre une clé composite, et l'unicité
-- du couple ne se déduit pas des tests unique posés colonne par colonne.
-- Écrit en test singulier plutôt qu'avec dbt_utils.unique_combination_of_columns,
-- pour ne pas ajouter une dépendance de package pour un seul test.
--
-- Le test échoue dès qu'au moins un couple remonte.
SELECT
    user_id,
    symbol,
    COUNT(*) AS total_lignes
FROM {{ ref('stg_daily_alert_preferences') }}
GROUP BY
    user_id,
    symbol
HAVING COUNT(*) > 1
