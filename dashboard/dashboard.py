"""
Dashboard Streamlit du projet Crypto Alerts.
"""

import os

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh


API_URL = os.getenv("API_URL", "http://api:8000")
ALL_SYMBOLS_LABEL = "Toutes"

st.set_page_config(
    page_title="Crypto Alerts Dashboard",
    page_icon="📊",
    layout="wide",
)

st_autorefresh(interval=1000, key="dashboard_refresh")


@st.cache_data(ttl=1)
def get_api_data(endpoint):
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def build_endpoint(endpoint, selected_symbol):
    if selected_symbol == ALL_SYMBOLS_LABEL:
        return endpoint

    return f"{endpoint}?symbol={selected_symbol}"


def to_dataframe(data):
    if isinstance(data, list):
        return pd.DataFrame(data)

    if isinstance(data, dict) and "error" not in data:
        return pd.DataFrame([data])

    return pd.DataFrame()


def get_available_symbols():
    symbols_data = get_api_data("/symbols")

    if isinstance(symbols_data, list) and symbols_data:
        symbols = [item["symbol"] for item in symbols_data]
        return [ALL_SYMBOLS_LABEL] + symbols

    return [ALL_SYMBOLS_LABEL]


st.title("📊 Crypto Alerts Dashboard")
st.caption("Dashboard opérationnel — prédictions crypto, données live et alertes utilisateurs")

health = get_api_data("/health")

if health and health.get("status") == "ok":
    st.success("API FastAPI connectée")
else:
    st.error("API FastAPI indisponible")

available_symbols = get_available_symbols()

selected_symbol = st.selectbox(
    "Sélectionner une cryptomonnaie",
    available_symbols,
)

if selected_symbol == ALL_SYMBOLS_LABEL:
    symbols_text = ", ".join(
        symbol for symbol in available_symbols
        if symbol != ALL_SYMBOLS_LABEL
    )

    st.info(f"Toutes les cryptomonnaies ({symbols_text})")
else:
    st.info(f"Focus {selected_symbol}")


users_count = get_api_data("/users/count")
market_latest = get_api_data(build_endpoint("/market/latest", selected_symbol))
live_market = get_api_data(build_endpoint("/market/live", selected_symbol))
latest_predictions = get_api_data(build_endpoint("/predictions/latest", selected_symbol))
daily_alerts = get_api_data(build_endpoint("/daily-alerts/count", selected_symbol))
notifications_stats = get_api_data(build_endpoint("/notifications/stats", selected_symbol))
notifications_by_type = get_api_data(build_endpoint("/notifications/by-type", selected_symbol))
model_metrics = get_api_data(build_endpoint("/metrics/model/latest", selected_symbol))


df_market_latest = to_dataframe(market_latest)
df_live_market = to_dataframe(live_market)
df_predictions = to_dataframe(latest_predictions)
df_metrics = to_dataframe(model_metrics)
df_daily_alerts = to_dataframe(daily_alerts)
df_notifications_stats = to_dataframe(notifications_stats)
df_notifications_by_type = to_dataframe(notifications_by_type)


col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Utilisateurs",
        users_count.get("users_count", 0)
        if isinstance(users_count, dict)
        else 0,
    )

with col2:
    total_notifications = (
        int(df_notifications_stats["count"].sum())
        if not df_notifications_stats.empty and "count" in df_notifications_stats
        else 0
    )
    st.metric("Notifications", total_notifications)

with col3:
    if selected_symbol == ALL_SYMBOLS_LABEL:
        st.metric(
            "Cryptos suivies",
            max(len(available_symbols) - 1, 0),
        )

    elif not df_live_market.empty:
        live_price = df_live_market.iloc[0]["close"]

        st.metric(
            f"Cours actuel {selected_symbol}",
            f"{live_price:.2f} USDT",
        )

    else:
        st.metric(
            f"Cours actuel {selected_symbol}",
            "N/A",
        )

with col4:
    if selected_symbol == ALL_SYMBOLS_LABEL:
        st.metric(
            "Prix modèle",
            "Toutes",
        )
    elif not df_market_latest.empty:
        model_price = df_market_latest.iloc[0]["close"]

        st.metric(
            f"Prix utilisé modèle {selected_symbol}",
            f"{model_price:.2f} USDT",
        )
    else:
        st.metric(f"Prix utilisé modèle {selected_symbol}", "N/A")

with col5:
    if selected_symbol != ALL_SYMBOLS_LABEL and not df_predictions.empty:
        pred = df_predictions.iloc[0]
        st.metric(
            f"Prévision 24h {selected_symbol}",
            f"{pred['predicted_change_24h']:.2f}%",
            pred["trend"],
        )
    else:
        st.metric("Mode d'affichage", selected_symbol)


st.divider()
st.subheader(
    "📡 Bougies live"
    if selected_symbol == ALL_SYMBOLS_LABEL
    else f"📡 Bougie live {selected_symbol}"
)

if not df_live_market.empty:
    if selected_symbol == ALL_SYMBOLS_LABEL:
        st.dataframe(df_live_market, use_container_width=True)
    else:
        live = df_live_market.iloc[0]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Close live", f"{live['close']:.2f}")
        c2.metric("Open", f"{live['open']:.2f}")
        c3.metric("High", f"{live['high']:.2f}")
        c4.metric("Low", f"{live['low']:.2f}")
        c5.metric("Volume", f"{live['volume']:.2f}")

        st.json({
            "symbol": live["symbol"],
            "timeframe": live["timeframe"],
            "datetime": str(live["datetime"]),
            "is_closed": bool(live["is_closed"]),
            "updated_at": str(live["updated_at"]),
        })
else:
    st.info("Aucune donnée live disponible.")


st.divider()
st.subheader(
    "🔮 Dernières prédictions"
    if selected_symbol == ALL_SYMBOLS_LABEL
    else f"🔮 Dernière prédiction - {selected_symbol}"
)

if not df_predictions.empty:
    st.dataframe(df_predictions, use_container_width=True)
else:
    st.info("Aucune prédiction disponible.")


st.divider()
st.subheader(
    "📈 Performance des modèles"
    if selected_symbol == ALL_SYMBOLS_LABEL
    else f"📈 Performance du modèle - {selected_symbol}"
)

if not df_metrics.empty:
    st.dataframe(df_metrics, use_container_width=True)

    if selected_symbol != ALL_SYMBOLS_LABEL:
        metrics = df_metrics.iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("MAE", f"{metrics['mae']:.2f}%")
        c2.metric("RMSE", f"{metrics['rmse']:.2f}%")
        c3.metric("MAPE", f"{metrics['mape']:.2f}%")
        c4.metric("R²", f"{metrics['r2']:.3f}")
else:
    st.info("Aucune métrique modèle disponible.")


st.divider()
st.subheader("📩 Notifications par type")

if not df_notifications_stats.empty:
    st.dataframe(
        df_notifications_stats,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Aucune statistique de notification disponible.")


st.divider()
st.subheader("📬 Notifications par type et statut")

if not df_notifications_by_type.empty:
    st.dataframe(
        df_notifications_by_type,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Aucune notification disponible.")


st.divider()
st.subheader("🔔 Alertes quotidiennes")

if not df_daily_alerts.empty:
    df_daily_alerts["enabled"] = df_daily_alerts["enabled"].map({
        True: "Activées",
        False: "Désactivées",
    })

    st.dataframe(
        df_daily_alerts,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Aucune préférence d'alerte disponible.")