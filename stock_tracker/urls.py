from django.urls import path
from .views import (
    StockAnalyticsView,
    StockCategoryViewSet,
    StockItemTypeViewSet,
    StockItemViewSet,
    StockViewSet,
    StockMovementViewSet,
    IngredientViewSet,
    CocktailRecipeViewSet,
    CocktailConsumptionViewSet,
    IngredientUsageView
)

# StockCategory endpoints
stock_category_list   = StockCategoryViewSet.as_view({'get': 'list',   'post': 'create'})
stock_category_detail = StockCategoryViewSet.as_view({
    'get':    'retrieve',
    'put':    'update',
    'patch':  'partial_update',
    'delete': 'destroy'
})

# StockItem endpoints
stock_item_list   = StockItemViewSet.as_view({'get': 'list',   'post': 'create'})
stock_item_detail = StockItemViewSet.as_view({
    'get':    'retrieve',
    'put':    'update',
    'patch':  'partial_update',
    'delete': 'destroy'
})

# Stock (storage buckets) endpoints
stock_list   = StockViewSet.as_view({'get': 'list',   'post': 'create'})
stock_detail = StockViewSet.as_view({
    'get':    'retrieve',
    'put':    'update',
    'patch':  'partial_update',
    'delete': 'destroy'
})

# StockMovement endpoints
stock_movement_list   = StockMovementViewSet.as_view({'get': 'list',   'post': 'create'})
stock_movement_detail = StockMovementViewSet.as_view({
    'get':    'retrieve',
    'put':    'update',
    'patch':  'partial_update',
    'delete': 'destroy'
})

# Include the bulk action endpoint
bulk_stock_action = StockMovementViewSet.as_view({'post': 'bulk_stock_action'})

low_stock = StockItemViewSet.as_view({'get': 'low_stock'})


# Ingredient endpoints
ingredient_list   = IngredientViewSet.as_view({'get': 'list', 'post': 'create'})
ingredient_detail = IngredientViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

# CocktailRecipe endpoints
cocktail_list   = CocktailRecipeViewSet.as_view({'get': 'list', 'post': 'create'})
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

# StockItemType endpoints
stock_itemtype_list = StockItemTypeViewSet.as_view({'get': 'list', 'post': 'create'})
stock_itemtype_detail = StockItemTypeViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})
urlpatterns = [
    # StockCategory
    path(
        '<slug:hotel_slug>/stock-categories/',
        stock_category_list,
        name='stockcategory-list'
    ),
    path(
        '<slug:hotel_slug>/stock-categories/<int:pk>/',
        stock_category_detail,
        name='stockcategory-detail'
    ),

    # StockItem
    path(
        '<slug:hotel_slug>/items/',
        stock_item_list,
        name='stockitem-list'
    ),
    path(
        '<slug:hotel_slug>/items/<int:pk>/',
        stock_item_detail,
        name='stockitem-detail'
    ),

    # Stock
    path(
        '<slug:hotel_slug>/stocks/',
        stock_list,
        name='stock-list'
    ),
    path(
        '<slug:hotel_slug>/stocks/<int:pk>/',
        stock_detail,
        name='stock-detail'
    ),

    # StockMovement
    path(
        '<slug:hotel_slug>/movements/',
        stock_movement_list,
        name='stockmovement-list'
    ),
    path(
        '<slug:hotel_slug>/movements/<int:pk>/',
        stock_movement_detail,
        name='stockmovement-detail'
    ),
    
    # Add Bulk Stock Action Endpoint
    path(
        '<slug:hotel_slug>/movements/bulk/',
        bulk_stock_action,
        name='bulk-stock-action'
    ),
    
    path('<slug:hotel_slug>/items/low_stock/', low_stock, name='stockitem-low-stock'),
    
    path(
        '<slug:hotel_slug>/items/<int:pk>/deactivate/',
        StockItemViewSet.as_view({'post': 'deactivate'}),
        name='stockitem-deactivate'
    ),
    path(
        '<slug:hotel_slug>/items/<int:pk>/activate/',
        StockItemViewSet.as_view({'post': 'activate'}),
        name='stockitem-activate'
    ),
    
    path('ingredients/', ingredient_list, name='ingredient-list'),
    path('ingredients/<int:pk>/', ingredient_detail, name='ingredient-detail'),

    # Cocktails
    path('cocktails/', cocktail_list, name='cocktail-list'),
    path('cocktails/<int:pk>/', cocktail_detail, name='cocktail-detail'),

    # Cocktail Consumption Logs
    path('consumptions/', consumption_list, name='consumption-list'),
    path('consumptions/<int:pk>/', consumption_detail, name='consumption-detail'),
    
    path('analytics/ingredient-usage/', IngredientUsageView.as_view(), name='ingredient-usage'),

    path(
        '<slug:hotel_slug>/analytics/stock/',
        StockAnalyticsView.as_view(),
        name='stock-analytics'
    ),

    # StockItemType
    path(
        '<slug:hotel_slug>/item-types/',
        stock_itemtype_list,
        name='stockitemtype-list'
    ),
    path(
        '<slug:hotel_slug>/item-types/<int:pk>/',
        stock_itemtype_detail,
        name='stockitemtype-detail'
    ),

]
