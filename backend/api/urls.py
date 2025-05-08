from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views.recipes import (
    IngredientViewSet,
    RecipeViewSet,
)
from api.views.users import CustomUserViewSet


router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
