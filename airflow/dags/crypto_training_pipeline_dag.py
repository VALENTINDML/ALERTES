from airflow import DAG
from airflow.operators.bash import BashOperator

from datetime import datetime


with DAG(
    dag_id="crypto_training_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule="@daily", # None , 
    catchup=False,
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