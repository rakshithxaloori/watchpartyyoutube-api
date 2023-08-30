from django.contrib import admin

from streamlist.models import (
    StreamList,
    StreamListStatus,
    Video,
    MediaConvertJob,
    StreamVideo,
    MediaLiveChannel,
)

admin.site.register(StreamList)
admin.site.register(StreamListStatus)
admin.site.register(Video)
admin.site.register(MediaConvertJob)
admin.site.register(StreamVideo)
admin.site.register(MediaLiveChannel)
