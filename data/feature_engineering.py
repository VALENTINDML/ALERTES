"""
Feature engineering pour le modèle de prédiction crypto.

Ce script lit les bougies OHLCV stockées dans PostgreSQL,
calcule des indicateurs techniques simples, puis sauvegarde
les features dans la table features_crypto.

La cible du modèle est target_24h_percent :
variation future du prix de clôture sur les prochaines 24 heures.
"""
import pandas as pd
from psycopg2.extras import execute_values

from config.config_db import TIMEFRAME
from config.symbols import SYMBOLS
from config.db import get_connection


def compute_rsi(close, period=14):
    """
    Calcule le RSI sur une série de prix de clôture.

    Args:
        close (pd.Series):
            Série des prix de clôture.
        period (int):
            Nombre de périodes utilisées pour le calcul du RSI.

    Returns:
        pd.Series:
            Série contenant le RSI calculé.
    """
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def build_features(df):
    """
    Calcule les features utilisées par le modèle ML.

    Args:
        df (pd.DataFrame):
            Données OHLCV issues de la table ccxt_ohlcv.

    Returns:
        pd.DataFrame:
            DataFrame enrichi avec les features et la cible.
    """

    # Tri chronologique indispensable avant les pct_change, rolling et shift.
    df = df.sort_values("datetime").copy()

    # Variations passées du prix.
    df["return_1h"] = df["close"].pct_change(1)
    df["return_6h"] = df["close"].pct_change(6)
    df["return_24h"] = df["close"].pct_change(24)

    # Moyennes mobiles exponentielles.
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()

    # Momentum.
    df["rsi_14"] = compute_rsi(df["close"], period=14)

    # Volatilité récente.
    df["volatility_24h"] = df["return_1h"].rolling(24).std()

    # Activité relative du marché.
    df["volume_ma_24h"] = df["volume"].rolling(24).mean()
    df["volume_ratio"] = df["volume"] / df["volume_ma_24h"]

    # Cible à prédire : variation du close dans 24h.
    df["target_24h_percent"] = (
        (df["close"].shift(-24) - df["close"]) / df["close"]
    ) * 100

    # Suppression des lignes incomplètes générées par rolling/shift.
    df = df.dropna()

    return df


def save_features(df):
    """
    Sauvegarde les features calculées dans PostgreSQL.

    Args:
        df (pd.DataFrame):
            DataFrame contenant les features calculées.

    Returns:
        None
    """
    if df.empty:
        return

    conn = get_connection()
    cur = conn.cursor()

    rows = [
        (
            row.symbol,
            row.timestamp,
            row.datetime,
            row.timeframe,
            row.open,
            row.high,
            row.low,
            row.close,
            row.volume,
            row.return_1h,
            row.return_6h,
            row.return_24h,
            row.ema_20,
            row.ema_50,
            row.rsi_14,
            row.volatility_24h,
            row.volume_ratio,
            row.target_24h_percent,
        )
        for row in df.itertuples(index=False)
    ]

    # Insertion batch pour sauvegarder efficacement plusieurs lignes de features.
    execute_values(
        cur,
        """
        INSERT INTO features_crypto (
            symbol, timestamp, datetime, timeframe,
            open, high, low, close, volume,
            return_1h, return_6h, return_24h,
            ema_20, ema_50, rsi_14,
            volatility_24h, volume_ratio,
            target_24h_percent
        )
        VALUES %s
        ON CONFLICT (symbol, timestamp, timeframe)
        DO UPDATE SET
            datetime = EXCLUDED.datetime,
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            return_1h = EXCLUDED.return_1h,
            return_6h = EXCLUDED.return_6h,
            return_24h = EXCLUDED.return_24h,
            ema_20 = EXCLUDED.ema_20,
            ema_50 = EXCLUDED.ema_50,
            rsi_14 = EXCLUDED.rsi_14,
            volatility_24h = EXCLUDED.volatility_24h,
            volume_ratio = EXCLUDED.volume_ratio,
            target_24h_percent = EXCLUDED.target_24h_percent;
        """,
        rows,
    )

    conn.commit()
    cur.close()
    conn.close()


def main():
    """
    Point d'entrée du script.

    Pour chaque symbole configuré :
    - lit les bougies OHLCV depuis ccxt_ohlcv ;
    - calcule les features ;
    - sauvegarde les résultats dans features_crypto.
    """

    for symbol in SYMBOLS:
        print(f"Création des features pour {symbol}...")

        # Les features sont recalculées symbole par symbole pour isoler les séries temporelles.
        query = """
            SELECT *
            FROM ccxt_ohlcv
            WHERE symbol = %(symbol)s
            ORDER BY datetime ASC
        """

        conn = get_connection()

        df = pd.read_sql(
            query,
            conn,
            params={"symbol": symbol}
        )

        conn.close()

        if df.empty:
            print(f"Aucune donnée trouvée pour {symbol}")
            continue

        features_df = build_features(df)

        save_features(features_df)

        print(
            f"{symbol} : "
            f"{len(features_df)} lignes de features sauvegardées"
        )

    print("Feature engineering terminé.")


if __name__ == "__main__":
    main()