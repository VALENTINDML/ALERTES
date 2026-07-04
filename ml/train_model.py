"""
Entraînement des modèles de prédiction crypto.

Pour chaque symbole configuré :
- charge les features depuis PostgreSQL ;
- entraîne un modèle RandomForestRegressor ;
- évalue ses performances ;
- sauvegarde le modèle dans le dossier models/.

La cible prédite est la variation future du prix
sur les prochaines 24 heures.
"""
import os
import joblib
import pandas as pd
import numpy as np
import shutil

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from datetime import datetime, timedelta, timezone

from config.symbols import SYMBOLS
from config.db import get_connection
from config.config_db import DAYS_HISTORY

# Features utilisées à l'entraînement.
# Cette liste doit rester strictement identique à celle utilisée dans predict.py.
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

# Variable cible : variation future du prix à horizon 24h.
TARGET = "target_24h_percent"

MODELS_DIR = "models"
MODEL_ARCHIVE_DIR = f"{MODELS_DIR}/archive"

def get_model_path(symbol):
    safe_symbol = symbol.replace("/", "_")
    return f"{MODELS_DIR}/{safe_symbol}_model.pkl"


def get_archived_model_path(symbol):
    safe_symbol = symbol.replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{MODEL_ARCHIVE_DIR}/{safe_symbol}_model_{timestamp}.pkl"


def archive_existing_model(symbol):
    """
    Archive le modèle actif avant de le remplacer.
    """
    model_path = get_model_path(symbol)

    if not os.path.exists(model_path):
        return None

    os.makedirs(MODEL_ARCHIVE_DIR, exist_ok=True)

    archived_path = get_archived_model_path(symbol)

    shutil.copy2(model_path, archived_path)

    return archived_path

def load_features(symbol):
    """
    Charge les features d'un symbole depuis PostgreSQL.

    Les données sont limitées aux DAYS_HISTORY derniers jours.
    La dernière ligne est exclue afin d'être réservée à la prédiction.
    """
    conn = get_connection()

    start_datetime = (
        datetime.now(timezone.utc)
        - timedelta(days=DAYS_HISTORY)
    ).replace(tzinfo=None)

    query = """
        SELECT *
        FROM features_crypto
        WHERE symbol = %(symbol)s
          AND datetime >= %(start_datetime)s
        ORDER BY datetime ASC;
    """

    df = pd.read_sql(
        query,
        conn,
        params={
            "symbol": symbol,
            "start_datetime": start_datetime,
        },
    )

    conn.close()

    if len(df) <= 1:
        return pd.DataFrame()

    # La dernière ligne est réservée à predict.py.
    return df.iloc[:-1].copy()


def save_metrics(symbol, mae, rmse, mape, r2):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO model_metrics (
            symbol,
            mae,
            rmse,
            mape,
            r2
        )
        VALUES (%s,%s,%s,%s,%s);
        """,
        (
            symbol,
            mae,
            rmse,
            mape,
            r2,
        )
    )

    conn.commit()
    cur.close()
    conn.close()

def evaluate_model(model, X_test, y_test):
    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)

    rmse = np.sqrt(
        mean_squared_error(y_test, predictions)
    )

    mape = (
        np.abs((y_test - predictions) / y_test)
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .mean()
        * 100
    )

    r2 = r2_score(y_test, predictions)

    return {
        "predictions": predictions,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "r2": r2,
    }


def is_new_model_better(old_metrics, new_metrics):
    if new_metrics["rmse"] < old_metrics["rmse"]:
        return True

    if new_metrics["rmse"] == old_metrics["rmse"]:
        return new_metrics["mae"] < old_metrics["mae"]

    return False

def train_symbol_model(symbol):
    """
    Entraîne un nouveau modèle RandomForest pour un symbole donné.

    Si aucun ancien modèle n'existe, le nouveau modèle est sauvegardé.

    Si un ancien modèle existe :
    - l'ancien modèle est évalué sur le même jeu de test ;
    - le nouveau modèle est évalué sur le même jeu de test ;
    - si le nouveau modèle est meilleur, l'ancien est archivé
      puis le nouveau devient le modèle actif ;
    - sinon, l'ancien modèle reste actif.

    Args:
        symbol (str):
            Symbole crypto à entraîner.

    Returns:
        None
    """
    print(f"Entraînement du modèle pour {symbol}...")

    df = load_features(symbol)

    if df.empty:
        print(f"Aucune feature trouvée pour {symbol}")
        return

    if len(df) < 10:
        print(f"Pas assez de données pour entraîner {symbol}")
        return

    print(df[TARGET].describe())

    # Split chronologique : on évite le shuffle pour respecter l'ordre temporel
    # des données financières et limiter le risque de data leakage.
    X = df[FEATURES]
    y = df[TARGET]

    split_index = int(len(df) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    if X_train.empty or X_test.empty:
        print(f"Split train/test invalide pour {symbol}")
        return

    # Modèle robuste et simple à maintenir pour une première version.
    # n_jobs=-1 permet d'utiliser tous les cœurs CPU disponibles.
    model = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    new_metrics = evaluate_model(model, X_test, y_test)

    results = pd.DataFrame({
        "real": y_test,
        "pred": new_metrics["predictions"],
    })

    print(results.head(20))

    print(f"{symbol} - Nouveau modèle")
    print(f"MAE  : {new_metrics['mae']:.4f}%")
    print(f"RMSE : {new_metrics['rmse']:.4f}%")
    print(f"MAPE : {new_metrics['mape']:.2f}%")
    print(f"R2   : {new_metrics['r2']:.4f}")

    os.makedirs(MODELS_DIR, exist_ok=True)

    model_path = get_model_path(symbol)

    should_save_new_model = True

    if os.path.exists(model_path):
        old_model = joblib.load(model_path)

        old_metrics = evaluate_model(old_model, X_test, y_test)

        print(f"{symbol} - Ancien modèle")
        print(f"MAE  : {old_metrics['mae']:.4f}%")
        print(f"RMSE : {old_metrics['rmse']:.4f}%")
        print(f"MAPE : {old_metrics['mape']:.2f}%")
        print(f"R2   : {old_metrics['r2']:.4f}")

        # Le nouveau modèle est accepté uniquement s'il améliore le RMSE,
        # puis le MAE en cas d'égalité.
        should_save_new_model = is_new_model_better(
            old_metrics,
            new_metrics,
        )

    if should_save_new_model:
        archived_path = archive_existing_model(symbol)

        joblib.dump(model, model_path)

        save_metrics(
            symbol,
            new_metrics["mae"],
            new_metrics["rmse"],
            new_metrics["mape"],
            new_metrics["r2"],
        )

        if archived_path:
            print(f"Ancien modèle archivé : {archived_path}")

        print(f"Nouveau modèle accepté et sauvegardé : {model_path}\n")

    else:
        print(f"Nouveau modèle refusé pour {symbol}. Ancien modèle conservé.\n")

def main():
    """
    Lance l'entraînement pour tous les symboles configurés.
    """
    for symbol in SYMBOLS:
        train_symbol_model(symbol)

    print("Entraînement terminé.")


if __name__ == "__main__":
    main()