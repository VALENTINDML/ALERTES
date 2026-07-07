"""
API FastAPI robuste pour Crypto Alerts.

Optimisations :
- limites maximales sur les endpoints de listing ;
- cache léger pour les endpoints statistiques ;
- requêtes mieux encadrées ;
- endpoints compatibles gros volume.
"""

import time
from functools import wraps

from fastapi import FastAPI, Query
from prometheus_fastapi_instrumentator import Instrumentator

from config.db import get_connection


app = FastAPI(
    title="Crypto Alerts API",
    description="API du projet Crypto Alerts",
    version="1.1.0",
)

# Expose automatiquement les métriques Prometheus sur /metrics.
# Ces métriques sont ensuite collectées par Prometheus et affichées dans Grafana.
Instrumentator().instrument(app).expose(app)

# Cache mémoire simple pour limiter les requêtes répétées sur les endpoints statistiques.
# Suffisant pour un projet local / portfolio, mais à remplacer par Redis en production.
CACHE = {}
CACHE_TTL_SECONDS = 30


def cached(key, ttl=CACHE_TTL_SECONDS):
    # La clé de cache dépend du nom logique de l'endpoint
    # ainsi que des arguments passés à la fonction.
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            cache_key = f"{key}:{args}:{kwargs}"

            if cache_key in CACHE:
                created_at, value = CACHE[cache_key]
                if now - created_at < ttl:
                    return value

            value = func(*args, **kwargs)
            CACHE[cache_key] = (now, value)
            return value

        return wrapper

    return decorator

# Helper pour exécuter une requête SQL retournant une seule ligne.
def fetch_one(query, params=None):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(query, params or ())
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

# Helper pour exécuter une requête SQL retournant plusieurs lignes.
def fetch_all(query, params=None):
    conn = get_connection()
    cur = conn.cursor()

    try: 
        cur.execute(query, params or ())
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/users/count")
@cached("users_count", ttl=30)
def users_count():
    row = fetch_one("""
        SELECT COUNT(*)
        FROM users;
    """)

    return {"users_count": row[0]}

@app.get("/symbols")
@cached("symbols", ttl=300)
def available_symbols():
    rows = fetch_all("""
        SELECT symbol
        FROM (
            SELECT symbol FROM ccxt_ohlcv
            UNION
            SELECT symbol FROM live_market_data
            UNION
            SELECT symbol FROM predictions
            UNION
            SELECT symbol FROM model_metrics
            UNION
            SELECT symbol FROM daily_alert_preferences
            UNION
            SELECT symbol FROM notifications
            UNION
            SELECT symbol FROM price_alerts
            UNION
            SELECT symbol FROM user_positions
        ) s
        WHERE symbol IS NOT NULL
        ORDER BY symbol;
    """)

    return [{"symbol": row[0]} for row in rows]


