import boto3


from django.conf import settings

s3_client = boto3.client(
    service_name="s3",
    aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
    region_name=settings.AWS_DEFAULT_REGION,
)
