from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
import base64
from base.models import (
    Ingredient, Recipe, RecipeIngredient,
    Favorite, Subscription, ShoppingCart, Profile
)

User = get_user_model()


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""
    class Meta:
        model = Favorite
        fields = '__all__'


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины покупок."""
    class Meta:
        model = ShoppingCart
        fields = '__all__'


class Base64ImageField(serializers.ImageField):
    """Поле для обработки изображений в формате base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'avatar.{ext}')
        return super().to_internal_value(data)


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя."""
    class Meta:
        model = Profile
        fields = ('avatar',)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на автора."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False

    def get_avatar(self, obj):
        """Возвращает URL аватарки пользователя."""
        profile = Profile.objects.filter(user=obj).first()
        if profile and profile.avatar:
            return profile.avatar.url
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def validate_email(self, value):
        """Проверяет уникальность email."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.'
            )
        return value

    def validate_password(self, value):
        """Проверяет сложность пароля."""
        validate_password(value)
        return value

    def create(self, validated_data):
        """Создаёт пользователя и профиль."""
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user)
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля."""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        """Проверяет сложность нового пароля."""
        validate_password(value)
        return value


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватарки пользователя."""
    avatar = Base64ImageField()

    class Meta:
        model = Profile
        fields = ('avatar',)


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для подписок."""
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_recipes(self, obj):
        """Возвращает рецепты автора с ограничением по количеству."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass

        serializer = RecipeSerializer(recipes, many=True, context=self.context)
        return serializer.data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов автора."""
        return obj.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_internal_value(self, data):
        """Обрабатывает входные данные для ингредиентов."""
        if isinstance(data, dict) and 'ingredient' in data:
            ingredient_id = data['ingredient'].get('id')
            return {
                'ingredient': {'id': ingredient_id},
                'amount': data['amount']
            }
        return data


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients', many=True
    )
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

        ingredient_ids = {ingredient['ingredient']['id'] for ingredient in ingredients}

        existing_ingredients = Ingredient.objects.filter(id__in=ingredient_ids)
        if len(existing_ingredients) != len(ingredient_ids):
            missing_ids = ingredient_ids - set(existing_ingredients.values_list('id', flat=True))
            raise serializers.ValidationError(
                f"Ингредиенты с id {missing_ids} не существуют."
            )

        if len(ingredient_ids) != len(ingredients):
            raise serializers.ValidationError(
                "Дублирование ингредиентов не допускается."
            )

        return data

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину покупок."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.shopping_carts.filter(user=request.user).exists()
        return False

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
                ingredient_id=ingredient['ingredient']['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        )
