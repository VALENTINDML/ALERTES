SELECT
    id AS daily_alert_preference_id,
    user_id,
    symbol,
    enabled,
    created_at
FROM {{ source('crypto_db', 'daily_alert_preferences') }}