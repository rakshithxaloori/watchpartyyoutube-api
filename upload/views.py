import hashlib

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
from upload.utils import create_presigned_s3_post
from upload.models import Video

MAX_UPLOADS_COUNT = 30
MAX_FILE_SIZE = 1024 * 1024 * 1024 * 10  # 10 GB


@api_view(["POST"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
def get_presigned_posts_view(request):
    files = request.data.get("files", None)
    if (
        files is None
        or type(files) != list
        or len(files) == 0
        or len(files) > MAX_UPLOADS_COUNT
    ):
        return BAD_REQUEST_RESPONSE

    presigned_posts = []
    for file in files:
        file_size = file.get("size", None)
        file_name = file.get("name", None)

        if (
            file_size is None
            or file_name is None
            or file_size > MAX_FILE_SIZE
            or type(file_size) != int
            or file_size < 0
        ):
            return BAD_REQUEST_RESPONSE

    for file in files:
        file_size = file.get("size", None)
        file_name = file.get("name", None)
        # Create a hash of the filename
        hash_object = hashlib.md5(file_name.encode())
        hex_dig = hash_object.hexdigest()
        file_path = f"{request.user.username}/{hex_dig}.mp4"
        presigned_post = create_presigned_s3_post(file_size, file_path)
        presigned_posts.append(presigned_post)

        # Create a video instance
        Video.objects.create(
            user=request.user,
            title=file_name,
            size=file_size,
            path=file_path,
        )

    return JsonResponse(
        {
            "detail": "Presigned posts generated",
            "payload": {
                "urls": presigned_posts,
            },
        },
        status=status.HTTP_200_OK,
    )
