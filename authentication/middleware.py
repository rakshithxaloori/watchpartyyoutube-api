import logging
from django.conf import settings
from rest_framework import authentication

from authentication.models import Session
from watchpartyyoutube.utils import BAD_REQUEST_RESPONSE


logger = logging.getLogger(__name__)


X_AUTH_KEY = settings.X_AUTH_KEY


def auth_key_middleware(get_response):
    def middleware(request):
        # Check X-Auth-Key
        auth_key = request.headers.get("X-Auth-Key", None)
        if auth_key is None or auth_key != X_AUTH_KEY:
            return BAD_REQUEST_RESPONSE

        response = get_response(request)
        return response

    return middleware


class CustomAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # Get token from header
        token = request.headers.get("Authorization", None)
        token = token.split(" ")[1] if token is not None else None
        if token is None:
            return None

        # Get session from token
        try:
            session = Session.objects.get(sessionToken=token)
        except Session.DoesNotExist:
            return None

        # Get user from session
        user = session.user
        return (user, None)
