"""
Dashboard Streamlit du projet Crypto Alerts.

Ce dashboard consomme l'API FastAPI afin d'afficher :

- l'état de l'API ;
- les statistiques utilisateurs ;
- les prédictions récentes ;
- les alertes générées ;
- les dernières données de marché.

Il constitue l'interface de visualisation du MVP.
"""
import requests
import pandas as pd
import streamlit as st
import os


API_URL = os.getenv(
    "API_URL",
    "http://api:8000"
)


st.set_page_config(
    page_title="Crypto Alerts Dashboard",
    page_icon="📊",
    layout="wide",
)


def get_api_data(endpoint):
    """
    Interroge l'API FastAPI et retourne la réponse JSON.

    Args:
        endpoint (str):
            Endpoint à appeler.

    Returns:
        dict | list | None:
            Données retournées par l'API ou None en cas d'erreur.
    """
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erreur API : {e}")
        return None


st.title("📊 Crypto Alerts Dashboard")
st.caption("Dashboard MVP — Prédiction crypto + alertes utilisateurs")


# =========================
# API STATUS
# =========================

health = get_api_data("/health")

if health and health.get("status") == "ok":
    st.success("API FastAPI connectée")
else:
    st.error("API FastAPI indisponible")


# =========================
# METRICS
# =========================

users_count = get_api_data("/users/count")
notifications_count = get_api_data("/notifications/count")
market_latest = get_api_data("/market/latest")
daily_alerts = get_api_data("/daily-alerts/count")
latest_predictions = get_api_data("/predictions/latest")


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Utilisateurs",
        users_count["users_count"] if users_count else 0
    )

with col2:
    st.metric(
        "Notifications",
        notifications_count["notifications_count"] if notifications_count else 0
    )

with col3:
    if market_latest and "close" in market_latest:
        st.metric(
            "Dernier prix BTC",
            f"{market_latest['close']:.2f} USDT"
        )
    else:
        st.metric("Dernier prix BTC", "N/A")

with col4:
    if latest_predictions:
        pred = latest_predictions[0]
        st.metric(
            "Prévision 24h",
            f"{pred['predicted_change_24h']:.2f}%",
            pred["trend"]
        )
    else:
        st.metric("Prévision 24h", "N/A")


# =========================
# LATEST PREDICTIONS
# =========================

st.divider()
st.subheader("🔮 Dernières prédictions")

if latest_predictions:
    df_predictions = pd.DataFrame(latest_predictions)
    st.dataframe(df_predictions, use_container_width=True)
else:
    st.info("Aucune prédiction disponible.")


# =========================
# DAILY ALERTS STATUS
# =========================

st.divider()
st.subheader("🔔 Alertes quotidiennes")

if daily_alerts:
    df_alerts = pd.DataFrame(daily_alerts)

    df_alerts["enabled"] = df_alerts["enabled"].map({
        True: "Activées",
        False: "Désactivées",
    })

    st.bar_chart(
        data=df_alerts,
        x="enabled",
        y="count"
    )

    st.dataframe(df_alerts, use_container_width=True)
else:
    st.info("Aucune préférence d'alerte disponible.")


# =========================
# MARKET DATA
# =========================

st.divider()
st.subheader("💰 Dernière bougie BTC/USDT")

if market_latest and "error" not in market_latest:
    st.json(market_latest)
else:
    st.info("Aucune donnée marché disponible.")


# =========================
# LATEST NOTIFICATIONS
# =========================

st.divider()
st.subheader("📩 Dernières notifications")

latest_notifications = get_api_data("/notifications/latest?limit=20")

if latest_notifications:
    df_notifications = pd.DataFrame(latest_notifications)
    st.dataframe(df_notifications, use_container_width=True)
else:
    st.info("Aucune notification disponible.")