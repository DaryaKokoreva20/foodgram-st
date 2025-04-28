from djoser.views import UserViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import Follow
from users.models import User
from users.serializers import CustomUserSerializer


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
