SELECT
    id AS ohlcv_id,
    symbol,
    timestamp,
    datetime,
    timeframe,
    open,
    high,
    low,
    close,
    volume
FROM {{ source('crypto_db', 'ccxt_ohlcv') }}