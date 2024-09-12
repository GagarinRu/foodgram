from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .constants import (MIN_VALUE, INGREDIENT_LEN, MEASUREMENT_UNIT_LEN,
                        RECIPE_LEN, TAG_LEN, SLICE_LENGTH, MAX_VALUE)


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название тега',
        max_length=TAG_LEN,
        unique=True,
    )

    slug = models.SlugField(
        verbose_name='Идентификатор',
        max_length=TAG_LEN,
        unique=True,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:SLICE_LENGTH]


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название Ингредиента',
        max_length=INGREDIENT_LEN,
        unique=True,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MEASUREMENT_UNIT_LEN,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit',),
                name='unique_ingredient',
            ),
        )

    def __str__(self):
        return self.name[:SLICE_LENGTH]


class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=RECIPE_LEN
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )
    image = models.ImageField(
        verbose_name='Картинка рецепта',
        upload_to='recipes/images/',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список ингредиентов',
        through='RecipeIngredient',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=(
            (MinValueValidator(
                MIN_VALUE,
                message=f'Время приготовления не менее {MIN_VALUE}!')),
            (MaxValueValidator(
                MAX_VALUE,
                message=f'Время приготовления не более {MAX_VALUE}!'))
        ),
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'author',),
                name='unique_recipe',
            ),
        )

    def __str__(self):
        return self.name[:SLICE_LENGTH]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецерт',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
    )

    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(
                MIN_VALUE,
                message=f'Количество ингридиентов не менее {MIN_VALUE}!'
            ),
        ),
    )

    class Meta:
        verbose_name = 'Кол-во ингредиента в рецепте'
        verbose_name_plural = 'Кол-во ингредиентов в рецепте'
        default_related_name = 'recipeingredient_set'
        ordering = ('ingredient',)
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient',),
                name='unique_recipeingredient',
            ),
        )

    def __str__(self):
        return (f'{self.recipe} {self.ingredient}')[:SLICE_LENGTH]


class UserRecipe(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_%(class)s',
            ),
        )

    def __str__(self):
        return (
            f'{self.recipe}'
            f'{self.user}'
            f'{self._meta.verbose_name}'
        )[:SLICE_LENGTH]


class Favorite(UserRecipe):

    class Meta(UserRecipe.Meta):
        ordering = ('id',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favorite_set'


class ShoppingCart(UserRecipe):

    class Meta(UserRecipe.Meta):
        verbose_name = 'Список Покупок'
        verbose_name_plural = 'Списки Покупок'
        default_related_name = 'shoppingcart_set'
