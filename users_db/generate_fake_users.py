"""
Génération d'utilisateurs fictifs.

Ce script permet d'ajouter un nombre variable de faux utilisateurs
dans la base PostgreSQL, ainsi que leurs positions BTC/USDT et leurs
préférences d'alertes quotidiennes.

Il est relançable plusieurs fois : chaque exécution ajoute de nouveaux
utilisateurs sans modifier ceux déjà présents.
"""
import random
import sys
from datetime import datetime, timedelta

from psycopg2.extras import execute_values

from config.db import get_connection
from config.symbols import SYMBOLS

# Nombre d'utilisateurs générés par défaut si aucun argument n'est fourni.
DEFAULT_TOTAL_USERS = 1000
# Prix BTC de référence utilisé pour générer des prix d'achat réalistes.
BTC_REFERENCE_PRICE = 53477


def get_total_users_to_generate():
    """
    Récupère le nombre d'utilisateurs à générer.

    Si un argument est passé en ligne de commande, il est utilisé.
    Sinon, DEFAULT_TOTAL_USERS est utilisé.

    Exemple:
        python users_db/generate_fake_users.py 250

    Returns:
        int: Nombre d'utilisateurs à générer.
    """
    if len(sys.argv) > 1:
        return int(sys.argv[1])

    return DEFAULT_TOTAL_USERS


def get_next_user_index():
    """
    Calcule le prochain index utilisateur à utiliser.

    Le calcul se base sur MAX(id) afin d'éviter de réutiliser
    un identifiant même si certains utilisateurs ont été supprimés.

    Returns:
        int: Prochain index utilisateur.
    """
    conn = get_connection()
    cur = conn.cursor()

    # On utilise MAX(id) plutôt que COUNT(*)
    # pour éviter de réutiliser un index après suppression d'utilisateurs.
    cur.execute("""
        SELECT COALESCE(MAX(id), 0)
        FROM users;
    """)

    max_id = cur.fetchone()[0]

    cur.close()
    conn.close()

    return max_id + 1


def generate_users(total_users):
    """
    Génère les données des nouveaux utilisateurs fictifs.

    Args:
        total_users (int): Nombre d'utilisateurs à générer.

    Returns:
        list[tuple]: Données utilisateurs prêtes à être insérées.
    """
    start_index = get_next_user_index()
    end_index = start_index + total_users

    users = []

    for i in range(start_index, end_index):
        users.append(
            (
                f"user{i}@test.com",
                f"User{i}",
                "Test",
                True,
            )
        )

    return users


def save_users(users):
    """
    Insère les utilisateurs fictifs dans PostgreSQL.

    Args:
        users (list[tuple]): Liste des utilisateurs à insérer.

    Returns:
        None
    """
    conn = get_connection()
    cur = conn.cursor()

    execute_values(
        cur,
        """
        INSERT INTO users (
            email,
            first_name,
            last_name,
            is_active
        )
        VALUES %s
        ON CONFLICT (email)
        DO NOTHING;
        """,
        users,
    )

    conn.commit()
    cur.close()
    conn.close()


def get_new_user_ids(total_users):
    """
    Récupère les IDs des derniers utilisateurs créés.

    Args:
        total_users (int): Nombre d'utilisateurs récemment générés.

    Returns:
        list[int]: IDs des nouveaux utilisateurs.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Les derniers IDs correspondent aux utilisateurs créés par cette exécution.
    cur.execute("""
        SELECT id
        FROM users
        ORDER BY id DESC
        LIMIT %s;
    """, (total_users,))

    user_ids = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return user_ids


def generate_positions(user_ids):
    """
    Génère une position BTC/USDT fictive pour chaque utilisateur.

    Le prix d'achat est généré autour d'un prix BTC de référence
    afin d'obtenir des positions réalistes pour le MVP.

    Args:
        user_ids (list[int]): Liste des IDs utilisateurs.

    Returns:
        None
    """
    conn = get_connection()
    cur = conn.cursor()

    positions = []

    for user_id in user_ids:
        buy_price = BTC_REFERENCE_PRICE * random.uniform(0.97, 1.03)

        quantity = round(random.uniform(0.01, 2.0), 4)

        buy_datetime = (
            datetime.now()
            - timedelta(days=random.randint(1, 30))
        )

        positions.append(
            (
                user_id,
                "BTC/USDT",
                round(buy_price, 2),
                quantity,
                buy_datetime,
                True,
            )
        )

    execute_values(
        cur,
        """
        INSERT INTO user_positions (
            user_id,
            symbol,
            buy_price,
            quantity,
            buy_datetime,
            is_active
        )
        VALUES %s;
        """,
        positions,
    )

    conn.commit()
    cur.close()
    conn.close()


def generate_alert_preferences(user_ids):
    """
    Génère les préférences d'alertes quotidiennes des utilisateurs.

    Pour chaque utilisateur et chaque symbole configuré, une préférence
    est créée avec un statut activé ou désactivé aléatoire.

    Args:
        user_ids (list[int]): Liste des IDs utilisateurs.

    Returns:
        None
    """
    conn = get_connection()
    cur = conn.cursor()

    preferences = []

    for user_id in user_ids:
        for symbol in SYMBOLS:
            preferences.append(
                (
                    user_id,
                    symbol,
                    random.choice([True, False]),
                )
            )

    execute_values(
        cur,
        """
        INSERT INTO daily_alert_preferences (
            user_id,
            symbol,
            enabled
        )
        VALUES %s
        ON CONFLICT (user_id, symbol)
        DO NOTHING;
        """,
        preferences,
    )

    conn.commit()
    cur.close()
    conn.close()


def main():
    """
    Point d'entrée du script.

    Génère les utilisateurs, les sauvegarde, puis crée leurs positions
    et leurs préférences d'alertes.
    """
    total_users = get_total_users_to_generate()

    users = generate_users(total_users)

    save_users(users)

    new_user_ids = get_new_user_ids(total_users)

    generate_positions(new_user_ids)

    generate_alert_preferences(new_user_ids)

    print(f"{total_users} nouveaux utilisateurs générés.")


if __name__ == "__main__":
    main()