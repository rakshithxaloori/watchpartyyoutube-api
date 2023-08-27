from django.http import JsonResponse

from rest_framework import status
from rest_framework.decorators import api_view


from authentication.models import User, Account, Session, generate_random_username
from authentication.serializers import UserAuthSerializer, SessionAuthSerializer
from watchpartyyoutube.utils import BAD_REQUEST_RESPONSE
from authentication.middleware import auth_key_middleware
from authentication.validators import (
    UserCreateValidator,
    UserUpdateValidator,
    LinkAccountValidator,
)


EMAIL_PROVIDER = "email"


@api_view(["POST"])
@auth_key_middleware
def create_user_view(request):
    user_info = request.data.get("user", None)
    if user_info is None:
        return BAD_REQUEST_RESPONSE

    validator = UserCreateValidator(data=user_info)
    if not validator.is_valid():
        return BAD_REQUEST_RESPONSE

    name = user_info.get("name", None)
    email = user_info.get("email", None)
    image = user_info.get("image", None)

    name_split = name.split(" ")

    try:
        user, created = User.objects.update_or_create(
            email=email,
            defaults={
                "username": generate_random_username(),
                "first_name": name_split[0] if len(name_split) > 0 else None,
                "last_name": name_split[1] if len(name_split) > 1 else None,
                "image": image,
            },
        )
        user.set_unusable_password()
        user.save()
        user_data = UserAuthSerializer(user).data
        return JsonResponse(
            {
                "detail": "User created",
                "payload": {
                    "user": user_data,
                },
            }
        )

    except Exception as e:
        print(e)
        return BAD_REQUEST_RESPONSE


@api_view(["POST"])
@auth_key_middleware
def get_user_view(request):
    username = request.data.get("id", None)
    email = request.data.get("email", None)
    provider_account_id = request.data.get("providerAccountId", None)
    provider = request.data.get("provider", None)

    user = None
    if username is not None:
        user = User.objects.filter(username=username).first()
    elif email is not None:
        user = User.objects.filter(email=email).first()
    elif provider_account_id is not None and provider is not None:
        account = Account.objects.filter(
            providerAccountId=provider_account_id, provider=provider
        ).first()
        if account is not None:
            user = account.user

    user_data = None
    if user is not None:
        user_data = UserAuthSerializer(user).data
    return JsonResponse({"detail": "User found", "payload": {"user": user_data}})


@api_view(["POST"])
@auth_key_middleware
def update_user_view(request):
    validator = UserUpdateValidator(data=request.data)
    if not validator.is_valid():
        return BAD_REQUEST_RESPONSE

    username = request.data.get("id", None)
    email = request.data.get("email", None)
    image = request.data.get("image", None)
    name = request.data.get("name", None)
    emailVerified = request.data.get("emailVerified", None)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return BAD_REQUEST_RESPONSE

    user.email = email
    user.image = image
    user.first_name = name.split(" ")[0] if len(name.split(" ")) > 0 else None
    user.last_name = name.split(" ")[1] if len(name.split(" ")) > 1 else None
    user.emailVerified = emailVerified
    user.save()

    user_data = UserAuthSerializer(user).data
    return JsonResponse(
        {"detail": "User updated", "payload": {"user": user_data}},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@auth_key_middleware
def link_account_view(request):
    validator = LinkAccountValidator(data=request.data)
    if not validator.is_valid():
        return BAD_REQUEST_RESPONSE

    type = request.data.get("type", None)
    provider = request.data.get("provider", None)
    providerAccountId = request.data.get("providerAccountId", None)
    refresh_token = request.data.get("refresh_token", None)
    access_token = request.data.get("access_token", None)
    expires_at = request.data.get("expires_at", None)
    token_type = request.data.get("token_type", None)
    scope = request.data.get("scope", None)
    id_token = request.data.get("id_token", None)

    userId = request.data.get("userId", None)

    try:
        user = User.objects.get(username=userId)
    except User.DoesNotExist:
        return BAD_REQUEST_RESPONSE

    account = Account.objects.update_or_create(
        user=user,
        type=type,
        provider=provider,
        providerAccountId=providerAccountId,
        defaults={
            "access_token": access_token,
            "expires_at": expires_at,
            "refresh_token": refresh_token,
            "scope": scope,
            "token_type": token_type,
            "id_token": id_token,
        },
    )

    return JsonResponse({"detail": "Account linked"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@auth_key_middleware
def create_session_view(request):
    sessionToken = request.data.get("sessionToken", None)
    userId = request.data.get("userId", None)
    expires = request.data.get("expires", None)

    if None in [sessionToken, userId, expires]:
        return BAD_REQUEST_RESPONSE

    try:
        user = User.objects.get(username=userId)
    except User.DoesNotExist:
        return BAD_REQUEST_RESPONSE

    session = Session.objects.create(
        user=user,
        sessionToken=sessionToken,
        expires=expires,
    )
    session_serializer = SessionAuthSerializer(session)

    return JsonResponse(
        {"detail": "Session created", "payload": {"session": session_serializer.data}},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@auth_key_middleware
def get_session_view(request):
    sessionToken = request.data.get("sessionToken", None)

    if sessionToken is None:
        print("Session token not found")
        return BAD_REQUEST_RESPONSE

    try:
        session = Session.objects.get(sessionToken=sessionToken)
    except Session.DoesNotExist:
        print("Session not found")
        return JsonResponse(
            {
                "detail": "Session not found",
                "payload": {
                    "user": None,
                    "session": None,
                },
            },
            status=status.HTTP_200_OK,
        )

    session_data = SessionAuthSerializer(session).data
    user = session.user
    user_data = UserAuthSerializer(user).data

    return JsonResponse(
        {
            "detail": "Session found",
            "payload": {
                "user": user_data,
                "session": session_data,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@auth_key_middleware
def update_session_view(request):
    sessionToken = request.data.get("sessionToken", None)
    expires = request.data.get("expires", None)

    if None in [sessionToken, expires]:
        return BAD_REQUEST_RESPONSE

    try:
        session = Session.objects.get(sessionToken=sessionToken)
    except Session.DoesNotExist:
        return BAD_REQUEST_RESPONSE

    session.expires = expires
    session.save(update_fields=["expires"])
    session_data = SessionAuthSerializer(session).data
    return JsonResponse(
        {"detail": "Session updated", "payload": {"session": session_data}},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@auth_key_middleware
def delete_session_view(request):
    sessionToken = request.data.get("sessionToken", None)

    if sessionToken is None:
        return BAD_REQUEST_RESPONSE

    try:
        session = Session.objects.get(sessionToken=sessionToken)
    except Session.DoesNotExist:
        return BAD_REQUEST_RESPONSE

    session.delete()
    return JsonResponse({"detail": "Session deleted"}, status=status.HTTP_200_OK)
