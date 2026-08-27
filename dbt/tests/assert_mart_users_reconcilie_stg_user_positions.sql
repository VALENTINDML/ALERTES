-- Test de réconciliation entre mart_users et sa source stg_user_positions.
--
-- CLASSE DE BUG DÉTECTÉE : la duplication de lignes en amont d'une
-- agrégation — fan-out de jointure, jointure sur une clé non unique,
-- filtre perdu, grain accidentellement changé. Toutes ces erreurs laissent
-- le grain de sortie intact (une ligne par utilisateur) mais gonflent les
-- mesures. C'est exactement le défaut qui affectait mart_users : trois
-- LEFT JOIN 1-N simultanés multipliaient COUNT() et SUM(), avec un facteur
-- de 4,39 sur l'ensemble de la base.
--
-- POURQUOI AUCUN TEST GÉNÉRIQUE NE PEUT LE FAIRE : unique et not_null
-- portent sur une seule colonne d'un seul modèle. Ils vérifient la forme,
-- jamais la conservation d'une quantité entre deux modèles.
-- unique_mart_users_user_id passait sans broncher pendant que cost_basis
-- était multiplié par 4,39, parce que le GROUP BY garantit l'unicité de
-- user_id quelle que soit la duplication en amont. accepted_values et
-- relationships ne comparent pas davantage deux agrégats entre eux.
-- Seul un test de réconciliation ferme cet angle mort.
--
-- TOLÉRANCE : mart_users arrondit cost_basis à 2 décimales par utilisateur
-- avant de sommer, la référence somme les produits non arrondis. L'écart
-- attendu est donc l'accumulation des arrondis, bornée par 0,005 par
-- utilisateur. La tolérance retenue est 0,01 par utilisateur détenant au
-- moins une position, soit le double de cette borne, la marge couvrant
-- l'accumulation d'erreur flottante sur les colonnes DOUBLE PRECISION.
-- Sur la base actuelle : écart réel 2,75 pour une tolérance de 2 000, quand
-- le fan-out produisait un écart de l'ordre de 87 milliards.
--
-- total_positions ne compte que des entiers : aucun arrondi n'intervient,
-- la tolérance y est nulle et l'égalité doit être exacte.
--
-- Le test échoue dès qu'une ligne remonte.
WITH mart AS (
    SELECT
        COALESCE(SUM(cost_basis), 0) AS cost_basis_mart,
        COALESCE(SUM(total_positions), 0) AS total_positions_mart,
        COUNT(*) FILTER (WHERE total_positions > 0) AS users_avec_positions
    FROM {{ ref('mart_users') }}
),

reference AS (
    SELECT
        COALESCE(ROUND(SUM(buy_price * quantity) FILTER (WHERE is_active = TRUE)::numeric, 2), 0) AS cost_basis_reference,
        COUNT(*) FILTER (WHERE is_active = TRUE) AS total_positions_reference
    FROM {{ ref('stg_user_positions') }}
),

ecarts AS (
    SELECT
        m.users_avec_positions,

        m.cost_basis_mart,
        r.cost_basis_reference,
        ABS(m.cost_basis_mart - r.cost_basis_reference) AS ecart_cost_basis,
        0.01 * m.users_avec_positions AS tolerance_cost_basis,

        m.total_positions_mart,
        r.total_positions_reference,
        ABS(m.total_positions_mart - r.total_positions_reference) AS ecart_total_positions

    FROM mart m
    CROSS JOIN reference r
)

SELECT *
FROM ecarts
WHERE ecart_cost_basis > tolerance_cost_basis
   OR ecart_total_positions > 0
