import short_url
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FollowSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, ShortRecipeSerializer,
                          TagSerializer, UserAvatarSerializer,
                          UserFollowSerializer, UserSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_favorite_or_cart(self, request, model, instance):
        obj = model.objects.filter(
            user=request.user,
            recipe=instance
        )
        if obj.exists():
            return Response(
                'Рецепт уже добавлен',
                status=status.HTTP_400_BAD_REQUEST
            )
        short_item = model.objects.create(
            user=request.user,
            recipe=instance
        )
        serializer = ShortRecipeSerializer(short_item.recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def del_favorite_or_cart(self, request, model, instance):
        obj = model.objects.filter(
            user=request.user,
            recipe=instance
        )
        if obj.exists():
            obj.delete()
            return Response(
                'Рецепт удален',
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk):
        recipe = self.get_object()
        if request.method == 'POST':
            return self.get_favorite_or_cart(request, Favorite, recipe)
        return self.del_favorite_or_cart(request, Favorite, recipe)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            return self.get_favorite_or_cart(request, ShoppingCart, recipe)
        return self.del_favorite_or_cart(request, ShoppingCart, recipe)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        shopping_cart = []
        for item in ingredients:
            shopping_cart.append(f'\n{item["ingredient__name"]}'
                                 f', {item["amount"]}'
                                 f', {item["ingredient__measurement_unit"]}')
        response = HttpResponse(shopping_cart, content_type="text")
        return response

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link',
    )
    def get_link(self, request, pk):
        recipe = self.get_object()
        short_link = short_url.encode_url(recipe.id)
        short_link = request.build_absolute_uri(
            reverse(
                'shortlink',
                kwargs={'short_link': short_link}
            )
        )
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )


def get_short_link(self, short_link):
    if not set(short_link).issubset(set(short_url.DEFAULT_ALPHABET)):
        return Response(
            {'Недопустимые символы в короткой ссылке.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    recipe_id = short_url.decode_url(short_link)
    return redirect(f'/recipes/{recipe_id}/', )


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageLimitPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated,)
    )
    def get_users_info(self, request):
        user = User.objects.get(id=request.user.id)
        serializer = UserSerializer(
            user,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = UserAvatarSerializer(
                user,
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(authors__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = UserFollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, **kwargs):
        author_id = self.kwargs.get('id')
        user = request.user
        author = get_object_or_404(User, id=author_id)
        if request.method == 'POST':
            serializer = FollowSerializer(
                data={
                    'user': user.id,
                    'author': author.id
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        if request.method == 'DELETE':
            follow = Follow.objects.filter(
                user=user,
                author=author
            )
            if not follow.exists():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
