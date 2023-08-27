import boto3

from django.conf import settings

from watchpartyyoutube.celery import app as celery_app
from upload.clients import s3_client


@celery_app.task
def del_s3_object_task(path, bucket_name):
    # If the object exists in the bucket, delete it
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=path)
    except Exception as e:
        print(e)
