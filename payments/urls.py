from django.urls import path

from payments import views

urlpatterns = [
    path("check/", views.check_subscription_view, name="check subscription"),
    path("webhook/", views.webhook, name="stripe webhook"),
]
