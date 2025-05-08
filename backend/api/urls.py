from django.urls import include, path
from djoser import views as djoser_views
from rest_framework.routers import DefaultRouter

from api.views.recipes import (
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartViewSet,
    TagViewSet,
)
from api.views.users import CustomUserViewSet


router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('cart', ShoppingCartViewSet, basename='cart')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'auth/set_password/',
        djoser_views.UserViewSet.as_view({'post': 'set_password'}),
        name='set_password'
    ),
]
