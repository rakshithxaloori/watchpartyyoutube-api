from django.urls import path

from authentication import views


urlpatterns = [
    path("user/create/", views.create_user_view, name="create user"),
    path("user/get/", views.get_user_view, name="get user"),
    # TODO test
    path("user/update/", views.update_user_view, name="update user"),
    # path("user/delete/", views.delete_user_view, name="delete user"),
    path("user/link/", views.link_account_view, name="link account"),
    # path("user/unlink/", views.unlink_account_view, name="unlink account"),
    path("session/create/", views.create_session_view, name="create session"),
    path("session/get/", views.get_session_view, name="get session"),
    # TODO test
    path("session/update/", views.update_session_view, name="update session"),
    # TODO test
    path("session/delete/", views.delete_session_view, name="delete session"),
    # path(
    #     "verification/create/",
    #     views.create_verification_token_view,
    #     name="create verification token",
    # ),
    # path(
    #     "verification/use/",
    #     views.use_verification_token_view,
    #     name="use verification token",
    # ),
]
