WITH positions AS (
    SELECT
        symbol,
        COUNT(DISTINCT user_id) FILTER (WHERE is_active = TRUE) AS total_holders,
        COUNT(position_id) FILTER (WHERE is_active = TRUE) AS total_positions,
        ROUND(AVG(buy_price) FILTER (WHERE is_active = TRUE)::numeric, 4) AS avg_buy_price,
        ROUND(AVG(quantity) FILTER (WHERE is_active = TRUE)::numeric, 4) AS avg_quantity,
        COALESCE(
            ROUND(SUM(buy_price * quantity) FILTER (WHERE is_active = TRUE)::numeric, 2),
            0
        ) AS total_portfolio_value
    FROM {{ ref('stg_user_positions') }}
    GROUP BY symbol
),

daily_alerts AS (
    SELECT
        symbol,
        COUNT(daily_alert_preference_id) AS total_daily_alert_preferences,
        COUNT(daily_alert_preference_id) FILTER (WHERE enabled = TRUE) AS enabled_daily_alerts
    FROM {{ ref('stg_daily_alert_preferences') }}
    GROUP BY symbol
),

price_alerts AS (
    SELECT
        symbol,
        COUNT(price_alert_id) AS total_price_alerts,
        COUNT(price_alert_id) FILTER (WHERE is_active = TRUE) AS active_price_alerts,
        COUNT(price_alert_id) FILTER (WHERE is_active = FALSE) AS triggered_price_alerts
    FROM {{ ref('stg_price_alerts') }}
    GROUP BY symbol
)

SELECT
    p.symbol,

    p.total_holders,
    p.total_positions,
    p.avg_buy_price,
    p.avg_quantity,
    p.total_portfolio_value,

    COALESCE(d.total_daily_alert_preferences, 0) AS total_daily_alert_preferences,
    COALESCE(d.enabled_daily_alerts, 0) AS enabled_daily_alerts,

    COALESCE(pa.total_price_alerts, 0) AS total_price_alerts,
    COALESCE(pa.active_price_alerts, 0) AS active_price_alerts,
    COALESCE(pa.triggered_price_alerts, 0) AS triggered_price_alerts

FROM positions p

LEFT JOIN daily_alerts d
    ON p.symbol = d.symbol

LEFT JOIN price_alerts pa
    ON p.symbol = pa.symbol