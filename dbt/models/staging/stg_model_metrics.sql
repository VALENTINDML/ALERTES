SELECT
    id AS metric_id,
    symbol,
    mae,
    rmse,
    mape,
    r2,
    created_at
FROM public.model_metrics