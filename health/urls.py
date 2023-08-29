from django.urls import path

from health import views

urlpatterns = [path("", views.health_check, name="health check")]
