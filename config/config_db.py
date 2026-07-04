"""
Chargement des variables d'environnement.

Ce module centralise l'accès aux paramètres de configuration
utilisés par l'ensemble de l'application.
"""

import os 
from dotenv import load_dotenv

# Charge les variables définies dans le fichier .env
load_dotenv()

# Configuration PostgreSQL
DB_NAME=os.getenv("DB_NAME")
DB_USER=os.getenv("DB_USER")
DB_PASSWORD=os.getenv("DB_PASSWORD")
DB_HOST=os.getenv("DB_HOST")
DB_PORT=os.getenv("DB_PORT")

# Configuration métier
TIMEFRAME=os.getenv("TIMEFRAME", "1h")
DAYS_HISTORY=int(os.getenv("DAYS_HISTORY", "180"))