from djoser.views import UserViewSet
from djoser.serializers import SetPasswordSerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.serializers.users import (
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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'set_password':
            return SetPasswordSerializer
        if self.action == 'create':
            return CustomUserCreateSerializer
        if self.action in ('retrieve', 'list', 'me'):
            return UserListSerializer
        return CustomUserSerializer

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        authors = User.objects.filter(following__user=request.user)

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
                data={'author': author.id, 'user': user.id},
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
