"""
API FastAPI du projet Crypto Alerts.

Cette API expose des endpoints de lecture permettant au dashboard Streamlit
et à d'autres futurs clients d'accéder aux données du projet :
utilisateurs, prédictions, notifications et dernières données de marché.
"""
from fastapi import FastAPI
from config.db import get_connection


app = FastAPI(
    title="Crypto Alerts API",
    description="API du MVP de prédiction et d'alertes crypto",
    version="1.0.0",
)


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


@app.get("/notifications/count")
def notifications_count():
    """
    Retourne le nombre total de notifications générées.
    """
    row = fetch_one("""
        SELECT COUNT(*)
        FROM notifications;
    """)

    return {
        "notifications_count": row[0]
    }


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