from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import F, Sum, Q
from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from rest_framework.views import APIView
from .analytics import get_hotel_analytics, ingredient_usage
from .models import (StockCategory, StockItem, Stock, StockItemType,
                     StockMovement, StockInventory, Ingredient, CocktailRecipe,
                     RecipeIngredient, CocktailConsumption)
from .serializers import (
    StockAnalyticsSerializer,
    StockCategorySerializer,
    StockItemSerializer,
    StockItemTypeSerializer,
    StockSerializer,
    StockMovementSerializer
)
from .cocktail_serializers import (
    IngredientSerializer,
    CocktailRecipeSerializer,
    RecipeIngredientSerializer,
    CocktailConsumptionSerializer
)
# In pagination.py or views.py
from rest_framework.pagination import PageNumberPagination


import logging

logger = logging.getLogger(__name__)

class StockItemPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 10000


class StockCategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for StockCategory (with slug support).
    """
    queryset = StockCategory.objects.all()
    serializer_class = StockCategorySerializer
    filterset_fields = ['hotel', 'name', 'slug']
    search_fields = ['name', 'slug']
    ordering_fields = ['hotel', 'name', 'slug']


class StockItemViewSet(viewsets.ModelViewSet):
    serializer_class = StockItemSerializer
    filterset_fields = ['hotel', 'sku', 'name', 'type']
    search_fields = ['name', 'sku']
    ordering_fields = ['hotel', 'name', 'sku']
    pagination_class = StockItemPagination

    def get_queryset(self):
        queryset = StockItem.objects.all()
        hotel_slug = self.request.query_params.get('hotel_slug')
        if hotel_slug:
            queryset = queryset.filter(hotel__slug=hotel_slug)
        return queryset

    @action(detail=True, methods=['post'])
    def move_to_bar(self, request, pk=None):
        item = self.get_object()
        qty = int(request.data.get('quantity', 0))
        if qty <= 0:
            return Response({"error": "Quantity must be > 0"}, status=status.HTTP_400_BAD_REQUEST)

        if item.quantity < qty:
            return Response({"error": "Not enough stock in storage"}, status=status.HTTP_400_BAD_REQUEST)

        item.quantity -= qty
        item.stock_in_bar += qty
        item.save(update_fields=['quantity', 'stock_in_bar'])

        StockMovement.objects.create(
            hotel=item.hotel,
            stock=None,  # or assign default stock if needed
            item=item,
            staff=request.user,
            direction=StockMovement.MOVE_TO_BAR,
            quantity=qty
        )
        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def register_sale(self, request, pk=None):
        item = self.get_object()
        qty = int(request.data.get('quantity', 0))
        if qty <= 0:
            return Response({"error": "Quantity must be > 0"}, status=status.HTTP_400_BAD_REQUEST)

        if item.stock_in_bar < qty:
            return Response({"error": "Not enough stock in bar"}, status=status.HTTP_400_BAD_REQUEST)

        item.stock_in_bar -= qty
        item.save(update_fields=['stock_in_bar'])

        StockMovement.objects.create(
            hotel=item.hotel,
            stock=None,
            item=item,
            staff=request.user,
            direction=StockMovement.SALE,
            quantity=qty
        )
        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # ✅ Low stock action: only items below alert_quantity
    @action(detail=False, methods=['get'], url_path='low_stock')
    def low_stock(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        if not hotel_slug:
            return Response({"error": "Missing hotel_slug"}, status=400)

        # Filter items where storage quantity is below alert_quantity
        low_items = StockItem.objects.filter(
            hotel__slug=hotel_slug,
            quantity__lt=F('alert_quantity')  # only items with less than alert threshold
        )

        serializer = self.get_serializer(low_items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def register_waste(self, request, pk=None):
        item = self.get_object()
        qty = int(request.data.get('quantity', 0))
        if qty <= 0:
            return Response({"error": "Quantity must be > 0"}, status=status.HTTP_400_BAD_REQUEST)

        if item.stock_in_bar < qty:
            return Response({"error": "Not enough stock in bar"}, status=status.HTTP_400_BAD_REQUEST)

        item.stock_in_bar -= qty
        item.save(update_fields=['stock_in_bar'])

        StockMovement.objects.create(
            hotel=item.hotel,
            stock=None,
            item=item,
            staff=request.user,
            direction=StockMovement.WASTE,
            quantity=qty
        )
        serializer = self.get_serializer(item)
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

        hotel_slug = self.kwargs.get('hotel_slug')
        stock_id = request.query_params.get('stock')
        direction = request.query_params.get('direction')  # 'in' or 'move_to_bar'
        date_str = request.query_params.get('date')
        staff_username = request.query_params.get('staff')
        item_name = request.query_params.get('item_name')

        if hotel_slug:
            queryset = queryset.filter(hotel__slug=hotel_slug)

        if stock_id:
            queryset = queryset.filter(item__stocks__id=stock_id)

        if direction in [StockMovement.IN, StockMovement.MOVE_TO_BAR, StockMovement.SALE, StockMovement.WASTE]:
            queryset = queryset.filter(direction=direction)

        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_dt = make_aware(datetime.combine(date_obj, datetime.min.time()))
            end_dt = start_dt + timedelta(days=1)
            queryset = queryset.filter(timestamp__gte=start_dt, timestamp__lt=end_dt)

        if staff_username:
            queryset = queryset.filter(staff__username=staff_username)

        if item_name:
            queryset = queryset.filter(item__name__icontains=item_name)

        return queryset

    @action(detail=False, methods=['post'], url_path=r'bulk/')
    def bulk_stock_action(self, request, hotel_slug):
        """
        Bulk create StockMovements (only IN / MOVE_TO_BAR)
        """
        transactions = request.data.get('transactions', [])
        created_movements = []
        low_stock_items = []

        for t in transactions:
            item = get_object_or_404(StockItem, pk=t['id'], hotel__slug=hotel_slug)
            qty = Decimal(t['qty'])
            direction = t['direction']

            # Only allow IN or MOVE_TO_BAR for storage operations
            if direction == StockMovement.IN:
                item.quantity += qty
            elif direction == StockMovement.MOVE_TO_BAR:
                if item.quantity < qty:
                    return Response(
                        {"error": f"Not enough stock in storage for {item.name}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                item.quantity -= qty
                item.stock_in_bar += qty
            else:
                return Response({"error": f"Invalid direction: {direction}"}, status=status.HTTP_400_BAD_REQUEST)

            item.save(update_fields=['quantity', 'stock_in_bar'])

            if item.total_available < item.alert_quantity:
                low_stock_items.append(item)

            movement = StockMovement.objects.create(
                hotel=item.hotel,
                item=item,
                staff=request.user,
                direction=direction,
                quantity=qty
            )
            created_movements.append(movement)

        return Response({
            "movements": StockMovementSerializer(created_movements, many=True).data,
            "low_stock_alerts": StockItemSerializer(low_stock_items, many=True).data
        }, status=status.HTTP_201_CREATED)

# --- Ingredient ---
class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    search_fields = ['name']
    ordering_fields = ['name']


# --- CocktailRecipe ---
class CocktailRecipeViewSet(viewsets.ModelViewSet):
    queryset = CocktailRecipe.objects.prefetch_related('ingredients__ingredient').all()
    serializer_class = CocktailRecipeSerializer
    search_fields = ['name']
    ordering_fields = ['name']


# --- CocktailConsumption ---
class CocktailConsumptionViewSet(viewsets.ModelViewSet):
    queryset = CocktailConsumption.objects.select_related('cocktail').all()
    serializer_class = CocktailConsumptionSerializer
    ordering = ['-timestamp']

    def get_queryset(self):
        qs = super().get_queryset()
        cocktail_id = self.request.query_params.get('cocktail_id')
        if cocktail_id:
            qs = qs.filter(cocktail_id=cocktail_id)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request  # Pass request for serializer to access user
        return context


class IngredientUsageView(APIView):
    """
    API endpoint to get ingredient usage for a hotel.
    Query params:
        - hotel_id (int, optional)
    """

    def get(self, request):
        hotel_id = request.query_params.get('hotel_id')

        try:
            data = ingredient_usage(hotel_id=hotel_id)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)


class StockAnalyticsView(APIView):
    """
    Returns STORAGE stock analytics per item for a hotel in a given period.
    Opening stock = stock at the start date (storage only).
    """

    def get(self, request, hotel_slug):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        changed_only = str(request.query_params.get("changed_only")).lower() == "true"

        if not start_date or not end_date:
            return Response({"error": "start_date and end_date are required"}, status=400)

        start_dt = make_aware(datetime.strptime(start_date, "%Y-%m-%d"))
        end_dt = make_aware(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

        items = StockItem.objects.filter(hotel__slug=hotel_slug)
        analytics = []

        for item in items:
            # Opening stock: all IN before start - all moved_to_bar before start
            opening_in = item.movements.filter(
                direction=item.movements.model.IN,
                timestamp__lt=start_dt
            ).aggregate(Sum("quantity"))["quantity__sum"] or 0

            opening_moved_to_bar = item.movements.filter(
                direction=item.movements.model.MOVE_TO_BAR,
                timestamp__lt=start_dt
            ).aggregate(Sum("quantity"))["quantity__sum"] or 0

            opening_stock = opening_in - opening_moved_to_bar

            # Movements during the period
            added = item.movements.filter(
                direction=item.movements.model.IN,
                timestamp__gte=start_dt,
                timestamp__lt=end_dt
            ).aggregate(Sum("quantity"))["quantity__sum"] or 0

            moved_to_bar = item.movements.filter(
                direction=item.movements.model.MOVE_TO_BAR,
                timestamp__gte=start_dt,
                timestamp__lt=end_dt
            ).aggregate(Sum("quantity"))["quantity__sum"] or 0

            # Closing = opening + added - moved_to_bar
            closing_stock = opening_stock + added - moved_to_bar

            if changed_only and added == 0 and moved_to_bar == 0:
                continue  # skip unchanged

            analytics.append({
                "item_id": item.id,
                "item_name": item.name,
                "opening_stock": opening_stock,
                "added": added,
                "moved_to_bar": moved_to_bar,
                "closing_stock": closing_stock,
            })

        return Response(analytics)

class StockItemTypeViewSet(viewsets.ModelViewSet):
    """
    CRUD for StockItemType.
    """
    queryset = StockItemType.objects.all()
    serializer_class = StockItemTypeSerializer
    filterset_fields = ["name", "slug"]
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "slug"]
    pagination_class = None

