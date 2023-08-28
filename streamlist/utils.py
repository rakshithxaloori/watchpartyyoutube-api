from django.conf import settings

from streamlist.clients import s3_client


def create_presigned_s3_post(file_size, file_path):
    EXPIRES_IN = 60 * 60 * 24 * 2  # 2 days
    fields = {
        "Content-Type": "multipart/form-data",
        # "x-amz-storage-class": "INTELLIGENT_TIERING",
    }

    conditions = [
        ["content-length-range", file_size - 10, file_size + 10],
        {"content-type": "multipart/form-data"},
    ]

    url = s3_client.generate_presigned_post(
        Bucket=settings.AWS_INPUT_BUCKET_NAME,
        Key=file_path,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=EXPIRES_IN,
    )
    return url


def create_mediaconvert_job(stream_list_id):
    pass
