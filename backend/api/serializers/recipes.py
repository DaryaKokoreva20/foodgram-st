from rest_framework import serializers
from recipes.models import (
    Ingredient, Tag, Recipe, RecipeIngredient, Favorite, ShoppingCart
)
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from api.fields import Base64ImageField


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиента."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели тега."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientInRecipeWriteSerializer(serializers.Serializer):
    """Сериализатор для записи ингредиента в рецепте (id и количество)."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(validators=[MinValueValidator(1)])


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
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецептов с валидацией ингредиентов
    и тегов.
    """
    ingredients = serializers.SerializerMethodField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False
    )
    author = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
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
            'tags',
            'pub_date',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_author(self, obj):
        from api.serializers.users import UserListSerializer
        return UserListSerializer(obj.author, context=self.context).data

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientInRecipeReadSerializer(ingredients, many=True).data

    def validate(self, data):
        if not data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Картинка обязательна.'}
            )

        ingredients_data = self.initial_data.get('ingredients')
        if not isinstance(ingredients_data, list):
            raise ValidationError({'ingredients': 'Неверный формат данных.'})

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
        self.create_ingredients(recipe, ingredients_data)
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
            user.is_authenticated and Favorite.objects.filter(
                user=user, recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated and ShoppingCart.objects.filter(
                user=user, recipe=obj
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
