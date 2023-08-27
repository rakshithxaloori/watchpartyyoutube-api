from django.urls import path

from upload import views

urlpatterns = [
    path("get/", views.get_presigned_posts_view, name="get presigned posts"),
]
