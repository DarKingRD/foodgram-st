from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
)
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from base.models import (
    Ingredient, Recipe, RecipeIngredient, Favorite, 
    Subscription, ShoppingCart
)
from .serializers import (
    IngredientSerializer, RecipeSerializer, UserCreateSerializer,
    FavoriteSerializer, SubscriptionSerializer, ShoppingCartSerializer,
    UserSerializer, PasswordChangeSerializer
)

User = get_user_model()


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """ViewSet для управления корзиной покупок."""
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецептов из корзины покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
            return Response(
                {'status': 'добавлено в корзину'},
                status=status.HTTP_201_CREATED
            )

        ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(viewsets.ModelViewSet):
    """ViewSet для управления избранными рецептами."""
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Добавление и удаление рецептов из избранного."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            Favorite.objects.get_or_create(user=user, recipe=recipe)
            return Response(
                {'status': 'добавлено в избранное'},
                status=status.HTTP_201_CREATED
            )

        Favorite.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Отключение пагинации для ингредиентов

    def get_queryset(self):
        """Фильтрация ингредиентов по имени."""
        queryset = Ingredient.objects.all().order_by('name')
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        """Добавление ингредиентов в контекст сериализатора."""
        context = super().get_serializer_context()
        if self.request.method in ['POST', 'PATCH']:
            context['ingredients'] = self.request.data.get('ingredients', [])
        return context

    def get_queryset(self):
        """Фильтрация рецептов по автору, корзине и избранному."""
        queryset = Recipe.objects.all().order_by('-date_published')
        params = self.request.query_params

        author_id = params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        if self.request.user.is_authenticated:
            is_in_shopping_cart = params.get('is_in_shopping_cart')
            if is_in_shopping_cart is not None:
                if is_in_shopping_cart == '1':
                    queryset = queryset.filter(
                        shopping_carts__user=self.request.user
                    )
                elif is_in_shopping_cart == '0':
                    queryset = queryset.exclude(
                        shopping_carts__user=self.request.user
                    )

            is_favorited = params.get('is_favorited')
            if is_favorited is not None:
                if is_favorited == '1':
                    queryset = queryset.filter(
                        favorites__user=self.request.user
                    )
                elif is_favorited == '0':
                    queryset = queryset.exclude(
                        favorites__user=self.request.user
                    )

        return queryset.distinct()

    def perform_create(self, serializer):
        """Создание рецепта с указанием автора."""
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """Проверка прав на редактирование рецепта."""
        if self.get_object().author != self.request.user:
            raise PermissionDenied(
                "У вас нет прав на редактирование этого рецепта."
            )
        serializer.save()

    def perform_destroy(self, instance):
        """Проверка прав на удаление рецепта."""
        if instance.author != self.request.user:
            raise PermissionDenied(
                "У вас нет прав на удаление этого рецепта."
            )
        instance.delete()

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Добавление и удаление рецепта из избранного."""
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            Favorite.objects.get_or_create(user=user, recipe=recipe)
            return Response(
                {'status': 'добавлено в избранное'},
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            Favorite.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта из корзины."""
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
            return Response(
                {'status': 'добавлено в корзину'},
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by('ingredient__name')

        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )

        for item in ingredients:
            response.write(
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) - "
                f"{item['total_amount']}\n"
            )

        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        ...


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пользователями."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """Определение прав доступа в зависимости от действия."""
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """Определение сериализатора в зависимости от действия."""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[
        permissions.IsAuthenticated])
    def me(self, request):
        """Получение данных текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[
        permissions.IsAuthenticated])
    def set_password(self, request):
        """Изменение пароля пользователя."""
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data['current_password']):
                user.set_password(serializer.data['new_password'])
                user.save()
                return Response({'status': 'пароль изменен'})
            return Response(
                {'current_password': ['Неверный пароль']},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put', 'delete'], permission_classes=[
        permissions.IsAuthenticated], url_path='me/avatar')
    def avatar(self, request):
        ...

    @action(detail=False, methods=['get'], permission_classes=[
        permissions.IsAuthenticated])
    def subscriptions(self, request):
        """Получение списка подписок пользователя."""
        subscriptions = request.user.subscriptions.select_related(
            'author', 'author__profiles'
        ).prefetch_related('author__recipes')

        authors = [subscription.author for subscription in subscriptions]
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписка и отписка от автора."""
        author = get_object_or_404(User, id=pk)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                user=user, author=author
            )

            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {'success': 'Подписка успешно оформлена'},
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            subscription = get_object_or_404(
                Subscription, user=user, author=author
            )
            subscription.delete()
            return Response(
                {'success': 'Подписка успешно отменена'},
                status=status.HTTP_204_NO_CONTENT
            )


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet для управления подписками."""
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        """Подписка и отписка от автора."""
        author = get_object_or_404(User, id=pk)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                user=user,
                author=author,
                defaults={'recipes_count': author.recipes.count()}
            )

            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            get_object_or_404(
                Subscription,
                user=user,
                author=author
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
