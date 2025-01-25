from django.contrib import admin
from .models import (Ingredient, Recipe, Favorite,
                     Subscription, ShoppingCart, RecipeIngredient, Profile)

admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(Favorite)
admin.site.register(Subscription)
admin.site.register(ShoppingCart)
admin.site.register(RecipeIngredient)
admin.site.register(Profile)
