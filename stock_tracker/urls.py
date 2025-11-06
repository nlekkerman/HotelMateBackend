from django.urls import path
from .views import (
    IngredientViewSet,
    CocktailRecipeViewSet,
    CocktailConsumptionViewSet,
    IngredientUsageView
)

# Ingredient endpoints
ingredient_list = IngredientViewSet.as_view({'get': 'list', 'post': 'create'})
ingredient_detail = IngredientViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

# CocktailRecipe endpoints
cocktail_list = CocktailRecipeViewSet.as_view({'get': 'list', 'post': 'create'})
cocktail_detail = CocktailRecipeViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

# CocktailConsumption endpoints
consumption_list = CocktailConsumptionViewSet.as_view({'get': 'list', 'post': 'create'})
consumption_detail = CocktailConsumptionViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    # Ingredients
    path('ingredients/', ingredient_list, name='ingredient-list'),
    path('ingredients/<int:pk>/', ingredient_detail, name='ingredient-detail'),

    # Cocktails
    path('cocktails/', cocktail_list, name='cocktail-list'),
    path('cocktails/<int:pk>/', cocktail_detail, name='cocktail-detail'),

    # Cocktail Consumption Logs
    path('consumptions/', consumption_list, name='consumption-list'),
    path('consumptions/<int:pk>/', consumption_detail, name='consumption-detail'),
    
    # Analytics
    path('analytics/ingredient-usage/', IngredientUsageView.as_view(), name='ingredient-usage'),
]
