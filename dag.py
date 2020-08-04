from datetime import timedelta
from datetime import datetime
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.models import Variable

default_args = {
    'owner': 'hakase',
    'start_date': datetime(2020, 8, 4, 15, 52, 0),
    'email': ['blabla@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=10)
}

dag = DAG(
    'mangadex_notif',
    default_args=default_args,
    description='DAG for mangadex_notif project',
    schedule_interval='0 */1 * * *',
    # to prevent undesired dagrun catchup which would happen if pausing and editing DAG
    catchup=False 
)

t1 = BashOperator(
    task_id='scraper',
    bash_command='python3 /path/to/scraper.py',
    dag=dag
)