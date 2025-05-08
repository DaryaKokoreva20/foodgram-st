from django.conf import settings
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator
)
from django.db import models

from constants import (
    MIN_INGREDIENT_AMOUNT,
    MAX_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
    INGREDIENT_NAME_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH,
)


class Ingredient(models.Model):
    """Модель ингредиента с названием и единицей измерения."""

    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта, связанная с автором, ингредиентами и тегами."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Картинка'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME)],
        verbose_name='Время приготовления (мин.)'
    )

    pub_date = models.DateTimeField(auto_now_add=True)

    @property
    def favorites_count(self):
        return self.favorited_by.count()

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецепта и ингредиента с количеством."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        validators=[
            MinValueValidator(MIN_INGREDIENT_AMOUNT),
            MaxValueValidator(MAX_INGREDIENT_AMOUNT),
        ],
        verbose_name='Количество'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ],
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f"{self.ingredient.name} — {self.amount}"


class Favorite(models.Model):
    """Модель избранных рецептов пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ],
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f"{self.user} favorited {self.recipe}"


class ShoppingCart(models.Model):
    """Модель корзины покупок, связывает пользователя с рецептами."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f"{self.user} added {self.recipe} to cart"
