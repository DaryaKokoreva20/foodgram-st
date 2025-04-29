from rest_framework import viewsets
from recipes.models import Ingredient
from recipes.serializers import IngredientSerializer
from rest_framework.permissions import AllowAny


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
