import asyncio
import json
from datetime import datetime

import websockets

from config.db import get_connection
from config.symbols import SYMBOLS


BINANCE_WS_URL = "wss://stream.binance.com:9443/stream?streams="


def normalize_symbol(symbol):
    return symbol.replace("/", "").lower()


def get_project_symbol(binance_symbol):
    for symbol in SYMBOLS:
        if normalize_symbol(symbol).upper() == binance_symbol:
            return symbol

    return None

def get_active_price_alerts(symbol):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            pa.id,
            pa.user_id,
            pa.symbol,
            pa.target_price,
            pa.direction
        FROM price_alerts pa
        JOIN users u
            ON pa.user_id = u.id
        WHERE pa.symbol = %s
          AND pa.is_active = TRUE
          AND u.is_active = TRUE;
    """, (symbol,))

    alerts = cur.fetchall()

    cur.close()
    conn.close()

    return alerts


def should_trigger_alert(current_price, target_price, direction):
    if direction == "above":
        return current_price >= target_price

    if direction == "below":
        return current_price <= target_price

    return False


def create_price_notification(alert, current_price):
    alert_id, user_id, symbol, target_price, direction = alert

    conn = get_connection()
    cur = conn.cursor()

    message = (
        f"Alerte prix {symbol} : "
        f"prix actuel {current_price:.2f}, "
        f"objectif {target_price:.2f}, "
        f"direction {direction}."
    )

    cur.execute("""
        INSERT INTO notifications (
            user_id,
            prediction_id,
            symbol,
            notification_type,
            message,
            status,
            sent_at
        )
        VALUES (%s, NULL, %s, %s, %s, %s, NULL);
    """, (
        user_id,
        symbol,
        "price_target",
        message,
        "pending",
    ))

    cur.execute("""
        UPDATE price_alerts
        SET is_active = FALSE,
            triggered_at = %s
        WHERE id = %s;
    """, (
        datetime.now(),
        alert_id,
    ))

    conn.commit()
    cur.close()
    conn.close()

    print(
        f"Notification price_target créée | "
        f"user_id={user_id} | {symbol} | prix={current_price}"
    )


def check_price_alerts(symbol, current_price):
    alerts = get_active_price_alerts(symbol)

    for alert in alerts:
        _, _, _, target_price, direction = alert

        if should_trigger_alert(current_price, target_price, direction):
            create_price_notification(alert, current_price)


async def listen_price_stream():

    streams = "/".join(
        f"{normalize_symbol(symbol)}@trade"
        for symbol in SYMBOLS
    )

    url = BINANCE_WS_URL + streams

    print(f"Connexion WebSocket prix Binance : {url}")

    async with websockets.connect(url, ping_interval=20, ping_timeout=20) as websocket:
        async for message in websocket:
            payload = json.loads(message)
            data = payload["data"]

            symbol = get_project_symbol(data["s"])

            if symbol is None:
                continue

            current_price = float(data["p"])

            print(f"{symbol} | prix live : {current_price}")

            check_price_alerts(symbol, current_price)


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