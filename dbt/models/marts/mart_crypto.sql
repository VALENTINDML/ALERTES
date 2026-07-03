SELECT
    p.symbol,

    COUNT(DISTINCT p.user_id) FILTER (WHERE p.is_active = TRUE) AS total_holders,
    COUNT(p.position_id) FILTER (WHERE p.is_active = TRUE) AS total_positions,

    ROUND(AVG(p.buy_price) FILTER (WHERE p.is_active = TRUE)::numeric, 4) AS avg_buy_price,
    ROUND(AVG(p.quantity) FILTER (WHERE p.is_active = TRUE)::numeric, 4) AS avg_quantity,

    COALESCE(
        ROUND(SUM(p.buy_price * p.quantity) FILTER (WHERE p.is_active = TRUE)::numeric, 2),
        0
    ) AS total_portfolio_value,

    COUNT(d.daily_alert_preference_id) AS total_daily_alert_preferences,
    COUNT(d.daily_alert_preference_id) FILTER (WHERE d.enabled = TRUE) AS enabled_daily_alerts,

    COUNT(pa.price_alert_id) AS total_price_alerts,
    COUNT(pa.price_alert_id) FILTER (WHERE pa.is_active = TRUE) AS active_price_alerts,
    COUNT(pa.price_alert_id) FILTER (WHERE pa.is_active = FALSE) AS triggered_price_alerts

FROM {{ ref('stg_user_positions') }} p

LEFT JOIN {{ ref('stg_daily_alert_preferences') }} d
    ON p.symbol = d.symbol

LEFT JOIN {{ ref('stg_price_alerts') }} pa
    ON p.symbol = pa.symbol

GROUP BY
    p.symbol