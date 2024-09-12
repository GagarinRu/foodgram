from djoser.serializers import UserSerializer as UserBaseSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .constants import MIN_VALUE
from recipes.models import (Ingredient, Favorite, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User


class UserSerializer(UserBaseSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserBaseSerializer.Meta):
        model = User
        fields = UserBaseSerializer.Meta.fields + ('is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return (
            request and request.user
            and obj.subscriptions_to_author.filter(
                user=request.user.id
            ).exists()
        )


class UserAvatarSerializer(UserBaseSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = (
            'avatar',
        )

    def validate_avatar(self, avatar):
        if not avatar:
            raise serializers.ValidationError(
                'Заполните поле "avatar".'
            )
        return avatar


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientsAddSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(min_value=MIN_VALUE)

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id',
        required=False
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name',
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipeingredient_set'
    )
    tags = TagSerializer(many=True)
    amount = RecipeIngredientSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'tags',
            'amount',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request and request.user
            and obj.subscriptions_to_author.filter(
                user=request.user.id
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request and request.user
            and obj.subscriptions_to_author.filter(
                user=request.user.id
            ).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientsAddSerializer(
        many=True,
        allow_empty=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False
    )
    image = Base64ImageField(
        required=True,
        allow_null=True,
        allow_empty_file=False
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'tags',
            'image',
            'cooking_time',
            'ingredients',
            'author'
        )
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data['ingredients']
        tags = data['tags']
        ingredient_ids = [
            ingredient['id'] for ingredient in ingredients
        ]
        if len(set(ingredient_ids)) != len(ingredients):
            raise serializers.ValidationError(
                'Нельзя дублировать ингредиенты'
            )
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError(
                'Нельзя дублировать теги'
            )
        return data

    @staticmethod
    def get_ingredients(ingredients, recipe):
        data_list = []
        for ingredient in ingredients:
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient.get('ingredient'),
                amount=ingredient.get('amount')
            )
        RecipeIngredient.objects.bulk_create(data_list)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data, author=author)
        recipe.tags.set(tags)
        self.get_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance.recipeingredient_set.all().delete()
        self.get_ingredients(ingredients, instance)
        instance.tags.set(validated_data.pop('tags'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(
            instance=instance,
            context=self.context
        ).data


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = (
            'user',
            'recipe',
        )

    def validate(self, data):
        model = self.Meta.model
        if model.objects.filter(
                user=data['user'],
                recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                {f'{model._meta.verbose_name} error': 'Рецепт уже добавлен'}
            )
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance=instance.recipe,
            context=self.context
        ).data


class FavoriteSerializer(FavoriteShoppingCartSerializer):
    class Meta(FavoriteShoppingCartSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(FavoriteShoppingCartSerializer):
    class Meta(FavoriteShoppingCartSerializer.Meta):
        model = ShoppingCart


class UserFollowSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(default=0)
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes_count', 'recipes')
        read_only_fields = (
            'recipes_count',
            'recipes',
        )

    def get_recipes(self, obj):
        limit = self.context['request'].query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                limit = None
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = (
            'user',
            'author'
        )

    def validate_author(self, author):
        user = self.context['request'].user
        if user == author:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя.'
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )
        return author

    def to_representation(self, instance):
        return UserFollowSerializer(
            instance.author,
            context=self.context
        ).data
