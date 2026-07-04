"""
Streaming temps réel des alertes de prix.

Ce service écoute les trades Binance en WebSocket pour chaque symbole
configuré, puis déclenche les alertes de prix personnalisées lorsque
le prix courant atteint l'objectif défini par l'utilisateur.

Le traitement est volontairement SQL-first afin d'éviter de charger
des millions d'alertes actives en mémoire Python.
"""
import asyncio
import json
import time

import websockets

from config.db import get_connection
from config.symbols import SYMBOLS


BINANCE_WS_URL = "wss://stream.binance.com:9443/stream?streams="

# Nombre maximal d'alertes traitées par transaction SQL.
# Le batch évite les transactions trop longues sur de gros volumes.
BATCH_SIZE = 5000
# Limite la fréquence de traitement par symbole.
# Binance envoie beaucoup de trades ; on évite de requêter PostgreSQL
# à chaque tick de marché.
PRICE_PROCESS_INTERVAL_SECONDS = 1.0

last_processed_at = {}


def normalize_symbol(symbol):
    return symbol.replace("/", "").lower()


def get_project_symbol(binance_symbol):
    for symbol in SYMBOLS:
        if normalize_symbol(symbol).upper() == binance_symbol:
            return symbol
    return None


def should_process_symbol(symbol):
    """
    Détermine si le symbole peut être traité maintenant.

    Cela agit comme un throttling par crypto afin de réduire
    la pression sur PostgreSQL.
    """
    now = time.time()
    previous = last_processed_at.get(symbol, 0)

    if now - previous < PRICE_PROCESS_INTERVAL_SECONDS:
        return False

    last_processed_at[symbol] = now
    return True


def process_triggered_alerts_batch(symbol, current_price):
    """
    Déclenche les alertes prix directement côté SQL.

    Le SQL :
    - sélectionne uniquement les alertes réellement déclenchées ;
    - verrouille les lignes avec FOR UPDATE SKIP LOCKED ;
    - insère les notifications en batch ;
    - désactive les alertes déclenchées ;
    - évite les doublons via price_alert_id.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            WITH triggered AS (
                SELECT
                    pa.id AS price_alert_id,
                    pa.user_id,
                    pa.symbol,
                    pa.target_price,
                    pa.direction
                FROM price_alerts pa
                JOIN users u
                    ON u.id = pa.user_id
                WHERE pa.symbol = %s
                  AND pa.is_active = TRUE
                  AND u.is_active = TRUE
                  AND (
                        (pa.direction = 'above' AND pa.target_price <= %s)
                     OR (pa.direction = 'below' AND pa.target_price >= %s)
                  )
                ORDER BY pa.target_price
                LIMIT %s
                FOR UPDATE OF pa SKIP LOCKED
            ),
            inserted AS (
                INSERT INTO notifications (
                    user_id,
                    prediction_id,
                    price_alert_id,
                    symbol,
                    notification_type,
                    message,
                    status,
                    sent_at
                )
                SELECT
                    user_id,
                    NULL,
                    price_alert_id,
                    symbol,
                    'price_target',
                    CONCAT(
                        'Alerte prix ', symbol,
                        ' : prix actuel ', %s,
                        ', objectif ', target_price,
                        ', direction ', direction,
                        '.'
                    ),
                    'pending',
                    NULL
                FROM triggered
                ON CONFLICT DO NOTHING
                RETURNING price_alert_id
            ),
            updated AS (
                UPDATE price_alerts pa
                SET is_active = FALSE,
                    triggered_at = CURRENT_TIMESTAMP
                WHERE pa.id IN (
                    SELECT price_alert_id FROM inserted
                )
                RETURNING pa.id
            )
            SELECT
                (SELECT COUNT(*) FROM triggered) AS triggered_count,
                (SELECT COUNT(*) FROM inserted) AS inserted_count,
                (SELECT COUNT(*) FROM updated) AS updated_count;
        """, (
            symbol,
            current_price,
            current_price,
            BATCH_SIZE,
            round(current_price, 4),
        ))

        result = cur.fetchone()
        conn.commit()

        triggered_count, inserted_count, updated_count = result

        return {
            "triggered": triggered_count,
            "inserted": inserted_count,
            "updated": updated_count,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


def process_price_event(symbol, current_price):
    # Continue de traiter les alertes par lots tant que le dernier batch
    # a atteint la taille maximale. Cela signifie qu'il reste potentiellement
    # d'autres alertes déclenchées à traiter.
    total_triggered = 0
    total_inserted = 0
    total_updated = 0

    while True:
        result = process_triggered_alerts_batch(symbol, current_price)

        total_triggered += result["triggered"]
        total_inserted += result["inserted"]
        total_updated += result["updated"]

        if result["triggered"] < BATCH_SIZE:
            break

    if total_triggered > 0:
        print(
            f"{symbol} | prix={current_price} | "
            f"alertes déclenchées={total_triggered} | "
            f"notifications créées={total_inserted} | "
            f"alertes désactivées={total_updated}"
        )


async def listen_price_stream():
    """
    Écoute les trades Binance en temps réel pour toutes les cryptos suivies.

    Le flux est multiplexé : une seule connexion WebSocket permet
    de recevoir les trades de tous les symboles configurés.
    """
    streams = "/".join(
        f"{normalize_symbol(symbol)}@trade"
        for symbol in SYMBOLS
    )

    url = BINANCE_WS_URL + streams

    print(f"Connexion WebSocket prix Binance : {url}")

    async with websockets.connect(
        url,
        ping_interval=20,
        ping_timeout=20,
        close_timeout=10,
    ) as websocket:
        async for message in websocket:
            payload = json.loads(message)
            data = payload.get("data", {})

            binance_symbol = data.get("s")
            price = data.get("p")

            if not binance_symbol or not price:
                continue

            symbol = get_project_symbol(binance_symbol)

            if symbol is None:
                continue

            if not should_process_symbol(symbol):
                continue

            current_price = float(price)

            process_price_event(symbol, current_price)


async def main():
    while True:
        try:
            await listen_price_stream()
        except Exception as e:
            print(f"Erreur WebSocket price_alert_stream : {e}")
            print("Reconnexion dans 10 secondes...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())