@app.get("/predictions/latest")
@cached("predictions_latest", ttl=10)
def latest_predictions(symbol: str | None = None):
    if symbol:
        rows = fetch_all("""
            SELECT
                id,
                symbol,
                prediction_datetime,
                predicted_change_24h,
                trend,
                created_at
            FROM predictions
            WHERE symbol = %s
            ORDER BY created_at DESC
            LIMIT 1;
        """, (symbol,))
    else:
        rows = fetch_all("""
            SELECT DISTINCT ON (symbol)
                id,
                symbol,
                prediction_datetime,
                predicted_change_24h,
                trend,
                created_at
            FROM predictions
            ORDER BY symbol, created_at DESC;
        """)

    return [
        {
            "id": row[0],
            "symbol": row[1],
            "prediction_datetime": row[2],
            "predicted_change_24h": row[3],
            "trend": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


@app.get("/market/latest")
@cached("market_latest")
def latest_market_data(symbol: str | None = None):
    if symbol:
        rows = fetch_all("""
            SELECT
                symbol,
                datetime,
                open,
                high,
                low,
                close,
                volume
            FROM ccxt_ohlcv
            WHERE symbol = %s
            ORDER BY datetime DESC
            LIMIT 1;
        """, (symbol,))
    else:
        rows = fetch_all("""
            SELECT DISTINCT ON (symbol)
                symbol,
                datetime,
                open,
                high,
                low,
                close,
                volume
            FROM ccxt_ohlcv
            ORDER BY symbol, datetime DESC;
        """)

    if not rows:
        return []

    return [
        {
            "symbol": row[0],
            "datetime": row[1],
            "open": row[2],
            "high": row[3],
            "low": row[4],
            "close": row[5],
            "volume": row[6],
        }
        for row in rows
    ]


@app.get("/market/live")
#@cached("market_live", ttl=1)
def live_market_data(symbol: str | None = None):
    if symbol:
        rows = fetch_all("""
            SELECT
                symbol,
                timestamp,
                datetime,
                timeframe,
                open,
                high,
                low,
                close,
                volume,
                is_closed,
                updated_at
            FROM live_market_data
            WHERE symbol = %s
            ORDER BY updated_at DESC
            LIMIT 1;
        """, (symbol,))
    else:
        rows = fetch_all("""
            SELECT DISTINCT ON (symbol)
                symbol,
                timestamp,
                datetime,
                timeframe,
                open,
                high,
                low,
                close,
                volume,
                is_closed,
                updated_at
            FROM live_market_data
            ORDER BY symbol, updated_at DESC;
        """)

    if not rows:
        return []

    return [
        {
            "symbol": row[0],
            "timestamp": row[1],
            "datetime": row[2],
            "timeframe": row[3],
            "open": row[4],
            "high": row[5],
            "low": row[6],
            "close": row[7],
            "volume": row[8],
            "is_closed": row[9],
            "updated_at": row[10],
        }
        for row in rows
    ]


@app.get("/daily-alerts/count")
@cached("daily_alerts_count", ttl=30)
def daily_alerts_count(symbol: str | None = None):
    if symbol:
        rows = fetch_all("""
            SELECT enabled, COUNT(*)
            FROM daily_alert_preferences
            WHERE symbol = %s
            GROUP BY enabled;
        """, (symbol,))
    else:
        rows = fetch_all("""
            SELECT enabled, COUNT(*)
            FROM daily_alert_preferences
            GROUP BY enabled;
        """)

    return [
        {
            "enabled": row[0],
            "count": row[1],
        }
        for row in rows
    ]


@app.get("/notifications/stats")
@cached("notifications_stats", ttl=30)
def notifications_stats(symbol: str | None = None):
    if symbol:
        rows = fetch_all("""
            SELECT
                notification_type,
                COUNT(*)
            FROM notifications
            WHERE symbol = %s
            GROUP BY notification_type;
        """, (symbol,))
    else:
        rows = fetch_all("""
            SELECT
                notification_type,
                COUNT(*)
            FROM notifications
            GROUP BY notification_type;
        """)

    return [
        {
            "notification_type": row[0],
            "count": row[1],
        }
        for row in rows
    ]


@app.get("/notifications/by-type")
@cached("notifications_by_type", ttl=30)
def notifications_by_type(symbol: str | None = None):
    if symbol:
        rows = fetch_all("""
            SELECT
                notification_type,
                status,
                COUNT(*)
            FROM notifications
            WHERE symbol = %s
            GROUP BY notification_type, status
            ORDER BY notification_type, status;
        """, (symbol,))
    else:
        rows = fetch_all("""
            SELECT
                notification_type,
                status,
                COUNT(*)
            FROM notifications
            GROUP BY notification_type, status
            ORDER BY notification_type, status;
        """)

    return [
        {
            "notification_type": row[0],
            "status": row[1],
            "count": row[2],
        }
        for row in rows
    ]


@app.get("/notifications/latest")
def latest_notifications(
    symbol: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
):
    if symbol:
        rows = fetch_all("""
            SELECT
                id,
                user_id,
                prediction_id,
                price_alert_id,
                symbol,
                notification_type,
                message,
                status,
                created_at
            FROM notifications
            WHERE symbol = %s
            ORDER BY created_at DESC
            LIMIT %s;
        """, (symbol, limit))
    else:
        rows = fetch_all("""
            SELECT
                id,
                user_id,
                prediction_id,
                price_alert_id,
                symbol,
                notification_type,
                message,
                status,
                created_at
            FROM notifications
            ORDER BY created_at DESC
            LIMIT %s;
        """, (limit,))

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "prediction_id": row[2],
            "price_alert_id": row[3],
            "symbol": row[4],
            "notification_type": row[5],
            "message": row[6],
            "status": row[7],
            "created_at": row[8],
        }
        for row in rows
    ]


