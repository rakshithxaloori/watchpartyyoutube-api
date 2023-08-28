from django.contrib import admin

from streamlist.models import StreamList, Video, MediaConvertJob, StreamVideo

admin.site.register(StreamList)
admin.site.register(Video)
admin.site.register(MediaConvertJob)
admin.site.register(StreamVideo)
