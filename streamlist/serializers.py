from rest_framework.serializers import ModelSerializer, SerializerMethodField

from streamlist.models import StreamList


class StreamListSerializer(ModelSerializer):
    status = SerializerMethodField()

    class Meta:
        model = StreamList
        fields = [
            "id",
            "created_at",
            "title",
            "status",
        ]
        read_only_fields = ["id", "user", "created_at", "status"]

    def get_status(self, obj):
        return obj.stream_list_status.all().order_by("-created_at").first().status
