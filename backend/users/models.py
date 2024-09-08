from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import UniqueConstraint

from .constants import MAX_LENGTH
from .validators import validate_username, validate_subscribe_yourself


class UserManager(BaseUserManager):
    def create_user(self, email, username, password, **extra_fields):
        if email is None:
            raise TypeError('email должен быть заполнен.')
        if username is None:
            raise TypeError('username" должен быть заполнен.')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('У суперюзера "is_staff" должен быть "True".')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('У суперюзера "is_superuser" должен быть "True"')
        return self.create_user(
            email, username, password, **extra_fields
        )


class User(AbstractUser, PermissionsMixin):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', 'password')
    username = models.CharField(
        validators=[UnicodeUsernameValidator(), validate_username],
        verbose_name='Логин',
        max_length=MAX_LENGTH,
        unique=True,
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/images/',
        null=True,
        default=None
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
    password = models.CharField(
        verbose_name='Пароль',
        max_length=MAX_LENGTH,
    )
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True)

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользватель'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    objects = UserManager()


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='followers'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор подписки',
        on_delete=models.CASCADE,
        related_name='authors'
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
