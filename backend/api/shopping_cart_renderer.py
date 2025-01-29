from django.utils.timezone import now
from django.db.models import Sum
from base.models import RecipeIngredient


def render_shopping_cart(user):
    """Генерирует текст для списка покупок пользователя."""

    # Получаем ингредиенты и их количество
    ingredients = (
        RecipeIngredient.objects
        .filter(recipe__shoppingcart__user=user)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )

    # Получаем перечень рецептов
    recipes = (
        RecipeIngredient.objects
        .filter(recipe__shoppingcart__user=user)
        .values('recipe__name')
        .distinct()
    )

    # Формируем заголовок списка покупок
    shopping_cart_header = (
        f"Список покупок на {now().strftime('%d-%m-%Y %H:%M:%S')}\n"
    )

    # Формируем список ингредиентов
    ingredient_lines = [
        f"{idx + 1}. {item['ingredient__name'].capitalize()} "
        f"({item['ingredient__measurement_unit']}) - {item['total_amount']}"
        for idx, item in enumerate(ingredients)
    ]

    # Формируем список рецептов
    recipe_lines = [f"- {recipe['recipe__name']}" for recipe in recipes]

    # Собираем итоговый текст
    return '\n'.join([
        shopping_cart_header,
        'Продукты:\n',
        *ingredient_lines,
        '\nРецепты, использующие эти продукты:\n',
        *recipe_lines,
    ])
