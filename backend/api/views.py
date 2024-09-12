import short_url
from django.db.models import Count, Exists, F, Sum, OuterRef
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django.urls import reverse
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
                          RecipeSerializer,
                          TagSerializer, UserAvatarSerializer,
                          UserFollowSerializer, UserSerializer,
                          FavoriteSerializer, ShoppingCartSerializer)
from recipes.models import (Favorite, Ingredient,
                            Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'tags',
            'ingredients',
        )
        user = self.request.user
        if user.is_authenticated:
            is_favorited = user.favorite_set.filter(
                recipe=OuterRef('pk')
            )
            is_in_shopping_cart = user.shoppingcart_set.filter(
                recipe=OuterRef('pk')
            )
            queryset.annotate(
                is_favorited=Exists(is_favorited),
                is_in_shopping_cart=Exists(is_in_shopping_cart)
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    @staticmethod
    def get_favorite_or_cart(request, serializer_class, pk):
        serializer = serializer_class(
            data={
                'user': request.user.id,
                'recipe': get_object_or_404(Recipe, pk=pk).pk
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def del_favorite_or_cart(request, model, pk):
        delete_status, _ = model.objects.filter(
            user=request.user,
            recipe=get_object_or_404(Recipe, pk=pk).pk
        ).delete()
        return Response(
            'Рецепт удален',
            status=status.HTTP_204_NO_CONTENT
            if delete_status
            else status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        return self.get_favorite_or_cart(request, FavoriteSerializer, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.del_favorite_or_cart(request, Favorite, pk)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        return self.get_favorite_or_cart(request, ShoppingCartSerializer, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.del_favorite_or_cart(request, ShoppingCart, pk)

    @staticmethod
    def shopping_list(ingredients):
        shopping_list = ()
        for item in ingredients:
            shopping_list.append(f'\n{item["name"]}'
                                 f', {item["amount"]}'
                                 f', {item["measurement"]}')
        return shopping_list

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart_set__user=user
        ).values(
            name=F('ingredient__name'),
            measurement=F('ingredient__measurement_unit'),
        ).annotate(
            amount=Sum('amount')
        ).order_by('name')
        return FileResponse(
            self.shopping_list(ingredients,),
            content_type="text"
        )

    @action(
        methods=('get',),
        detail=True,
        url_path='get-link',
    )
    def get_link(self, request, pk):
        recipe = self.get_object()
        short_link = short_url.encode_url(recipe.id)
        short_link = request.build_absolute_uri(
            reverse(
                'shortlink',
                kwargs={'slug': short_link}
            )
        )
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )


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
        serializer = UserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=('put',),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
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

    @avatar.mapping.delete
    def del_avatar(self, request):
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(
            subscriptions_to_author__user=user
        ).annotate(
            recipes_count=Count('recipes')
        ).order_by('username')
        pages = self.paginate_queryset(queryset)
        serializer = UserFollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        serializer = FollowSerializer(
            data={
                'user': request.user.id,
                'author': get_object_or_404(User, pk=id).id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def del_subscribe(self, request, id):
        delete_status, _ = Follow.objects.filter(
            user=request.user,
            author=get_object_or_404(User, pk=id).id
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
            if delete_status
            else status.HTTP_400_BAD_REQUEST
        )
