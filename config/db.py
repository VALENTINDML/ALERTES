"""
Connexion PostgreSQL.

Centralise la création des connexions à la base de données
afin d'éviter de dupliquer la configuration dans les scripts.
"""

import psycopg2
from config.config_db import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

def get_connection():
    """
    Crée et retourne une connexion PostgreSQL.

    Les paramètres de connexion sont récupérés depuis les
    variables d'environnement définies dans config_db.py.

    Returns:
        psycopg2.extensions.connection:
            Connexion PostgreSQL active.
    """

    params = {
        "dbname": DB_NAME,
        "user": DB_USER,
        "host": DB_HOST,
        "port": DB_PORT,
    }

    # Ajout du mot de passe uniquement s'il est défini.
    if DB_PASSWORD:
        params["password"] = DB_PASSWORD

    return psycopg2.connect(**params)
