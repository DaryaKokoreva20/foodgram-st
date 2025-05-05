from rest_framework import viewsets
from recipes.models import (
    Ingredient, Tag, Recipe, Favorite, ShoppingCart, RecipeIngredient
)
from api.serializers.recipes import (
    IngredientSerializer, TagSerializer, RecipeSerializer,
    ShoppingCartSerializer, FavoriteSerializer, RecipeResponseSerializer,
    RecipeShortSerializer
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import permissions
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import FilterSet, CharFilter
from django_filters.rest_framework import DjangoFilterBackend


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешение на изменение/удаление только для автора."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    permission_classes = [AllowAny]
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        return [AllowAny()]

    def perform_create(self, serializer):
        recipe = serializer.save(author=self.request.user)
        response_serializer = RecipeResponseSerializer(
            recipe, context=self.get_serializer_context()
        )
        self._recipe_response = response_serializer.data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            self._recipe_response,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_serializer = RecipeResponseSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeResponseSerializer
        return RecipeSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        base_url = request.build_absolute_uri('/')[:-1]
        recipe_url = f"{base_url}/recipes/{pk}/"
        return Response({'short-link': recipe_url})

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def manage_cart(self, request, pk=None):
        user = request.user

        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

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

            recipe_serializer = RecipeShortSerializer(
                recipe, context={'request': request}
            )
            return Response(
                recipe_serializer.data, status=status.HTTP_201_CREATED
            )

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

            recipe_serializer = RecipeShortSerializer(
                recipe, context={'request': request}
            )
            return Response(
                recipe_serializer.data, status=status.HTTP_201_CREATED
            )

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


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
