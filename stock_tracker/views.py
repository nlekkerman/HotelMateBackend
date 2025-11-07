from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q

from hotel.models import Hotel
from .analytics import ingredient_usage
from .models import (
    Ingredient,
    CocktailRecipe,
    CocktailConsumption,
    StockCategory,
    StockItem,
    StockPeriod,
    StockSnapshot,
    StockMovement,
    Location,
    Stocktake,
    StocktakeLine
)
from .cocktail_serializers import (
    IngredientSerializer,
    CocktailRecipeSerializer,
    CocktailConsumptionSerializer
)
from .stock_serializers import (
    StockCategorySerializer,
    StockItemSerializer,
    StockPeriodSerializer,
    StockSnapshotSerializer,
    StockMovementSerializer,
    LocationSerializer,
    StocktakeSerializer,
    StocktakeListSerializer,
    StocktakeLineSerializer
)
from .stocktake_service import (
    populate_stocktake,
    approve_stocktake,
    calculate_category_totals
)


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    pagination_class = None
    search_fields = ['name']
    ordering_fields = ['name']

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        return Ingredient.objects.filter(hotel=hotel)


class CocktailRecipeViewSet(viewsets.ModelViewSet):
    serializer_class = CocktailRecipeSerializer
    pagination_class = None
    search_fields = ['name']
    ordering_fields = ['name']

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        return CocktailRecipe.objects.filter(hotel=hotel).prefetch_related(
            'ingredients__ingredient'
        )


class CocktailConsumptionViewSet(viewsets.ModelViewSet):
    serializer_class = CocktailConsumptionSerializer
    pagination_class = None
    ordering = ['-timestamp']

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        qs = CocktailConsumption.objects.filter(
            hotel=hotel
        ).select_related('cocktail')
        
        cocktail_id = self.request.query_params.get('cocktail_id')
        if cocktail_id:
            qs = qs.filter(cocktail_id=cocktail_id)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class IngredientUsageView(APIView):
    def get(self, request, hotel_identifier):
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )

        try:
            data = ingredient_usage(hotel_id=hotel.id)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(data, status=status.HTTP_200_OK)


# Stock Management ViewSets

class StockCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for stock categories (D, B, S, W, M)"""
    serializer_class = StockCategorySerializer
    pagination_class = None

    def get_queryset(self):
        return StockCategory.objects.all()
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None, hotel_identifier=None):
        """Get all items in this category"""
        category = self.get_object()
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        items = StockItem.objects.filter(
            hotel=hotel,
            category=category
        )
        serializer = StockItemSerializer(items, many=True)
        return Response(serializer.data)


class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet for stock locations (Bar, Cellar, Storage)"""
    serializer_class = LocationSerializer
    pagination_class = None

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        return Location.objects.filter(hotel=hotel)
    
    def perform_create(self, serializer):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        serializer.save(hotel=hotel)


