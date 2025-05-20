from rest_framework import serializers
from djoser.serializers import (
    SetPasswordSerializer,
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
)

from api.fields import Base64ImageField
from api.serializers.recipes import RecipeShortSerializer
from recipes.models import Recipe
from users.models import User, Follow


class CustomUserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя с данными о подписке и рецептах."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        return user and user.is_authenticated and user.follower.filter(
            author=obj
        ).exists()

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
        return user and user.is_authenticated and user.follower.filter(
            author=obj
        ).exists()


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

    class Meta:
        fields = ('current_password', 'new_password')

    def to_representation(self, instance):
        return {"new_password": self.validated_data["new_password"]}


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор подписки: включает рецепты, счётчик и статус подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        queryset = obj.recipes.all()
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        return RecipeShortSerializer(
            queryset, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки на пользователя."""

    class Meta:
        model = Follow
        fields = ('author', 'user')
        read_only_fields = ('user',)

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )
        data['user'] = user
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.author,
            context=self.context
        ).data
