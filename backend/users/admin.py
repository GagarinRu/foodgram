from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from rest_framework.authtoken.models import TokenProxy

from .models import User, Follow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'user_avatar',
    )
    list_display_links = (
        'username',
    )
    search_fields = ('email',)
    list_filter = (
        'first_name',
        'last_name'
    )
    ordering = ('email',)
    empty_value_display = 'Не задано'
    readonly_fields = ('user_avatar',)
    fieldsets = (
        (
            'Данные для входа',
            {'fields': ('email', 'password',)}
        ),
        (
            'Персональная информация',
            {'fields': (
                'username',
                'first_name',
                'last_name',
                'avatar',
                'user_avatar',
            )}
        ),
        (
            'Права доступа',
            {'fields': ('is_active', 'is_superuser', 'is_staff',)}
        ),
        (
            'Права редактирования',
            {'fields': ('user_permissions',)}
        ),
        (
            'События посещений',
            {'fields': ('last_login', 'date_joined')}
        ),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2',),
        }),
    )
    filter_horizontal = ()

    @admin.display(description='Аватар')
    def user_avatar(self, obj):
        if obj.avatar:
            return mark_safe(
                f'<img src={obj.avatar.url} width="80" height="60">'
            )
        return 'Не задано'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    empty_value_display = 'Нет Информации'


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
admin.site.empty_value_display = 'Не задано'
