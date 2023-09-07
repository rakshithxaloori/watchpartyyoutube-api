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
from streamlist.models import (
    StreamList,
    StreamListStatus,
    Video,
    MediaConvertJob,
    StreamVideo,
    MediaLiveChannel,
)
from streamlist.tasks import (
    check_streamlist_status_task,
    create_channel_task,
    start_channel_task,
    stop_channel_task,
    delete_channel_task,
    delete_input_task,
)
from streamlist.clients import sns_client
from streamlist.serializers import StreamListShortSerializer, StreamListLongSerializer
from payments.middleware import subscription_middleware

MAX_UPLOADS_COUNT = 30
MAX_FILE_SIZE = 1024 * 1024 * 1024 * 10  # 10 GB
AWS_SNS_TOPIC_ARN = settings.AWS_SNS_TOPIC_ARN


@api_view(["POST"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
@subscription_middleware
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

    stream_list = StreamList.objects.filter(
        id=stream_list_id, user=request.user
    ).first()
    if stream_list is None:
        return BAD_REQUEST_RESPONSE

    StreamListStatus.objects.create(
        stream_list=stream_list, status=StreamListStatus.QUEUED
    )
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


@api_view(["GET"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
def list_streamlists_view(request):
    stream_lists = StreamList.objects.filter(user=request.user).order_by("-created_at")[
        :5
    ]
    stream_lists_list = StreamListShortSerializer(stream_lists, many=True).data

    return JsonResponse(
        {
            "detail": "StreamLists retrieved",
            "payload": {
                "stream_lists": stream_lists_list,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
def get_streamlist_view(request):
    stream_list_id = request.data.get("stream_list_id", None)
    stream_list = StreamList.objects.filter(
        id=stream_list_id, user=request.user
    ).first()
    if stream_list is None:
        return BAD_REQUEST_RESPONSE

    stream_list_data = StreamListLongSerializer(stream_list).data

    return JsonResponse(
        {
            "detail": "StreamList retrieved",
            "payload": {
                "stream_list": stream_list_data,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
def get_streamlist_status_view(request):
    stream_list_id = request.data.get("stream_list_id", None)
    stream_list = StreamList.objects.filter(
        id=stream_list_id, user=request.user
    ).first()
    if stream_list is None:
        return BAD_REQUEST_RESPONSE

    stream_list_status = (
        stream_list.stream_list_status.all().order_by("-created_at").first().status
    )

    return JsonResponse(
        {
            "detail": "StreamList status retrieved",
            "payload": {
                "stream_list_status": stream_list_status,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
@subscription_middleware
def start_stream_view(request):
    stream_list_id = request.data.get("stream_list_id", None)
    stream_key = request.data.get("stream_key", None)
    if stream_list_id is None or stream_key is None:
        return BAD_REQUEST_RESPONSE
    try:
        stream_list = StreamList.objects.get(id=stream_list_id, user=request.user)
        stream_list.stream_key = stream_key
        stream_list.save(update_fields=["stream_key"])
        create_channel_task.delay(stream_list_id)
        return JsonResponse(
            {
                "detail": "StreamList started",
                "payload": {
                    "stream_list_id": stream_list.id,
                },
            },
            status=status.HTTP_200_OK,
        )
    except StreamList.DoesNotExist:
        return BAD_REQUEST_RESPONSE


@api_view(["POST"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
def stop_stream_view(request):
    stream_list_id = request.data.get("stream_list_id", None)
    if stream_list_id is None:
        return BAD_REQUEST_RESPONSE
    try:
        stream_list = StreamList.objects.get(id=stream_list_id, user=request.user)
        latest_status = (
            stream_list.stream_list_status.all().order_by("-created_at").first()
        )
        if latest_status.status == StreamListStatus.STREAMING:
            stop_channel_task.delay(stream_list.media_live_channel.channel_id)
        return JsonResponse(
            {
                "detail": "Stopping stream",
                "payload": {
                    "stream_list_id": stream_list.id,
                },
            },
            status=status.HTTP_200_OK,
        )
    except StreamList.DoesNotExist:
        return BAD_REQUEST_RESPONSE


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
                if message["source"] == "aws.mediaconvert":
                    job_id = message["detail"]["jobId"]
                    status = message["detail"]["status"]
                    print(f"MediaConvert job {job_id} status: {status}")
                    job = MediaConvertJob.objects.get(job_id=job_id)
                    stream_list = job.stream_list
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
                                user=stream_list.user,
                                stream_list=stream_list,
                                path=output_path,
                                duration_in_ms=duration_in_ms,
                            )
                            # Create new StreamListStatus
                            StreamListStatus.objects.create(
                                stream_list=stream_list,
                                status=StreamListStatus.READY,
                            )
                        elif status == "ERROR":
                            job.status = MediaConvertJob.ERROR
                            job.error_message = message["detail"]["errorMessage"]

                        job.save()
                elif message["source"] == "aws.medialive":
                    print(message)
                    channel_arn = message["detail"]["channel_arn"]
                    try:
                        channel_id = channel_arn.split(":")[-1]
                        channel_state = message["detail"]["state"]

                        medialive_channel = MediaLiveChannel.objects.get(
                            channel_id=channel_id
                        )
                        stream_list = medialive_channel.stream_list

                        if channel_state == "CREATED":
                            medialive_channel.state = MediaLiveChannel.CREATED
                            start_channel_task.delay(channel_id)
                        elif channel_state == "RUNNING":
                            medialive_channel.state = MediaLiveChannel.RUNNING
                            duration_in_ms = stream_list.stream_video.duration_in_ms
                            # Create new StreamListStatus
                            StreamListStatus.objects.create(
                                stream_list=stream_list,
                                status=StreamListStatus.STREAMING,
                            )
                            eta_stop_at = (
                                timezone.now()
                                + timezone.timedelta(milliseconds=duration_in_ms)
                                + timezone.timedelta(minutes=1)
                            )
                            medialive_channel.stop_at = eta_stop_at
                            medialive_channel.save(update_fields=["stop_at"])
                            stop_channel_task.apply_async(
                                (channel_id,), eta=eta_stop_at
                            )
                        elif channel_state == "STOPPED":
                            medialive_channel.state = MediaLiveChannel.STOPPED
                            # Create new StreamListStatus
                            StreamListStatus.objects.create(
                                stream_list=stream_list,
                                status=StreamListStatus.FINISHED,
                            )
                            try:
                                # Recalculate the credit minutes
                                customer = stream_list.user.stripe_customer
                                streaming_stream_list_status = (
                                    StreamListStatus.objects.filter(
                                        stream_list=stream_list,
                                        status=StreamListStatus.STREAMING,
                                    ).first()
                                )
                                if streaming_stream_list_status is not None:
                                    stream_video_duration_in_minutes = (
                                        (stream_list.stream_video.duration_in_ms)
                                        / 1000
                                        / 60
                                    )
                                    actual_duration_in_minutes = (
                                        timezone.now()
                                        - streaming_stream_list_status.created_at
                                    ).total_seconds() / 60
                                    customer.credit_minutes += (
                                        stream_video_duration_in_minutes
                                        - actual_duration_in_minutes
                                    )
                                    customer.save(update_fields=["credit_minutes"])

                                    stream_list.credit_minutes_used = (
                                        actual_duration_in_minutes
                                    )
                                    stream_list.save(
                                        update_fields=["credit_minutes_used"]
                                    )

                            except Exception as e:
                                pass

                            delete_channel_task.delay(channel_id)
                        elif channel_state == "DELETED":
                            medialive_channel.state = MediaLiveChannel.DELETED
                            input_id = medialive_channel.input_id
                            delete_input_task.delay(input_id)
                        # TODO If the channel has failed, delete the channel

                        medialive_channel.save(update_fields=["state"])

                    except MediaLiveChannel.DoesNotExist:
                        print("MediaLiveChannel does not exist", channel_arn)

            return HttpResponse(status=200)

        except Exception as e:
            print("Error processing SNS message:", str(e))
            return HttpResponse(status=200)
    else:
        return HttpResponse(status=405)  # Method Not Allowed
