SELECT
    id AS notification_id,
    user_id,
    prediction_id,
    price_alert_id,
    symbol,
    notification_type,
    message,
    status,
    sent_at,
    created_at
FROM public.notifications