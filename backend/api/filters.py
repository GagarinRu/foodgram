from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
    )

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )

    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author']

    def filter_is_favorited(self, queryset, item, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, item, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset
