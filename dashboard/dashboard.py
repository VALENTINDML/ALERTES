"""
Dashboard Streamlit du projet Crypto Alerts.
"""
import os

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh


API_URL = os.getenv("API_URL", "http://api:8000")


st.set_page_config(
    page_title="Alertes Dashboard",
    page_icon="📊",
    layout="wide",
)

st_autorefresh(interval=2000, key="live_refresh")


def get_api_data(endpoint):
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erreur API : {e}")
        return None


st.title("📊 Crypto Alerts Dashboard")
st.caption("Dashboard MVP — Prédiction crypto + alertes utilisateurs")


health = get_api_data("/health")

if health and health.get("status") == "ok":
    st.success("API FastAPI connectée")
else:
    st.error("API FastAPI indisponible")


users_count = get_api_data("/users/count")
market_latest = get_api_data("/market/latest")
live_market = get_api_data("/market/live?symbol=BTC/USDT")
latest_predictions = get_api_data("/predictions/latest")
daily_alerts = get_api_data("/daily-alerts/count")
notifications_stats = get_api_data("/notifications/stats")
notifications_by_type = get_api_data("/notifications/by-type")
model_metrics = get_api_data("/metrics/model/latest")


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Utilisateurs",
        users_count["users_count"] if users_count else 0,
    )

with col2:
    total_notifications = 0

    if notifications_stats:
        total_notifications = sum(
            item["count"] for item in notifications_stats
        )

    st.metric(
        "Notifications",
        total_notifications,
    )

with col3:
    if market_latest and "close" in market_latest:
        st.metric(
            "Prix utilisé par le modèle",
            f"{market_latest['close']:.2f} USDT",
        )
    else:
        st.metric("Prix utilisé par le modèle", "N/A")

with col4:
    if latest_predictions:
        pred = latest_predictions[0]
        st.metric(
            "Prévision 24h",
            f"{pred['predicted_change_24h']:.2f}%",
            pred["trend"],
        )
    else:
        st.metric("Prévision 24h", "N/A")


st.divider()
st.subheader("📡 Bougie live BTC/USDT — 1h")

if live_market and "error" not in live_market:
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Open", f"{live_market['open']:.2f}")
    c2.metric("High", f"{live_market['high']:.2f}")
    c3.metric("Low", f"{live_market['low']:.2f}")
    c4.metric("Close live", f"{live_market['close']:.2f}")
    c5.metric("Volume", f"{live_market['volume']:.2f}")

    st.json({
        "symbol": live_market["symbol"],
        "timeframe": live_market["timeframe"],
        "datetime": live_market["datetime"],
        "is_closed": live_market["is_closed"],
        "updated_at": live_market["updated_at"],
    })
else:
    st.info("Aucune donnée live disponible pour le moment.")


st.divider()
st.subheader("💰 Dernière bougie historique BTC/USDT")

if market_latest and "error" not in market_latest:
    st.json(market_latest)
else:
    st.info("Aucune donnée marché disponible.")


st.divider()
st.subheader("🔮 Dernières prédictions")

if latest_predictions:
    df_predictions = pd.DataFrame(latest_predictions)
    st.dataframe(df_predictions, use_container_width=True)
else:
    st.info("Aucune prédiction disponible.")


st.divider()
st.subheader("📈 Performance du modèle")

if model_metrics:
    df_metrics = pd.DataFrame(model_metrics)
    st.dataframe(df_metrics, use_container_width=True)

    btc_metrics = df_metrics[df_metrics["symbol"] == "BTC/USDT"]

    if not btc_metrics.empty:
        btc = btc_metrics.iloc[0]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("MAE", f"{btc['mae']:.2f}%")
        c2.metric("RMSE", f"{btc['rmse']:.2f}%")
        c3.metric("MAPE", f"{btc['mape']:.2f}%")
        c4.metric("R²", f"{btc['r2']:.3f}")
else:
    st.info("Aucune métrique modèle disponible.")


st.divider()
st.subheader("📩 Notifications par type")

if notifications_stats:
    df_notifications_stats = pd.DataFrame(notifications_stats)

    st.dataframe(df_notifications_stats, use_container_width=True)
else:
    st.info("Aucune statistique de notification disponible.")


st.divider()
st.subheader("📬 Notifications par type et statut")

if notifications_by_type:
    df_notifications_by_type = pd.DataFrame(notifications_by_type)

    st.dataframe(df_notifications_by_type, use_container_width=True)
else:
    st.info("Aucune notification disponible.")


st.divider()
st.subheader("🔔 Alertes quotidiennes")

if daily_alerts:
    df_alerts = pd.DataFrame(daily_alerts)

    df_alerts["enabled"] = df_alerts["enabled"].map({
        True: "Activées",
        False: "Désactivées",
    })

    st.dataframe(
        df_alerts,
        use_container_width=True,
    )
else:
    st.info("Aucune préférence d'alerte disponible.")