from django.urls import path
from .views import (
    IngredientViewSet,
    CocktailRecipeViewSet,
    CocktailConsumptionViewSet,
    IngredientUsageView,
    StockCategoryViewSet,
    LocationViewSet,
    StockPeriodViewSet,
    StockSnapshotViewSet,
    StockItemViewSet,
    StockMovementViewSet,
    StocktakeViewSet,
    StocktakeLineViewSet
)
from .report_views import (
    StockValueReportView,
    SalesReportView
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
stock_category_items = StockCategoryViewSet.as_view({
    'get': 'items'
})

location_list = LocationViewSet.as_view({
    'get': 'list', 'post': 'create'
})
location_detail = LocationViewSet.as_view({
    'get': 'retrieve', 'put': 'update',
    'patch': 'partial_update', 'delete': 'destroy'
})

period_list = StockPeriodViewSet.as_view({
    'get': 'list', 'post': 'create'
})
period_detail = StockPeriodViewSet.as_view({
    'get': 'retrieve', 'put': 'update',
    'patch': 'partial_update', 'delete': 'destroy'
})
period_snapshots = StockPeriodViewSet.as_view({
    'get': 'snapshots'
})
period_compare = StockPeriodViewSet.as_view({
    'get': 'compare'
})
period_populate_opening_stock = StockPeriodViewSet.as_view({
    'post': 'populate_opening_stock'
})

snapshot_list = StockSnapshotViewSet.as_view({
    'get': 'list', 'post': 'create'
})
snapshot_detail = StockSnapshotViewSet.as_view({
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
stock_item_profitability = StockItemViewSet.as_view({
    'get': 'profitability'
})
stock_item_low_stock = StockItemViewSet.as_view({
    'get': 'low_stock'
})
stock_item_history = StockItemViewSet.as_view({
    'get': 'history'
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
stocktake_line_add_movement = StocktakeLineViewSet.as_view({
    'post': 'add_movement'
})
stocktake_line_movements = StocktakeLineViewSet.as_view({
    'get': 'movements'
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
        '<str:hotel_identifier>/categories/<str:pk>/',
        stock_category_detail,
        name='category-detail'
    ),
    path(
        '<str:hotel_identifier>/categories/<str:pk>/items/',
        stock_category_items,
        name='category-items'
    ),

    # Locations
    path(
        '<str:hotel_identifier>/locations/',
        location_list,
        name='location-list'
    ),
    path(
        '<str:hotel_identifier>/locations/<int:pk>/',
        location_detail,
        name='location-detail'
    ),

    # Stock Periods
    path(
        '<str:hotel_identifier>/periods/',
        period_list,
        name='period-list'
    ),
    path(
        '<str:hotel_identifier>/periods/<int:pk>/',
        period_detail,
        name='period-detail'
    ),
    path(
        '<str:hotel_identifier>/periods/<int:pk>/snapshots/',
        period_snapshots,
        name='period-snapshots'
    ),
    path(
        '<str:hotel_identifier>/periods/<int:pk>/populate-opening-stock/',
        period_populate_opening_stock,
        name='period-populate-opening-stock'
    ),
    path(
        '<str:hotel_identifier>/periods/compare/',
        period_compare,
        name='period-compare'
    ),

    # Stock Snapshots
    path(
        '<str:hotel_identifier>/snapshots/',
        snapshot_list,
        name='snapshot-list'
    ),
    path(
        '<str:hotel_identifier>/snapshots/<int:pk>/',
        snapshot_detail,
        name='snapshot-detail'
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
    path(
        '<str:hotel_identifier>/items/profitability/',
        stock_item_profitability,
        name='item-profitability'
    ),
    path(
        '<str:hotel_identifier>/items/low-stock/',
        stock_item_low_stock,
        name='item-low-stock'
    ),
    path(
        '<str:hotel_identifier>/items/<int:pk>/history/',
        stock_item_history,
        name='item-history'
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
        '<str:hotel_identifier>/stocktakes/<int:pk>/category_totals/',
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
    path(
        '<str:hotel_identifier>/stocktake-lines/<int:pk>/add-movement/',
        stocktake_line_add_movement,
        name='line-add-movement'
    ),
    path(
        '<str:hotel_identifier>/stocktake-lines/<int:pk>/movements/',
        stocktake_line_movements,
        name='line-movements'
    ),

    # Reports
    path(
        '<str:hotel_identifier>/reports/stock-value/',
        StockValueReportView.as_view(),
        name='stock-value-report'
    ),
    path(
        '<str:hotel_identifier>/reports/sales/',
        SalesReportView.as_view(),
        name='sales-report'
    ),
]
