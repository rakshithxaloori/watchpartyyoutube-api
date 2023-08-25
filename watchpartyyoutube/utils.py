import requests

from django.http import JsonResponse
from django.utils import timezone

from rest_framework import status


from authentication.models import User


BAD_REQUEST_RESPONSE = JsonResponse(
    {"detail": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST
)


def get_ip_address(http_forwarded_for, remote_addr):
    x_forwarded_for = http_forwarded_for
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = remote_addr
    return ip


def get_country_code(http_forwarded_for, remote_addr):
    ip = get_ip_address(http_forwarded_for, remote_addr)
    r = requests.get("http://www.geoplugin.net/json.gp?ip={}".format(ip))
    if not r.ok:
        return User.DEFAULT_COUNTRY_CODE
    data = r.json()
    country_code = data["geoplugin_countryCode"]
    return country_code if country_code else User.DEFAULT_COUNTRY_CODE


def get_now_timestamp():
    return int(timezone.now().timestamp())


def get_serializer_first_error(errors):
    errors_dict = dict(errors)
    return (
        f"{list(errors_dict.keys())[0]}: {errors_dict[list(errors_dict.keys())[0]][0]}"
    )
