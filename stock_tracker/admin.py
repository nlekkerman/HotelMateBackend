from django.contrib import admin
from .models import (
    Ingredient,
    CocktailRecipe,
    RecipeIngredient,
    CocktailConsumption
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit', 'hotel')
    search_fields = ('name',)
    list_filter = ('hotel',)
    ordering = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)
    fields = ('ingredient', 'quantity_per_cocktail')


@admin.register(CocktailRecipe)
class CocktailRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'hotel')
    search_fields = ('name',)
    list_filter = ('hotel',)
    ordering = ('name',)
    inlines = (RecipeIngredientInline,)


@admin.register(CocktailConsumption)
class CocktailConsumptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cocktail', 'quantity_made', 'timestamp', 'hotel')
    list_filter = ('cocktail', 'timestamp', 'cocktail__hotel')
    search_fields = ('cocktail__name',)
    ordering = ('-timestamp',)
