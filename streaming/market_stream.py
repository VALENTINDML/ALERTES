"""
Streaming temps réel des bougies de marché Binance.

Ce service écoute les flux WebSocket kline de Binance pour chaque symbole
configuré dans config/symbols.py, puis maintient en base la dernière bougie
connue dans la table live_market_data.

Cette table est utilisée par l'API et le dashboard Streamlit pour afficher
les données de marché en quasi temps réel.
"""
import asyncio
import json
from datetime import datetime, timezone

import websockets

from config.config_db import TIMEFRAME
from config.db import get_connection
from config.symbols import SYMBOLS


BINANCE_WS_URL = "wss://stream.binance.com:9443/stream?streams="


def normalize_symbol(symbol):
    """
    Convertit un symbole projet au format BTC/USDT
    vers le format attendu par Binance WebSocket : btcusdt.
    """
    return symbol.replace("/", "").lower()


def get_project_symbol(binance_symbol):
    """
    Convertit un symbole Binance, par exemple BTCUSDT,
    vers le symbole utilisé dans le projet, par exemple BTC/USDT.
    """
    for symbol in SYMBOLS:
        if normalize_symbol(symbol).upper() == binance_symbol:
            return symbol

    return None


def save_live_candle(symbol, kline):
    """
    Sauvegarde la dernière bougie reçue pour un symbole.

    La contrainte UNIQUE(symbol, timeframe) permet de maintenir
    une seule ligne par crypto et par timeframe. À chaque nouveau message,
    la ligne existante est mise à jour avec les dernières valeurs.
    """
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
    """
    Ouvre une connexion WebSocket Binance multiplexée.

    Un seul flux WebSocket permet d'écouter toutes les paires configurées
    dans SYMBOLS, au lieu d'ouvrir une connexion séparée par crypto.
    """

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
    """
    Boucle de supervision du WebSocket.

    En cas d'erreur réseau ou de coupure Binance,
    le service attend 10 secondes puis se reconnecte automatiquement.
    """
    while True:
        try:
            await listen_market_stream()
        except Exception as e:
            print(f"Erreur market stream : {e}")
            print("Reconnexion dans 10 secondes...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())