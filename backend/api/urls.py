from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet, CurrentUserViewSet, FollowViewSet
from recipes.views import (
    IngredientViewSet, TagViewSet, RecipeViewSet, FavoriteViewSet
)


router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')

follow = DefaultRouter()
follow.register('users', FollowViewSet, basename='follows')

ingredients_router = DefaultRouter()
ingredients_router.register(
    'ingredients', IngredientViewSet, basename='ingredients'
)

tags_router = DefaultRouter()
tags_router.register('tags', TagViewSet, basename='tags')

recipes_router = DefaultRouter()
recipes_router.register('recipes', RecipeViewSet, basename='recipes')

favorites_router = DefaultRouter()
favorites_router.register('favorites', FavoriteViewSet, basename='favorites')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(follow.urls)),
    path('', include(ingredients_router.urls)),
    path('', include(tags_router.urls)),
    path('', include(recipes_router.urls)),
    path('', include(favorites_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'auth/user/',
        CurrentUserViewSet.as_view({'get': 'retrieve'}),
        name='current-user'
    ),
]
