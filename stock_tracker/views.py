from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from decimal import Decimal, InvalidOperation
import logging

from hotel.models import Hotel
from .pusher_utils import (
    broadcast_stocktake_created,
    broadcast_stocktake_status_changed,
    broadcast_stocktake_populated,
    broadcast_line_counted_updated,
    broadcast_line_movement_added,
)

logger = logging.getLogger(__name__)
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
    StocktakeLine,
    Sale
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
    populate_period_opening_stock
)


# ============================================================================
# HELPER FUNCTION: Get Periods by Multiple Methods
# ============================================================================
def get_periods_from_request(request, hotel):
    """
    Universal helper to get periods from request parameters.
    Supports 3 methods: IDs, year/month, or date range.
    
    Returns: (periods_queryset, error_response)
    If error_response is not None, return it to client.
    """
    from datetime import datetime
    
    period_ids_str = request.GET.get('period_ids', '')
    periods_str = request.GET.get('periods', '')  # Alternative param name
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    periods = None
    
    # Option 1: By period IDs
    if period_ids_str or periods_str:
        ids_str = period_ids_str or periods_str
        try:
            period_ids = [int(pid.strip()) for pid in ids_str.split(',')]
            periods = StockPeriod.objects.filter(
                id__in=period_ids,
                hotel=hotel
            ).order_by('end_date')
        except ValueError:
            return None, Response(
                {"error": "Invalid period IDs format"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Option 2: By year and optional month
    elif year:
        try:
            year_int = int(year)
            query = Q(hotel=hotel, year=year_int)
            if month:
                month_int = int(month)
                query &= Q(month=month_int)
            periods = StockPeriod.objects.filter(query).order_by('end_date')
        except ValueError:
            return None, Response(
                {"error": "Invalid year/month format"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Option 3: By date range
    elif start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            periods = StockPeriod.objects.filter(
                hotel=hotel,
                end_date__gte=start,
                start_date__lte=end
            ).order_by('end_date')
        except ValueError:
            return None, Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # No valid params
    else:
        return None, Response(
            {
                "error": "Period selection required",
                "options": [
                    "period_ids=1,2,3 or periods=1,2,3",
                    "year=2024 (optionally with month=10)",
                    "start_date=2024-09-01&end_date=2024-11-30"
                ]
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if periods exist
    if not periods or not periods.exists():
        return None, Response(
            {"error": "No valid periods found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return periods, None


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
    pagination_class = None
    ordering = ['-start_date']

    def get_serializer_class(self):
        """Use detailed serializer for retrieve, simple for list"""
        if self.action == 'retrieve':
            from .stock_serializers import StockPeriodDetailSerializer
            return StockPeriodDetailSerializer
        return StockPeriodSerializer

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
                value_change = float(
                    s2.closing_stock_value - s1.closing_stock_value
                )
                servings_change = float(
                    s2.total_servings - s1.total_servings
                )
                percentage_change = float(
                    ((s2.closing_stock_value - s1.closing_stock_value) /
                     s1.closing_stock_value * 100)
                    if s1.closing_stock_value > 0 else 0
                )
                
                comparison.append({
                    'item_id': item_id,
                    'sku': s1.item.sku,
                    'name': s1.item.name,
                    'category': s1.item.category.code,
                    'period1': {
                        'period_name': period1.period_name,
                        'closing_stock': float(s1.closing_stock_value),
                        'servings': float(s1.total_servings)
                    },
                    'period2': {
                        'period_name': period2.period_name,
                        'closing_stock': float(s2.closing_stock_value),
                        'servings': float(s2.total_servings)
                    },
                    'change': {
                        'value': value_change,
                        'servings': servings_change,
                        'percentage': percentage_change
                    }
                })
        
        return Response({
            'period1': StockPeriodSerializer(period1).data,
            'period2': StockPeriodSerializer(period2).data,
            'comparison': comparison
        })
    
    @action(detail=True, methods=['post'])
    def populate_opening_stock(self, request, pk=None, hotel_identifier=None):
        """
        Populate a new period with opening stock from previous closed period.
        
        Opening stock = Last closed period's closing + movements between.
        Creates snapshots for all items with opening balances.
        """
        period = self.get_object()
        
        try:
            result = populate_period_opening_stock(period)
            
            prev_period_info = None
            if result['previous_period']:
                prev_period_info = {
                    'id': result['previous_period'].id,
                    'period_name': result['previous_period'].period_name,
                    'end_date': result['previous_period'].end_date
                }
            
            return Response({
                'success': True,
                'message': (
                    f"Created {result['snapshots_created']} snapshots "
                    f"with opening stock"
                ),
                'snapshots_created': result['snapshots_created'],
                'total_opening_value': float(result['total_value']),
                'previous_period': prev_period_info,
                'period': {
                    'id': period.id,
                    'period_name': period.period_name,
                    'start_date': period.start_date
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None, hotel_identifier=None):
        """
        Reopen a closed period.
        Only accessible by:
        - Superusers
        - Staff with PeriodReopenPermission for this hotel
        """
        from .models import PeriodReopenPermission
        
        period = self.get_object()
        
        # Check if period is already open
        if not period.is_closed:
            return Response({
                'success': False,
                'error': 'Period is already open'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check permissions
        user = request.user
        can_reopen = False
        
        if user.is_superuser:
            can_reopen = True
        else:
            try:
                staff = user.staff_profile
                can_reopen = PeriodReopenPermission.objects.filter(
                    hotel=period.hotel,
                    staff=staff,
                    is_active=True
                ).exists()
            except AttributeError:
                pass
        
        if not can_reopen:
            return Response({
                'success': False,
                'error': 'You do not have permission to reopen periods'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Combined reopen: Period first, then Stocktake
        # STEP 1: Reopen the period
        from django.utils import timezone
        period.is_closed = False
        period.reopened_at = timezone.now()
        # Track who reopened it
        try:
            period.reopened_by = request.user.staff_profile
        except AttributeError:
            period.reopened_by = None
        # Keep closed_at and closed_by for audit trail
        period.save()
        
        # STEP 2: Change related stocktake from APPROVED to DRAFT
        from .models import Stocktake
        stocktake_updated = False
        try:
            stocktake = Stocktake.objects.get(
                hotel=period.hotel,
                period_start=period.start_date,
                period_end=period.end_date
            )
            if stocktake.status == Stocktake.APPROVED:
                stocktake.status = Stocktake.DRAFT
                stocktake.approved_at = None
                stocktake.approved_by = None
                stocktake.save()
                stocktake_updated = True
                
                # Broadcast stocktake status change
                from .stock_serializers import StocktakeSerializer
                serializer = StocktakeSerializer(stocktake, context={'request': request})
                broadcast_stocktake_status_changed(
                    hotel_identifier,
                    stocktake.id,
                    {
                        "stocktake_id": stocktake.id,
                        "status": "DRAFT",
                        "message": "Stocktake reopened",
                        "stocktake": serializer.data
                    }
                )
        except Stocktake.DoesNotExist:
            pass
        
        message = f'Period "{period.period_name}" has been reopened'
        if stocktake_updated:
            message += ' and stocktake changed to DRAFT'
        
        return Response({
            'success': True,
            'message': message,
            'stocktake_updated': stocktake_updated,
            'period': StockPeriodSerializer(
                period, context={'request': request}
            ).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def reopen_permissions(self, request, hotel_identifier=None):
        """
        List all staff with reopen permissions for this hotel.
        Only accessible by superusers.
        """
        from .models import PeriodReopenPermission
        from .stock_serializers import PeriodReopenPermissionSerializer
        
        if not request.user.is_superuser:
            return Response({
                'error': 'Only superusers can view reopen permissions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        permissions = PeriodReopenPermission.objects.filter(
            hotel=hotel
        ).select_related('staff', 'staff__user', 'granted_by')
        
        serializer = PeriodReopenPermissionSerializer(
            permissions, many=True
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def grant_reopen_permission(self, request, hotel_identifier=None):
        """
        Grant reopen permission to a staff member.
        Accessible by:
        - Superusers (always)
        - Staff with can_grant_to_others=True (managers)
        
        Request body:
        {
            "staff_id": 123,
            "can_grant_to_others": false,  // Optional, only superusers can set to true
            "notes": "Optional notes"
        }
        """
        from .models import PeriodReopenPermission
        from .stock_serializers import PeriodReopenPermissionSerializer
        from staff.models import Staff
        
        # Check if user can grant permissions
        can_grant = False
        is_superuser = request.user.is_superuser
        
        if is_superuser:
            can_grant = True
        else:
            # Check if user has permission with can_grant_to_others
            try:
                staff = request.user.staff_profile
                hotel = get_object_or_404(
                    Hotel,
                    Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
                )
                manager_permission = PeriodReopenPermission.objects.filter(
                    hotel=hotel,
                    staff=staff,
                    is_active=True,
                    can_grant_to_others=True
                ).exists()
                can_grant = manager_permission
            except AttributeError:
                pass
        
        if not can_grant:
            return Response({
                'error': 'You do not have permission to grant reopen access. Only superusers or managers can grant permissions.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        staff_id = request.data.get('staff_id')
        notes = request.data.get('notes', '')
        can_grant_to_others = request.data.get('can_grant_to_others', False)
        
        # Only superusers can set can_grant_to_others to True
        if can_grant_to_others and not is_superuser:
            return Response({
                'error': 'Only superusers can grant manager-level permissions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not staff_id:
            return Response({
                'error': 'staff_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            staff = Staff.objects.get(id=staff_id)
        except Staff.DoesNotExist:
            return Response({
                'error': f'Staff member with ID {staff_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get or create permission
        permission, created = PeriodReopenPermission.objects.get_or_create(
            hotel=hotel,
            staff=staff,
            defaults={
                'granted_by': request.user.staff_profile,
                'is_active': True,
                'can_grant_to_others': can_grant_to_others,
                'notes': notes
            }
        )
        
        if not created:
            # Update existing permission
            if not permission.is_active:
                permission.is_active = True
                message = 'Permission reactivated'
            else:
                message = 'Permission updated'
            
            permission.granted_by = request.user.staff_profile
            permission.notes = notes
            
            # Only superusers can change can_grant_to_others
            if is_superuser:
                permission.can_grant_to_others = can_grant_to_others
            
            permission.save()
        else:
            message = 'Permission granted successfully'
        
        serializer = PeriodReopenPermissionSerializer(permission)
        return Response({
            'success': True,
            'message': message,
            'permission': serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def revoke_reopen_permission(self, request, hotel_identifier=None):
        """
        Revoke reopen permission from a staff member.
        Accessible by:
        - Superusers (always)
        - Staff with can_grant_to_others=True (managers)
        
        Request body:
        {
            "staff_id": 123
        }
        """
        from .models import PeriodReopenPermission
        
        # Check if user can revoke permissions
        can_revoke = False
        is_superuser = request.user.is_superuser
        
        if is_superuser:
            can_revoke = True
        else:
            # Check if user has manager permission
            try:
                staff = request.user.staff_profile
                hotel = get_object_or_404(
                    Hotel,
                    Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
                )
                manager_permission = PeriodReopenPermission.objects.filter(
                    hotel=hotel,
                    staff=staff,
                    is_active=True,
                    can_grant_to_others=True
                ).exists()
                can_revoke = manager_permission
            except AttributeError:
                pass
        
        if not can_revoke:
            return Response({
                'error': 'You do not have permission to revoke reopen access'
            }, status=status.HTTP_403_FORBIDDEN)
        
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        staff_id = request.data.get('staff_id')
        
        if not staff_id:
            return Response({
                'error': 'staff_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            permission = PeriodReopenPermission.objects.get(
                hotel=hotel,
                staff_id=staff_id
            )
            permission.is_active = False
            permission.save()
            
            return Response({
                'success': True,
                'message': 'Permission revoked successfully'
            }, status=status.HTTP_200_OK)
        except PeriodReopenPermission.DoesNotExist:
            return Response({
                'error': 'Permission not found for this staff member'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def approve_and_close(self, request, pk=None, hotel_identifier=None):
        """
        Combined action: Approve stocktake AND close period in one operation.
        
        Order of operations:
        1. First: Approve the stocktake (DRAFT → APPROVED)
        2. Then: Close the period (OPEN → CLOSED)
        
        This ensures the stocktake is finalized before period is locked.
        """
        from django.utils import timezone
        from .models import Stocktake
        
        period = self.get_object()
        
        # Check if period is already closed
        if period.is_closed:
            return Response({
                'success': False,
                'error': 'Period is already closed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get staff member
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response({
                'success': False,
                'error': 'User must be associated with a staff profile'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Find the stocktake
        try:
            stocktake = Stocktake.objects.get(
                hotel=period.hotel,
                period_start=period.start_date,
                period_end=period.end_date
            )
        except Stocktake.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No stocktake found for this period'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # STEP 1: Approve the stocktake
        if stocktake.status != Stocktake.APPROVED:
            stocktake.status = Stocktake.APPROVED
            stocktake.approved_at = timezone.now()
            stocktake.approved_by = staff
            stocktake.save()
            
            # Broadcast stocktake status change
            from .stock_serializers import StocktakeSerializer
            serializer = StocktakeSerializer(stocktake, context={'request': request})
            broadcast_stocktake_status_changed(
                hotel_identifier,
                stocktake.id,
                {
                    "stocktake_id": stocktake.id,
                    "status": "APPROVED",
                    "message": "Stocktake approved",
                    "stocktake": serializer.data
                }
            )
        
        # STEP 2: Close the period
        period.is_closed = True
        period.closed_at = timezone.now()
        period.closed_by = staff
        period.save()
        
        return Response({
            'success': True,
            'message': f'Stocktake approved and period "{period.period_name}" closed successfully',
            'period': StockPeriodSerializer(
                period, context={'request': request}
            ).data,
            'stocktake': {
                'id': stocktake.id,
                'status': stocktake.status,
                'approved_at': stocktake.approved_at,
                'approved_by': stocktake.approved_by.user.username if stocktake.approved_by else None
            }
        }, status=status.HTTP_200_OK)


class StockSnapshotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for stock snapshots.
    
    Allows creating and updating snapshots during stocktake entry.
    Staff can POST new counts or PATCH existing snapshots.
    """
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
    
    def perform_create(self, serializer):
        """Set hotel when creating snapshot"""
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        serializer.save(hotel=hotel)


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
        # Return null for unavailable metrics (better than fake zeros)
        def _safe_float(val):
            """Convert to float, or return None if not available."""
            try:
                return float(val) if val is not None else None
            except (TypeError, ValueError):
                return None

        analysis = []
        for item in items:
            # Only consider items with a positive menu price
            if item.menu_price and item.menu_price > 0:
                analysis.append({
                    'id': item.id,
                    'sku': item.sku,
                    'name': item.name,
                    'category': item.category.code if item.category else None,
                    'unit_cost': _safe_float(item.unit_cost),
                    'menu_price': _safe_float(item.menu_price),
                    'cost_per_serving': _safe_float(item.cost_per_serving),
                    'gross_profit': _safe_float(
                        item.gross_profit_per_serving
                    ),
                    'gross_profit_percentage': _safe_float(
                        item.gross_profit_percentage
                    ),
                    'markup_percentage': _safe_float(item.markup_percentage),
                    'pour_cost_percentage': _safe_float(
                        item.pour_cost_percentage
                    ),
                    'current_stock_value': _safe_float(item.total_stock_value)
                })
        
        # Sort by GP% descending
        analysis.sort(
            key=lambda x: x['gross_profit_percentage'], reverse=True
        )
        
        return Response(analysis)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request, hotel_identifier=None):
        """
        Get items with low stock levels based on total servings.
        Uses total_stock_in_servings property which accounts for both
        full units and partial units.
        
        Query params:
        - threshold: minimum servings (default: 50)
        """
        threshold = int(request.query_params.get('threshold', 50))
        
        # Get all items and filter by total servings
        all_items = self.get_queryset()
        low_stock_items = [
            item for item in all_items
            if item.total_stock_in_servings < threshold
        ]
        
        serializer = self.get_serializer(low_stock_items, many=True)
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
        """Auto-set hotel from URL parameter and broadcast creation"""
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        instance = serializer.save(hotel=hotel)
        
        # Broadcast stocktake creation to all users viewing stocktakes list
        try:
            broadcast_stocktake_created(
                hotel_identifier,
                serializer.data
            )
            logger.info(
                f"Broadcasted stocktake creation: {instance.id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to broadcast stocktake creation: {e}"
            )

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
            
            # Broadcast populate event to all viewing this stocktake
            try:
                broadcast_stocktake_populated(
                    hotel_identifier,
                    stocktake.id,
                    {
                        "stocktake_id": stocktake.id,
                        "lines_created": lines_created,
                        "message": f"Created {lines_created} stocktake lines"
                    }
                )
                logger.info(
                    f"Broadcasted stocktake populate: {stocktake.id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to broadcast stocktake populate: {e}"
                )
            
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
            
            # Broadcast status change to both list and detail views
            try:
                serializer = self.get_serializer(stocktake)
                broadcast_stocktake_status_changed(
                    hotel_identifier,
                    stocktake.id,
                    {
                        "stocktake_id": stocktake.id,
                        "status": "APPROVED",
                        "adjustments_created": adjustments_created,
                        "stocktake": serializer.data
                    }
                )
                logger.info(
                    f"Broadcasted stocktake approval: {stocktake.id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to broadcast stocktake approval: {e}"
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
    
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None, hotel_identifier=None):
        """
        Reopen an approved stocktake (change from APPROVED to DRAFT).
        Only accessible by:
        - Superusers
        - Staff with PeriodReopenPermission for this hotel
        """
        from .models import PeriodReopenPermission
        
        stocktake = self.get_object()
        
        # Check if stocktake is already in DRAFT
        if stocktake.status == Stocktake.DRAFT:
            return Response({
                'success': False,
                'error': 'Stocktake is already in DRAFT status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check permissions (same as period reopen)
        user = request.user
        can_reopen = False
        
        if user.is_superuser:
            can_reopen = True
        else:
            try:
                staff = user.staff_profile
                can_reopen = PeriodReopenPermission.objects.filter(
                    hotel=stocktake.hotel,
                    staff=staff,
                    is_active=True
                ).exists()
            except AttributeError:
                pass
        
        if not can_reopen:
            return Response({
                'success': False,
                'error': 'You do not have permission to reopen stocktakes'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Reopen the stocktake
        stocktake.status = Stocktake.DRAFT
        stocktake.approved_at = None
        stocktake.approved_by = None
        stocktake.save()
        
        # Broadcast status change
        try:
            serializer = self.get_serializer(stocktake)
            broadcast_stocktake_status_changed(
                hotel_identifier,
                stocktake.id,
                {
                    "stocktake_id": stocktake.id,
                    "status": "DRAFT",
                    "message": "Stocktake reopened",
                    "stocktake": serializer.data
                }
            )
            logger.info(f"Broadcasted stocktake reopen: {stocktake.id}")
        except Exception as e:
            logger.error(f"Failed to broadcast stocktake reopen: {e}")
        
        return Response({
            'success': True,
            'message': f'Stocktake for {stocktake.period_start} to {stocktake.period_end} has been reopened',
            'stocktake': StocktakeSerializer(
                stocktake, context={'request': request}
            ).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def category_totals(self, request, pk=None, hotel_identifier=None):
        """
        Get expected_qty totals grouped by category.
        
        Returns category-level calculations including:
        - opening_qty, purchases, sales, waste, transfers, adjustments
        - expected_qty (calculated using the formula)
        - counted_qty, variance_qty
        - expected_value, counted_value, variance_value
        
        Optional query parameter:
        - category: Filter by category code (D, B, S, W, M)
        
        Examples:
        - GET /api/stock_tracker/1/stocktakes/4/category_totals/
        - GET /api/stock_tracker/1/stocktakes/4/category_totals/?category=D
        """
        stocktake = self.get_object()
        
        # Check for category filter
        category_code = request.query_params.get('category', None)
        if category_code:
            category_code = category_code.upper()
        
        # Use the new model method
        totals = stocktake.get_category_totals(category_code=category_code)
        
        if category_code and not totals:
            return Response(
                {"error": f"No data found for category {category_code}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
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
        """
        Override to prevent updates on locked stocktakes and ensure
        proper recalculation of counted_value and variance_value.

        This method ensures that when counted_full_units or
        counted_partial_units are updated, all calculated properties
        (counted_qty, counted_value, variance_value) are recalculated
        and returned in the response.
        """
        instance = self.get_object()
        hotel_identifier = kwargs.get('hotel_identifier')
        
        if instance.stocktake.is_locked:
            return Response(
                {"error": "Cannot edit approved stocktake"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Perform the update using parent class method
        partial = kwargs.get('partial', False)
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # CRITICAL: Refresh from database to get fresh calculated values
        instance.refresh_from_db()
        
        # Re-serialize with ALL fields including calculated properties
        response_serializer = self.get_serializer(instance)
        
        # Broadcast line update to all viewing this stocktake
        try:
            broadcast_line_counted_updated(
                hotel_identifier,
                instance.stocktake.id,
                {
                    "line_id": instance.id,
                    "item_sku": instance.item.sku,
                    "line": response_serializer.data
                }
            )
            logger.info(
                f"Broadcasted line update: {instance.id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to broadcast line update: {e}"
            )
        
        return Response(response_serializer.data)

    @action(detail=True, methods=['post'])
    def add_movement(self, request, pk=None, hotel_identifier=None):
        """
        Create a StockMovement directly from a stocktake line.
        Only PURCHASE and WASTE movement types are tracked.
        
        POST data expected:
        {
            "movement_type": "PURCHASE|WASTE",
            "quantity": 10.5,
            "unit_cost": 2.50,  // optional
            "reference": "INV-12345",  // optional
            "notes": "Manual entry from stocktake"  // optional
        }
        
        This creates a real StockMovement record that will be reflected
        in the line's totals immediately.
        """
        line = self.get_object()
        
        if line.stocktake.is_locked:
            return Response(
                {"error": "Cannot add movements to approved stocktake"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movement_type = request.data.get('movement_type')
        quantity = request.data.get('quantity')
        
        if not movement_type or quantity is None:
            return Response(
                {"error": "movement_type and quantity are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only allow PURCHASE and WASTE movement types
        valid_types = ['PURCHASE', 'WASTE']
        if movement_type not in valid_types:
            error_msg = (
                f"Invalid movement_type. "
                f"Must be one of: {', '.join(valid_types)}"
            )
            return Response(
                {"error": error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Default reference if not provided
        default_ref = f'Stocktake-{line.stocktake.id}'
        
        # Get staff if available
        staff_user = None
        if hasattr(request.user, 'staff'):
            staff_user = request.user.staff
        
        # Find the matching StockPeriod for this stocktake
        period = StockPeriod.objects.filter(
            hotel=line.stocktake.hotel,
            start_date=line.stocktake.period_start,
            end_date=line.stocktake.period_end
        ).first()
        
        # Create the movement
        movement = StockMovement.objects.create(
            hotel=line.stocktake.hotel,
            item=line.item,
            period=period,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=request.data.get('unit_cost'),
            reference=request.data.get('reference', default_ref),
            notes=request.data.get('notes', ''),
            staff=staff_user
        )
        
        # Recalculate the line by re-populating from movements
        from .stocktake_service import _calculate_period_movements
        
        movements = _calculate_period_movements(
            line.item,
            line.stocktake.period_start,
            line.stocktake.period_end
        )
        
        # Update hotel-wide movement types (purchases and waste)
        line.purchases = movements['purchases']
        line.waste = movements['waste']
        line.save()
        
        # Return updated line data
        serializer = self.get_serializer(line)
        response_data = {
            'message': 'Movement created successfully',
            'movement': {
                'id': movement.id,
                'movement_type': movement.movement_type,
                'quantity': str(movement.quantity),
                'timestamp': movement.timestamp
            },
            'line': serializer.data
        }
        
        # Broadcast movement added to all viewing this stocktake
        try:
            broadcast_line_movement_added(
                hotel_identifier,
                line.stocktake.id,
                {
                    "line_id": line.id,
                    "item_sku": line.item.sku,
                    "movement": response_data['movement'],
                    "line": serializer.data
                }
            )
            logger.info(
                f"Broadcasted movement added: {movement.id} "
                f"to line {line.id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to broadcast movement added: {e}"
            )
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def movements(self, request, pk=None, hotel_identifier=None):
        """
        Get all movements for this line item within the stocktake period.
        
        Returns a list of all StockMovement records that affect this
        line's calculations, allowing the UI to display both auto-calculated
        and manually entered movements together.
        """
        line = self.get_object()
        
        movements = StockMovement.objects.filter(
            item=line.item,
            timestamp__gte=line.stocktake.period_start,
            timestamp__lte=line.stocktake.period_end
        ).order_by('-timestamp')
        
        serializer = StockMovementSerializer(movements, many=True)
        
        # Summary for hotel-wide system (only relevant movement types)
        summary = {
            'total_purchases': line.purchases,
            'total_waste': line.waste,
            'movement_count': movements.count()
        }
        
        return Response({
            'movements': serializer.data,
            'summary': summary
        })

    @action(detail=True, methods=['delete'], url_path='delete-movement/(?P<movement_id>[^/.]+)')
    def delete_movement(self, request, pk=None, movement_id=None, hotel_identifier=None):
        """
        Delete a specific movement and recalculate the line.
        
        Use this to correct mistakes when wrong purchase/waste was entered.
        
        DELETE /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/delete-movement/{movement_id}/
        
        This will:
        1. Delete the StockMovement record
        2. Recalculate purchases/waste from remaining movements
        3. Update the line's expected_qty and variance
        4. Broadcast update via Pusher
        """
        line = self.get_object()
        
        if line.stocktake.is_locked:
            return Response(
                {"error": "Cannot delete movements from approved stocktake"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the movement
        try:
            movement = StockMovement.objects.get(
                id=movement_id,
                item=line.item,
                timestamp__gte=line.stocktake.period_start,
                timestamp__lte=line.stocktake.period_end
            )
        except StockMovement.DoesNotExist:
            return Response(
                {"error": f"Movement {movement_id} not found for this line"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store info before deletion
        deleted_movement_type = movement.movement_type
        deleted_quantity = movement.quantity
        
        # Delete the movement
        movement.delete()
        
        # Recalculate the line
        from .stocktake_service import _calculate_period_movements
        
        movements = _calculate_period_movements(
            line.item,
            line.stocktake.period_start,
            line.stocktake.period_end
        )
        
        # Update line
        line.purchases = movements['purchases']
        line.waste = movements['waste']
        line.save()
        
        # Return updated line data
        serializer = self.get_serializer(line)
        response_data = {
            'message': 'Movement deleted successfully',
            'deleted_movement': {
                'id': movement_id,
                'movement_type': deleted_movement_type,
                'quantity': str(deleted_quantity)
            },
            'line': serializer.data
        }
        
        # Broadcast movement deleted to all viewing this stocktake
        try:
            from .pusher_utils import broadcast_line_movement_deleted
            broadcast_line_movement_deleted(
                hotel_identifier,
                line.stocktake.id,
                {
                    "line_id": line.id,
                    "item_sku": line.item.sku,
                    "deleted_movement_id": movement_id,
                    "line": serializer.data
                }
            )
            logger.info(
                f"Broadcasted movement deletion: {movement_id} "
                f"from line {line.id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to broadcast movement deletion: {e}"
            )
        
        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='update-movement/(?P<movement_id>[^/.]+)')
    def update_movement(self, request, pk=None, movement_id=None, hotel_identifier=None):
        """
        Update an existing movement and recalculate the line.
        
        PATCH /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/update-movement/{movement_id}/
        
        Body:
        {
          "movement_type": "PURCHASE",  // or "WASTE"
          "quantity": 75.0,
          "unit_cost": 2.50,  // optional
          "reference": "Updated ref",  // optional
          "notes": "Corrected quantity"  // optional
        }
        
        This will:
        1. Update the StockMovement record
        2. Recalculate purchases/waste from all movements
        3. Update the line's expected_qty and variance
        4. Broadcast update via Pusher
        """
        line = self.get_object()
        
        if line.stocktake.is_locked:
            return Response(
                {"error": "Cannot edit movements on approved stocktake"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the movement
        try:
            movement = StockMovement.objects.get(
                id=movement_id,
                item=line.item,
                timestamp__gte=line.stocktake.period_start,
                timestamp__lte=line.stocktake.period_end
            )
        except StockMovement.DoesNotExist:
            return Response(
                {"error": f"Movement {movement_id} not found for this line"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store old values for audit
        old_values = {
            'movement_type': movement.movement_type,
            'quantity': str(movement.quantity),
            'unit_cost': str(movement.unit_cost) if movement.unit_cost else None,
            'reference': movement.reference,
            'notes': movement.notes
        }
        
        # Get new values from request
        movement_type = request.data.get('movement_type', movement.movement_type)
        quantity = request.data.get('quantity')
        unit_cost = request.data.get('unit_cost')
        reference = request.data.get('reference', movement.reference)
        notes = request.data.get('notes', movement.notes)
        
        # Validate movement type
        if movement_type not in ['PURCHASE', 'WASTE']:
            return Response(
                {"error": "movement_type must be 'PURCHASE' or 'WASTE'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate and update quantity
        if quantity is not None:
            try:
                quantity = Decimal(str(quantity))
                if quantity <= 0:
                    return Response(
                        {"error": "Quantity must be greater than 0"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                movement.quantity = quantity
            except (ValueError, InvalidOperation):
                return Response(
                    {"error": "Invalid quantity format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate and update unit_cost if provided
        if unit_cost is not None:
            try:
                movement.unit_cost = Decimal(str(unit_cost))
            except (ValueError, InvalidOperation):
                return Response(
                    {"error": "Invalid unit_cost format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update other fields
        movement.movement_type = movement_type
        movement.reference = reference
        movement.notes = notes
        movement.save()
        
        # Recalculate the line from all movements
        from .stocktake_service import _calculate_period_movements
        
        movements = _calculate_period_movements(
            line.item,
            line.stocktake.period_start,
            line.stocktake.period_end
        )
        
        # Update line
        line.purchases = movements['purchases']
        line.waste = movements['waste']
        line.save()
        
        # Return updated data
        serializer = self.get_serializer(line)
        response_data = {
            'message': 'Movement updated successfully',
            'movement': {
                'id': movement.id,
                'movement_type': movement.movement_type,
                'quantity': str(movement.quantity),
                'unit_cost': str(movement.unit_cost) if movement.unit_cost else None,
                'reference': movement.reference,
                'notes': movement.notes,
                'timestamp': movement.timestamp.isoformat()
            },
            'old_values': old_values,
            'line': serializer.data
        }
        
        # Broadcast movement updated to all viewing this stocktake
        try:
            from .pusher_utils import broadcast_line_movement_updated
            broadcast_line_movement_updated(
                hotel_identifier,
                line.stocktake.id,
                {
                    "line_id": line.id,
                    "item_sku": line.item.sku,
                    "movement": response_data['movement'],
                    "old_values": old_values,
                    "line": serializer.data
                }
            )
            logger.info(
                f"Broadcasted movement update: {movement_id} "
                f"for line {line.id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to broadcast movement update: {e}"
            )
        
        return Response(response_data, status=status.HTTP_200_OK)


class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Sales - independent sales tracking.
    Allows CRUD operations on sales records for stocktakes.
    """
    pagination_class = None
    ordering = ['-sale_date', '-created_at']

    def get_serializer_class(self):
        from .stock_serializers import SaleSerializer
        return SaleSerializer

    def get_queryset(self):
        hotel_identifier = self.kwargs.get('hotel_identifier')
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )

        # Base queryset
        queryset = Sale.objects.filter(
            stocktake__hotel=hotel
        ).select_related('stocktake', 'item', 'created_by')

        # Filter by stocktake if provided
        stocktake_id = self.request.query_params.get('stocktake')
        if stocktake_id:
            queryset = queryset.filter(stocktake_id=stocktake_id)

        # Filter by item if provided
        item_id = self.request.query_params.get('item')
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        # Filter by category if provided
        category_code = self.request.query_params.get('category')
        if category_code:
            queryset = queryset.filter(item__category__code=category_code)

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(sale_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(sale_date__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        """Auto-set created_by from request user"""
        staff_user = None
        if hasattr(self.request.user, 'staff'):
            staff_user = self.request.user.staff

        serializer.save(created_by=staff_user)

    @action(detail=False, methods=['get'])
    def summary(self, request, hotel_identifier=None):
        """
        Get sales summary for a stocktake.
        Returns total sales by category.
        """
        from django.db.models import Sum, Count

        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )

        stocktake_id = request.query_params.get('stocktake')
        if not stocktake_id:
            return Response(
                {"error": "stocktake parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get sales grouped by category
        sales_by_category = Sale.objects.filter(
            stocktake_id=stocktake_id,
            stocktake__hotel=hotel
        ).values(
            'item__category__code',
            'item__category__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_cost=Sum('total_cost'),
            total_revenue=Sum('total_revenue'),
            sale_count=Count('id')
        ).order_by('item__category__code')

        # Calculate overall totals
        overall = Sale.objects.filter(
            stocktake_id=stocktake_id,
            stocktake__hotel=hotel
        ).aggregate(
            total_quantity=Sum('quantity'),
            total_cost=Sum('total_cost'),
            total_revenue=Sum('total_revenue'),
            sale_count=Count('id')
        )

        # Calculate overall gross profit
        if overall['total_revenue'] and overall['total_cost']:
            overall['gross_profit'] = (
                overall['total_revenue'] - overall['total_cost']
            )
            overall['gross_profit_percentage'] = (
                (overall['gross_profit'] / overall['total_revenue']) * 100
            )
        else:
            overall['gross_profit'] = None
            overall['gross_profit_percentage'] = None

        return Response({
            'stocktake_id': stocktake_id,
            'by_category': list(sales_by_category),
            'overall': overall
        })

    @action(detail=False, methods=['post'])
    def bulk_create(self, request, hotel_identifier=None):
        """
        Create multiple sales at once.
        Accepts a list of sale objects in request body.
        """
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )

        sales_data = request.data.get('sales', [])
        if not sales_data:
            return Response(
                {"error": "sales array is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get staff if available
        staff_user = None
        if hasattr(request.user, 'staff'):
            staff_user = request.user.staff

        created_sales = []
        errors = []

        for idx, sale_data in enumerate(sales_data):
            serializer = self.get_serializer(data=sale_data)
            if serializer.is_valid():
                sale = serializer.save(created_by=staff_user)
                created_sales.append(sale)
            else:
                errors.append({
                    'index': idx,
                    'errors': serializer.errors
                })

        if errors:
            return Response(
                {
                    "message": "Some sales failed to create",
                    "created_count": len(created_sales),
                    "errors": errors
                },
                status=status.HTTP_207_MULTI_STATUS
            )

        return Response(
            {
                "message": "All sales created successfully",
                "created_count": len(created_sales),
                "sales": self.get_serializer(created_sales, many=True).data
            },
            status=status.HTTP_201_CREATED
        )


class KPISummaryView(APIView):
    """
    Comprehensive KPI metrics endpoint that calculates ALL metrics on the backend.
    Frontend just displays the ready-to-use numbers.
    
    GET /api/stock-tracker/<hotel>/kpi-summary/?period_ids=1,2,3
    """
    
    def get(self, request, hotel_identifier):
        # Get hotel
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        # Use helper function to get periods
        periods, error_response = get_periods_from_request(request, hotel)
        if error_response:
            return error_response
        
        # Calculate all KPIs
        data = {
            "stock_value_metrics": self._calculate_stock_value_metrics(periods),
            "profitability_metrics": self._calculate_profitability_metrics(periods),
            "category_performance": self._calculate_category_performance(periods),
            "inventory_health": self._calculate_inventory_health(periods),
            "period_comparison": self._calculate_period_comparison(periods) if len(periods) >= 2 else None,
            "performance_score": self._calculate_performance_score(periods),
            "additional_metrics": self._calculate_additional_metrics(periods),
        }
        
        return Response({
            "success": True,
            "data": data,
            "meta": {
                "periods_analyzed": len(periods),
                "period_names": [p.period_name for p in periods],
                "date_range": {
                    "from": periods.first().start_date.isoformat(),
                    "to": periods.last().end_date.isoformat()
                }
            }
        })
    
    def _calculate_stock_value_metrics(self, periods):
        """Calculate stock value KPIs"""
        latest_period = periods.last()
        
        # Get snapshots for all periods
        all_snapshots = StockSnapshot.objects.filter(period__in=periods)
        
        # Current/latest period value
        latest_snapshots = all_snapshots.filter(period=latest_period)
        total_current_value = sum(
            snapshot.closing_stock_value for snapshot in latest_snapshots
        )
        
        # Calculate value per period
        period_values = []
        for period in periods:
            period_snapshots = all_snapshots.filter(period=period)
            period_value = sum(s.closing_stock_value for s in period_snapshots)
            period_values.append({
                "period_id": period.id,
                "period_name": period.period_name,
                "value": float(period_value),
                "date": period.end_date.isoformat()
            })
        
        # Calculate average
        avg_value = sum(pv["value"] for pv in period_values) / len(period_values) if period_values else 0
        
        # Highest and lowest
        highest = max(period_values, key=lambda x: x["value"]) if period_values else None
        lowest = min(period_values, key=lambda x: x["value"]) if period_values else None
        
        # Trend calculation
        if len(period_values) >= 2:
            first_value = period_values[0]["value"]
            last_value = period_values[-1]["value"]
            if first_value > 0:
                trend_percentage = ((last_value - first_value) / first_value) * 100
                if trend_percentage > 2:
                    trend_direction = "increasing"
                elif trend_percentage < -2:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                trend_percentage = 0
                trend_direction = "stable"
        else:
            trend_percentage = 0
            trend_direction = "stable"
        
        return {
            "total_current_value": float(total_current_value),
            "average_value": float(avg_value),
            "highest_period": highest,
            "lowest_period": lowest,
            "trend": {
                "direction": trend_direction,
                "percentage": round(trend_percentage, 2)
            },
            "period_values": period_values
        }
    
    def _calculate_profitability_metrics(self, periods):
        """Calculate profitability KPIs"""
        # Get stocktakes for periods
        stocktakes = Stocktake.objects.filter(
            hotel=periods.first().hotel,
            period_start__in=[p.start_date for p in periods],
            period_end__in=[p.end_date for p in periods]
        )
        
        gp_percentages = []
        for period in periods:
            stocktake = stocktakes.filter(
                period_start=period.start_date,
                period_end=period.end_date
            ).first()
            
            if stocktake and stocktake.gross_profit_percentage:
                gp_percentages.append({
                    "period_name": period.period_name,
                    "gp_percentage": float(stocktake.gross_profit_percentage),
                    "pour_cost": float(stocktake.pour_cost_percentage) if stocktake.pour_cost_percentage else None,
                    "date": period.end_date.isoformat()
                })
        
        if gp_percentages:
            avg_gp = sum(gp["gp_percentage"] for gp in gp_percentages) / len(gp_percentages)
            highest_gp = max(gp_percentages, key=lambda x: x["gp_percentage"])
            lowest_gp = min(gp_percentages, key=lambda x: x["gp_percentage"])
            
            # Average pour cost
            pour_costs = [gp["pour_cost"] for gp in gp_percentages if gp["pour_cost"]]
            avg_pour_cost = sum(pour_costs) / len(pour_costs) if pour_costs else None
            
            # Trend
            if len(gp_percentages) >= 2:
                first_gp = gp_percentages[0]["gp_percentage"]
                last_gp = gp_percentages[-1]["gp_percentage"]
                gp_change = last_gp - first_gp
                if gp_change > 2:
                    trend_direction = "improving"
                elif gp_change < -2:
                    trend_direction = "declining"
                else:
                    trend_direction = "stable"
            else:
                gp_change = 0
                trend_direction = "stable"
        else:
            avg_gp = None
            highest_gp = None
            lowest_gp = None
            avg_pour_cost = None
            gp_change = 0
            trend_direction = "unknown"
        
        return {
            "average_gp_percentage": round(avg_gp, 2) if avg_gp else None,
            "highest_gp_period": highest_gp,
            "lowest_gp_period": lowest_gp,
            "average_pour_cost_percentage": round(avg_pour_cost, 2) if avg_pour_cost else None,
            "trend": {
                "direction": trend_direction,
                "change": round(gp_change, 2)
            },
            "all_periods": gp_percentages
        }
    
    def _calculate_category_performance(self, periods):
        """Calculate category performance KPIs"""
        latest_period = periods.last()
        
        # Get snapshots for latest period grouped by category
        snapshots = StockSnapshot.objects.filter(
            period=latest_period
        ).select_related('item__category')
        
        category_data = {}
        for snapshot in snapshots:
            cat_code = snapshot.item.category.code
            cat_name = snapshot.item.category.name
            
            if cat_code not in category_data:
                category_data[cat_code] = {
                    "category_name": cat_name,
                    "total_value": Decimal('0'),
                    "item_count": 0,
                    "total_gp": Decimal('0'),
                    "gp_count": 0
                }
            
            category_data[cat_code]["total_value"] += snapshot.closing_stock_value
            category_data[cat_code]["item_count"] += 1
            
            # Calculate GP if menu price available
            if snapshot.menu_price and snapshot.menu_price > 0:
                gp = ((snapshot.menu_price - snapshot.cost_per_serving) / snapshot.menu_price) * 100
                category_data[cat_code]["total_gp"] += Decimal(str(gp))
                category_data[cat_code]["gp_count"] += 1
        
        # Calculate averages and find top performers
        category_list = []
        for cat_code, data in category_data.items():
            avg_gp = (data["total_gp"] / data["gp_count"]) if data["gp_count"] > 0 else None
            total_value = float(data["total_value"])
            
            category_list.append({
                "category_code": cat_code,
                "category_name": data["category_name"],
                "total_value": total_value,
                "item_count": data["item_count"],
                "average_gp_percentage": float(round(avg_gp, 2)) if avg_gp else None
            })
        
        # Sort and find top performers
        category_list_by_value = sorted(category_list, key=lambda x: x["total_value"], reverse=True)
        top_by_value = category_list_by_value[0] if category_list_by_value else None
        
        categories_with_gp = [c for c in category_list if c["average_gp_percentage"] is not None]
        top_by_gp = max(categories_with_gp, key=lambda x: x["average_gp_percentage"]) if categories_with_gp else None
        
        # Calculate total for percentages
        total_value = sum(c["total_value"] for c in category_list)
        for cat in category_list:
            cat["percentage_of_total"] = round((cat["total_value"] / total_value * 100), 2) if total_value > 0 else 0
        
        # Category growth (if multiple periods)
        most_growth = None
        if len(periods) >= 2:
            first_period = periods.first()
            last_period = periods.last()
            
            growth_data = {}
            for cat_code in category_data.keys():
                first_value = sum(
                    s.closing_stock_value for s in StockSnapshot.objects.filter(
                        period=first_period,
                        item__category__code=cat_code
                    )
                )
                last_value = sum(
                    s.closing_stock_value for s in StockSnapshot.objects.filter(
                        period=last_period,
                        item__category__code=cat_code
                    )
                )
                
                if first_value > 0:
                    growth_pct = ((last_value - first_value) / first_value) * 100
                    growth_data[cat_code] = {
                        "category_name": category_data[cat_code]["category_name"],
                        "growth_percentage": float(round(growth_pct, 2)),
                        "value_increase": float(last_value - first_value)
                    }
            
            if growth_data:
                most_growth_cat = max(growth_data.items(), key=lambda x: x[1]["growth_percentage"])
                most_growth = {
                    "category_code": most_growth_cat[0],
                    **most_growth_cat[1]
                }
        
        return {
            "top_by_value": top_by_value,
            "top_by_gp": top_by_gp,
            "most_growth": most_growth,
            "distribution": category_list
        }
    
    def _calculate_inventory_health(self, periods):
        """Calculate inventory health KPIs"""
        hotel = periods.first().hotel
        latest_period = periods.last()
        
        # Get current stock items
        stock_items = StockItem.objects.filter(hotel=hotel, active=True)
        
        low_stock_items = []
        out_of_stock_items = []
        overstocked_items = []
        dead_stock_items = []
        
        for item in stock_items:
            total_servings = item.total_stock_in_servings
            
            # Low stock check
            if item.par_level and total_servings < item.par_level:
                low_stock_items.append({
                    "item_name": item.name,
                    "sku": item.sku,
                    "current_quantity": float(total_servings),
                    "par_level": float(item.par_level),
                    "percentage_of_par": float(round((total_servings / item.par_level * 100), 2)) if item.par_level > 0 else 0
                })
            
            # Out of stock
            if total_servings == 0:
                out_of_stock_items.append({
                    "item_name": item.name,
                    "sku": item.sku
                })
            
            # Overstocked (>150% of par)
            if item.par_level and total_servings > (item.par_level * Decimal('1.5')):
                overstocked_items.append({
                    "item_name": item.name,
                    "sku": item.sku,
                    "current_quantity": float(total_servings),
                    "par_level": float(item.par_level),
                    "percentage_of_par": float(round((total_servings / item.par_level * 100), 2))
                })
        
        # Dead stock (no movement in latest period)
        movements_in_period = StockMovement.objects.filter(
            hotel=hotel,
            period=latest_period
        ).values_list('item_id', flat=True).distinct()
        
        for item in stock_items:
            if item.id not in movements_in_period and item.total_stock_in_servings > 0:
                dead_stock_items.append({
                    "item_name": item.name,
                    "sku": item.sku,
                    "stock_value": float(item.total_stock_value)
                })
        
        # Calculate health score (0-100)
        total_items = stock_items.count()
        if total_items > 0:
            low_stock_penalty = (len(low_stock_items) / total_items) * 20
            out_of_stock_penalty = (len(out_of_stock_items) / total_items) * 30
            overstock_penalty = (len(overstocked_items) / total_items) * 15
            dead_stock_penalty = (len(dead_stock_items) / total_items) * 15
            
            health_score = 100 - (low_stock_penalty + out_of_stock_penalty + overstock_penalty + dead_stock_penalty)
            health_score = max(0, min(100, health_score))  # Clamp between 0-100
        else:
            health_score = 100
        
        # Determine rating
        if health_score >= 90:
            health_rating = "Excellent"
        elif health_score >= 75:
            health_rating = "Good"
        elif health_score >= 60:
            health_rating = "Fair"
        else:
            health_rating = "Poor"
        
        return {
            "low_stock_count": len(low_stock_items),
            "low_stock_items": low_stock_items[:10],  # Top 10
            "out_of_stock_count": len(out_of_stock_items),
            "out_of_stock_items": [item["item_name"] for item in out_of_stock_items[:10]],
            "overstocked_count": len(overstocked_items),
            "overstocked_items": overstocked_items[:5],
            "dead_stock_count": len(dead_stock_items),
            "dead_stock_items": [item["item_name"] for item in dead_stock_items[:5]],
            "overall_health_score": int(round(health_score)),
            "health_rating": health_rating,
            "total_items_analyzed": total_items
        }
    
    def _calculate_period_comparison(self, periods):
        """Calculate period comparison KPIs (requires 2+ periods)"""
        if len(periods) < 2:
            return None
        
        first_period = periods.first()
        last_period = periods.last()
        
        # Get snapshots
        first_snapshots = {s.item_id: s for s in StockSnapshot.objects.filter(period=first_period)}
        last_snapshots = {s.item_id: s for s in StockSnapshot.objects.filter(period=last_period)}
        
        increases = []
        decreases = []
        total_movers = 0
        
        # Compare common items
        common_item_ids = set(first_snapshots.keys()) & set(last_snapshots.keys())
        
        for item_id in common_item_ids:
            first_snap = first_snapshots[item_id]
            last_snap = last_snapshots[item_id]
            
            first_value = first_snap.closing_stock_value
            last_value = last_snap.closing_stock_value
            
            if first_value > 0:
                change = last_value - first_value
                percentage_change = (change / first_value) * 100
                
                # Significant change threshold (>10%)
                if abs(percentage_change) > 10:
                    total_movers += 1
                    
                    change_data = {
                        "item_name": last_snap.item.name,
                        "sku": last_snap.item.sku,
                        "category": last_snap.item.category.name,
                        "previous_value": float(first_value),
                        "current_value": float(last_value),
                        "change": float(change),
                        "percentage_change": round(float(percentage_change), 2)
                    }
                    
                    if change > 0:
                        increases.append(change_data)
                    else:
                        decreases.append(change_data)
        
        # Sort and get top movers
        increases.sort(key=lambda x: x["percentage_change"], reverse=True)
        decreases.sort(key=lambda x: x["percentage_change"])
        
        # Category changes
        category_changes = {}
        for cat in StockCategory.objects.all():
            first_cat_value = sum(
                s.closing_stock_value for s in first_snapshots.values()
                if s.item.category.code == cat.code
            )
            last_cat_value = sum(
                s.closing_stock_value for s in last_snapshots.values()
                if s.item.category.code == cat.code
            )
            
            if first_cat_value > 0:
                change = last_cat_value - first_cat_value
                percentage_change = (change / first_cat_value) * 100
                
                category_changes[cat.code] = {
                    "category_name": cat.name,
                    "change": float(change),
                    "percentage_change": round(float(percentage_change), 2),
                    "direction": "increase" if change > 0 else "decrease"
                }
        
        # Overall variance
        total_first_value = sum(s.closing_stock_value for s in first_snapshots.values())
        total_last_value = sum(s.closing_stock_value for s in last_snapshots.values())
        
        if total_first_value > 0:
            overall_variance = ((total_last_value - total_first_value) / total_first_value) * 100
            variance_direction = "increase" if overall_variance > 0 else "decrease"
        else:
            overall_variance = 0
            variance_direction = "stable"
        
        return {
            "periods_compared": [p.period_name for p in [first_period, last_period]],
            "total_movers_count": total_movers,
            "threshold_percentage": 10,
            "biggest_increases": increases[:5],
            "biggest_decreases": decreases[:5],
            "categories_with_most_change": sorted(
                category_changes.values(),
                key=lambda x: abs(x["percentage_change"]),
                reverse=True
            )[:5],
            "overall_variance": {
                "percentage": round(float(overall_variance), 2),
                "direction": variance_direction,
                "value_change": float(total_last_value - total_first_value)
            }
        }
    
    def _calculate_performance_score(self, periods):
        """Calculate overall performance score"""
        # Get component scores
        profitability = self._calculate_profitability_metrics(periods)
        health = self._calculate_inventory_health(periods)
        
        # Profitability score (based on avg GP%)
        avg_gp = profitability.get("average_gp_percentage")
        if avg_gp:
            if avg_gp >= 70:
                profitability_score = 100
            elif avg_gp >= 60:
                profitability_score = 85
            elif avg_gp >= 50:
                profitability_score = 70
            else:
                profitability_score = 50
        else:
            profitability_score = None
        
        # Stock health score
        stock_health_score = health.get("overall_health_score", 0)
        
        # Turnover score (placeholder - would need sales data)
        turnover_score = 75  # Default
        
        # Category balance score (how evenly distributed)
        category_perf = self._calculate_category_performance(periods)
        category_dist = category_perf.get("distribution", [])
        if category_dist:
            percentages = [c["percentage_of_total"] for c in category_dist]
            # Better balance = higher score (none should dominate too much)
            max_percentage = max(percentages) if percentages else 100
            if max_percentage < 40:
                category_balance_score = 100
            elif max_percentage < 50:
                category_balance_score = 85
            elif max_percentage < 60:
                category_balance_score = 70
            else:
                category_balance_score = 60
        else:
            category_balance_score = 70
        
        # Variance control score
        comparison = self._calculate_period_comparison(periods)
        if comparison:
            movers_count = comparison.get("total_movers_count", 0)
            total_items = health.get("total_items_analyzed", 1)
            mover_percentage = (movers_count / total_items * 100) if total_items > 0 else 0
            
            # Lower variance = better control
            if mover_percentage < 20:
                variance_control_score = 100
            elif mover_percentage < 40:
                variance_control_score = 80
            elif mover_percentage < 60:
                variance_control_score = 60
            else:
                variance_control_score = 40
        else:
            variance_control_score = 75
        
        # Calculate overall score (weighted average)
        scores = []
        if profitability_score:
            scores.append(profitability_score * 0.30)  # 30% weight
        scores.append(stock_health_score * 0.25)  # 25% weight
        scores.append(turnover_score * 0.20)  # 20% weight
        scores.append(category_balance_score * 0.15)  # 15% weight
        scores.append(variance_control_score * 0.10)  # 10% weight
        
        overall_score = int(round(sum(scores)))
        
        # Determine rating
        if overall_score >= 90:
            rating = "Excellent"
        elif overall_score >= 75:
            rating = "Good"
        elif overall_score >= 60:
            rating = "Fair"
        else:
            rating = "Poor"
        
        # Improvement areas
        improvement_areas = []
        if profitability_score and profitability_score < 80:
            improvement_areas.append({
                "area": "Profitability",
                "current_score": profitability_score,
                "priority": "high" if profitability_score < 60 else "medium",
                "recommendation": "Review pricing strategy and reduce pour costs"
            })
        
        if stock_health_score < 75:
            improvement_areas.append({
                "area": "Stock Health",
                "current_score": stock_health_score,
                "priority": "high" if stock_health_score < 60 else "medium",
                "recommendation": f"Address {health['low_stock_count']} low stock items and {health['out_of_stock_count']} out of stock items"
            })
        
        if variance_control_score < 75:
            improvement_areas.append({
                "area": "Variance Control",
                "current_score": variance_control_score,
                "priority": "medium",
                "recommendation": "Reduce stock level fluctuations through better ordering"
            })
        
        return {
            "overall_score": overall_score,
            "rating": rating,
            "breakdown": {
                "profitability_score": profitability_score,
                "stock_health_score": stock_health_score,
                "turnover_score": turnover_score,
                "category_balance_score": category_balance_score,
                "variance_control_score": variance_control_score
            },
            "improvement_areas": improvement_areas,
            "strengths": self._identify_strengths(profitability_score, stock_health_score, category_balance_score)
        }
    
    def _identify_strengths(self, prof_score, health_score, balance_score):
        """Identify strengths based on scores"""
        strengths = []
        if prof_score and prof_score >= 85:
            strengths.append("Excellent profitability margins")
        if health_score >= 85:
            strengths.append("Strong inventory health")
        if balance_score >= 85:
            strengths.append("Well-balanced category distribution")
        
        if not strengths:
            strengths.append("Good operational consistency")
        
        return strengths
    
    def _calculate_additional_metrics(self, periods):
        """Calculate additional useful metrics"""
        hotel = periods.first().hotel
        
        # Total items
        stock_items = StockItem.objects.filter(hotel=hotel, active=True)
        total_items = stock_items.count()
        
        # Active items (with recent movement)
        latest_period = periods.last()
        active_item_ids = StockMovement.objects.filter(
            hotel=hotel,
            period=latest_period
        ).values_list('item_id', flat=True).distinct()
        active_items_count = len(set(active_item_ids))
        
        # Total categories
        total_categories = StockCategory.objects.count()
        
        # Average item value
        latest_snapshots = StockSnapshot.objects.filter(period=latest_period)
        if latest_snapshots.exists():
            total_value = sum(s.closing_stock_value for s in latest_snapshots)
            avg_item_value = total_value / latest_snapshots.count() if latest_snapshots.count() > 0 else 0
        else:
            avg_item_value = 0
        
        # Purchase activity
        purchases = StockMovement.objects.filter(
            hotel=hotel,
            period__in=periods,
            movement_type=StockMovement.PURCHASE
        )
        purchase_count = purchases.count()
        avg_purchases_per_period = purchase_count / len(periods) if len(periods) > 0 else 0
        
        # Most purchased category
        if purchases.exists():
            from collections import Counter
            purchase_categories = purchases.select_related('item__category').values_list('item__category__name', flat=True)
            most_purchased_cat = Counter(purchase_categories).most_common(1)[0][0] if purchase_categories else None
        else:
            most_purchased_cat = None
        
        return {
            "total_items_count": total_items,
            "active_items_count": active_items_count,
            "inactive_items_count": total_items - active_items_count,
            "total_categories": total_categories,
            "average_item_value": float(round(avg_item_value, 2)),
            "purchase_activity": {
                "total_purchases": purchase_count,
                "average_per_period": round(avg_purchases_per_period, 1),
                "most_purchased_category": most_purchased_cat
            }
        }
