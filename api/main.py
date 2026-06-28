"""
API FastAPI du projet Crypto Alerts.

Cette API expose des endpoints de lecture permettant au dashboard Streamlit
et à d'autres futurs clients d'accéder aux données du projet :
utilisateurs, prédictions, notifications et dernières données de marché.
"""
from fastapi import FastAPI
from config.db import get_connection
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(
    title="Alertes API",
    description="API du MVP de prédiction et d'alertes crypto",
    version="1.0.0",
)

Instrumentator().instrument(app).expose(app)

def fetch_one(query, params=None):
    """
    Exécute une requête SQL retournant une seule ligne.

    Args:
        query (str):
            Requête SQL à exécuter.
        params (tuple | None):
            Paramètres optionnels de la requête.

    Returns:
        tuple | None:
            Première ligne retournée par PostgreSQL.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, params or ())
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row


def fetch_all(query, params=None):
    """
    Exécute une requête SQL retournant plusieurs lignes.

    Args:
        query (str):
            Requête SQL à exécuter.
        params (tuple | None):
            Paramètres optionnels de la requête.

    Returns:
        list[tuple]:
            Liste des lignes retournées par PostgreSQL.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, params or ())
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


@app.get("/health")
def health():
    """
    Vérifie que l'API est disponible.
    """
    return {
        "status": "ok"
    }


@app.get("/users/count")
def users_count():
    """
    Retourne le nombre total d'utilisateurs.
    """
    row = fetch_one("""
        SELECT COUNT(*)
        FROM users;
    """)

    return {
        "users_count": row[0]
    }


@app.get("/predictions/latest")
def latest_predictions():
    """
    Retourne la dernière prédiction disponible pour chaque symbole.
    """
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



@app.get("/notifications/latest")
def latest_notifications(limit: int = 20):
    """
    Retourne les dernières notifications générées.

    Args:
        limit (int):
            Nombre maximum de notifications à retourner.
    """
    rows = fetch_all("""
        SELECT
            id,
            user_id,
            prediction_id,
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
            "symbol": row[3],
            "notification_type": row[4],
            "message": row[5],
            "status": row[6],
            "created_at": row[7],
        }
        for row in rows
    ]


@app.get("/market/latest")
def latest_market_data(symbol: str = "BTC/USDT"):
    """
    Retourne la dernière bougie OHLCV disponible pour un symbole.

    Args:
        symbol (str):
            Symbole crypto à consulter.
    """
    row = fetch_one("""
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

    if row is None:
        return {
            "error": f"Aucune donnée trouvée pour {symbol}"
        }

    return {
        "symbol": row[0],
        "datetime": row[1],
        "open": row[2],
        "high": row[3],
        "low": row[4],
        "close": row[5],
        "volume": row[6],
    }


@app.get("/daily-alerts/count")
def daily_alerts_count():
    """
    Retourne la répartition des alertes quotidiennes activées/désactivées.
    """
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


@app.get("/notifications/by-type")
def notifications_by_type():
    """
    Retourne le nombre de notifications par type et par statut.

    Permet de distinguer :
    - daily_prediction : notifications issues des prédictions ML ;
    - price_target : notifications issues des alertes prix temps réel.
    """
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


@app.get("/notifications/price-target/latest")
def latest_price_target_notifications(limit: int = 20):
    """
    Retourne les dernières notifications issues des alertes de prix.

    Ces notifications proviennent du service de streaming Binance
    et ont notification_type = 'price_target'.
    """
    rows = fetch_all("""
        SELECT
            n.id,
            n.user_id,
            u.email,
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
            "symbol": row[3],
            "message": row[4],
            "status": row[5],
            "created_at": row[6],
        }
        for row in rows
    ]


@app.get("/notifications/daily-prediction/latest")
def latest_daily_prediction_notifications(limit: int = 20):
    """
    Retourne les dernières notifications issues des prédictions ML.

    Ces notifications ont notification_type = 'daily_prediction'.
    """
    rows = fetch_all("""
        SELECT
            n.id,
            n.user_id,
            u.email,
            n.prediction_id,
            n.symbol,
            n.message,
            n.status,
            n.created_at
        FROM notifications n
        JOIN users u
            ON n.user_id = u.id
        WHERE n.notification_type = 'daily_prediction'
        ORDER BY n.created_at DESC
        LIMIT %s;
    """, (limit,))

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "email": row[2],
            "prediction_id": row[3],
            "symbol": row[4],
            "message": row[5],
            "status": row[6],
            "created_at": row[7],
        }
        for row in rows
    ]


@app.get("/price-alerts/latest")
def latest_price_alerts(limit: int = 20):
    """
    Retourne les dernières alertes de prix configurées par les utilisateurs.

    Cette table représente les seuils surveillés par le service streaming.
    """
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
def latest_model_metrics():
    rows = fetch_all("""
        SELECT
            symbol,
            mae,
            rmse,
            mape,
            r2,
            created_at
        FROM model_metrics
        ORDER BY created_at DESC;
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

@app.get("/market/live")
def live_market_data(symbol: str = "BTC/USDT"):
    """
    Retourne la dernière bougie live reçue depuis le WebSocket Binance.
    """
    row = fetch_one("""
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

    if row is None:
        return {
            "error": f"Aucune donnée live disponible pour {symbol}"
        }

    return {
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

@app.get("/notifications/stats")
def notifications_stats():
    """
    Retourne le nombre d'alertes envoyées quotidiennes et personnalisées 
    """
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
            "count": row[1]
        }
        for row in rows
    ]