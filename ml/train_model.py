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

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from config.symbols import SYMBOLS
from config.db import get_connection


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

TARGET = "target_24h_percent"

MODELS_DIR = "models"


def load_features(symbol):
    """
    Charge les features d'un symbole depuis PostgreSQL.

    Args:
        symbol (str):
            Symbole crypto à charger.

    Returns:
        pd.DataFrame:
            Dataset complet contenant les features et la cible.
    """
    conn = get_connection()

    query = """
        SELECT *
        FROM features_crypto
        WHERE symbol = %(symbol)s
        ORDER BY datetime ASC
    """

    df = pd.read_sql(
        query,
        conn,
        params={"symbol": symbol}
    )

    conn.close()

    return df


def train_symbol_model(symbol):
    """
    Entraîne un modèle RandomForest pour un symbole donné.

    Étapes :
    - chargement des features ;
    - séparation train/test chronologique ;
    - entraînement ;
    - évaluation ;
    - sauvegarde du modèle.

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

    print(df[TARGET].describe())

    X = df[FEATURES]
    y = df[TARGET]

    # Conserve l'ordre temporel des données.
    # On évite volontairement un train_test_split aléatoire
    # pour reproduire un scénario réel de prédiction.
    split_index = int(len(df) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    # Random Forest utilisée comme premier modèle baseline.
    model = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    results=pd.DataFrame({
        "real": y_test,
        "pred": predictions
    })

    print(results.head(20))

    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"{symbol} - MAE : {mae:.4f}%")
    print(f"{symbol} - R2  : {r2:.4f}")

    os.makedirs(MODELS_DIR, exist_ok=True)

    # Un modèle est sauvegardé par symbole.
    safe_symbol = symbol.replace("/", "_")
    model_path = f"{MODELS_DIR}/{safe_symbol}_model.pkl"

    joblib.dump(model, model_path)

    print(f"Modèle sauvegardé : {model_path}\n")


def main():
    """
    Lance l'entraînement pour tous les symboles configurés.
    """
    for symbol in SYMBOLS:
        train_symbol_model(symbol)

    print("Entraînement terminé.")


if __name__ == "__main__":
    main()