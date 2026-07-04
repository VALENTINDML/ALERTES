"""
Initialisation des tables liées aux utilisateurs.

Ce script est exécuté une seule fois lors de l'initialisation
du projet sur une base vide.

Tables créées :

- users
- user_positions
- daily_alert_preferences
- notifications
"""
from config.db import get_connection

def init_users_db():
    conn = get_connection()
    cur = conn.cursor()

    # Utilisateurs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,

            country_code VARCHAR(2),
            country TEXT,
            region TEXT,
            city TEXT,
            postal_code TEXT,
            phone TEXT,
            phone_code TEXT,
            currency VARCHAR(10),
            language VARCHAR(10),
            timezone TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Positions crypto détenues par les utilisateurs.
    # Utilisées pour les futures alertes personnalisées.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_positions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            symbol TEXT NOT NULL,
            buy_price DOUBLE PRECISION NOT NULL CHECK (buy_price > 0),
            quantity DOUBLE PRECISION NOT NULL CHECK (quantity > 0),
            buy_datetime TIMESTAMP NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)

    # Préférences d'abonnement aux alertes quotidiennes.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_alert_preferences (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            symbol TEXT NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            UNIQUE(user_id, symbol)
        );
    """)

    # Création de la table predictions 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id BIGSERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            prediction_datetime TIMESTAMP NOT NULL,
            predicted_change_24h DOUBLE PRECISION NOT NULL,
            trend TEXT NOT NULL CHECK (trend IN('hausse', 'baisse', 'stagnation')),
            model_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            UNIQUE(symbol, prediction_datetime)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            symbol TEXT NOT NULL,
            target_price DOUBLE PRECISION NOT NULL CHECK (target_price > 0),
            direction TEXT NOT NULL CHECK (direction IN ('above', 'below')),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            triggered_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)

    # Historique des notifications générées.
    # Le statut permettra plus tard de gérer l'envoi réel.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            prediction_id BIGINT REFERENCES predictions(id) ON DELETE CASCADE,
            price_alert_id BIGINT REFERENCES price_alerts(id) ON DELETE CASCADE,
            symbol TEXT NOT NULL,
            notification_type TEXT NOT NULL CHECK (notification_type IN ('daily_prediction', 'price_target')),
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)

    # Historique des performances des modèles de Machine Learning.
    # Une ligne est ajoutée à chaque entraînement accepté.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS model_metrics (
            id BIGSERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            mae DOUBLE PRECISION NOT NULL,
            rmse DOUBLE PRECISION NOT NULL,
            mape DOUBLE PRECISION NOT NULL,
            r2 DOUBLE PRECISION NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
    """)

    # Historique des bougies OHLCV collectées depuis Binance.
    # Cette table constitue la source de données brute du pipeline ML.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ccxt_ohlcv (
            id BIGSERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            timestamp BIGINT NOT NULL,
            datetime TIMESTAMP NOT NULL,
            timeframe TEXT NOT NULL,
            open DOUBLE PRECISION NOT NULL,
            high DOUBLE PRECISION NOT NULL,
            low DOUBLE PRECISION NOT NULL,
            close DOUBLE PRECISION NOT NULL,
            volume DOUBLE PRECISION NOT NULL,
            UNIQUE(symbol, timestamp, timeframe)
        );
    """)

    # Données enrichies utilisées pour l'entraînement
    # et les prédictions des modèles de Machine Learning.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS features_crypto (
            id BIGSERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            timestamp BIGINT NOT NULL,
            datetime TIMESTAMP NOT NULL,
            timeframe TEXT NOT NULL,

            open DOUBLE PRECISION NOT NULL,
            high DOUBLE PRECISION NOT NULL,
            low DOUBLE PRECISION NOT NULL,
            close DOUBLE PRECISION NOT NULL,
            volume DOUBLE PRECISION NOT NULL,

            return_1h DOUBLE PRECISION NOT NULL,
            return_6h DOUBLE PRECISION NOT NULL,
            return_24h DOUBLE PRECISION NOT NULL,
            ema_20 DOUBLE PRECISION NOT NULL,
            ema_50 DOUBLE PRECISION NOT NULL,
            rsi_14 DOUBLE PRECISION NOT NULL,
            volatility_24h DOUBLE PRECISION NOT NULL,
            volume_ratio DOUBLE PRECISION NOT NULL,
            target_24h_percent DOUBLE PRECISION NOT NULL,

            UNIQUE(symbol, timestamp, timeframe)
        );
    """)

    # Dernière bougie en temps réel maintenue par le WebSocket Binance.
    # Cette table est utilisée par l'API et le dashboard Streamlit.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_market_data (
            id BIGSERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            timestamp BIGINT NOT NULL,
            datetime TIMESTAMP NOT NULL,
            timeframe TEXT NOT NULL,
            open DOUBLE PRECISION NOT NULL,
            high DOUBLE PRECISION NOT NULL,
            low DOUBLE PRECISION NOT NULL,
            close DOUBLE PRECISION NOT NULL,
            volume DOUBLE PRECISION NOT NULL,
            is_closed BOOLEAN NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            UNIQUE(symbol, timeframe)
        );
    """)



    # ------------------------------------------------------------------
    # Création des index PostgreSQL
    # Optimisation des performances de lecture.
    # ------------------------------------------------------------------

    # Users
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_active
        ON users(is_active);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_country_code
        ON users(country_code);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_city
        ON users(city);
    """)

    # User positions
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_positions_user_id
        ON user_positions(user_id);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_positions_symbol_active
        ON user_positions(symbol, is_active);
    """)

    # Daily alert preferences
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_daily_alert_preferences_user_symbol
        ON daily_alert_preferences(user_id, symbol);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_daily_alert_preferences_symbol_enabled
        ON daily_alert_preferences(symbol, enabled)
        WHERE enabled = TRUE;
    """)

    # Les index partiels permettent d'accélérer la recherche
    # uniquement sur les alertes encore actives.

    # Price alerts
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_price_alerts_above_active
        ON price_alerts(symbol, target_price)
        WHERE is_active = TRUE AND direction = 'above';
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_price_alerts_below_active
        ON price_alerts(symbol, target_price)
        WHERE is_active = TRUE AND direction = 'below';
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_price_alerts_user_active
        ON price_alerts(user_id, is_active);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_price_alerts_created_at
        ON price_alerts(created_at DESC);
    """)

    # Empêche la génération de notifications en double
    # pour une même prédiction ou une même alerte de prix.

    # Notifications
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_user_id_created
        ON notifications(user_id, created_at DESC);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_type_status_created
        ON notifications(notification_type, status, created_at DESC);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_created_at
        ON notifications(created_at DESC);
    """)

    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_daily_notification
        ON notifications(user_id, prediction_id, notification_type)
        WHERE notification_type = 'daily_prediction'
          AND prediction_id IS NOT NULL;
    """)

    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_price_alert_notification
        ON notifications(price_alert_id)
        WHERE notification_type = 'price_target'
          AND price_alert_id IS NOT NULL;
    """)

    # Predictions
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_predictions_symbol_created
        ON predictions(symbol, created_at DESC);
    """)

    # Model metrics
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_model_metrics_symbol_created
        ON model_metrics(symbol, created_at DESC);
    """)

    # OHLCV
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ccxt_ohlcv_symbol_timestamp
        ON ccxt_ohlcv(symbol, timestamp);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ccxt_ohlcv_symbol_datetime
        ON ccxt_ohlcv(symbol, datetime DESC);
    """)

    # Features
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_features_crypto_symbol_timestamp
        ON features_crypto(symbol, timestamp);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_features_crypto_symbol_datetime
        ON features_crypto(symbol, datetime DESC);
    """)

    # Live market
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_live_market_data_symbol_updated
        ON live_market_data(symbol, updated_at DESC);
    """)

    #Lastest prediction
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_predictions_datetime
        ON predictions(prediction_datetime DESC);
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("Base de données initialisée avec succès.")


if __name__ == "__main__":
    init_users_db()