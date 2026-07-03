from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "crypto-alerts",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="setup",
    description="Pipeline manuel de premier lancement : collecte, features, entraînement et prédiction.",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["crypto", "setup", "manual"],
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

    predict = BashOperator(
        task_id="predict",
        bash_command="cd /app && PYTHONPATH=/app python ml/predict.py",
    )

    collect >> features >> train >> predict