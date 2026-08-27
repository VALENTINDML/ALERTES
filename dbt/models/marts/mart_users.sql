-- Chaque table source est pré-agrégée au grain user_id AVANT la jointure.
-- Joindre directement les trois tables 1-N à stg_users produirait un
-- produit cartésien : les COUNT() et le SUM() porteraient sur des lignes
-- dupliquées. Même patron que mart_crypto.
WITH positions AS (
    SELECT
        user_id,
        COUNT(position_id) FILTER (WHERE is_active = TRUE) AS total_positions,
        COUNT(DISTINCT symbol) FILTER (WHERE is_active = TRUE) AS total_distinct_symbols,
        COALESCE(
            ROUND(SUM(buy_price * quantity) FILTER (WHERE is_active = TRUE)::numeric, 2),
            0
        ) AS cost_basis
    FROM {{ ref('stg_user_positions') }}
    GROUP BY user_id
),

daily_alerts AS (
    SELECT
        user_id,
        COUNT(daily_alert_preference_id) AS total_daily_alert_preferences,
        COUNT(daily_alert_preference_id) FILTER (WHERE enabled = TRUE) AS enabled_daily_alerts
    FROM {{ ref('stg_daily_alert_preferences') }}
    GROUP BY user_id
),

price_alerts AS (
    SELECT
        user_id,
        COUNT(price_alert_id) AS total_price_alerts,
        COUNT(price_alert_id) FILTER (WHERE is_active = TRUE) AS active_price_alerts
    FROM {{ ref('stg_price_alerts') }}
    GROUP BY user_id
)

SELECT
    u.user_id,
    u.email,
    u.country,
    u.country_code,
    u.region,
    u.city,
    u.currency,
    u.language,
    u.timezone,
    u.is_active,
    u.created_at,

    COALESCE(p.total_positions, 0) AS total_positions,
    COALESCE(p.total_distinct_symbols, 0) AS total_distinct_symbols,

    COALESCE(p.cost_basis, 0) AS cost_basis,

    COALESCE(d.enabled_daily_alerts, 0) AS enabled_daily_alerts,
    COALESCE(d.total_daily_alert_preferences, 0) AS total_daily_alert_preferences,

    COALESCE(pa.active_price_alerts, 0) AS active_price_alerts,
    COALESCE(pa.total_price_alerts, 0) AS total_price_alerts

FROM {{ ref('stg_users') }} u

LEFT JOIN positions p
    ON u.user_id = p.user_id

LEFT JOIN daily_alerts d
    ON u.user_id = d.user_id

LEFT JOIN price_alerts pa
    ON u.user_id = pa.user_id
