import uuid
from django.db import models

from authentication.models import User


class StreamList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    stream_key = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} | {self.title}"

    class Meta:
        verbose_name = "StreamList"


class StreamListStatus(models.Model):
    QUEUED = "Q"
    PROCESSING = "P"
    READY = "R"
    STREAMING = "S"
    FINISHED = "F"
    CANCELLED = "C"
    ERROR = "E"

    STATUS_CHOICES = [
        (QUEUED, "Queued"),
        (PROCESSING, "Processing"),
        (READY, "Ready"),
        (STREAMING, "Streaming"),
        (FINISHED, "Finished"),
        (CANCELLED, "Cancelled"),
        (ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream_list = models.ForeignKey(
        StreamList, related_name="stream_list_status", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=QUEUED,
    )

    def __str__(self):
        return f"{self.stream_list.title} | {self.status}"

    class Meta:
        verbose_name = "StreamListStatus"
        ordering = ["-stream_list__created_at", "-created_at"]


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
    stream_list = models.ForeignKey(
        StreamList, related_name="videos", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    ordering = models.PositiveSmallIntegerField()
    title = models.TextField()
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
    stream_list = models.OneToOneField(
        StreamList, related_name="media_convert_job", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    job_id = models.CharField(max_length=100)
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=QUEUED,
    )
    error_message = models.CharField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return f"{self.stream_list.title} | {self.status}"

    class Meta:
        verbose_name = "MediaConvertJob"


class StreamVideo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stream_list = models.OneToOneField(
        StreamList, related_name="stream_video", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    path = models.URLField()
    duration_in_ms = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.username} | {self.stream_list.title}"

    class Meta:
        verbose_name = "StreamVideo"


class MediaLiveChannel(models.Model):
    CREATED = "C"
    RUNNING = "R"
    STOPPING = "S"
    STOPPED = "T"
    DELETED = "D"

    STATUS_CHOICES = [
        (CREATED, "Created"),
        (RUNNING, "Running"),
        (STOPPING, "Stopping"),
        (STOPPED, "Stopped"),
        (DELETED, "Deleted"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream_list = models.OneToOneField(
        StreamList, related_name="media_live_channel", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    channel_id = models.CharField(max_length=100, null=True, blank=True)
    input_id = models.CharField(max_length=100)
    stream_key = models.CharField(max_length=100)
    audio_description_name = models.CharField(max_length=100)
    video_description_name = models.CharField(max_length=100)
    state = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=CREATED,
    )

    def __str__(self):
        return f"{self.stream_list.title} | {self.state}"

    class Meta:
        verbose_name = "MediaLiveChannel"
