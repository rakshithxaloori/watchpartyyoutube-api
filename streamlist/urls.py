from django.urls import path

from streamlist import views

urlpatterns = [
    path("create/", views.create_streamlist_view, name="create_streamlist"),
    path("success/", views.success_view, name="success"),
    path("list/", views.get_streamlists_view, name="streamlist_list"),
    path("start/", views.start_stream_view, name="start_stream"),
    # path("stop/", views.stop_stream_view, name="stop_stream"),
    path("webhook/", views.mediaconvert_webhook_view, name="webhook"),
]
