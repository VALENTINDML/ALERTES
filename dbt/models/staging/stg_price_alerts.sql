SELECT
    id AS price_alert_id,
    user_id,
    symbol,
    target_price,
    direction,
    is_active,
    triggered_at,
    created_at
FROM public.price_alerts