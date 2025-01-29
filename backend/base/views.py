from django.shortcuts import redirect
from .models import Recipe
from django.http import HttpResponse


def short_link(request, pk):
    """Генерация короткой ссылки для рецепта и редирект на неё"""
    try:
        recipe = Recipe.objects.get(pk=pk)
    except Recipe.DoesNotExist:
        return HttpResponse({'error': 'Recipe not found'}, status=404)

    short_url = f"http://localhost:3000/recipes/{recipe.pk}"
    return redirect(short_url)
