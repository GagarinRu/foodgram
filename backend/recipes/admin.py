from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (Ingredient, Favorite,
                     Recipe, Tag, RecipeIngredient,
                     ShoppingCart)


class RecipeInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (
        RecipeInline,
    )
    list_display = (
        'name',
        'author',
        'text',
        'recipe_photo',
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
    readonly_fields = ('recipe_photo',)
    filter_vertical = ('tags',)

    @admin.display(description='Теги')
    def get_tags(self, recipe):
        return ', '.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, recipe):
        return ', '.join(
            ingredient.name for ingredient in recipe.ingredients.all()
        )

    @admin.display(description='Изображение')
    def recipe_photo(self, recipe):
        if recipe.image:
            return mark_safe(
                f'<img src={recipe.image.url} width="80" height="60">'
            )
        return 'Не задано'

    @admin.display(
        description='Добавлений в избранное'
    )
    def favorite_amount(self, recipe):
        return recipe.favorite_set.count()


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


admin.site.empty_value_display = 'Не задано'
