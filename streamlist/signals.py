from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_delete


from streamlist.models import Video
from streamlist.tasks import del_s3_object_task


@receiver(pre_delete, sender=Video)
def delete_video_from_s3(sender, instance, **kwargs):
    del_s3_object_task.delay(instance.path, settings.AWS_INPUT_BUCKET_NAME)
