"""
Génération des notifications quotidiennes.

Ce script récupère les dernières prédictions disponibles,
identifie les utilisateurs ayant activé les alertes pour chaque symbole,
puis génère les notifications à envoyer.

Les notifications sont stockées dans PostgreSQL avec le statut "pending".
L'envoi réel (email, Telegram, Discord, etc.) pourra être ajouté ultérieurement.
"""
from psycopg2.extras import execute_values

from config.db import get_connection
from config.symbols import SYMBOLS


def get_latest_prediction(symbol):
    """
    Récupère la dernière prédiction disponible pour un symbole.

    Args:
        symbol (str):
            Symbole crypto concerné.

    Returns:
        tuple | None:
            Dernière prédiction trouvée ou None.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            symbol,
            prediction_datetime,
            predicted_change_24h,
            trend
        FROM predictions
        WHERE symbol = %s
        ORDER BY created_at DESC
        LIMIT 1;
    """, (symbol,))

    prediction = cur.fetchone()

    cur.close()
    conn.close()

    return prediction


def get_users_with_daily_alert_enabled(symbol):
    """
    Récupère les utilisateurs ayant activé les alertes
    quotidiennes pour un symbole donné.

    Args:
        symbol (str):
            Symbole crypto concerné.

    Returns:
        list[tuple]:
            Liste des utilisateurs éligibles.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            u.id,
            u.email
        FROM users u
        JOIN daily_alert_preferences d
            ON u.id = d.user_id
        WHERE d.symbol = %s
        AND d.enabled = TRUE
        AND u.is_active = TRUE;
    """, (symbol,))

    users = cur.fetchall()

    cur.close()
    conn.close()

    return users


def save_notifications(notifications):
    """
    Sauvegarde une liste de notifications dans PostgreSQL.

    Les doublons sont évités grâce à la contrainte :

        (user_id, prediction_id, notification_type)

    Args:
        notifications (list):
            Notifications à enregistrer.

    Returns:
        None
    """
    if not notifications:
        return

    conn = get_connection()
    cur = conn.cursor()

    execute_values(
        cur,
        """
        INSERT INTO notifications (
            user_id,
            prediction_id,
            symbol,
            notification_type,
            message,
            status,
            sent_at
        )
        VALUES %s
        ON CONFLICT (user_id, prediction_id, notification_type)
        DO NOTHING;
        """,
        notifications,
    )

    conn.commit()
    cur.close()
    conn.close()


def generate_daily_notifications(symbol):
    """
    Génère les notifications quotidiennes pour un symbole.

    Étapes :
    - récupération de la dernière prédiction ;
    - récupération des utilisateurs abonnés ;
    - génération du message ;
    - insertion des notifications en base.

    Args:
        symbol (str):
            Symbole crypto concerné.

    Returns:
        None
    """
    prediction = get_latest_prediction(symbol)

    if prediction is None:
        print(f"Aucune prédiction trouvée pour {symbol}")
        return

    prediction_id, symbol, prediction_datetime, predicted_change, trend = prediction

    users = get_users_with_daily_alert_enabled(symbol)

    if not users:
        print(f"Aucun utilisateur avec alerte activée pour {symbol}")
        return

    # Message générique envoyé à tous les utilisateurs
    # abonnés à ce symbole.
    message = (
        f"Prévision quotidienne {symbol} : "
        f"{predicted_change:.2f}% sur 24h. "
        f"Tendance : {trend}. "
        f"Référence : {prediction_datetime}."
    )

    notifications = []

    # email est gardé pour un éventuel service d'envoi
    for user_id, email in users:
        notifications.append(
            (
                user_id,
                prediction_id,
                symbol,
                "daily_prediction",
                message,
                "pending",
                None,
            )
        )

    # Les notifications sont créées avec le statut "pending".
    # Un futur service d'envoi pourra les traiter et les marquer
    # comme "sent" après livraison.
    save_notifications(notifications)

    print(
        f"{symbol} : {len(notifications)} notifications quotidiennes générées."
    )


def main():
    """
    Génère les notifications pour tous les symboles configurés.
    """
    for symbol in SYMBOLS:
        generate_daily_notifications(symbol)

    print("Génération des notifications terminée.")


if __name__ == "__main__":
    main()