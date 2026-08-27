SELECT
    id AS user_id,
    email,
    first_name,
    last_name,
    is_active,
    country_code,
    country,
    region,
    city,
    postal_code,
    currency,
    language,
    timezone,
    created_at
FROM {{ source('crypto_db', 'users') }}