@app.get("/notifications/price-target/latest")
def latest_price_target_notifications(
    symbol: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
):
    if symbol:
        rows = fetch_all("""
            SELECT
                n.id,
                n.user_id,
                u.email,
                n.price_alert_id,
                n.symbol,
                n.message,
                n.status,
                n.created_at
            FROM notifications n
            JOIN users u
                ON n.user_id = u.id
            WHERE n.notification_type = 'price_target'
              AND n.symbol = %s
            ORDER BY n.created_at DESC
            LIMIT %s;
        """, (symbol, limit))
    else:
        rows = fetch_all("""
            SELECT
                n.id,
                n.user_id,
                u.email,
                n.price_alert_id,
                n.symbol,
                n.message,
                n.status,
                n.created_at
            FROM notifications n
            JOIN users u
                ON n.user_id = u.id
            WHERE n.notification_type = 'price_target'
            ORDER BY n.created_at DESC
            LIMIT %s;
        """, (limit,))

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "email": row[2],
            "price_alert_id": row[3],
            "symbol": row[4],
            "message": row[5],
            "status": row[6],
            "created_at": row[7],
        }
        for row in rows
    ]


@app.get("/price-alerts/latest")
def latest_price_alerts(
    symbol: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
):
    if symbol:
        rows = fetch_all("""
            SELECT
                pa.id,
                pa.user_id,
                u.email,
                pa.symbol,
                pa.target_price,
                pa.direction,
                pa.is_active,
                pa.triggered_at,
                pa.created_at
            FROM price_alerts pa
            JOIN users u
                ON pa.user_id = u.id
            WHERE pa.symbol = %s
            ORDER BY pa.created_at DESC
            LIMIT %s;
        """, (symbol, limit))
    else:
        rows = fetch_all("""
            SELECT
                pa.id,
                pa.user_id,
                u.email,
                pa.symbol,
                pa.target_price,
                pa.direction,
                pa.is_active,
                pa.triggered_at,
                pa.created_at
            FROM price_alerts pa
            JOIN users u
                ON pa.user_id = u.id
            ORDER BY pa.created_at DESC
            LIMIT %s;
        """, (limit,))

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "email": row[2],
            "symbol": row[3],
            "target_price": row[4],
            "direction": row[5],
            "is_active": row[6],
            "triggered_at": row[7],
            "created_at": row[8],
        }
        for row in rows
    ]


@app.get("/metrics/model/latest")
@cached("model_metrics_latest", ttl=30)
def latest_model_metrics(symbol: str | None = None):
    if symbol:
        rows = fetch_all("""
            SELECT
                symbol,
                mae,
                rmse,
                mape,
                r2,
                created_at
            FROM model_metrics
            WHERE symbol = %s
            ORDER BY created_at DESC
            LIMIT 1;
        """, (symbol,))
    else:
        rows = fetch_all("""
            SELECT DISTINCT ON (symbol)
                symbol,
                mae,
                rmse,
                mape,
                r2,
                created_at
            FROM model_metrics
            ORDER BY symbol, created_at DESC;
        """)

    return [
        {
            "symbol": row[0],
            "mae": row[1],
            "rmse": row[2],
            "mape": row[3],
            "r2": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]