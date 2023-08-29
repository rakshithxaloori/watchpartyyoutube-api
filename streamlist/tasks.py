import boto3

from django.conf import settings

from watchpartyyoutube.celery import app as celery_app
from streamlist.clients import s3_client, mediaconvert_client
from streamlist.models import StreamList, Video, MediaConvertJob

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
    job_settings = {
        "TimecodeConfig": {"Source": "ZEROBASED"},
        "OutputGroups": [
            {
                "CustomName": output_filename,
                "Name": "File Group",
                "Outputs": [
                    {
                        "ContainerSettings": {"Container": "MP4", "Mp4Settings": {}},
                        "VideoDescription": {
                            "CodecSettings": {
                                "Codec": "H_264",
                                "H264Settings": {
                                    "FramerateDenominator": 1,
                                    "MaxBitrate": 8000000,
                                    "FramerateControl": "SPECIFIED",
                                    "RateControlMode": "QVBR",
                                    "FramerateNumerator": 30,
                                    "SceneChangeDetect": "TRANSITION_DETECTION",
                                },
                            }
                        },
                        "AudioDescriptions": [
                            {
                                "CodecSettings": {
                                    "Codec": "AAC",
                                    "AacSettings": {
                                        "Bitrate": 96000,
                                        "CodingMode": "CODING_MODE_2_0",
                                        "SampleRate": 48000,
                                    },
                                }
                            }
                        ],
                    }
                ],
                "OutputGroupSettings": {
                    "Type": "FILE_GROUP_SETTINGS",
                    "FileGroupSettings": {
                        "Destination": f"s3://{AWS_OUTPUT_BUCKET_NAME}/{output_filename}"
                    },
                },
            }
        ],
        "Inputs": [
            {
                "AudioSelectors": {"Audio Selector 1": {"DefaultSelection": "DEFAULT"}},
                "VideoSelector": {},
                "TimecodeSource": "ZEROBASED",
                "FileInput": url,
            }
            for url in file_s3_urls
        ],
    }

    # Create the job
    job = mediaconvert_client.create_job(
        AccelerationSettings={"Mode": "PREFERRED"},
        Role=AWS_MC_ROLE_ARN,
        Settings=job_settings,
    )

    print("Job created: ", job["Job"]["Id"])

    # Update the streamlist status
    stream_list.status = StreamList.PROCESSING
    stream_list.save(update_fields=["status"])

    # Create a MediaConvertJob instance
    MediaConvertJob.objects.create(
        stream_list=stream_list,
        job_id=job["Job"]["Id"],
    )
