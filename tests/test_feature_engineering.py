import pandas as pd

from data.feature_engineering import compute_rsi, build_features


def make_ohlcv_dataframe(total_rows=80):
    """
    Génère un jeu de bougies OHLCV fictif et déterministe.

    80 lignes permettent d'avoir assez d'historique pour calculer :
    - les rolling windows ;
    - le RSI ;
    - la volatilité 24h ;
    - la cible décalée à +24h.
    """
    rows = []

    for i in range(total_rows):
        rows.append(
            {
                "symbol": "BTC/USDT",
                "timestamp": 1700000000000 + i * 3600000,
                "datetime": pd.Timestamp("2025-01-01") + pd.Timedelta(hours=i),
                "timeframe": "1h",
                "open": 100 + i,
                "high": 101 + i,
                "low": 99 + i,
                "close": 100 + i,
                "volume": 1000 + i,
            }
        )

    return pd.DataFrame(rows)


def test_compute_rsi_returns_series():
    """
    Vérifie que le calcul du RSI conserve la structure attendue :
    une Series Pandas de même longueur que les prix d'entrée.
    """
    close = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114])

    rsi = compute_rsi(close, period=14)

    assert isinstance(rsi, pd.Series)
    assert len(rsi) == len(close)


def test_build_features_creates_expected_columns():
    """
    Vérifie que toutes les colonnes nécessaires au modèle ML
    sont bien générées par le feature engineering.
    """
    df = make_ohlcv_dataframe()

    features_df = build_features(df)

    expected_columns = {
        "return_1h",
        "return_6h",
        "return_24h",
        "ema_20",
        "ema_50",
        "rsi_14",
        "volatility_24h",
        "volume_ratio",
        "target_24h_percent",
    }

    assert expected_columns.issubset(set(features_df.columns))


def test_build_features_removes_missing_values():
    """
    Vérifie que les lignes incomplètes créées par les rolling windows
    et le shift de la cible sont bien supprimées.
    """
    df = make_ohlcv_dataframe()

    features_df = build_features(df)

    assert not features_df.empty
    assert features_df.isna().sum().sum() == 0


def test_target_24h_percent_is_correct():
    """
    Vérifie que la cible ML correspond bien à la variation future
    du prix de clôture à horizon 24h.
    """
    df = make_ohlcv_dataframe()

    features_df = build_features(df)

    first_row = features_df.iloc[0]
    original_index = df[df["timestamp"] == first_row["timestamp"]].index[0]

    expected_target = (
        (df.iloc[original_index + 24]["close"] - df.iloc[original_index]["close"])
        / df.iloc[original_index]["close"]
    ) * 100

    assert round(first_row["target_24h_percent"], 6) == round(expected_target, 6)