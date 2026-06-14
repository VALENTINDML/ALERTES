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
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Positions crypto détenues par les utilisateurs.
    # Utilisées pour les futures alertes personnalisées.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_positions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            symbol TEXT NOT NULL,
            buy_price DOUBLE PRECISION NOT NULL,
            quantity DOUBLE PRECISION NOT NULL,
            buy_datetime TIMESTAMP NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Préférences d'abonnement aux alertes quotidiennes.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_alert_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            symbol TEXT NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, symbol)
        );
    """)

    # Création de la table predictions 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            prediction_datetime TIMESTAMP NOT NULL,
            predicted_change_24h DOUBLE PRECISION NOT NULL,
            trend TEXT NOT NULL,
            model_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, prediction_datetime)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            symbol TEXT NOT NULL,
            target_price DOUBLE PRECISION NOT NULL,
            direction TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            triggered_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Historique des notifications générées.
    # Le statut permettra plus tard de gérer l'envoi réel.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            prediction_id INTEGER REFERENCES predictions(id) ON DELETE CASCADE,
            symbol TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, prediction_id, notification_type)
        );
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_positions_user_id
        ON user_positions(user_id);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_positions_symbol
        ON user_positions(symbol);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_daily_alert_preferences_user_symbol
        ON daily_alert_preferences(user_id, symbol);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_price_alerts_symbol_active
        ON price_alerts(symbol, is_active);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_user_id
        ON notifications(user_id);
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("Tables utilisateurs créées avec succès.")


if __name__ == "__main__":
    init_users_db()

"""
...
À terme, ce schéma pourra être migré vers un système
de migrations dédié (Alembic).
"""