import boto3

from django.conf import settings

from watchpartyyoutube.celery import app as celery_app
from streamlist.clients import s3_client, mediaconvert_client, medialive_client
from streamlist.models import (
    StreamList,
    StreamListStatus,
    Video,
    MediaConvertJob,
    StreamVideo,
    MediaLiveChannel,
)
from streamlist.utils import get_mediaconvert_job_settings, create_medialive_channel

AWS_INPUT_BUCKET_NAME = settings.AWS_INPUT_BUCKET_NAME
AWS_OUTPUT_BUCKET_NAME = settings.AWS_OUTPUT_BUCKET_NAME
AWS_MC_ROLE_ARN = settings.AWS_MC_ROLE_ARN


@celery_app.task
def del_s3_object_task(path, bucket_name):
    # If the object exists in the bucket, delete it
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=path)
    except Exception as e:
        print(e)
        return


@celery_app.task
def check_streamlist_status_task(stream_list_id):
    stream_list = StreamList.objects.filter(id=stream_list_id).first()
    if stream_list is None:
        return
    videos = Video.objects.filter(stream_list_id=stream_list_id)
    for video in videos:
        try:
            s3_client.head_object(Bucket=settings.AWS_INPUT_BUCKET_NAME, Key=video.path)
            video.status = Video.UPLOADED
            video.save(update_fields=["status"])
        except Exception as e:
            print(e)
            return
    create_mediaconvert_job_task.delay(stream_list_id)


@celery_app.task
def create_mediaconvert_job_task(stream_list_id):
    stream_list = StreamList.objects.filter(id=stream_list_id).first()
    if stream_list is None:
        return
    if MediaConvertJob.objects.filter(stream_list_id=stream_list_id).exists():
        return
    videos = Video.objects.filter(stream_list_id=stream_list_id)
    file_s3_urls = [f"s3://{AWS_INPUT_BUCKET_NAME}/{video.path}" for video in videos]

    # Specify the job settings
    output_filename = f"{stream_list.user.username}/{stream_list.id}"
    job_settings = get_mediaconvert_job_settings(file_s3_urls, output_filename)
    # Create the job
    job = mediaconvert_client.create_job(
        AccelerationSettings={"Mode": "PREFERRED"},
        Role=AWS_MC_ROLE_ARN,
        Settings=job_settings,
    )

    print("Job created: ", job["Job"]["Id"])

    # Create new StreamListStatus
    StreamListStatus.objects.create(
        stream_list=stream_list,
        status=StreamListStatus.PROCESSING,
    )

    # Create a MediaConvertJob instance
    MediaConvertJob.objects.create(
        stream_list=stream_list,
        job_id=job["Job"]["Id"],
    )


@celery_app.task
def del_inputs_from_s3_task(stream_list_id):
    try:
        stream_list = StreamList.objects.get(id=stream_list_id)
        videos = stream_list.videos.all()
        for video in videos:
            del_s3_object_task(video.path, AWS_INPUT_BUCKET_NAME)
            video.status = Video.DELETED
            video.save(update_fields=["status"])
    except StreamList.DoesNotExist:
        return


@celery_app.task
def del_outputs_from_s3_task(stream_list_id):
    try:
        stream_list = StreamList.objects.get(id=stream_list_id)
        stream_video = stream_list.stream_video
        del_s3_object_task(stream_video.path, AWS_OUTPUT_BUCKET_NAME)
        stream_video.status = StreamVideo.DELETED
        stream_video.save(update_fields=["status"])
    except StreamList.DoesNotExist:
        return


@celery_app.task
def create_channel_task(stream_list_id):
    try:
        stream_list = StreamList.objects.get(id=stream_list_id)
        latest_status = (
            stream_list.stream_list_status.all().order_by("-created_at").first()
        )
        if latest_status.status != StreamListStatus.READY:
            return

        input_name = f"{stream_list.user.username}_{stream_list.id}"
        channel_name = f"{stream_list.user.username}_{stream_list.id}"
        stream_key = stream_list.stream_key
        audio_description_name = f"{stream_list.user.username}_{stream_list.id}"
        video_description_name = f"{stream_list.user.username}_{stream_list.id}"

        stream_video = stream_list.stream_video

        # Create an input
        input_s3_url = "s3ssl://{}/{}".format(AWS_OUTPUT_BUCKET_NAME, stream_video.path)
        input_response = medialive_client.create_input(
            Name=input_name,
            Type="MP4_FILE",
            Sources=[
                {"Url": input_s3_url},
            ],
        )
        input_id = input_response["Input"]["Id"]

        # Create a MediaLiveChannel instance
        medialive_channel = MediaLiveChannel.objects.create(
            stream_list=stream_list,
            input_id=input_id,
            stream_key=stream_key,
            audio_description_name=audio_description_name,
            video_description_name=video_description_name,
        )

        # Create a channel
        channel_id = create_medialive_channel(
            channel_name,
            input_id,
            stream_key,
            audio_description_name,
            video_description_name,
        )
        print("Channel created: ", channel_id)

        try:
            # Deduct the credit minutes
            minutes_used = stream_video.duration_in_ms / 1000 / 60
            customer = stream_list.user.stripe_customer
            customer.credit_minutes -= minutes_used
            customer.save(update_fields=["credit_minutes"])

        except Exception as e:
            print(e)

        # Update the medialive_channel instance
        medialive_channel.channel_id = channel_id
        medialive_channel.save(update_fields=["channel_id"])

    except StreamList.DoesNotExist:
        return


@celery_app.task
def start_channel_task(channel_id):
    # Triggered after the channel is created
    try:
        medialive_client.start_channel(ChannelId=channel_id)
    except Exception as e:
        print(e)
        return


@celery_app.task
def stop_channel_task(channel_id):
    try:
        medialive_client.stop_channel(ChannelId=channel_id)
    except Exception as e:
        print(e)
        return


@celery_app.task
def delete_channel_task(channel_id):
    try:
        medialive_client.delete_channel(ChannelId=channel_id)
    except Exception as e:
        print(e)
        return


@celery_app.task
def delete_input_task(input_id):
    try:
        medialive_client.delete_input(InputId=input_id)
    except Exception as e:
        print(e)
        return


# Every half hour
# TODO delete channels that have stop_at < now
# TODO delete channels that are not in the database
# TODO delete inputs that are not in the database
