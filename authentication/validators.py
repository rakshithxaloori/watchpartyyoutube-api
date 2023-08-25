from rest_framework import serializers

from authentication.models import User, Account


class UserCreateValidator(serializers.ModelSerializer):
    name = serializers.CharField(allow_null=True, allow_blank=True)
    image = serializers.URLField(allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = ["name", "email", "image"]


class UserUpdateValidator(serializers.ModelSerializer):
    name = serializers.CharField(allow_null=True, allow_blank=True)
    image = serializers.URLField(allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "email", "image", "emailVerified", "name"]


class LinkAccountValidator(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "type",
            "provider",
            "providerAccountId",
            "refresh_token",
            "access_token",
            "expires_at",
            "token_type",
            "scope",
            "id_token",
        ]


# sample data for UserUpdateValidator
data = {
    "username": "test",
    "email": "test@gmal.com",
    "image": "https://test.com",
    "emailVerified": "2021-09-09T12:00:00.000Z",
    "name": "",
}
