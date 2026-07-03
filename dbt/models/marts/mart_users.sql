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

    COUNT(p.position_id) FILTER (WHERE p.is_active = TRUE) AS total_positions,
    COUNT(DISTINCT p.symbol) FILTER (WHERE p.is_active = TRUE) AS total_distinct_symbols,

    COALESCE(
        ROUND(SUM(p.buy_price * p.quantity) FILTER (WHERE p.is_active = TRUE)::numeric, 2),
        0
    ) AS portfolio_value,

    COUNT(d.daily_alert_preference_id) FILTER (WHERE d.enabled = TRUE) AS enabled_daily_alerts,
    COUNT(d.daily_alert_preference_id) AS total_daily_alert_preferences,

    COUNT(pa.price_alert_id) FILTER (WHERE pa.is_active = TRUE) AS active_price_alerts,
    COUNT(pa.price_alert_id) AS total_price_alerts

FROM {{ ref('stg_users') }} u

LEFT JOIN {{ ref('stg_user_positions') }} p
    ON u.user_id = p.user_id

LEFT JOIN {{ ref('stg_daily_alert_preferences') }} d
    ON u.user_id = d.user_id

LEFT JOIN {{ ref('stg_price_alerts') }} pa
    ON u.user_id = pa.user_id

GROUP BY
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
    u.created_at