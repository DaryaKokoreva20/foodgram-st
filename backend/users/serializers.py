from rest_framework import serializers
from users.models import User
from users.models import Follow
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    SetPasswordSerializer
)


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Follow.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
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


class CustomSetPasswordSerializer(SetPasswordSerializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def save(self, **kwargs):
        user = self.context['request'].user
        password = self.validated_data['new_password']
        user.set_password(password)
        user.save()
        return user

    def validate(self, attrs):
        print("VALIDATING:", attrs)
        return super().validate(attrs)
