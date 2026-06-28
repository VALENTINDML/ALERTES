from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="crypto_prediction",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
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

    predict = BashOperator(
        task_id="predict",
        bash_command="cd /app && PYTHONPATH=/app python ml/predict.py",
    )

    collect >> features >> predict