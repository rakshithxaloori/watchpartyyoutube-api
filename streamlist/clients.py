import boto3


from django.conf import settings

s3_client = boto3.client(
    service_name="s3",
    aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
    region_name=settings.AWS_DEFAULT_REGION,
)

mediaconvert_client = boto3.client(
    "mediaconvert",
    aws_access_key_id=settings.AWS_MC_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_MC_SECRET_ACCESS_KEY,
    endpoint_url=settings.AWS_MC_ENDPOINT_URL,
    region_name=settings.AWS_DEFAULT_REGION,
)

sns_client = boto3.client(
    "sns",
    aws_access_key_id=settings.AWS_SNS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SNS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_DEFAULT_REGION,
)

medialive_client = boto3.client(
    "medialive",
    aws_access_key_id=settings.AWS_MEDIALIVE_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_MEDIALIVE_SECRET_ACCESS_KEY,
    region_name=settings.AWS_DEFAULT_REGION,
)
