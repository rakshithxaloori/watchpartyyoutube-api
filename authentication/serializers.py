from rest_framework.serializers import ModelSerializer, SerializerMethodField

from authentication.models import User, Session


class UserAuthSerializer(ModelSerializer):
    id = SerializerMethodField()
    name = SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "email", "image", "emailVerified"]

    def get_id(self, obj):
        return obj.username

    def get_name(self, obj):
        return obj.get_full_name()


class SessionAuthSerializer(ModelSerializer):
    userId = SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            "userId",
            "sessionToken",
            "expires",
        ]

    def get_userId(self, obj):
        return obj.user.username
