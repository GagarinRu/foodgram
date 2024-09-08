from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe
from rest_framework.authtoken.models import TokenProxy
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (Ingredient, Favorite,
                     Recipe, Tag, RecipeIngredient,
                     RecipeTag, ShoppingCart)
from users.models import User, Follow


class RecipeInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 0


class TagsInline(admin.TabularInline):
    model = RecipeTag
    min_num = 1
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (
        RecipeInline,
        TagsInline,
    )
    list_display = (
        'name',
        'author',
        'text',
        'post_photo',
        'cooking_time',
        'get_tags',
        'get_ingredients',
        'favorite_amount'
    )
    list_display_links = (
        'name',
    )
    list_editable = (
        'author',
        'cooking_time',

    )
    search_fields = (
        'name',
        'author',

    )
    list_filter = (
        'tags__name',

    )
    readonly_fields = ['post_photo']
    filter_vertical = ('tags',)

    @admin.display(description='Теги')
    def get_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return ', '.join(
            [ingredient.name for ingredient in obj.ingredients.all()]
        )

    @admin.display(description="Изображение")
    def post_photo(self, obj):
        if obj:
            return mark_safe(f'<img src={obj.image.url}\
                            \n width="80" height="60">')
        return 'Не задано'

    @admin.display(
        description='Добавлений в избранное'
    )
    def favorite_amount(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_display_links = (
        'username',
    )
    search_fields = ["email"]
    list_filter = (
        'first_name',
        'last_name'
    )
    ordering = ["email"]
    empty_value_display = 'Не задано'
    readonly_fields = ['post_avatar']
    fieldsets = [
        (
            'Данные для входа',
            {'fields': ['email', 'password']}
        ),
        (
            'Персональная информация',
            {'fields': ['username', 'first_name', 'last_name']}
        ),
        (
            'Права доступа',
            {'fields': ['is_active', 'is_superuser', 'is_staff']}
        ),
        (
            'Права редактирования',
            {'fields': ['user_permissions']}
        ),
        (
            'События посещений',
            {'fields': ('last_login', 'date_joined')}
        ),
    ]
    add_fieldsets = [
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2',),
        }),
    ]
    filter_horizontal = []

    @admin.display(description="Аватар")
    def post_avatar(self, obj):
        if obj:
            return mark_safe(f'<img src={obj.avatar.url}\
                            \n width="80" height="60">')
        return 'Не задано'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )
    search_fields = ('name',)
    empty_value_display = 'Не задано'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    inlines = (
        RecipeInline,
    )
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)
    empty_value_display = 'Не задано'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    empty_value_display = 'Нет Информации'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    empty_value_display = 'Нет Информации'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    empty_value_display = 'Нет Информации'


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
admin.site.empty_value_display = 'Не задано'
