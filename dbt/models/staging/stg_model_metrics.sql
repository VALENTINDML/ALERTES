SELECT
    id AS metric_id,
    symbol,
    mae,
    rmse,
    mape,
    r2,
    created_at
FROM {{ source('crypto_db', 'model_metrics') }}