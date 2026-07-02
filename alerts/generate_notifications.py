"""
Génération robuste des notifications quotidiennes.

Cette version est pensée pour de gros volumes :
- millions d'utilisateurs ;
- génération massive de notifications ;
- pas de chargement des utilisateurs en mémoire Python ;
- insertion directe côté PostgreSQL via INSERT ... SELECT ;
- idempotence via ON CONFLICT DO NOTHING.

Le script récupère la dernière prédiction disponible pour chaque symbole,
puis crée une notification quotidienne pour tous les utilisateurs actifs
ayant activé les alertes quotidiennes sur ce symbole.
"""

from config.db import get_connection
from config.symbols import SYMBOLS


def generate_daily_notifications(symbol):
    """
    Génère les notifications quotidiennes pour un symbole donné.

    La logique est entièrement déléguée à PostgreSQL :
    - récupération de la dernière prédiction du symbole ;
    - sélection des utilisateurs actifs abonnés ;
    - insertion des notifications ;
    - prévention des doublons avec ON CONFLICT DO NOTHING.

    Args:
        symbol (str): symbole crypto, par exemple "BTC/USDT".

    Returns:
        int: nombre de notifications créées.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            WITH latest_prediction AS (
                SELECT
                    id,
                    symbol,
                    prediction_datetime,
                    predicted_change_24h,
                    trend
                FROM predictions
                WHERE symbol = %s
                ORDER BY created_at DESC
                LIMIT 1
            )
            INSERT INTO notifications (
                user_id,
                prediction_id,
                price_alert_id,
                symbol,
                notification_type,
                message,
                status,
                sent_at
            )
            SELECT
                u.id,
                lp.id,
                NULL,
                lp.symbol,
                'daily_prediction',
                CONCAT(
                    'Prévision quotidienne ', lp.symbol,
                    ' : ',
                    ROUND(lp.predicted_change_24h::numeric, 2),
                    '%% sur 24h. Tendance : ',
                    lp.trend,
                    '. Référence : ',
                    lp.prediction_datetime,
                    '.'
                ),
                'pending',
                NULL
            FROM latest_prediction lp
            JOIN daily_alert_preferences d
                ON d.symbol = lp.symbol
            JOIN users u
                ON u.id = d.user_id
            WHERE d.enabled = TRUE
              AND u.is_active = TRUE
            ON CONFLICT DO NOTHING;
        """, (symbol,))

        inserted_count = cur.rowcount
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()

    print(f"{symbol} : {inserted_count} notifications quotidiennes créées.")
    return inserted_count


def main():
    total_created = 0

    for symbol in SYMBOLS:
        total_created += generate_daily_notifications(symbol)

    print(
        f"Génération terminée. "
        f"Total notifications quotidiennes créées : {total_created}"
    )


if __name__ == "__main__":
    main()