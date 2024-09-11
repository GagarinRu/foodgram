import short_url

from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response


def get_short_link(self, short_link):
    if not set(short_link).issubset(set(short_url.DEFAULT_ALPHABET)):
        return Response(
            {'Недопустимые символы в короткой ссылке.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    recipe_id = short_url.decode_url(short_link)
    return redirect(f'/recipes/{recipe_id}/', )
