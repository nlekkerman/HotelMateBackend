from django.urls import path
from .views import (
    StockCategoryViewSet,
    StockItemViewSet,
    StockViewSet,
    StockMovementViewSet,       # ← import your new ViewSet
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
]
