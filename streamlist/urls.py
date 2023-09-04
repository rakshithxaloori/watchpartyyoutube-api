from django.urls import path

from streamlist import views

urlpatterns = [
    path("create/", views.create_streamlist_view, name="create_streamlist"),
    path("success/", views.success_view, name="success"),
    path("list/", views.list_streamlists_view, name="streamlist_list"),
    path("get/", views.get_streamlist_view, name="get_streamlist"),
    path("status/get/", views.get_streamlist_status_view, name="get_streamlist_status"),
    path("start/", views.start_stream_view, name="start_stream"),
    path("stop/", views.stop_stream_view, name="stop_stream"),
    path("webhook/", views.mediaconvert_webhook_view, name="webhook"),
]
