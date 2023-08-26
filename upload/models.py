import uuid
from django.db import models

from authentication.models import User


class Video(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)
    size = models.IntegerField()
    path = models.URLField()
