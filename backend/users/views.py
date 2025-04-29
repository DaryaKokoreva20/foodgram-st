from djoser.views import UserViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import Follow
from users.models import User
from users.serializers import CustomUserSerializer

from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Список подписок пользователя"""
        follows = Follow.objects.filter(user=request.user)
        authors = [follow.author for follow in follows]
        serializer = self.get_serializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data)


class CurrentUserViewSet(UserViewSet):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class FollowViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        follows = Follow.objects.filter(user=user)
        authors = [follow.author for follow in follows]
        serializer = CustomUserSerializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(user=user, author=author)
            serializer = CustomUserSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            follow = Follow.objects.filter(user=user, author=author)
            if follow.exists():
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
