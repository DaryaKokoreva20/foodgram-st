from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator
)
from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)

MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 10000


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeWriteSerializer(serializers.Serializer):
    """Сериализатор для записи ингредиента в рецепте (id и количество)."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(MIN_INGREDIENT_AMOUNT),
            MaxValueValidator(MAX_INGREDIENT_AMOUNT),
        ]
    )


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения ингредиента в рецепте с данными из связанной
    модели.
    """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецептов с валидацией ингредиентов
    и тегов.
    """

    ingredients = IngredientInRecipeWriteSerializer(many=True)
    author = serializers.SerializerMethodField()
    image = Base64ImageField()

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
            'pub_date'
        )

    def validate_image(self, image):
        if self.instance is None and not image:
            raise serializers.ValidationError('Картинка обязательна.')
        return image

    def validate(self, data):
        ingredients_data = self.initial_data.get('ingredients')
        if not isinstance(ingredients_data, list):
            raise ValidationError({'ingredients': 'Неверный формат данных.'})

        if not ingredients_data:
            raise ValidationError(
                {'ingredients': 'Нужно добавить хотя бы один ингредиент.'}
            )

        ingredient_ids = [item['id'] for item in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        validated_data.pop('author', None)
        user = self.context['request'].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def create_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)

        instance = super().update(instance, validated_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeResponseSerializer(instance, context=self.context).data


class RecipeResponseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения рецептов (чтение), включает вложенные данные.
    """

    ingredients = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text', 'cooking_time',
            'ingredients', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_author(self, obj):
        from api.serializers.users import UserListSerializer
        return UserListSerializer(obj.author, context=self.context).data

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientInRecipeReadSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated and user.favorites.filter(
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated and user.shopping_cart.filter(
                recipe=obj
            ).exists()
        )


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Краткий сериализатор рецепта — для отображения в избранном или корзине.
    """

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели избранного рецепта.
    Используется при добавлении/удалении.
    """

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')
        read_only_fields = ('user', 'recipe')

    def create(self, validated_data):
        request = self.context['request']
        recipe = self.context['view'].get_object()
        return Favorite.objects.create(user=request.user, recipe=recipe)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели корзины покупок.
    Используется при добавлении/удалении.
    """

    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
        read_only_fields = ('user',)

    def create(self, validated_data):
        request = self.context['request']
        recipe = self.context['view'].get_object()
        return ShoppingCart.objects.create(user=request.user, recipe=recipe)
