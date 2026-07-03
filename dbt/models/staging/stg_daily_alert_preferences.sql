SELECT
    id AS daily_alert_preference_id,
    user_id,
    symbol,
    enabled,
    created_at
FROM public.daily_alert_preferences