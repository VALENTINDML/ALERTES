import asyncio
import json
from datetime import datetime, timezone

import websockets

from config.config_db import TIMEFRAME
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


def init_live_market_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_market_data (
            id SERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            timestamp BIGINT NOT NULL,
            datetime TIMESTAMP NOT NULL,
            timeframe TEXT NOT NULL,
            open DOUBLE PRECISION NOT NULL,
            high DOUBLE PRECISION NOT NULL,
            low DOUBLE PRECISION NOT NULL,
            close DOUBLE PRECISION NOT NULL,
            volume DOUBLE PRECISION NOT NULL,
            is_closed BOOLEAN NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timeframe)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


def save_live_candle(symbol, kline):
    conn = get_connection()
    cur = conn.cursor()

    timestamp = int(kline["t"])
    candle_datetime = datetime.fromtimestamp(
        timestamp / 1000,
        tz=timezone.utc
    ).replace(tzinfo=None)

    cur.execute("""
        INSERT INTO live_market_data (
            symbol,
            timestamp,
            datetime,
            timeframe,
            open,
            high,
            low,
            close,
            volume,
            is_closed
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, timeframe)
        DO UPDATE SET
            timestamp = EXCLUDED.timestamp,
            datetime = EXCLUDED.datetime,
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            is_closed = EXCLUDED.is_closed,
            updated_at = CURRENT_TIMESTAMP;
    """, (
        symbol,
        timestamp,
        candle_datetime,
        TIMEFRAME,
        float(kline["o"]),
        float(kline["h"]),
        float(kline["l"]),
        float(kline["c"]),
        float(kline["v"]),
        bool(kline["x"]),
    ))

    conn.commit()
    cur.close()
    conn.close()


async def listen_market_stream():
    init_live_market_table()

    streams = "/".join(
        f"{normalize_symbol(symbol)}@kline_{TIMEFRAME}"
        for symbol in SYMBOLS
    )

    url = BINANCE_WS_URL + streams

    print(f"Connexion WebSocket market stream : {url}")

    async with websockets.connect(url, ping_interval=20, ping_timeout=20) as websocket:
        async for message in websocket:
            payload = json.loads(message)
            kline = payload["data"]["k"]

            symbol = get_project_symbol(kline["s"])

            if symbol is None:
                continue

            save_live_candle(symbol, kline)

            print(
                f"{symbol} | close={float(kline['c']):.2f} | closed={bool(kline['x'])}"
            )


async def main():
    while True:
        try:
            await listen_market_stream()
        except Exception as e:
            print(f"Erreur market stream : {e}")
            print("Reconnexion dans 10 secondes...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())