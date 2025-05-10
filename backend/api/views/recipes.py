from django.db.models import Sum
from django.http import FileResponse
from io import BytesIO
from django_filters.rest_framework import (
    DjangoFilterBackend,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers.recipes import (
    FavoriteCreateSerializer,
    IngredientSerializer,
    RecipeResponseSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    ShoppingCartCreateSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для просмотра списка и отдельных ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    permission_classes = [AllowAny]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """
    CRUD-рецептов с дополнительными действиями (избранное, корзина,
    скачивание).
    """

    queryset = Recipe.objects.all().distinct()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeResponseSerializer
        return RecipeSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        base_url = request.build_absolute_uri('/')[:-1]
        recipe_url = f"{base_url}/recipes/{pk}/"
        return Response({'short-link': recipe_url})

    def _short_response(self, recipe, status_code=status.HTTP_201_CREATED):
        serializer = RecipeShortSerializer(
            recipe, context=self.get_serializer_context()
        )
        return Response(serializer.data, status=status_code)

    @staticmethod
    def _handle_post_action(request, recipe, serializer_class):
        serializer = serializer_class(
            data={'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _handle_delete_action(model_class, user, recipe, not_found_message):
        deleted, _ = model_class.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': not_found_message},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def manage_cart(self, request, pk=None):
        """Добавление или удаление рецепта из корзины покупок."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            return self._handle_post_action(
                request, recipe, ShoppingCartCreateSerializer
            )

        return self._handle_delete_action(
            ShoppingCart, user, recipe, 'Рецепта не было в корзине.'
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = self._get_aggregated_ingredients(request.user)
        content = self._format_ingredients_for_download(ingredients)

        file = BytesIO(content.encode('utf-8'))
        return FileResponse(
            file,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain'
        )

    @staticmethod
    def _get_aggregated_ingredients(user):
        return RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

    @staticmethod
    def _format_ingredients_for_download(ingredients):
        return '\n'.join([
            f'{item["ingredient__name"]} '
            f'({item["ingredient__measurement_unit"]}) — {item["amount"]}'
            for item in ingredients
        ])

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление или удаление рецепта из избранного."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            serializer = FavoriteCreateSerializer(
                data={'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return self._short_response(recipe)

        return self._handle_delete_action(
            Favorite, user, recipe, 'Рецепта не было в избранном.'
        )
