from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_delete, post_save


from streamlist.models import Video, StreamList, MediaConvertJob, StreamVideo
from streamlist.tasks import del_s3_object_task


AWS_INPUT_BUCKET_NAME = settings.AWS_INPUT_BUCKET_NAME
AWS_OUTPUT_BUCKET_NAME = settings.AWS_OUTPUT_BUCKET_NAME


@receiver(pre_delete, sender=Video)
def delete_video_from_s3(sender, instance, **kwargs):
    del_s3_object_task.delay(instance.path, AWS_INPUT_BUCKET_NAME)


@receiver(pre_delete, sender=StreamVideo)
def delete_stream_video_from_s3(sender, instance, **kwargs):
    del_s3_object_task.delay(instance.path, AWS_OUTPUT_BUCKET_NAME)


@receiver(post_save, sender=MediaConvertJob)
def post_status_update_mediaconvert_job(sender, instance, **kwargs):
    stream_list = instance.stream_list
    if instance.status == MediaConvertJob.PROGRESSING:
        stream_list.status = StreamList.PROCESSING
    elif instance.status == MediaConvertJob.COMPLETED:
        # TODO get the file size from S3 and update the streamvideo
        stream_list.status = StreamList.READY
    elif instance.status == MediaConvertJob.ERROR:
        stream_list.status = StreamList.ERROR
    stream_list.save(update_fields=["status"])
