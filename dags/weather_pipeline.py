from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="weather_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["weather", "snowflake"]
) as dag:

    extract_weather = BashOperator(
        task_id="extract_weather",
        bash_command="python /opt/airflow/scripts/weather_api.py"
    )

    load_snowflake = BashOperator(
        task_id="load_snowflake",
        bash_command="python /opt/airflow/scripts/autoloader.py"
    )

    extract_weather >> load_snowflake