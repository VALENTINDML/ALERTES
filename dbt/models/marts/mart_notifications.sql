SELECT
    n.notification_id,
    n.user_id,
    u.email,
    u.country,
    u.region,
    u.city,

    n.symbol,
    n.notification_type,
    n.status,
    n.created_at,
    n.sent_at,

    CASE
        WHEN n.sent_at IS NOT NULL THEN TRUE
        ELSE FALSE
    END AS is_sent,

    CASE
        WHEN n.notification_type = 'daily_prediction' THEN TRUE
        ELSE FALSE
    END AS is_daily_prediction,

    CASE
        WHEN n.notification_type = 'price_target' THEN TRUE
        ELSE FALSE
    END AS is_price_target

FROM {{ ref('stg_notifications') }} n

LEFT JOIN {{ ref('stg_users') }} u
    ON n.user_id = u.user_id