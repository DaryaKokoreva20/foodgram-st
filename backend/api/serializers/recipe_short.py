from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import Recipe


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
