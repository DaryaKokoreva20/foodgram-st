from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.serializers.users import (
    CustomSetPasswordSerializer,
    CustomUserCreateSerializer,
    CustomUserSerializer,
    SubscriptionCreateSerializer,
    SubscriptionSerializer,
    UserAvatarSerializer,
    UserListSerializer,
)
from users.models import Follow, User


class CustomUserViewSet(UserViewSet):
    """Расширенное представление пользователей."""

    queryset = User.objects.all()
    lookup_field = 'pk'

    permission_classes_by_action = {
        'retrieve': [AllowAny],
        'me': [IsAuthenticated],
        'list': [AllowAny],
        'subscriptions': [IsAuthenticated],
        'subscribe': [IsAuthenticated],
        'set_password': [IsAuthenticated],
        'update_avatar': [IsAuthenticated],
    }

    def get_permissions(self):
        try:
            return [
                permission(
                ) for permission in self.permission_classes_by_action[
                    self.action
                ]
            ]
        except KeyError:
            return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        if self.action == 'set_password':
            return CustomSetPasswordSerializer
        if self.action in ('retrieve', 'list', 'me'):
            return UserListSerializer
        return CustomUserSerializer

    @action(["post"], detail=False, permission_classes=[IsAuthenticated])
    def set_password(self, request, *args, **kwargs):
        """Позволяет авторизованному пользователю сменить пароль."""
        serializer = CustomSetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        follows = Follow.objects.filter(
            user=request.user
        ).select_related('author')
        authors = User.objects.filter(following__in=follows).distinct()

        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def update_avatar(self, request):
        """Позволяет загрузить или удалить аватар пользователя."""
        user = self.request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        if 'avatar' not in request.data or not request.data['avatar']:
            return Response(
                {'errors': 'Поле avatar не может быть пустым.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserAvatarSerializer(
            user, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        """Подписка или отписка от другого пользователя."""
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if request.method == 'POST':
            serializer = SubscriptionCreateSerializer(
                data={'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            follow = serializer.save()
            return Response(
                SubscriptionSerializer(
                    follow.author, context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        deleted, _ = Follow.objects.filter(user=user, author=author).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Вы не подписаны на этого автора'},
            status=status.HTTP_400_BAD_REQUEST
        )
