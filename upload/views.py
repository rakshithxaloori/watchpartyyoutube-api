from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)


from authentication.middleware import CustomAuthentication
from watchpartyyoutube.utils import BAD_REQUEST_RESPONSE


@api_view(["POST"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
def get_presigned_posts_view(request):
    uploads = request.data.get("uploads", None)
    if uploads is None:
        return BAD_REQUEST_RESPONSE

    presigned_posts = []

    return JsonResponse(
        {
            "detail": "Presigned posts generated",
            "payload": {
                "urls": presigned_posts,
            },
        },
        status=status.HTTP_200_OK,
    )
