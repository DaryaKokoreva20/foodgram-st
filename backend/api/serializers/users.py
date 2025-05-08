from rest_framework import serializers
from users.models import User, Follow
from recipes.models import Recipe
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    SetPasswordSerializer,
    UserSerializer as DjoserUserSerializer
)
from api.serializers.recipes import RecipeShortSerializer
from api.fields import Base64ImageField


class CustomUserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя с данными о подписке и рецептах."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Follow.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        queryset = Recipe.objects.filter(author=obj)
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        return RecipeShortSerializer(
            queryset, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор для регистрации нового пользователя."""
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'password'
        )
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}
        }


class UserListSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class CustomSetPasswordSerializer(SetPasswordSerializer):
    """Сериализатор для смены пароля пользователем."""
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def save(self, **kwargs):
        user = self.context['request'].user
        password = self.validated_data['new_password']
        user.set_password(password)
        user.save()
        return user

    def validate(self, attrs):
        return super().validate(attrs)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки: включает рецепты, счётчик и статус подписки."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        queryset = Recipe.objects.filter(author=obj)
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        return RecipeShortSerializer(
            queryset, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()
