from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import CustomAuthToken
from .views import (
    IngredientViewSet, RecipeViewSet, UserViewSet
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register('ingredients', IngredientViewSet, basename='ingredient')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', CustomAuthToken.as_view(), name='token_login'),
    path('auth/token/logout/', CustomAuthToken.as_view(), name='token_logout'),
]
