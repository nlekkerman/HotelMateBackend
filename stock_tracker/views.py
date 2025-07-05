from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import F
from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from .stock_alerts import notify_super_admins_about_stock_movement

from .models import StockCategory, StockItem, Stock, StockMovement, StockInventory
from .serializers import (
    StockCategorySerializer,
    StockItemSerializer,
    StockSerializer,
    StockMovementSerializer
)
# In pagination.py or views.py
from rest_framework.pagination import PageNumberPagination

class StockItemPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 10000
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
  
    serializer_class = StockItemSerializer
    filterset_fields = ['hotel', 'sku', 'name', 'type']
    search_fields    = ['name', 'sku']
    ordering_fields  = ['hotel', 'name', 'sku']
    pagination_class = StockItemPagination
    
    def get_queryset(self):
        queryset = StockItem.objects.all()
        hotel_slug = self.request.query_params.get('hotel_slug')
        if hotel_slug:
            queryset = queryset.filter(hotel__slug=hotel_slug)
        return queryset

    
    @action(detail=False, methods=['get'])
    def low_stock(self, request, hotel_slug=None):
        low_items = StockItem.objects.filter(
            hotel__slug=hotel_slug,
            quantity__lt=F('alert_quantity')
        )
        serializer = self.get_serializer(low_items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None, hotel_slug=None):
        stock_item = self.get_object()
        stock_id = request.data.get('stock_id')
        quantity = request.data.get('quantity')

        if not stock_id:
            return Response({"error": "Missing 'stock_id' in request data."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            stock = Stock.objects.get(pk=stock_id, hotel=stock_item.hotel)
        except Stock.DoesNotExist:
            return Response({"error": "Stock not found or does not belong to this hotel."},
                            status=status.HTTP_404_NOT_FOUND)

        if quantity is None or int(quantity) == 0:
            quantity = stock_item.quantity
        else:
            quantity = int(quantity)

        stock_item.activate_stock_item(stock=stock, quantity=quantity)
        serializer = self.get_serializer(stock_item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None, hotel_slug=None):
        """
        Deactivate this stock item (remove from stock inventory).
        """
        stock_item = self.get_object()
        stock_item.deactivate_stock_item()
        serializer = self.get_serializer(stock_item)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
    pagination_class = StockItemPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.request

        # hotel_slug from URL kwargs (not query params)
        hotel_slug = self.kwargs.get('hotel_slug')
        stock_id = request.query_params.get('stock')
        direction = request.query_params.get('direction')  # 'in' or 'out'
        date_str = request.query_params.get('date')
        staff_username = request.query_params.get('staff')
        item_name = request.query_params.get('item_name')

        if hotel_slug:
            queryset = queryset.filter(hotel__slug=hotel_slug)

        if stock_id:
            queryset = queryset.filter(stock__id=stock_id)

        if direction in ['in', 'out']:
            queryset = queryset.filter(direction=direction)

        if date_str:
            # Parse date (date only, no time)
            date_obj = parse_date(date_str)
            if not date_obj:
                raise ValidationError({"date": "Invalid date format. Use YYYY-MM-DD."})

            # Convert to datetime range: from start of the day to end of the day
            start_dt = make_aware(datetime.combine(date_obj, datetime.min.time()))
            end_dt = start_dt + timedelta(days=1)

            queryset = queryset.filter(timestamp__gte=start_dt, timestamp__lt=end_dt)
     
        
        if staff_username:
            queryset = queryset.filter(staff__username=staff_username)
            
        if item_name:  # 🔸 NEW
            queryset = queryset.filter(item__name__icontains=item_name)

        return queryset
    
    @action(detail=False, methods=['post'], url_path=r'bulk/')
    def bulk_stock_action(self, request, hotel_slug):
        transactions = request.data.get('transactions', [])
        created_movements = []
        low_stock_items = []

        for t in transactions:
            item = get_object_or_404(StockItem, pk=t['id'], hotel__slug=hotel_slug)
            inventory = get_object_or_404(StockInventory, item=item, stock__hotel__slug=hotel_slug)

            qty_change = Decimal(t['qty']) if t['direction'] == 'in' else -Decimal(t['qty'])

            inventory.quantity += qty_change
            inventory.save()

            item.quantity += qty_change
            item.save()

            if item.quantity < item.alert_quantity:
                low_stock_items.append(item)

            # This will trigger the post_save signal
            movement = StockMovement.objects.create(
                hotel=inventory.stock.hotel,
                stock=inventory.stock,
                item=item,
                staff=request.user,
                direction=t['direction'],
                quantity=Decimal(t['qty'])
            )
            created_movements.append(movement)

        return Response({
            "movements": StockMovementSerializer(created_movements, many=True).data,
            "low_stock_alerts": StockItemSerializer(low_stock_items, many=True).data
        }, status=status.HTTP_201_CREATED)

