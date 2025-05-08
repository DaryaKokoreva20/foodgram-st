from django.db.models import Sum
from django.http import HttpResponse
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

from api.filters import IngredientFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers.recipes import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeResponseSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    ShoppingCartSerializer,
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

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

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

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def manage_cart(self, request, pk=None):
        user = request.user

        recipe = self.get_object()

        if request.method == 'POST':

            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = ShoppingCartSerializer(
                data={'recipe': recipe.id},
                context={'request': request, 'view': self}
            )

            serializer.is_valid(raise_exception=True)
            serializer.save()

            return self._short_response(recipe)

        if request.method == 'DELETE':
            deleted, _ = ShoppingCart.objects.filter(
                user=user, recipe=recipe
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'detail': 'Рецепта не было в корзине.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        recipes_in_cart = ShoppingCart.objects.filter(
            user=request.user
        ).values_list('recipe', flat=True)

        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes_in_cart
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        lines = []
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['amount']
            lines.append(f'{name} ({unit}) — {amount}')

        content = '\n'.join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        user = request.user

        if not user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        recipe = self.get_object()

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FavoriteSerializer(
                data={}, context={'request': request, 'view': self}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return self._short_response(recipe)

        if request.method == 'DELETE':
            deleted, _ = Favorite.objects.filter(
                user=user, recipe=recipe
            ).delete()
            if deleted:
                return Response(
                    {'detail': 'Рецепт удалён из избранного.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'detail': 'Рецепта не было в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        params = self.request.query_params

        if params.get('is_favorited') == '1' and user.is_authenticated:
            queryset = queryset.filter(favorited_by__user=user)

        if params.get('is_in_shopping_cart') == '1' and user.is_authenticated:
            queryset = queryset.filter(in_shopping_cart__user=user)

        if params.get('author'):
            queryset = queryset.filter(author__id=params.get('author'))

        return queryset
