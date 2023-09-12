from rest_framework import serializers

from authentication.models import User, Account


class UserCreateValidator(serializers.ModelSerializer):
    name = serializers.CharField(allow_null=True, allow_blank=True)
    image = serializers.URLField(allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = ["name", "email", "image"]


class UserUpdateValidator(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    name = serializers.CharField(required=False)
    image = serializers.URLField(required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "emailVerified",
            "email",
            "name",
            "image",
        ]
        read_only_fields = ["username"]


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
