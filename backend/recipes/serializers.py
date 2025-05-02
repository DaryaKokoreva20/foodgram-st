from rest_framework import serializers
from recipes.models import (
    Ingredient, Tag, Recipe, RecipeIngredient, Favorite, ShoppingCart
)
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from utils.fields import Base64ImageField


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientInRecipeWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(validators=[MinValueValidator(1)])


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False
    )
    author = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
            'ingredients',
            'tags',
            'pub_date',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_author(self, obj):
        from users.serializers import CustomUserSerializer
        return CustomUserSerializer(obj.author, context=self.context).data

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientInRecipeReadSerializer(ingredients, many=True).data

    def validate(self, data):
        ingredients_data = self.initial_data.get('ingredients')
        if not ingredients_data:
            raise ValidationError(
                {'ingredients': 'Нужно добавить хотя бы один ингредиент.'}
            )

        seen = set()
        for item in ingredients_data:
            ingredient_id = item['id']
            amount = item.get('amount')
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise ValidationError({
                    'ingredients': (
                        f'Ингредиент с id={ingredient_id} не существует.'
                    )
                })
            if amount is None or int(amount) < 1:
                raise ValidationError({
                    'ingredients': (
                        f'У ингредиента с id={ingredient_id} '
                        'количество должно быть ≥ 1.'
                    )
                })

            if ingredient_id in seen:
                raise ValidationError(
                    {'ingredients': 'Ингредиенты не должны повторяться.'}
                )
            seen.add(ingredient_id)

        return data

    def create(self, validated_data):
        ingredients_data = self.initial_data.get('ingredients')
        tags = validated_data.pop('tags', [])
        validated_data.pop('author', None)

        user = self.context['request'].user

        recipe = Recipe.objects.create(author=user, **validated_data)

        recipe.tags.set(tags)
        for ingredient in ingredients_data:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            recipe.ingredients.add(
                ingredient_id,
                through_defaults={'amount': amount}
            )

        return recipe

    def create_ingredients(self, recipe, ingredients_data):
        for ingredient in ingredients_data:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            recipe.ingredients.add(
                ingredient_id,
                through_defaults={'amount': amount}
            )

    def update(self, instance, validated_data):
        ingredients_data = self.initial_data.get('ingredients')
        tags = validated_data.pop('tags', None)

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get(
            'text', instance.text
        )
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(instance, ingredients_data)

        return instance

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')
        read_only_fields = ('user', 'recipe')

    def create(self, validated_data):
        request = self.context['request']
        recipe = self.context['view'].get_object()
        return Favorite.objects.create(user=request.user, recipe=recipe)


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
        read_only_fields = ('user',)

    def create(self, validated_data):
        request = self.context['request']
        recipe = self.context['view'].get_object()
        return ShoppingCart.objects.create(user=request.user, recipe=recipe)
