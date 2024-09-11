from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import UniqueConstraint

from .constants import MAX_LENGTH
from .validators import validate_username, validate_subscribe_yourself


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    username = models.CharField(
        validators=(UnicodeUsernameValidator(), validate_username,),
        verbose_name='Логин',
        max_length=MAX_LENGTH,
        unique=True,
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/images/',
        null=True,
        blank=True,
    )
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH,
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользватель'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='user_subscriptions'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='author_subscriptions'
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Подсписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow',
            )
        ]

    def clean(self):
        validate_subscribe_yourself(self)

    def __str__(self):
        return f'{self.user} {self.author}'
