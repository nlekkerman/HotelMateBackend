from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .analytics import ingredient_usage
from .models import (
    Ingredient,
    CocktailRecipe,
    CocktailConsumption,
    StockCategory,
    StockItem,
    StockMovement,
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
    StockMovementSerializer,
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
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    search_fields = ['name']
    ordering_fields = ['name']


class CocktailRecipeViewSet(viewsets.ModelViewSet):
    queryset = CocktailRecipe.objects.prefetch_related(
        'ingredients__ingredient'
    ).all()
    serializer_class = CocktailRecipeSerializer
    search_fields = ['name']
    ordering_fields = ['name']


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
        context['request'] = self.request
        return context


class IngredientUsageView(APIView):
    def get(self, request):
        hotel_id = request.query_params.get('hotel_id')

        try:
            data = ingredient_usage(hotel_id=hotel_id)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(data, status=status.HTTP_200_OK)


# Stock Management ViewSets

class StockCategoryViewSet(viewsets.ModelViewSet):
    queryset = StockCategory.objects.all()
    serializer_class = StockCategorySerializer
    filterset_fields = ['hotel']


class StockItemViewSet(viewsets.ModelViewSet):
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    filterset_fields = ['hotel', 'category', 'code']
    search_fields = ['code', 'description']


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    filterset_fields = ['hotel', 'item', 'movement_type']
    ordering = ['-timestamp']


class StocktakeViewSet(viewsets.ModelViewSet):
    queryset = Stocktake.objects.all()
    filterset_fields = ['hotel', 'status']
    ordering = ['-period_end']

    def get_serializer_class(self):
        if self.action == 'list':
            return StocktakeListSerializer
        return StocktakeSerializer

    @action(detail=True, methods=['post'])
    def populate(self, request, pk=None):
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
    def approve(self, request, pk=None):
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
            adjustments_created = approve_stocktake(
                stocktake,
                request.user
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
    def category_totals(self, request, pk=None):
        """
        Get totals grouped by category.
        """
        stocktake = self.get_object()
        totals = calculate_category_totals(stocktake)
        return Response(totals)


class StocktakeLineViewSet(viewsets.ModelViewSet):
    queryset = StocktakeLine.objects.all()
    serializer_class = StocktakeLineSerializer
    filterset_fields = ['stocktake', 'item']

    def update(self, request, *args, **kwargs):
        """Override to prevent updates on locked stocktakes"""
        instance = self.get_object()
        if instance.stocktake.is_locked:
            return Response(
                {"error": "Cannot edit approved stocktake"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)
