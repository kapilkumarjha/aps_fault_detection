### this code sets up a workflow using Apache Airflow for sensor fault detection. It downloads files from an S3 bucket, performs batch predictions on the files using a custom function, and uploads the prediction results back to the S3 bucket. The tasks are executed sequentially based on their dependencies.

from asyncio import tasks
import json
from textwrap import dedent
import pendulum
import os
from airflow import DAG
from airflow.operators.python import PythonOperator

#code sets up a DAG (workflow) named "sensor_training" using the DAG class with several parameters.
with DAG(
    'sensor_training',
    default_args={'retries': 2}, #Specifies default arguments for the DAG, setting the number of retries to 2.
    # [END default_args]
    description='Sensor Fault Detection', #description for the DAG for sensor fault detection.
    schedule_interval="@weekly", #schedule for the DAG to run
    start_date=pendulum.datetime(2022, 12, 11, tz="UTC"), # Defines the schedule for the DAG to run
    catchup=False, #if the DAG should process past periods missed while the DAG was inactive.it is set to False
    tags=['example'],
) as dag:
#The code defines three Python functions that represent tasks in the workflow:
    
    def download_files(**kwargs): #Downloads files from an S3 bucket to a directory.
        bucket_name = os.getenv("BUCKET_NAME")
        input_dir = "/app/input_files"
        #creating directory
        os.makedirs(input_dir,exist_ok=True)
        os.system(f"aws s3 sync s3://{bucket_name}/input_files /app/input_files")

    def batch_prediction(**kwargs): #Performs batch predictions using a custom function 
        from sensor.pipeline.batch_prediction import start_batch_prediction #package on each file in a directory.
        input_dir = "/app/input_files" 
        for file_name in os.listdir(input_dir):
            #make prediction
            start_batch_prediction(input_file_path=os.path.join(input_dir,file_name)) #from a module in the 
    
    def sync_prediction_dir_to_s3_bucket(**kwargs): #Uploads the contents of a directory to an S3 bucket.
        bucket_name = os.getenv("BUCKET_NAME")
        #upload prediction folder to predictionfiles folder in s3 bucket
        os.system(f"aws s3 sync /app/prediction s3://{bucket_name}/prediction_files")
    
    #Three instances of the PythonOperator class are created to represent the tasks in the DAG
    download_input_files  = PythonOperator( #Executes the download_files task.
            task_id="download_file",
            python_callable=download_files

    )

    generate_prediction_files = PythonOperator( # Executes the batch_prediction task
            task_id="prediction",
            python_callable=batch_prediction

    )

    upload_prediction_files = PythonOperator( #Executes the sync_prediction_dir_to_s3_bucket task.
            task_id="upload_prediction_files",
            python_callable=sync_prediction_dir_to_s3_bucket

    )
#download_input_files complete before generate_prediction_files can start. 
#generate_prediction_files complete before upload_prediction_files can start.
    download_input_files >> generate_prediction_files >> upload_prediction_files