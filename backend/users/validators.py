from django.core.exceptions import ValidationError
from django.conf import settings


def validate_username(value):
    if value in settings.BAD_USERNAMES:
        raise ValidationError(f'Имя "{value}" использовать нельзя')
