"""
DAG de prédiction quotidienne.

Chaque exécution réalise les étapes suivantes :
- collecte des dernières données de marché ;
- recalcul des features ;
- application des modèles entraînés ;
- génération des nouvelles prédictions et des notifications associées.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# Paramètres communs à toutes les tâches du DAG.
# Deux tentatives sont effectuées en cas d'échec d'une tâche.
default_args = {
    "owner": "crypto-alerts",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="crypto_prediction",
    description="Collecte les données marché, met à jour les features et génère les prédictions quotidiennes.",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["crypto", "prediction", "ml", "notifications"],
) as dag:

    collect = BashOperator(
        task_id="collect_data",
        bash_command="cd /app && PYTHONPATH=/app python data/collector.py",
    )

    features = BashOperator(
        task_id="feature_engineering",
        bash_command="cd /app && PYTHONPATH=/app python data/feature_engineering.py",
    )

    predict = BashOperator(
        task_id="predict",
        bash_command="cd /app && PYTHONPATH=/app python ml/predict.py",
    )

    collect >> features >> predict