from rest_framework.serializers import ModelSerializer, SerializerMethodField

from streamlist.models import StreamList


class StreamListSerializer(ModelSerializer):
    class Meta:
        model = StreamList
        fields = [
            "id",
            "created_at",
            "title",
            "status",
        ]
        read_only_fields = ["id", "user", "created_at", "status"]
