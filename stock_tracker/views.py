from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .analytics import ingredient_usage, convert_units
from .models import (
    Ingredient,
    CocktailRecipe,
    CocktailConsumption
)
from .cocktail_serializers import (
    IngredientSerializer,
    CocktailRecipeSerializer,
    CocktailConsumptionSerializer
)

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

    @action(detail=False, methods=['post'], url_path=r'bulk')
    def bulk_stock_action(self, request, hotel_slug):
        transactions = request.data.get('transactions', [])
        created_movements = []
        low_stock_items = []

        # ⬇️ Zameni trenutni for-loop sa ovim
        for t in transactions:
            print("Transaction payload received:", t)
            item = get_object_or_404(StockItem, pk=t['id'], hotel__slug=hotel_slug)
            stock_line = StockInventory.objects.filter(item=item, stock__hotel__slug=hotel_slug).first()
            if not stock_line:
                return Response({"error": f"No stock inventory found for {item.name}"},
                                status=status.HTTP_400_BAD_REQUEST)
            qty = Decimal(t['qty'])
            direction = t['direction']

            if direction == StockMovement.IN:
                stock_line.quantity += qty
            elif direction == StockMovement.MOVE_TO_BAR:
                if stock_line.quantity < qty:
                    return Response(
                        {"error": f"Not enough stock in storage for {item.name}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                stock_line.quantity -= qty
                item.stock_in_bar += qty
            else:
                return Response({"error": f"Invalid direction: {direction}"}, status=status.HTTP_400_BAD_REQUEST)

            stock_line.save()
            item.save(update_fields=['stock_in_bar'])

            # Low stock check
            if (stock_line.quantity + item.stock_in_bar) < item.alert_quantity:
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
    Returns stock analytics for a hotel based on a period type:
    - week
    - month
    - half_year
    - year

    Query params:
        - period_type: required, one of the above
        - reference_date: optional, defaults to today, format YYYY-MM-DD
        - changed_only: optional, true/false, defaults to True
    """

    def get(self, request, hotel_slug):
        period_type = request.query_params.get("period_type", "")
        period_type = period_type.strip().lower()  # remove spaces and lowercase

        reference_date_str = request.query_params.get("reference_date")
        changed_only = str(request.query_params.get("changed_only", "true")).lower() == "true"

        if not period_type:
            return Response({"error": "period_type is required"}, status=400)

        period_type = period_type.strip().lower()  # normalize input

        # parse reference date or default to today
        if reference_date_str:
            try:
                reference_date = datetime.strptime(reference_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid reference_date format. Use YYYY-MM-DD."}, status=400)
        else:
            reference_date = date.today()

        # calculate start and end dates from period
        try:
            start_dt, end_dt = get_period_dates(period_type, reference_date)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        # fetch all items for this hotel
        items = StockItem.objects.filter(hotel__slug=hotel_slug)
        analytics = []

        for item in items:
            item_data = get_item_analytics(item, start_dt, end_dt, changed_only)
            if item_data:
                analytics.append(item_data)

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

    
class StockPeriodViewSet(viewsets.ModelViewSet):
    serializer_class = StockPeriodSerializer

    def get_queryset(self):
        hotel_slug = self.kwargs.get("hotel_slug")
        qs = StockPeriod.objects.all().select_related("hotel").prefetch_related("items__item")
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        hotel_slug = self.kwargs.get("hotel_slug")
        hotel = get_object_or_404(Hotel, slug=hotel_slug)

        # --- Determine period ---
        period_type = self.request.data.get("period_type", "week")
        reference_date_str = self.request.data.get("reference_date")
        reference_date = None
        if reference_date_str:
            reference_date = datetime.strptime(reference_date_str, "%Y-%m-%d").date()

        start_dt, end_dt = get_period_dates(period_type, reference_date)

        # --- Check for duplicate period ---
        existing = StockPeriod.objects.filter(hotel=hotel, start_date=start_dt, end_date=end_dt).first()
        if existing:
            raise IntegrityError(
                f"StockPeriod already exists for hotel {hotel.slug} from {start_dt} to {end_dt}"
            )

        # --- Create the StockPeriod instance ---
        period = serializer.save(hotel=hotel, start_date=start_dt, end_date=end_dt)

        # --- Populate items with snapshots ---
        items = StockItem.objects.filter(hotel=hotel)
        for item in items:
            # Snapshot now derives sales from opening + moved - current bar stock
            snapshot = calculate_item_snapshot(item, start_dt, end_dt)
            
            period.items.create(
                item=item,
                opening_storage=snapshot["opening_storage"],
                opening_bar=snapshot["opening_bar"],
                added=snapshot.get("added", 0),
                moved_to_bar=snapshot.get("moved_to_bar", 0),
                sales=snapshot["sales"],  # final bar stock → sales
                waste=snapshot.get("waste", 0),
                closing_storage=snapshot["closing_storage"],
                closing_bar=snapshot["closing_bar"],
                total_closing_stock=snapshot["total_closing_stock"],
            )
