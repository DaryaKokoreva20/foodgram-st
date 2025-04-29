from rest_framework import viewsets
from recipes.models import Ingredient, Tag
from recipes.serializers import IngredientSerializer, TagSerializer
from rest_framework.permissions import AllowAny


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
