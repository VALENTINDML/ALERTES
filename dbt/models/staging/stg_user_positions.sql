SELECT
    id AS position_id,
    user_id,
    symbol,
    buy_price,
    quantity,
    buy_datetime,
    is_active,
    created_at
FROM public.user_positions