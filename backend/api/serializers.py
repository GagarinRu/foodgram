import base64
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from .constants import MIN_VALUE
from users.models import Follow
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            **validated_data
        )
        return user.set_password(validated_data('password')).save()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return False
        return Follow.objects.filter(id=obj.id).exists()


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'avatar',
        )


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
        source='ingredient'
    )
    amount = serializers.IntegerField()

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
        source='recipe_ingredient'
    )
    tags = TagSerializer(many=True)
    amount = RecipeIngredientSerializer(many=True, read_only=True)
    image = Base64ImageField()
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
        if request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientsAddSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                f'Нужен {MIN_VALUE} ингредиент'
            )
        ingredient_ids = [
            ingredient.get('ingredient').id for ingredient in ingredients
        ]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise serializers.ValidationError(
                'Нельзя дублировать ингредиенты'
            )
        for ingredient in ingredients:
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    f'Количество ингридиентов не менее {MIN_VALUE}!'
                )
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                f'Требуется хотя бы {MIN_VALUE} тег'
            )
        tags_ids = [
            tag.id for tag in tags
        ]
        if len(set(tags_ids)) != len(tags_ids):
            raise serializers.ValidationError(
                'Нельзя дублировать теги'
            )
        return tags

    def validate(self, attrs):
        attrs['ingredients'] = (
            self.validate_ingredients(attrs.get('ingredients', []))
        )
        attrs['tags'] = self.validate_tags(attrs.get('tags', []))
        return attrs

    def get_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient.get('ingredient'),
                amount=ingredient.get('amount')
            )

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
        instance.recipe_ingredient.all().delete()
        self.get_ingredients(ingredients, instance)
        instance.tags.set(validated_data.pop('tags'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context['request']
        serializer = RecipeSerializer(
            instance, context={'request': request}
        )
        return serializer.data


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = (
            'user',
            'recipe',
        )

    def validate_recipe(self, recipe):
        request = self.context['request']
        user = request.user
        if request.method == 'POST':
            if Favorite.objects.filter(
                    user=user,
                    recipe=recipe
            ).exists():
                raise serializers.ValidationError(
                    'Рецепт уже есть в избранном'
                )
        if request.method == 'DELETE' and not Favorite.objects.filter(
                user=user,
                recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                'Рецепт не найден в избранном'
            )
        return recipe


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe'
        )

    def validate_recipe(self, recipe):
        request = self.context.get('request')
        user = request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                    user=user,
                    recipe=recipe
            ).exists():
                raise serializers.ValidationError(
                    'Рецепт уже есть в корзине'
                )
        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(
                    user=user,
                    recipe=recipe
            ).exists():
                raise serializers.ValidationError(
                    'Рецепт не найден в корзине'
                )
        return recipe


class FollowRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class UserFollowSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes_count', 'recipes')
        read_only_fields = (
            'recipes_count',
            'recipes',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        limit = self.context['request'].query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = FollowRecipeSerializer(
            recipes,
            many=True,
            read_only=True
        )
        return serializer.data


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
                "Вы не можете подписаться на себя."
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя."
            )
        return author

    def to_representation(self, instance):
        context = self.context
        context['request'].user = instance.user
        serializer = UserFollowSerializer(instance.author, context=context)
        return serializer.data
