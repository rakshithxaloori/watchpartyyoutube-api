import uuid
from django.db import models

from authentication.models import User


class StreamList(models.Model):
    QUEUED = "Q"
    PROCESSING = "P"
    READY = "R"
    ERROR = "E"

    STATUS_CHOICES = [
        (QUEUED, "Queued"),
        (PROCESSING, "Progressing"),
        (READY, "Ready"),
        (ERROR, "Error"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=QUEUED,
    )

    def __str__(self):
        return f"{self.user.username} | {self.title}"

    class Meta:
        verbose_name = "StreamList"


class Video(models.Model):
    UPLOADING = "U"
    UPLOADED = "D"
    ERROR = "E"

    STATUS_CHOICES = [
        (UPLOADING, "Uploading"),
        (UPLOADED, "Uploaded"),
        (ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stream_list = models.ForeignKey(StreamList, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    ordering = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=100)
    size = models.IntegerField()
    path = models.URLField()
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=UPLOADING,
    )

    def __str__(self):
        return f"{self.ordering} {self.title}"

    class Meta:
        ordering = ["stream_list", "ordering"]


class MediaConvertJob(models.Model):
    QUEUED = "Q"
    PROGRESSING = "P"
    INPUT_INFORMATION = "I"
    COMPLETED = "C"
    ERROR = "E"

    STATUS_CHOICES = [
        (QUEUED, "Queued"),
        (PROGRESSING, "Progressing"),
        (INPUT_INFORMATION, "Input Information"),
        (COMPLETED, "Completed"),
        (ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream_list = models.OneToOneField(StreamList, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    job_id = models.CharField(max_length=100)
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=QUEUED,
    )
    error_message = models.CharField(max_length=1000, null=True, blank=True)

    class Meta:
        verbose_name = "MediaConvertJob"


class StreamVideo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stream_list = models.ForeignKey(StreamList, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    size = models.IntegerField()
    path = models.URLField()

    class Meta:
        verbose_name = "StreamVideo"
