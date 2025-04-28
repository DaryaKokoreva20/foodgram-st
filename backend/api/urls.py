from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet, CurrentUserViewSet

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'auth/user/',
        CurrentUserViewSet.as_view({'get': 'retrieve'}),
        name='current-user'
    ),
]
