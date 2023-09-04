from django.conf import settings

from streamlist.clients import s3_client, medialive_client

AWS_INPUT_BUCKET_NAME = settings.AWS_INPUT_BUCKET_NAME
AWS_OUTPUT_BUCKET_NAME = settings.AWS_OUTPUT_BUCKET_NAME
AWS_MEDIALIVE_ROLE_ARN = settings.AWS_MEDIALIVE_ROLE_ARN


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
        Bucket=AWS_INPUT_BUCKET_NAME,
        Key=file_path,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=EXPIRES_IN,
    )
    return url


def get_mediaconvert_job_settings(file_s3_urls, output_filename):
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
                            "Height": 1080,
                            "CodecSettings": {
                                "Codec": "H_264",
                                "H264Settings": {
                                    "FramerateDenominator": 1,
                                    "MaxBitrate": 8 * 1000 * 1000,
                                    "FramerateControl": "SPECIFIED",
                                    "RateControlMode": "QVBR",
                                    "FramerateNumerator": 30,
                                    "SceneChangeDetect": "TRANSITION_DETECTION",
                                },
                            },
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

    return job_settings


def create_medialive_channel(
    channel_name, input_id, stream_key, audio_description_name, video_description_name
):
    channel_response = medialive_client.create_channel(
        Name=channel_name,
        ChannelClass="SINGLE_PIPELINE",
        InputAttachments=[
            {
                "InputId": input_id,
                "InputSettings": {
                    "SourceEndBehavior": "CONTINUE",
                },
            },
        ],
        Destinations=[
            {
                "Id": "destination1",
                "Settings": [
                    {
                        "Url": "rtmp://a.rtmp.youtube.com/live2",
                        "StreamName": stream_key,
                    },
                ],
            },
            {
                "Id": "destination2",
                "Settings": [
                    {
                        "Url": "rtmp://b.rtmp.youtube.com/live2?backup=1",
                        "StreamName": stream_key,
                    },
                ],
            },
        ],
        EncoderSettings={
            "AudioDescriptions": [
                {
                    "Name": audio_description_name,
                    "AudioSelectorName": "Default",
                }
            ],
            "VideoDescriptions": [
                {
                    "Name": video_description_name,
                }
            ],
            "OutputGroups": [
                {
                    "Name": "Default",
                    "OutputGroupSettings": {
                        "RtmpGroupSettings": {
                            "AuthenticationScheme": "COMMON",
                            "InputLossAction": "EMIT_OUTPUT",
                            "RestartDelay": 15,
                        },
                    },
                    "Outputs": [
                        {
                            "VideoDescriptionName": video_description_name,
                            "AudioDescriptionNames": [audio_description_name],
                            "OutputSettings": {
                                "RtmpOutputSettings": {
                                    "Destination": {
                                        "DestinationRefId": "destination1",
                                    },
                                },
                            },
                        },
                        {
                            "VideoDescriptionName": video_description_name,
                            "AudioDescriptionNames": [audio_description_name],
                            "OutputSettings": {
                                "RtmpOutputSettings": {
                                    "Destination": {
                                        "DestinationRefId": "destination2",
                                    },
                                },
                            },
                        },
                    ],
                }
            ],
            "TimecodeConfig": {
                "Source": "EMBEDDED",
            },
        },
        RoleArn=AWS_MEDIALIVE_ROLE_ARN,
    )

    channel_id = channel_response["Channel"]["Id"]
    return channel_id
