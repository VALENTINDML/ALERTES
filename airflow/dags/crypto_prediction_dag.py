from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


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