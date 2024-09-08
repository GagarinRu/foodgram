from django.core.exceptions import ValidationError
from django.conf import settings


def validate_subscribe_yourself(self):
    if self.user == self.author:
        raise ValidationError(
            f'{self.user} не может подписаться на себя, {self.author}.'
        )


def validate_username(value):
    if value in settings.BAD_USERNAMES:
        raise ValidationError(f'Имя "{value}" использовать нельзя')
