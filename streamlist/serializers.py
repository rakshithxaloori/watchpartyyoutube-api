from rest_framework.serializers import ModelSerializer, SerializerMethodField

from streamlist.models import StreamList, Video


class StreamListShortSerializer(ModelSerializer):
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


class VideoSerializer(ModelSerializer):
    class Meta:
        model = Video
        fields = ["id", "created_at", "ordering", "title"]
        read_only_fields = ["id", "user", "created_at", "ordering", "title"]


class StreamListLongSerializer(ModelSerializer):
    status = SerializerMethodField()
    videos = SerializerMethodField()

    class Meta:
        model = StreamList
        fields = ["id", "created_at", "title", "description", "status", "videos"]
        read_only_fields = ["id", "created_at", "title"]

    def get_status(self, obj):
        return obj.stream_list_status.all().order_by("-created_at").first().status

    def get_videos(self, obj):
        return VideoSerializer(obj.videos.all().order_by("ordering"), many=True).data
