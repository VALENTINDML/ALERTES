"""
Collecte des bougies OHLCV depuis Binance via CCXT.

Ce script récupère l'historique des bougies pour les paires définies
dans config.symbols, puis stocke les données dans PostgreSQL.

La table utilisée est ccxt_ohlcv.
Les doublons sont évités grâce à la contrainte UNIQUE(symbol, timestamp, timeframe)
et à l'instruction ON CONFLICT DO UPDATE.
"""

import time 
from datetime import datetime, timedelta, timezone

import ccxt 
from psycopg2.extras import execute_values 

from config.config_db import TIMEFRAME, DAYS_HISTORY
from config.symbols import SYMBOLS 
from config.db import get_connection


def fetch_ohlcv_history(exchange, symbol: str):
    """
    Récupère l'historique OHLCV d'une paire depuis Binance.

    Args:
        exchange:
            Instance CCXT de l'exchange utilisé.
        symbol (str):
            Paire crypto à récupérer, par exemple "BTC/USDT".

    Returns:
        list:
            Liste des bougies retournées par CCXT.
            Chaque bougie contient :
            [timestamp, open, high, low, close, volume].
    """

    # Point de départ de la collecte : on remonte sur DAYS_HISTORY jours
    # à partir de l'heure actuelle.
    since=int(
        (datetime.now(timezone.utc) - timedelta(days=DAYS_HISTORY)).timestamp() * 1000
    )

    all_rows=[]

    # Binance limite le nombre de bougies retournées par appel.
    # On pagine donc les résultats jusqu'à récupérer tout l'historique demandé.
    limit=1000

    while True:
        candles = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=TIMEFRAME,
            since=since,
            limit=limit,
        )

        if not candles:
            break

        all_rows.extend(candles)

        # On avance le curseur juste après la dernière bougie reçue
        # pour éviter de récupérer deux fois la même donnée.
        last_timestamp = candles[-1][0]
        since = last_timestamp + 1

        if len(candles) < limit:
            break

      # Respecte la limite de requêtes de l'exchange.
        time.sleep(exchange.rateLimit / 1000)

    return all_rows


def save_ohlcv(symbol: str, candles):
    """
    Sauvegarde les bougies OHLCV dans PostgreSQL.

    Args:
        symbol (str):
            Paire crypto concernée.
        candles (list):
            Liste de bougies au format CCXT.

    Returns:
        None
    """
    if not candles:
        return

    conn = get_connection()
    cur = conn.cursor()

    rows = [
        (
            symbol,
            candle[0],
            datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc).replace(tzinfo=None),
            TIMEFRAME,
            candle[1],
            candle[2],
            candle[3],
            candle[4],
            candle[5],
        )
        for candle in candles
    ]

    # Insertion batch pour éviter une requête SQL par bougie.
    execute_values(
        cur,
        """
        INSERT INTO ccxt_ohlcv (
            symbol, timestamp, datetime, timeframe,
            open, high, low, close, volume
        )
        VALUES %s
        ON CONFLICT (symbol, timestamp, timeframe)
        DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume;
        """,
        rows,
    )

    conn.commit()
    cur.close()
    conn.close()


def main():
    """
    Point d'entrée du script.

    Crée une instance Binance via CCXT, récupère les bougies
    pour chaque symbole configuré, puis sauvegarde les données en base.
    """

    exchange = ccxt.binance({
        "enableRateLimit": True,
    })

    for symbol in SYMBOLS:
        print(f"Récupération de {symbol} sur {DAYS_HISTORY} jours en {TIMEFRAME}...")

        candles = fetch_ohlcv_history(exchange, symbol)

        print(f"{symbol} : {len(candles)} bougies récupérées")

        save_ohlcv(symbol, candles)

        print(f"{symbol} : sauvegarde terminée\n")

    print("Collecte terminée.")


if __name__ == "__main__":
    main()