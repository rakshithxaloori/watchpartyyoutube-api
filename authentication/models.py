import uuid
import random
import string


from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


def generate_random_username():
    length = 20  # You can adjust the length of the username as per your requirement
    characters = string.ascii_letters + string.digits
    while True:
        username = "".join(random.choice(characters) for i in range(length))
        if not User.objects.filter(username=username).exists():
            return username


class User(AbstractUser):
    DEFAULT_COUNTRY_CODE = "###"

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    image = models.URLField(null=True, blank=True)
    emailVerified = models.DateTimeField(null=True, blank=True)
    country_code = models.CharField(max_length=3, default=DEFAULT_COUNTRY_CODE)
    last_open = models.DateTimeField(default=timezone.now)

    def __str__(self):
        days_diff = (timezone.now() - self.last_open).days
        if self.is_staff:
            return self.username
        else:
            return f"{self.first_name} {self.last_name} | active {days_diff} days ago"

    class Meta:
        ordering = ["-last_open"]


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")

    type = models.TextField()
    provider = models.TextField()
    providerAccountId = models.TextField()
    refresh_token = models.TextField()
    access_token = models.TextField()
    expires_at = models.BigIntegerField()
    token_type = models.TextField()
    scope = models.TextField()
    id_token = models.TextField()
    session_state = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.username} | {self.user.email}"


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")

    sessionToken = models.TextField(unique=True)
    expires = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.user.username} | {self.user.email}"
