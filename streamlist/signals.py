from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_delete, post_save


from streamlist.models import Video, StreamVideo, StreamListStatus
from streamlist.tasks import (
    del_s3_object_task,
    del_inputs_from_s3_task,
    del_outputs_from_s3_task,
)


AWS_INPUT_BUCKET_NAME = settings.AWS_INPUT_BUCKET_NAME
AWS_OUTPUT_BUCKET_NAME = settings.AWS_OUTPUT_BUCKET_NAME


@receiver(pre_delete, sender=Video)
def delete_video_from_s3(sender, instance, **kwargs):
    del_s3_object_task.delay(instance.path, AWS_INPUT_BUCKET_NAME)


@receiver(pre_delete, sender=StreamVideo)
def delete_stream_video_from_s3(sender, instance, **kwargs):
    del_s3_object_task.delay(instance.path, AWS_OUTPUT_BUCKET_NAME)


@receiver(post_save, sender=StreamListStatus)
def create_stream_list_status(sender, instance, created, **kwargs):
    if created:
        if instance.status == StreamListStatus.READY:
            stream_list_id = instance.stream_list.id
            del_inputs_from_s3_task.delay(stream_list_id)

        elif instance.status in [
            StreamListStatus.FINISHED,
            StreamListStatus.CANCELLED,
            StreamListStatus.ERROR,
        ]:
            stream_list_id = instance.stream_list.id
            del_outputs_from_s3_task.delay(stream_list_id)
