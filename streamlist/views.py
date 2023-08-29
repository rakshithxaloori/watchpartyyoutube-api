import hashlib
import json

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)


from authentication.middleware import CustomAuthentication
from watchpartyyoutube.utils import BAD_REQUEST_RESPONSE
from streamlist.utils import create_presigned_s3_post
from streamlist.models import StreamList, Video, MediaConvertJob, StreamVideo
from streamlist.tasks import check_streamlist_status_task
from streamlist.clients import sns_client

MAX_UPLOADS_COUNT = 30
MAX_FILE_SIZE = 1024 * 1024 * 1024 * 10  # 10 GB
AWS_SNS_TOPIC_ARN = settings.AWS_SNS_TOPIC_ARN


@api_view(["POST"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
def create_streamlist_view(request):
    files = request.data.get("files", None)
    if (
        files is None
        or type(files) != list
        or len(files) == 0
        or len(files) > MAX_UPLOADS_COUNT
    ):
        return BAD_REQUEST_RESPONSE

    presigned_posts = []
    for file in files:
        file_size = file.get("size", None)
        file_name = file.get("name", None)

        if (
            file_size is None
            or file_name is None
            or file_size > MAX_FILE_SIZE
            or type(file_size) != int
            or file_size < 0
        ):
            return BAD_REQUEST_RESPONSE

    # Create a new streamlist
    streamlist = StreamList.objects.create(
        user=request.user,
        title=request.data.get("title", timezone.now().strftime("%Y-%m-%d %H:%M:%S")),
        description=request.data.get(
            "description", f"StreamList created at {timezone.now()}"
        ),
    )

    for file, ordering in zip(files, range(len(files))):
        file_size = file.get("size", None)
        file_name = file.get("name", None)
        # Create a hash of the filename
        hash_object = hashlib.md5(file_name.encode())
        hex_dig = hash_object.hexdigest()
        file_path = f"{request.user.username}/{hex_dig}.mp4"
        presigned_post = create_presigned_s3_post(file_size, file_path)
        presigned_posts.append(presigned_post)

        # Create a video instance
        Video.objects.create(
            user=request.user,
            stream_list=streamlist,
            ordering=ordering,
            title=file_name,
            size=file_size,
            path=file_path,
        )

    return JsonResponse(
        {
            "detail": "Presigned posts generated",
            "payload": {
                "stream_list_id": streamlist.id,
                "urls": presigned_posts,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
def success_view(request):
    stream_list_id = request.data.get("stream_list_id", None)
    if stream_list_id is None:
        return BAD_REQUEST_RESPONSE

    stream_list = StreamList.objects.filter(id=stream_list_id).first()
    if stream_list is None:
        return BAD_REQUEST_RESPONSE

    check_streamlist_status_task.delay(stream_list_id)

    return JsonResponse(
        {
            "detail": "StreamList created",
            "payload": {
                "stream_list_id": stream_list.id,
            },
        },
        status=status.HTTP_200_OK,
    )


@csrf_exempt
def mediaconvert_webhook_view(request):
    if request.method == "POST":
        try:
            json_data = json.loads(request.body)
            if json_data["Type"] == "SubscriptionConfirmation":
                # Confirm subscription
                response = sns_client.confirm_subscription(
                    TopicArn=AWS_SNS_TOPIC_ARN, Token=json_data["Token"]
                )
                if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                    print("SNS subscription confirmation failed")

            else:
                # Process message
                message = json.loads(json_data["Message"])
                job_id = message["detail"]["jobId"]
                status = message["detail"]["status"]
                print(f"MediaConvert job {job_id} status: {status}")
                job = MediaConvertJob.objects.get(job_id=job_id)
                if status in ["PROGRESSING", "COMPLETE", "ERROR"]:
                    print("Updating MediaConvertJob status", message["detail"])
                    if status == "PROGRESSING":
                        job.status = MediaConvertJob.PROGRESSING
                    elif status == "COMPLETE":
                        job.status = MediaConvertJob.COMPLETED
                        duration_in_ms = message["detail"]["outputGroupDetails"][0][
                            "outputDetails"
                        ][0]["durationInMs"]
                        output_path = message["detail"]["outputGroupDetails"][0][
                            "outputDetails"
                        ][0]["outputFilePaths"][0]
                        output_path = output_path.split("/", 3)[3]
                        # Create a new StreamVideo instance
                        StreamVideo.objects.create(
                            user=job.stream_list.user,
                            stream_list=job.stream_list,
                            path=output_path,
                            duration_in_ms=duration_in_ms,
                        )
                    elif status == "ERROR":
                        job.status = MediaConvertJob.ERROR
                        job.error_message = message["detail"]["errorMessage"]

                    job.save()

            return HttpResponse(status=200)

        except Exception as e:
            print("Error processing SNS message:", str(e))
            return HttpResponse(status=200)
    else:
        return HttpResponse(status=405)  # Method Not Allowed
