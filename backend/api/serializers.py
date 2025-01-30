from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer as DjoserUserSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.password_validation import validate_password
from base.models import (
    Ingredient, Recipe, RecipeIngredient, Subscription,
    Favorite, ShoppingCart
)


User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, author):
        """Проверяет, подписан ли текущий пользователь на автора."""
        request = self.context.get('request')
        return bool(
            request and
            request.user.is_authenticated and
            Subscription.objects.filter(
                user=request.user, author=author).exists()
        )


class UserSubscriptionSerializer(UserSerializer):
    """Сериализатор для информации о пользователе
    с его подписками и рецептами"""
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_recipes(self, author):
        return RecipeSerializer(
            author.recipes.all()[:int(self.context.get('request').GET.get(
                'recipes_limit', 10**10))], 
            many=True, context=self.context
        ).data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients', many=True
    )
    cooking_time = serializers.IntegerField(min_value=1, required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def validate(self, data):
        """Проверяет корректность данных рецепта."""
        ingredients = data.get('recipe_ingredients', [])

        if not ingredients:
            raise serializers.ValidationError(
                "Должен быть хотя бы один ингредиент."
            )

        ingredient_ids = [ingredient['id'] for ingredient in ingredients]

        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise serializers.ValidationError(
                "Дублирование ингредиентов не допускается."
            )

        return data

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        return bool(
            request and
            request.user.is_authenticated and
            Favorite.objects.filter(
                user=request.user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину покупок."""
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        shoppingcart = ShoppingCart.objects.filter(
            user=request.user, recipe=obj).exists()
        return shoppingcart

    def create(self, validated_data):
        """Создаёт рецепт и связанные ингредиенты."""
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        recipe = super().create(validated_data)
        self.create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт и связанные ингредиенты."""
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        instance.recipe_ingredients.all().delete()
        self.create_recipe_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def create_recipe_ingredients(self, recipe, ingredients_data):
        """Создаёт ингредиенты для рецепта."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        )
