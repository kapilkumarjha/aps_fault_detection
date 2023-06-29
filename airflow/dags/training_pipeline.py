##this code sets up a DAG in Airflow for training a sensor fault detection model and syncing the resulting artifacts and saved models to an S3 bucket.

from asyncio import tasks
import json
from textwrap import dedent
import pendulum
import os
from airflow import DAG
from airflow.operators.python import PythonOperator


with DAG(
    'sensor_training',
    default_args={'retries': 2},
    # [END default_args]
    description='Sensor Fault Detection',
    schedule_interval="@weekly",
    start_date=pendulum.datetime(2022, 12, 11, tz="UTC"),
    catchup=False,
    tags=['example'],
) as dag:

    
    def training(**kwargs):
        from sensor.pipeline.training_pipeline import start_training_pipeline
        start_training_pipeline()
    # It retrieves the bucket name from the environment variable BUCKET_NAME and uses the os.system function to run AWS CLI commands to sync the contents of the /app/artifact and /app/saved_models directories to the specified S3 bucket.
    def sync_artifact_to_s3_bucket(**kwargs):
        bucket_name = os.getenv("BUCKET_NAME")
        os.system(f"aws s3 sync /app/artifact s3://{bucket_name}/artifacts")
        os.system(f"aws s3 sync /app/saved_models s3://{bucket_name}/saved_models")
#This operator is assigned the task ID "train_pipeline" and uses the training function as its callable.
    training_pipeline  = PythonOperator(
            task_id="train_pipeline",
            python_callable=training

    )
#This operator assigned the task ID "sync_data_to_s3" & uses sync_artifact_to_s3_bucket function as its callable.
    sync_data_to_s3 = PythonOperator(
            task_id="sync_data_to_s3",
            python_callable=sync_artifact_to_s3_bucket

    )
#It specifies that the training_pipeline task should be executed before the sync_data_to_s3 task
    training_pipeline >> sync_data_to_s3