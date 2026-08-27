-- Test de réconciliation croisée entre mart_users et mart_crypto.
--
-- Les deux marts agrègent la même grandeur — le prix de revient des
-- positions actives — par deux chemins indépendants : mart_users au grain
-- user_id via cost_basis, mart_crypto au grain symbol via total_cost_basis.
-- Les deux partitionnent le même ensemble de lignes de stg_user_positions,
-- leurs totaux doivent donc concorder.
--
-- CE QU'IL AJOUTE PAR RAPPORT A assert_mart_users_reconcilie_stg_user_positions :
-- ce test-là compare un mart à sa source, en vérifiant qu'un chemin
-- d'agrégation conserve la quantité de départ. Celui-ci compare les deux
-- marts entre eux. Il attrape donc une classe de bug différente : une
-- divergence entre les deux chemins d'agrégation. Un défaut introduit dans
-- mart_crypto seul — fan-out sur la jointure des alertes, filtre is_active
-- perdu dans la CTE positions, changement de grain — laisserait mart_users
-- parfaitement cohérent avec le staging, et passerait donc inaperçu du
-- premier test. La réciproque vaut aussi : les deux marts se surveillent
-- mutuellement.
--
-- TOLERANCE : l'égalité exacte n'est PAS attendue, et ce n'est pas un
-- défaut. Les deux marts arrondissent à 2 décimales, mais à des grains
-- différents : mart_users applique ROUND() une fois par utilisateur,
-- mart_crypto une fois par symbole. Les erreurs d'arrondi ne s'accumulent
-- donc pas au même rythme des deux côtés.
--
-- En notant T le total exact non arrondi, N_u le nombre d'utilisateurs
-- détenant au moins une position et N_s le nombre de symboles détenus :
--     |cote_users  - T| <= 0,005 * N_u
--     |cote_crypto - T| <= 0,005 * N_s
-- d'où, par inégalité triangulaire :
--     |cote_users - cote_crypto| <= 0,005 * (N_u + N_s)
--
-- La tolérance retenue est 0,01 * (N_u + N_s), soit le double de cette
-- borne, la marge couvrant l'accumulation d'erreur flottante sur les
-- colonnes DOUBLE PRECISION. Elle est calculée à l'exécution, pas figée.
--
-- L'écart est structurellement asymétrique : avec 200 000 utilisateurs et
-- 2 symboles, le côté users porte 200 000 arrondis quand le côté crypto en
-- porte 2. Sur la base actuelle l'écart mesuré est de 2,75 pour une
-- tolérance de 2 000,02 — le côté crypto coïncide d'ailleurs avec le total
-- non arrondi, ses deux arrondis ne pouvant dépasser 0,01 à eux deux.
--
-- Le test échoue dès qu'une ligne remonte.
WITH cote_users AS (
    SELECT
        COALESCE(SUM(cost_basis), 0) AS cost_basis_users,
        COUNT(*) FILTER (WHERE total_positions > 0) AS partitions_users
    FROM {{ ref('mart_users') }}
),

cote_crypto AS (
    SELECT
        COALESCE(SUM(total_cost_basis), 0) AS cost_basis_crypto,
        COUNT(*) FILTER (WHERE total_positions > 0) AS partitions_symboles
    FROM {{ ref('mart_crypto') }}
),

ecart AS (
    SELECT
        u.cost_basis_users,
        c.cost_basis_crypto,
        ABS(u.cost_basis_users - c.cost_basis_crypto) AS ecart_absolu,

        u.partitions_users,
        c.partitions_symboles,
        0.01 * (u.partitions_users + c.partitions_symboles) AS tolerance

    FROM cote_users u
    CROSS JOIN cote_crypto c
)

SELECT *
FROM ecart
WHERE ecart_absolu > tolerance
