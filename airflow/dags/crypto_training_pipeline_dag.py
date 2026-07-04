"""
DAG d'entraînement quotidien.

Chaque exécution réalise les étapes suivantes :
- collecte des nouvelles données de marché ;
- recalcul des features ;
- réentraînement des modèles de Machine Learning.

Les nouveaux modèles ne remplacent les modèles actifs que si leurs
performances sont meilleures sur le jeu de test.
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
    dag_id="crypto_training_pipeline",
    description="Collecte les données marché, calcule les features et réentraîne les modèles ML.",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["crypto", "training", "ml", "data-engineering"],
) as dag:

    collect = BashOperator(
        task_id="collect_data",
        bash_command="cd /app && PYTHONPATH=/app python data/collector.py",
    )

    features = BashOperator(
        task_id="feature_engineering",
        bash_command="cd /app && PYTHONPATH=/app python data/feature_engineering.py",
    )

    train = BashOperator(
        task_id="train_model",
        bash_command="cd /app && PYTHONPATH=/app python ml/train_model.py",
    )

    collect >> features >> train