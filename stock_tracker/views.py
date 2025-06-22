from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import StockCategory, StockItem, Stock, StockMovement, StockInventory
from .serializers import (
    StockCategorySerializer,
    StockItemSerializer,
    StockSerializer,
    StockMovementSerializer
)

class StockCategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for StockCategory (with slug support).
    """
    queryset         = StockCategory.objects.all()
    serializer_class = StockCategorySerializer
    filterset_fields = ['hotel', 'name', 'slug']
    search_fields    = ['name', 'slug']
    ordering_fields  = ['hotel', 'name', 'slug']


class StockItemViewSet(viewsets.ModelViewSet):
    """
    CRUD for StockItem.
    """
    queryset         = StockItem.objects.all()
    serializer_class = StockItemSerializer
    filterset_fields = ['hotel', 'sku', 'name']
    search_fields    = ['name', 'sku']
    ordering_fields  = ['hotel', 'name', 'sku']


class StockViewSet(viewsets.ModelViewSet):
    """
    CRUD for Stock, with nested inventory_lines to set per-item quantities.
    """
    queryset         = Stock.objects.all().prefetch_related('inventory_lines__item')
    serializer_class = StockSerializer
    filterset_fields = ['hotel', 'category']
    search_fields    = ['category__name']
    ordering_fields  = ['hotel', 'category']

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """
        Custom endpoint to list items + quantities for this stock:
        GET /api/stocks/{pk}/inventory/
        """
        stock = self.get_object()
        data = [
            {
                'item_id': line.item.id,
                'item_name': line.item.name,
                'quantity': line.quantity
            }
            for line in stock.inventory_lines.all()
        ]
        return Response(data)


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer

    @action(detail=False, methods=['post'], url_path=r'bulk/')
    def bulk_stock_action(self, request, hotel_slug):
        transactions = request.data.get('transactions', [])
        movements = []
        low_stock_items = []

        for t in transactions:
            item = get_object_or_404(StockItem, pk=t['id'], hotel__slug=hotel_slug)
            inventory = get_object_or_404(StockInventory, item=item, stock__hotel__slug=hotel_slug)

            qty_change = Decimal(t['qty']) if t['direction'] == 'in' else -Decimal(t['qty'])

            inventory.quantity += qty_change
            inventory.save()

            # Also update total item quantity if needed
            item.quantity += qty_change
            item.save()

            # Check for low stock
            if item.quantity < item.alert_quantity:
                low_stock_items.append(item)

            movement = StockMovement(
                hotel=inventory.stock.hotel,
                stock=inventory.stock,
                item=item,
                staff=request.user,
                direction=t['direction'],
                quantity=Decimal(t['qty'])
            )
            movements.append(movement)

        StockMovement.objects.bulk_create(movements)

        return Response({
            "movements": StockMovementSerializer(movements, many=True).data,
            "low_stock_alerts": StockItemSerializer(low_stock_items, many=True).data
        }, status=status.HTTP_201_CREATED)