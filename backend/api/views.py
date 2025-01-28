from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from base.models import ShortLink
from base.models import (
    Ingredient, Recipe, RecipeIngredient,
    Favorite, Subscription, ShoppingCart, Profile
)
from .serializers import (
    IngredientSerializer, RecipeSerializer, UserCreateSerializer,
    FavoriteSerializer, SubscriptionSerializer, ShoppingCartSerializer,
    UserSerializer, PasswordChangeSerializer, AvatarSerializer
)
from django.contrib.auth import get_user_model, authenticate, logout

from django.urls import reverse


User = get_user_model()


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
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


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
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


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None   # без этого не показывает ингредиенты!

    def get_queryset(self):
        queryset = Ingredient.objects.all().order_by('name')
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method in ['POST', 'PATCH']:
            context['ingredients'] = self.request.data.get('ingredients', [])
        return context

    def get_queryset(self):
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
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if self.get_object().author != self.request.user:
            raise PermissionDenied(
                "У вас нет прав на редактирование этого рецепта."
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied(
                "У вас нет прав на удаление этого рецепта."
            )
        instance.delete()

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
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

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()

        frontend_url = settings.FRONTEND_URL + f'/recipes/{pk}'

        short_link, created = ShortLink.objects.get_or_create(original_url=frontend_url)
        short_url = request.build_absolute_uri(f'/{short_link.short_code}')
        print({'short-link': short_url})
        return Response({'short-link': short_url}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def set_password(self, request):
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

    @action(detail=False, methods=['put', 'delete'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)

        if request.method == 'DELETE':
            if profile.avatar:
                profile.avatar.delete()
                profile.avatar = None
                profile.save()
                return Response(
                    {'avatar': None},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'error': 'Аватар отсутствует'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AvatarSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=[
                permissions.IsAuthenticated])
    def subscriptions(self, request):
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
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
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


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        if 'logout' in request.path:
            if request.user.is_authenticated:
                request.user.auth_token.delete()
                logout(request)
                return Response(
                    {'status': 'Выход выполнен успешно'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'error': 'Пользователь не аутентифицирован'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Требуется email и пароль.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь с таким email не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=user.username, password=password)

        if user is None:
            return Response(
                {'error': 'Неверные учетные данные'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'auth_token': token.key,
            'user_id': user.id,
            'email': user.email,
        })
