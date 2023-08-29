from django.urls import path

from streamlist import views

urlpatterns = [
    path("create/", views.create_streamlist_view, name="create_streamlist"),
    path("success/", views.success_view, name="success"),
    path("webhook/", views.mediaconvert_webhook_view, name="webhook"),
]