class StockPeriodViewSet(viewsets.ModelViewSet):
    """ViewSet for stock periods (Weekly, Monthly, Quarterly, Yearly)"""
    serializer_class = StockPeriodSerializer
    pagination_class = None
    ordering = ['-start_date']

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        return StockPeriod.objects.filter(hotel=hotel)
    
    def perform_create(self, serializer):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        serializer.save(hotel=hotel)
    
    @action(detail=True, methods=['get'])
    def snapshots(self, request, pk=None, hotel_identifier=None):
        """Get all stock snapshots for this period"""
        period = self.get_object()
        snapshots = StockSnapshot.objects.filter(
            hotel=period.hotel,
            period=period
        ).select_related('item', 'item__category')
        
        # Filter by category if provided
        category_code = request.query_params.get('category')
        if category_code:
            snapshots = snapshots.filter(item__category__code=category_code)
        
        serializer = StockSnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def compare(self, request, hotel_identifier=None):
        """Compare two periods"""
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        period1_id = request.query_params.get('period1')
        period2_id = request.query_params.get('period2')
        
        if not period1_id or not period2_id:
            return Response(
                {"error": "Both period1 and period2 are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            period1 = StockPeriod.objects.get(id=period1_id, hotel=hotel)
            period2 = StockPeriod.objects.get(id=period2_id, hotel=hotel)
        except StockPeriod.DoesNotExist:
            return Response(
                {"error": "One or both periods not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get snapshots for both periods
        snapshots1 = {
            s.item_id: s for s in 
            StockSnapshot.objects.filter(hotel=hotel, period=period1)
        }
        snapshots2 = {
            s.item_id: s for s in 
            StockSnapshot.objects.filter(hotel=hotel, period=period2)
        }
        
        # Build comparison
        comparison = []
        all_item_ids = set(snapshots1.keys()) | set(snapshots2.keys())
        
        for item_id in all_item_ids:
            s1 = snapshots1.get(item_id)
            s2 = snapshots2.get(item_id)
            
            if s1 and s2:
                comparison.append({
                    'item_id': item_id,
                    'sku': s1.item.sku,
                    'name': s1.item.name,
                    'category': s1.item.category.code,
                    'period1': {
                        'period_name': period1.period_name,
                        'closing_stock': float(s1.closing_stock_value),
                        'units': float(s1.total_units)
                    },
                    'period2': {
                        'period_name': period2.period_name,
                        'closing_stock': float(s2.closing_stock_value),
                        'units': float(s2.total_units)
                    },
                    'change': {
                        'value': float(s2.closing_stock_value - s1.closing_stock_value),
                        'units': float(s2.total_units - s1.total_units),
                        'percentage': float(
                            ((s2.closing_stock_value - s1.closing_stock_value) / 
                             s1.closing_stock_value * 100) 
                            if s1.closing_stock_value > 0 else 0
                        )
                    }
                })
        
        return Response({
            'period1': StockPeriodSerializer(period1).data,
            'period2': StockPeriodSerializer(period2).data,
            'comparison': comparison
        })


class StockSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for stock snapshots (read-only)"""
    serializer_class = StockSnapshotSerializer
    pagination_class = None
    filterset_fields = ['item', 'period']

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        return StockSnapshot.objects.filter(
            hotel=hotel
        ).select_related('item', 'period', 'item__category')


class StockItemViewSet(viewsets.ModelViewSet):
    """ViewSet for stock items with profitability analysis"""
    serializer_class = StockItemSerializer
    pagination_class = None
    filterset_fields = ['category']
    search_fields = ['sku', 'name']

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        return StockItem.objects.filter(
            hotel=hotel
        ).select_related('category')
    
    def perform_create(self, serializer):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        serializer.save(hotel=hotel)
    
    @action(detail=False, methods=['get'])
    def profitability(self, request, hotel_identifier=None):
        """Get profitability analysis for all items"""
        items = self.get_queryset()
        
        # Filter by category if provided
        category_code = request.query_params.get('category')
        if category_code:
            items = items.filter(category__code=category_code)
        
        # Calculate profitability metrics
        analysis = []
        for item in items:
            if item.menu_price and item.menu_price > 0:
                analysis.append({
                    'id': item.id,
                    'sku': item.sku,
                    'name': item.name,
                    'category': item.category.code,
                    'unit_cost': float(item.unit_cost),
                    'menu_price': float(item.menu_price),
                    'cost_per_serving': float(item.cost_per_serving),
                    'gross_profit': float(item.gross_profit_per_serving),
                    'gp_percentage': float(item.gp_percentage),
                    'markup_percentage': float(item.markup_percentage),
                    'pour_cost_percentage': float(item.pour_cost_percentage),
                    'current_stock_value': float(item.total_stock_value)
                })
        
        # Sort by GP% descending
        analysis.sort(key=lambda x: x['gp_percentage'], reverse=True)
        
        return Response(analysis)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request, hotel_identifier=None):
        """Get items with low stock levels"""
        items = self.get_queryset().filter(
            current_full_units__lte=2
        )
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None, hotel_identifier=None):
        """Get stock history for this item across all periods"""
        item = self.get_object()
        snapshots = StockSnapshot.objects.filter(
            item=item
        ).select_related('period').order_by('-period__start_date')
        
        serializer = StockSnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)


class StockMovementViewSet(viewsets.ModelViewSet):
    serializer_class = StockMovementSerializer
    pagination_class = None
    filterset_fields = ['item', 'movement_type']
    ordering = ['-timestamp']

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        return StockMovement.objects.filter(hotel=hotel)

    def perform_create(self, serializer):
        """
        Auto-set hotel from URL parameter and staff from request.user.
        This prevents the client needing to provide the hotel field and
        avoids invalid staff PK errors when client omits staff (we set it).
        """
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )

        staff = None
        if hasattr(self.request, 'user') and \
           self.request.user.is_authenticated:
            # Get the Staff instance from the authenticated user
            if hasattr(self.request.user, 'staff_profile'):
                staff = self.request.user.staff_profile

        # Save with hotel and staff (staff may be None)
        serializer.save(hotel=hotel, staff=staff)


class StocktakeViewSet(viewsets.ModelViewSet):
    pagination_class = None
    filterset_fields = ['status']
    ordering = ['-period_end']

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        return Stocktake.objects.filter(hotel=hotel)

    def get_serializer_class(self):
        if self.action == 'list':
            return StocktakeListSerializer
        return StocktakeSerializer

    def perform_create(self, serializer):
        """Auto-set hotel from URL parameter"""
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        serializer.save(hotel=hotel)

    @action(detail=True, methods=['post'])
    def populate(self, request, pk=None, hotel_identifier=None):
        """
        Generate stocktake lines with opening balances
        and period movements.
        """
        stocktake = self.get_object()

        if stocktake.is_locked:
            return Response(
                {"error": "Cannot populate approved stocktake"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lines_created = populate_stocktake(stocktake)
            return Response({
                "message": f"Created {lines_created} stocktake lines",
                "lines_created": lines_created
            })
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None, hotel_identifier=None):
        """
        Approve stocktake and create adjustment movements
        for variances.
        """
        stocktake = self.get_object()

        if stocktake.is_locked:
            return Response(
                {"error": "Stocktake already approved"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get Staff instance from authenticated user
            staff = None
            if hasattr(request.user, 'staff_profile'):
                staff = request.user.staff_profile
            
            adjustments_created = approve_stocktake(
                stocktake,
                staff
            )
            return Response({
                "message": "Stocktake approved",
                "adjustments_created": adjustments_created
            })
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def category_totals(self, request, pk=None, hotel_identifier=None):
        """
        Get totals grouped by category.
        """
        stocktake = self.get_object()
        totals = calculate_category_totals(stocktake)
        return Response(totals)


class StocktakeLineViewSet(viewsets.ModelViewSet):
    serializer_class = StocktakeLineSerializer
    pagination_class = None
    filterset_fields = ['stocktake', 'item']

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        return StocktakeLine.objects.filter(stocktake__hotel=hotel)

    def update(self, request, *args, **kwargs):
        """Override to prevent updates on locked stocktakes"""
        instance = self.get_object()
        if instance.stocktake.is_locked:
            return Response(
                {"error": "Cannot edit approved stocktake"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)
