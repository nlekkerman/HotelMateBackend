from django.urls import path
from .views import (
    IngredientViewSet,
    CocktailRecipeViewSet,
    CocktailConsumptionViewSet,
    IngredientUsageView,
    StockCategoryViewSet,
    StockItemViewSet,
    StockMovementViewSet,
    StocktakeViewSet,
    StocktakeLineViewSet
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

# Stock Management endpoints
stock_category_list = StockCategoryViewSet.as_view({
    'get': 'list', 'post': 'create'
})
stock_category_detail = StockCategoryViewSet.as_view({
    'get': 'retrieve', 'put': 'update',
    'patch': 'partial_update', 'delete': 'destroy'
})

stock_item_list = StockItemViewSet.as_view({
    'get': 'list', 'post': 'create'
})
stock_item_detail = StockItemViewSet.as_view({
    'get': 'retrieve', 'put': 'update',
    'patch': 'partial_update', 'delete': 'destroy'
})

stock_movement_list = StockMovementViewSet.as_view({
    'get': 'list', 'post': 'create'
})
stock_movement_detail = StockMovementViewSet.as_view({
    'get': 'retrieve', 'put': 'update',
    'patch': 'partial_update', 'delete': 'destroy'
})

stocktake_list = StocktakeViewSet.as_view({
    'get': 'list', 'post': 'create'
})
stocktake_detail = StocktakeViewSet.as_view({
    'get': 'retrieve', 'put': 'update',
    'patch': 'partial_update', 'delete': 'destroy'
})
stocktake_populate = StocktakeViewSet.as_view({'post': 'populate'})
stocktake_approve = StocktakeViewSet.as_view({'post': 'approve'})
stocktake_category_totals = StocktakeViewSet.as_view({
    'get': 'category_totals'
})

stocktake_line_list = StocktakeLineViewSet.as_view({
    'get': 'list'
})
stocktake_line_detail = StocktakeLineViewSet.as_view({
    'get': 'retrieve', 'put': 'update',
    'patch': 'partial_update', 'delete': 'destroy'
})

urlpatterns = [
    # Ingredients
    path(
        '<str:hotel_identifier>/ingredients/',
        ingredient_list,
        name='ingredient-list'
    ),
    path(
        '<str:hotel_identifier>/ingredients/<int:pk>/',
        ingredient_detail,
        name='ingredient-detail'
    ),

    # Cocktails
    path(
        '<str:hotel_identifier>/cocktails/',
        cocktail_list,
        name='cocktail-list'
    ),
    path(
        '<str:hotel_identifier>/cocktails/<int:pk>/',
        cocktail_detail,
        name='cocktail-detail'
    ),

    # Cocktail Consumption Logs
    path(
        '<str:hotel_identifier>/consumptions/',
        consumption_list,
        name='consumption-list'
    ),
    path(
        '<str:hotel_identifier>/consumptions/<int:pk>/',
        consumption_detail,
        name='consumption-detail'
    ),

    # Analytics
    path(
        '<str:hotel_identifier>/analytics/ingredient-usage/',
        IngredientUsageView.as_view(),
        name='ingredient-usage'
    ),

    # Stock Categories
    path(
        '<str:hotel_identifier>/categories/',
        stock_category_list,
        name='category-list'
    ),
    path(
        '<str:hotel_identifier>/categories/<int:pk>/',
        stock_category_detail,
        name='category-detail'
    ),

    # Stock Items
    path(
        '<str:hotel_identifier>/items/',
        stock_item_list,
        name='stock-item-list'
    ),
    path(
        '<str:hotel_identifier>/items/<int:pk>/',
        stock_item_detail,
        name='stock-item-detail'
    ),

    # Stock Movements
    path(
        '<str:hotel_identifier>/movements/',
        stock_movement_list,
        name='movement-list'
    ),
    path(
        '<str:hotel_identifier>/movements/<int:pk>/',
        stock_movement_detail,
        name='movement-detail'
    ),

    # Stocktakes
    path(
        '<str:hotel_identifier>/stocktakes/',
        stocktake_list,
        name='stocktake-list'
    ),
    path(
        '<str:hotel_identifier>/stocktakes/<int:pk>/',
        stocktake_detail,
        name='stocktake-detail'
    ),
    path(
        '<str:hotel_identifier>/stocktakes/<int:pk>/populate/',
        stocktake_populate,
        name='stocktake-populate'
    ),
    path(
        '<str:hotel_identifier>/stocktakes/<int:pk>/approve/',
        stocktake_approve,
        name='stocktake-approve'
    ),
    path(
        '<str:hotel_identifier>/stocktakes/<int:pk>/category-totals/',
        stocktake_category_totals,
        name='stocktake-category-totals'
    ),

    # Stocktake Lines
    path(
        '<str:hotel_identifier>/stocktake-lines/',
        stocktake_line_list,
        name='line-list'
    ),
    path(
        '<str:hotel_identifier>/stocktake-lines/<int:pk>/',
        stocktake_line_detail,
        name='line-detail'
    ),
]
