"""
Application des modèles entraînés.

Ce script charge le dernier jeu de features disponible pour chaque symbole,
applique le modèle ML correspondant, sauvegarde la prédiction dans PostgreSQL,
puis génère les notifications quotidiennes associées.

La table utilisée pour les résultats est predictions.
"""
import os
import joblib
import pandas as pd
from psycopg2.extras import execute_values

from config.symbols import SYMBOLS
from config.db import get_connection
from alerts.generate_notifications import generate_daily_notifications


FEATURES = [
    "return_1h",
    "return_6h",
    "return_24h",
    "ema_20",
    "ema_50",
    "rsi_14",
    "volatility_24h",
    "volume_ratio",
]

MODELS_DIR = "models"


def load_latest_features(symbol):
    """
    Charge la dernière ligne de features disponible pour un symbole.

    Args:
        symbol (str):
            Symbole crypto à prédire, par exemple "BTC/USDT".

    Returns:
        pd.DataFrame:
            DataFrame contenant la dernière ligne de features.
    """
    conn = get_connection()

    query = """
        SELECT *
        FROM features_crypto
        WHERE symbol = %(symbol)s
        ORDER BY datetime DESC
        LIMIT 1
    """

    df = pd.read_sql(
        query,
        conn,
        params={"symbol": symbol}
    )

    conn.close()

    return df


def classify_trend(predicted_change):
    """
    Convertit une variation prédite en tendance lisible.

    Args:
        predicted_change (float):
            Variation prédite en pourcentage sur 24h.

    Returns:
        str:
            "hausse", "baisse" ou "stagnation".
    """
    if predicted_change > 0.5:
        return "hausse"
    elif predicted_change < -0.5:
        return "baisse"
    else:
        return "stagnation"


def save_prediction(symbol, prediction_datetime, predicted_change, trend, model_path):
    """
    Sauvegarde une prédiction dans PostgreSQL.

    Si une prédiction existe déjà pour le même symbole et la même date,
    elle est mise à jour au lieu d'être dupliquée.

    Args:
        symbol (str):
            Symbole crypto concerné.
        prediction_datetime:
            Date de référence de la feature utilisée.
        predicted_change (float):
            Variation prédite sur 24h.
        trend (str):
            Tendance associée à la prédiction.
        model_path (str):
            Chemin du modèle utilisé.

    Returns:
        None
    """
    conn = get_connection()
    cur = conn.cursor()

    execute_values(
        cur,
        """
        INSERT INTO predictions (
            symbol,
            prediction_datetime,
            predicted_change_24h,
            trend,
            model_path
        )
        VALUES %s
        ON CONFLICT (symbol, prediction_datetime)
        DO UPDATE SET
            predicted_change_24h = EXCLUDED.predicted_change_24h,
            trend = EXCLUDED.trend,
            model_path = EXCLUDED.model_path,
            created_at = CURRENT_TIMESTAMP;
        """,
        [
            (
                symbol,
                prediction_datetime,
                predicted_change,
                trend,
                model_path,
            )
        ],
    )

    conn.commit()
    cur.close()
    conn.close()


def predict_symbol(symbol):
    """
    Charge le modèle d'un symbole, applique la prédiction,
    sauvegarde le résultat et déclenche les notifications.

    Args:
        symbol (str):
            Symbole crypto à prédire.

    Returns:
        None
    """
    safe_symbol = symbol.replace("/", "_")
    model_path = f"{MODELS_DIR}/{safe_symbol}_model.pkl"

    if not os.path.exists(model_path):
        print(f"Modèle introuvable pour {symbol} : {model_path}")
        return

    df = load_latest_features(symbol)

    if df.empty:
        print(f"Aucune feature disponible pour {symbol}")
        return

    model = joblib.load(model_path)

    X_latest = df[FEATURES]

    predicted_change = model.predict(X_latest)[0]

    trend = classify_trend(predicted_change)

    prediction_datetime = df.iloc[0]["datetime"]

    save_prediction(
        symbol=symbol,
        prediction_datetime=prediction_datetime,
        predicted_change=float(predicted_change),
        trend=trend,
        model_path=model_path,
    )

    # Les notifications sont générées après la sauvegarde,
    # afin de pouvoir relier chaque notification à une prediction_id.
    generate_daily_notifications(symbol)

    print(
        f"{symbol} | "
        f"Prévision 24h : {predicted_change:.2f}% | "
        f"Tendance : {trend}"
    )


def main():
    """
    Lance la prédiction pour tous les symboles configurés.
    """

    for symbol in SYMBOLS:
        predict_symbol(symbol)

    print("Prédictions terminées.")


if __name__ == "__main__":
    main()