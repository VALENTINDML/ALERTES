SELECT
    id AS prediction_id,
    symbol,
    prediction_datetime,
    predicted_change_24h,
    trend,
    model_path,
    created_at
FROM {{ source('crypto_db', 'predictions') }}