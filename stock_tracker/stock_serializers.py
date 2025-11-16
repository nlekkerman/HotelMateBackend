from rest_framework import serializers
from .models import (
    StockCategory,
    StockItem,
    StockPeriod,
    StockSnapshot,
    StockMovement,
    Location,
    Stocktake,
    StocktakeLine,
    Sale,
    PeriodReopenPermission
)


class StockCategorySerializer(serializers.ModelSerializer):
    """Serializer for stock categories (D, B, S, W, M)"""
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StockCategory
        fields = ['code', 'name', 'item_count']
        read_only_fields = ['code', 'name']
    
    def get_item_count(self, obj):
        """Get count of items in this category"""
        return obj.stock_items.count()


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for stock locations (Bar, Cellar, Storage, etc.)"""
    class Meta:
        model = Location
        fields = ['id', 'hotel', 'name', 'active']
        read_only_fields = ['hotel']


class StockSnapshotNestedSerializer(serializers.ModelSerializer):
    """Nested serializer for snapshots within period detail"""
    item = serializers.SerializerMethodField()
    
    # Calculated fields - use total_servings from model
    total_servings = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    
    # Display helpers for frontend (convert bottles to dozens for Doz items)
    display_full_units = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    display_partial_units = serializers.DecimalField(
        max_digits=10, decimal_places=4, read_only=True
    )
    
    # Opening stock (calculated from previous period)
    opening_full_units = serializers.SerializerMethodField()
    opening_partial_units = serializers.SerializerMethodField()
    opening_stock_value = serializers.SerializerMethodField()
    opening_display_full_units = serializers.SerializerMethodField()
    opening_display_partial_units = serializers.SerializerMethodField()
    
    # Closing stock display (calculated from closing raw values)
    closing_display_full_units = serializers.SerializerMethodField()
    closing_display_partial_units = serializers.SerializerMethodField()
    
    # Profitability metrics from item
    gp_percentage = serializers.SerializerMethodField()
    markup_percentage = serializers.SerializerMethodField()
    pour_cost_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = StockSnapshot
        fields = [
            'id', 'item',
            # Opening stock (from previous period's closing)
            'opening_full_units', 'opening_partial_units',
            'opening_stock_value',
            'opening_display_full_units', 'opening_display_partial_units',
            # Closing stock (counted at period end)
            'closing_full_units', 'closing_partial_units',
            'closing_stock_value',
            'closing_display_full_units', 'closing_display_partial_units',
            # Total servings and display (DEPRECATED)
            'total_servings', 'display_full_units', 'display_partial_units',
            # Cost information (for stocktake calculations)
            'unit_cost', 'cost_per_serving',
            # Profitability metrics
            'gp_percentage', 'markup_percentage', 'pour_cost_percentage'
        ]
    
    def get_item(self, obj):
        """Return item details"""
        return {
            'id': obj.item.id,
            'sku': obj.item.sku,
            'name': obj.item.name,
            'category': obj.item.category.code,
            'category_display': obj.item.category.name,
            'size': obj.item.size,
            'unit_cost': str(obj.item.unit_cost),
            'menu_price': (
                str(obj.item.menu_price)
                if obj.item.menu_price else None
            )
        }
    
    def get_opening_full_units(self, obj):
        """
        Get opening stock from previous period's closing stock.
        This is what was counted at END of previous period.
        """
        # Get previous period (by end_date)
        prev_snapshot = StockSnapshot.objects.filter(
            hotel=obj.hotel,
            item=obj.item,
            period__end_date__lt=obj.period.start_date
        ).order_by('-period__end_date').first()
        
        if prev_snapshot:
            return str(prev_snapshot.closing_full_units)
        return "0.00"
    
    def get_opening_partial_units(self, obj):
        """Get opening partial units from previous period"""
        prev_snapshot = StockSnapshot.objects.filter(
            hotel=obj.hotel,
            item=obj.item,
            period__end_date__lt=obj.period.start_date
        ).order_by('-period__end_date').first()
        
        if prev_snapshot:
            return str(prev_snapshot.closing_partial_units)
        return "0.0000"
    
    def get_opening_stock_value(self, obj):
        """Get opening stock value from previous period"""
        prev_snapshot = StockSnapshot.objects.filter(
            hotel=obj.hotel,
            item=obj.item,
            period__end_date__lt=obj.period.start_date
        ).order_by('-period__end_date').first()
        
        if prev_snapshot:
            return str(prev_snapshot.closing_stock_value)
        return "0.00"
    
    def get_opening_display_full_units(self, obj):
        """
        Get opening display full units (kegs/cases)
        Calculated from previous period's closing stock
        """
        prev_snapshot = StockSnapshot.objects.filter(
            hotel=obj.hotel,
            item=obj.item,
            period__end_date__lt=obj.period.start_date
        ).order_by('-period__end_date').first()
        
        if prev_snapshot:
            opening_servings = prev_snapshot.closing_partial_units
            display_full = obj.calculate_opening_display_full(
                opening_servings
            )
            return str(int(display_full))
        return "0"
    
    def get_opening_display_partial_units(self, obj):
        """
        Get opening display partial units (pints/bottles)
        Calculated from previous period's closing stock
        - Bottles (Doz): whole numbers (0, 1, 2, ... 11)
        - Pints (Draught): 2 decimals (0.00, 1.50, etc)
        - Others: 2 decimals
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        prev_snapshot = StockSnapshot.objects.filter(
            hotel=obj.hotel,
            item=obj.item,
            period__end_date__lt=obj.period.start_date
        ).order_by('-period__end_date').first()
        
        if prev_snapshot:
            opening_servings = prev_snapshot.closing_partial_units
            display_partial = obj.calculate_opening_display_partial(
                opening_servings
            )
            
            # Bottles (Doz) = whole numbers
            if obj.item.size and 'Doz' in obj.item.size:
                return str(int(round(float(display_partial))))
            
            # Pints/Others = 2 decimals
            decimal_val = Decimal(str(display_partial))
            rounded = decimal_val.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            return str(rounded)
        return "0.00"
    
    def get_closing_display_full_units(self, obj):
        """
        Get closing display full units (kegs/cases)
        Calculated from closing stock
        """
        closing_servings = obj.closing_partial_units
        display_full = obj.calculate_opening_display_full(
            closing_servings
        )
        return str(int(display_full))
    
    def get_closing_display_partial_units(self, obj):
        """
        Get closing display partial units (pints/bottles)
        Calculated from closing stock
        - Bottles (Doz): whole numbers (0, 1, 2, ... 11)
        - Pints (Draught): 2 decimals (0.00, 1.50, etc)
        - Others: 2 decimals
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        closing_servings = obj.closing_partial_units
        display_partial = obj.calculate_opening_display_partial(
            closing_servings
        )
        
        # Bottles (Doz) = whole numbers
        if obj.item.size and 'Doz' in obj.item.size:
            return str(int(round(float(display_partial))))
        
        # Pints/Others = 2 decimals
        decimal_val = Decimal(str(display_partial))
        rounded = decimal_val.quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        return str(rounded)
    
    def get_gp_percentage(self, obj):
        """Get gross profit percentage from item"""
        if obj.item.gross_profit_percentage:
            return str(obj.item.gross_profit_percentage)
        return None
    
    def get_markup_percentage(self, obj):
        """Get markup percentage from item"""
        if obj.item.markup_percentage:
            return str(obj.item.markup_percentage)
        return None
    
    def get_pour_cost_percentage(self, obj):
        """Get pour cost percentage from item"""
        if obj.item.pour_cost_percentage:
            return str(obj.item.pour_cost_percentage)
        return None


class StockPeriodSerializer(serializers.ModelSerializer):
    """Serializer for stock periods list view"""
    period_name = serializers.CharField(read_only=True)
    stocktake_id = serializers.SerializerMethodField()
    stocktake = serializers.SerializerMethodField()
    can_reopen = serializers.SerializerMethodField()
    can_manage_permissions = serializers.SerializerMethodField()
    closed_by_name = serializers.SerializerMethodField()
    reopened_by_name = serializers.SerializerMethodField()
    
    manual_sales_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    manual_purchases_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )

    class Meta:
        model = StockPeriod
        fields = [
            'id', 'hotel', 'period_type', 'start_date', 'end_date',
            'year', 'month', 'quarter', 'week', 'period_name', 'is_closed',
            'closed_at', 'closed_by', 'closed_by_name',
            'reopened_at', 'reopened_by', 'reopened_by_name',
            'manual_sales_amount', 'manual_purchases_amount',
            'stocktake_id', 'stocktake', 'can_reopen', 'can_manage_permissions'
        ]
        read_only_fields = [
            'hotel', 'period_name', 'year', 'month', 'quarter', 'week',
            'closed_at', 'closed_by', 'closed_by_name',
            'reopened_at', 'reopened_by', 'reopened_by_name',
            'can_reopen', 'can_manage_permissions'
        ]
    
    def get_stocktake_id(self, obj):
        """
        Get related stocktake ID (if exists).
        Matches by dates, not by ID.
        Returns None if no stocktake exists for this period.
        """
        from .models import Stocktake
        try:
            stocktake = Stocktake.objects.get(
                hotel=obj.hotel,
                period_start=obj.start_date,
                period_end=obj.end_date
            )
            return stocktake.id
        except Stocktake.DoesNotExist:
            return None
    
    def get_stocktake(self, obj):
        """
        Get basic stocktake information for this period.
        Returns None if no stocktake exists.
        
        Includes:
        - id: Stocktake ID
        - status: DRAFT or APPROVED
        - total_lines: Number of items in stocktake
        - lines_counted: Number of items with counted values
        - total_cogs: Cost of goods sold
        - total_revenue: Sales revenue
        - gross_profit_percentage: GP%
        - pour_cost_percentage: Pour cost%
        """
        from .models import Stocktake
        try:
            stocktake = Stocktake.objects.get(
                hotel=obj.hotel,
                period_start=obj.start_date,
                period_end=obj.end_date
            )
            
            # Count lines
            total_lines = stocktake.lines.count()
            lines_counted = stocktake.lines.exclude(
                counted_full_units=0,
                counted_partial_units=0
            ).count()
            
            return {
                'id': stocktake.id,
                'status': stocktake.status,
                'total_lines': total_lines,
                'lines_counted': lines_counted,
                'lines_at_zero': total_lines - lines_counted,
                'total_cogs': float(stocktake.total_cogs) if stocktake.total_cogs else None,
                'total_revenue': float(stocktake.total_revenue) if stocktake.total_revenue else None,
                'gross_profit_percentage': float(stocktake.gross_profit_percentage) if stocktake.gross_profit_percentage else None,
                'pour_cost_percentage': float(stocktake.pour_cost_percentage) if stocktake.pour_cost_percentage else None,
                'approved_at': stocktake.approved_at,
                'notes': stocktake.notes
            }
        except Stocktake.DoesNotExist:
            return None
    
    def get_can_reopen(self, obj):
        """
        Check if current user can reopen this period.
        Returns True if:
        - User is a superuser, OR
        - User has PeriodReopenPermission for this hotel
        """
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers can always reopen
        if request.user.is_superuser:
            return True
        
        # Check if staff has permission
        from .models import PeriodReopenPermission
        try:
            staff = request.user.staff_profile
            return PeriodReopenPermission.objects.filter(
                hotel=obj.hotel,
                staff=staff,
                is_active=True
            ).exists()
        except:
            return False
    
    def get_can_manage_permissions(self, obj):
        """
        Check if current user can manage reopen permissions (grant/revoke).
        Returns True if:
        - User is a superuser, OR
        - User has PeriodReopenPermission with can_grant_to_others=True (manager)
        """
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        # Superusers can always manage
        if request.user.is_superuser:
            return True
        
        # Check if user is a manager (has can_grant_to_others permission)
        from .models import PeriodReopenPermission
        try:
            staff = request.user.staff_profile
            return PeriodReopenPermission.objects.filter(
                hotel=obj.hotel,
                staff=staff,
                is_active=True,
                can_grant_to_others=True
            ).exists()
        except:
            return False
    
    def get_closed_by_name(self, obj):
        """Get the full name of staff who closed the period"""
        if obj.closed_by:
            return str(obj.closed_by)  # Returns "Nikola Simic - Front Office - Porter"
        return None
    
    def get_reopened_by_name(self, obj):
        """Get the full name of staff who reopened the period"""
        if obj.reopened_by:
            return str(obj.reopened_by)  # Returns "Nikola Simic - Front Office - Porter"
        return None


class StockPeriodDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for single period with all related data.
    Returns period + snapshots + stocktake info in one response.
    """
    period_name = serializers.CharField(read_only=True)
    snapshots = serializers.SerializerMethodField()
    snapshot_ids = serializers.SerializerMethodField()
    stocktake_id = serializers.SerializerMethodField()
    stocktake_status = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    
    manual_sales_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    manual_purchases_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )

    class Meta:
        model = StockPeriod
        fields = [
            'id', 'hotel', 'period_type', 'start_date', 'end_date',
            'year', 'month', 'quarter', 'week', 'period_name', 'is_closed',
            'manual_sales_amount', 'manual_purchases_amount',
            'snapshots', 'snapshot_ids', 'stocktake_id', 'stocktake_status',
            'total_items', 'total_value'
        ]
        read_only_fields = [
            'hotel', 'period_name', 'year', 'month', 'quarter', 'week'
        ]
    
    def get_snapshots(self, obj):
        """Get all snapshots for this period"""
        snapshots = StockSnapshot.objects.filter(
            period=obj
        ).select_related('item', 'item__category').order_by(
            'item__category__code', 'item__name'
        )
        return StockSnapshotNestedSerializer(snapshots, many=True).data
    
    def get_snapshot_ids(self, obj):
        """Get list of all snapshot IDs for this period"""
        return list(
            StockSnapshot.objects.filter(period=obj)
            .values_list('id', flat=True)
        )
    
    def get_stocktake_id(self, obj):
        """
        Get related stocktake ID (if exists).
        Matches via dates, not FK.
        """
        from .models import Stocktake
        stocktake = Stocktake.objects.filter(
            hotel=obj.hotel,
            period_start=obj.start_date,
            period_end=obj.end_date
        ).first()
        return stocktake.id if stocktake else None
    
    def get_stocktake_status(self, obj):
        """Get stocktake status (if exists)"""
        from .models import Stocktake
        stocktake = Stocktake.objects.filter(
            hotel=obj.hotel,
            period_start=obj.start_date,
            period_end=obj.end_date
        ).first()
        return stocktake.status if stocktake else None
    
    def get_total_items(self, obj):
        """Count of items in this period"""
        return StockSnapshot.objects.filter(period=obj).count()
    
    def get_total_value(self, obj):
        """Total stock value for this period"""
        from django.db.models import Sum
        result = StockSnapshot.objects.filter(period=obj).aggregate(
            total=Sum('closing_stock_value')
        )
        return str(result['total'] or 0)


class StockItemSerializer(serializers.ModelSerializer):
    """Serializer for stock items with profitability calculations"""
    category_code = serializers.CharField(
        source='category.code', read_only=True
    )
    category_name = serializers.CharField(
        source='category.name', read_only=True
    )
    
    # Minerals subcategory
    subcategory = serializers.CharField(read_only=True)
    subcategory_display = serializers.SerializerMethodField()
    
    def get_subcategory_display(self, obj):
        """Get human-readable subcategory name"""
        if obj.subcategory:
            return obj.get_subcategory_display()
        return None
    
    # Calculated fields from model properties
    total_stock_in_servings = serializers.DecimalField(
        max_digits=10, decimal_places=4, read_only=True
    )
    total_stock_value = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    cost_per_serving = serializers.DecimalField(
        max_digits=10, decimal_places=4, read_only=True
    )
    gross_profit_per_serving = serializers.DecimalField(
        max_digits=10, decimal_places=4, read_only=True
    )
    gross_profit_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    markup_percentage = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )
    pour_cost_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    
    # Display helpers for frontend (convert bottles to cases for Doz items)
    display_full_units = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    display_partial_units = serializers.DecimalField(
        max_digits=10, decimal_places=4, read_only=True
    )

    class Meta:
        model = StockItem
        fields = [
            'id', 'hotel', 'sku', 'name',
            'category', 'category_code', 'category_name',
            'subcategory', 'subcategory_display',
            'size', 'size_value', 'size_unit', 'uom',
            'unit_cost', 'current_full_units', 'current_partial_units',
            'menu_price', 'menu_price_large', 'bottle_price', 'promo_price',
            'available_on_menu', 'available_by_bottle', 'active',
            'created_at', 'updated_at',
            # Calculated fields
            'total_stock_in_servings', 'total_stock_value',
            'cost_per_serving', 'gross_profit_per_serving',
            'gross_profit_percentage', 'markup_percentage',
            'pour_cost_percentage',
            # Display helpers
            'display_full_units', 'display_partial_units'
        ]
        read_only_fields = ['hotel', 'created_at', 'updated_at']


class StockSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for stock snapshots at period end"""
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    category_code = serializers.CharField(
        source='item.category.code', read_only=True
    )
    period_name = serializers.CharField(
        source='period.period_name', read_only=True
    )
    # Use total_servings property from model
    total_servings = serializers.DecimalField(
        max_digits=10, decimal_places=4, read_only=True
    )
    
    # Display-friendly units (converts dozens for bottles)
    display_full_units = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    display_partial_units = serializers.DecimalField(
        max_digits=10, decimal_places=4, read_only=True
    )
    
    # Profitability metrics from item
    gp_percentage = serializers.SerializerMethodField()
    markup_percentage = serializers.SerializerMethodField()
    pour_cost_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = StockSnapshot
        fields = [
            'id', 'hotel', 'item', 'item_sku', 'item_name',
            'category_code', 'period', 'period_name',
            'closing_full_units', 'closing_partial_units', 'total_servings',
            'display_full_units', 'display_partial_units',
            'unit_cost', 'cost_per_serving', 'closing_stock_value',
            'gp_percentage', 'markup_percentage', 'pour_cost_percentage',
            'created_at'
        ]
        read_only_fields = ['hotel', 'created_at']
    
    def get_gp_percentage(self, obj):
        """Get gross profit percentage from item"""
        if obj.item.gross_profit_percentage:
            return str(obj.item.gross_profit_percentage)
        return None
    
    def get_markup_percentage(self, obj):
        """Get markup percentage from item"""
        if obj.item.markup_percentage:
            return str(obj.item.markup_percentage)
        return None
    
    def get_pour_cost_percentage(self, obj):
        """Get pour cost percentage from item"""
        if obj.item.pour_cost_percentage:
            return str(obj.item.pour_cost_percentage)
        return None


class StockMovementSerializer(serializers.ModelSerializer):
    """
    Serializer for stock movements
    (purchases, waste, transfers, adjustments)
    """
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = [
            'id', 'hotel', 'item', 'item_sku', 'item_name',
            'period', 'movement_type', 'quantity', 'unit_cost',
            'reference', 'notes', 'staff', 'staff_name', 'timestamp'
        ]
        read_only_fields = ['hotel', 'timestamp', 'staff']

    def get_staff_name(self, obj):
        """Get staff full name from Staff model"""
        if obj.staff:
            full_name = (
                f"{obj.staff.first_name} {obj.staff.last_name}".strip()
            )
            return full_name or obj.staff.email or f"Staff #{obj.staff.id}"
        return None


class StocktakeLineSerializer(serializers.ModelSerializer):
    """Serializer for stocktake lines with display fields"""
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    category_code = serializers.CharField(
        source='item.category.code', read_only=True
    )
    category_name = serializers.CharField(
        source='item.category.name', read_only=True
    )
    
    # Minerals subcategory
    subcategory = serializers.CharField(
        source='item.subcategory', read_only=True
    )
    
    # UI helper to show which fields to display for counting
    input_fields = serializers.SerializerMethodField()
    
    def get_input_fields(self, obj):
        """
        Return which fields the UI should show for counting.
        Based on category and subcategory.
        
        Returns dict with field names and labels for frontend display.
        """
        category = obj.item.category_id
        
        # Minerals subcategories
        if category == 'M' and obj.item.subcategory:
            if obj.item.subcategory == 'SOFT_DRINKS':
                return {
                    'full': {'name': 'counted_full_units', 'label': 'Cases'},
                    'partial': {'name': 'counted_partial_units', 'label': 'Bottles', 'max': 11}
                }
            elif obj.item.subcategory == 'SYRUPS':
                return {
                    'full': {'name': 'counted_full_units', 'label': 'Bottles'},
                    'partial': {'name': 'counted_partial_units', 'label': 'ml', 'max': 1000}
                }
            elif obj.item.subcategory == 'JUICES':
                return {
                    'full': {'name': 'counted_full_units', 'label': 'Bottles'},
                    'partial': {'name': 'counted_partial_units', 'label': 'ml', 'max': 1500}
                }
            elif obj.item.subcategory == 'CORDIALS':
                return {
                    'full': {'name': 'counted_full_units', 'label': 'Cases'},
                    'partial': {'name': 'counted_partial_units', 'label': 'Bottles'}
                }
            elif obj.item.subcategory == 'BIB':
                return {
                    'full': {'name': 'counted_full_units', 'label': 'Boxes'},
                    'partial': {'name': 'counted_partial_units', 'label': 'Liters', 'max': 18, 'step': 0.1}
                }
            elif obj.item.subcategory == 'BULK_JUICES':
                return {
                    'full': {'name': 'counted_full_units', 'label': 'Bottles'},
                    'partial': {'name': 'counted_partial_units', 'label': 'Partial', 'max': 0.99, 'step': 0.5}
                }
        
        # Draught Beer
        if category == 'D':
            return {
                'full': {'name': 'counted_full_units', 'label': 'Kegs'},
                'partial': {'name': 'counted_partial_units', 'label': 'Pints', 'step': 0.25}
            }
        
        # Bottled Beer
        if category == 'B':
            return {
                'full': {'name': 'counted_full_units', 'label': 'Cases'},
                'partial': {'name': 'counted_partial_units', 'label': 'Bottles', 'max': 23}
            }
        
        # Spirits
        if category == 'S':
            return {
                'full': {'name': 'counted_full_units', 'label': 'Bottles'},
                'partial': {'name': 'counted_partial_units', 'label': 'Fractional (0-0.99)', 'max': 0.99, 'step': 0.05}
            }
        
        # Wine
        if category == 'W':
            return {
                'full': {'name': 'counted_full_units', 'label': 'Bottles'},
                'partial': {'name': 'counted_partial_units', 'label': 'Fractional (0-0.99)', 'max': 0.99, 'step': 0.05}
            }
        
        # Fallback for unknown categories
        return {
            'full': {'name': 'counted_full_units', 'label': 'Full Units'},
            'partial': {'name': 'counted_partial_units', 'label': 'Partial Units'}
        }
    
    # Item details for display calculations
    item_size = serializers.CharField(source='item.size', read_only=True)
    item_uom = serializers.DecimalField(
        source='item.uom', max_digits=10, decimal_places=2, read_only=True
    )
    
    # Cost breakdown for dozen/case items and spirits bottles
    case_cost = serializers.SerializerMethodField()
    bottle_cost = serializers.SerializerMethodField()
    
    # Calculated fields from model properties (raw servings)
    sales_qty = serializers.DecimalField(
        max_digits=15, decimal_places=4, read_only=True
    )
    counted_qty = serializers.DecimalField(
        max_digits=15, decimal_places=4, read_only=True
    )
    expected_qty = serializers.DecimalField(
        max_digits=15, decimal_places=4, read_only=True
    )
    variance_qty = serializers.DecimalField(
        max_digits=15, decimal_places=4, read_only=True
    )
    expected_value = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    counted_value = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    variance_value = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    
    # Display fields (kegs+pints, cases+bottles, bottles+fractional)
    opening_display_full_units = serializers.SerializerMethodField()
    opening_display_partial_units = serializers.SerializerMethodField()
    expected_display_full_units = serializers.SerializerMethodField()
    expected_display_partial_units = serializers.SerializerMethodField()
    counted_display_full_units = serializers.SerializerMethodField()
    counted_display_partial_units = serializers.SerializerMethodField()
    variance_display_full_units = serializers.SerializerMethodField()
    variance_display_partial_units = serializers.SerializerMethodField()
    
    # COCKTAIL CONSUMPTION TRACKING (DISPLAY ONLY - NO STOCKTAKE IMPACT)
    available_cocktail_consumption_qty = serializers.DecimalField(
        max_digits=15,
        decimal_places=4,
        read_only=True,
        help_text="Unmerged cocktail consumption (display only)"
    )
    merged_cocktail_consumption_qty = serializers.DecimalField(
        max_digits=15,
        decimal_places=4,
        read_only=True,
        help_text="Already merged cocktail consumption (display only)"
    )
    available_cocktail_consumption_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
        help_text="Value of unmerged cocktails (display only)"
    )
    merged_cocktail_consumption_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
        help_text="Value of merged cocktails (display only)"
    )
    can_merge_cocktails = serializers.BooleanField(
        read_only=True,
        help_text="True if unmerged cocktail consumption exists"
    )

    # Helper field for SYRUPS single decimal input
    syrup_bottles_input = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        write_only=True,
        required=False,
        help_text="For SYRUPS: enter bottles as decimal (e.g., 10.5). Auto-splits to full+partial"
    )

    class Meta:
        model = StocktakeLine
        fields = [
            'id', 'stocktake', 'item', 'item_sku', 'item_name',
            'category_code', 'category_name', 'subcategory', 'input_fields',
            'item_size', 'item_uom',
            # Cost breakdown
            'case_cost', 'bottle_cost',
            # Raw quantities (servings)
            'opening_qty', 'purchases', 'sales_qty', 'waste',
            'transfers_in', 'transfers_out', 'adjustments',
            # Manual override fields
            'manual_purchases_value', 'manual_waste_value',
            'manual_sales_value',
            'counted_full_units', 'counted_partial_units',
            'syrup_bottles_input',  # Helper for SYRUPS
            'counted_qty', 'expected_qty', 'variance_qty',
            # Display quantities (kegs+pints, cases+bottles, etc)
            'opening_display_full_units', 'opening_display_partial_units',
            'expected_display_full_units', 'expected_display_partial_units',
            'counted_display_full_units', 'counted_display_partial_units',
            'variance_display_full_units', 'variance_display_partial_units',
            # Values
            'valuation_cost', 'expected_value', 'counted_value',
            'variance_value',
            # Cocktail consumption tracking (DISPLAY ONLY)
            'available_cocktail_consumption_qty',
            'merged_cocktail_consumption_qty',
            'available_cocktail_consumption_value',
            'merged_cocktail_consumption_value',
            'can_merge_cocktails'
        ]
        read_only_fields = [
            'waste',
            'transfers_in', 'transfers_out', 'adjustments', 'valuation_cost'
        ]
    
    def update(self, instance, validated_data):
        """Handle syrup_bottles_input for SYRUPS"""
        # Check if syrup_bottles_input was provided
        syrup_input = validated_data.pop('syrup_bottles_input', None)
        
        if syrup_input is not None and instance.item.subcategory == 'SYRUPS':
            # Split decimal into full + partial
            full_bottles = int(syrup_input)
            partial = float(syrup_input) - full_bottles
            
            # Set both fields
            validated_data['counted_full_units'] = full_bottles
            validated_data['counted_partial_units'] = round(partial, 2)
        
        return super().update(instance, validated_data)
    
    def _calculate_display_units(self, servings, item):
        """
        Calculate display full and partial units from servings.
        Returns (full_units, partial_units) as strings.
        
        Minerals subcategories:
          SOFT_DRINKS: servings(bottles) → cases + bottles
          SYRUPS: servings → bottles + ml
          JUICES: servings → bottles + ml
          CORDIALS: servings(bottles) → cases + bottles
          BIB: servings → boxes + liters
        
        Other categories:
          Draught: pints → kegs + pints
          Bottled: bottles → cases + bottles
          Spirits/Wine: shots/glasses → bottles + fractional
        """
        from decimal import Decimal, ROUND_HALF_UP
        from stock_tracker.models import (
            SYRUP_SERVING_SIZE,
            JUICE_SERVING_SIZE,
            BIB_SERVING_SIZE
        )
        
        if servings is None or servings == 0:
            return "0", "0"
        
        servings_decimal = Decimal(str(servings))
        category = item.category.code
        
        # Handle Minerals subcategories
        if category == 'M' and item.subcategory:
            if item.subcategory == 'SOFT_DRINKS':
                # servings = bottles → cases + bottles
                uom = Decimal(str(item.uom))
                full = int(servings_decimal / uom)  # cases
                partial = int(servings_decimal % uom)  # bottles (0-11)
                return str(full), str(partial)
            
            elif item.subcategory == 'SYRUPS':
                # servings → bottles (split into full + fractional)
                # full_units = whole bottles, partial_units = decimal fraction
                total_ml = servings_decimal * SYRUP_SERVING_SIZE
                uom = Decimal(str(item.uom))  # bottle size in ml
                
                # Calculate total bottles as decimal
                bottles_decimal = total_ml / uom
                
                # Split into full bottles + fractional
                full_bottles = int(bottles_decimal)
                fractional = bottles_decimal - full_bottles
                fractional_rounded = fractional.quantize(
                    Decimal('0.001'), rounding=ROUND_HALF_UP
                )
                
                # Return: full_units = whole bottles, partial_units = fraction
                return str(full_bottles), str(fractional_rounded)
            
            elif item.subcategory == 'JUICES':
                # servings → cases + bottles (with decimal)
                # Cases in full, bottles+ml as decimal in partial
                from stock_tracker.juice_helpers import (
                    servings_to_cases_bottles_ml
                )
                
                # Convert servings to cases + bottles + ml
                cases, bottles, ml = servings_to_cases_bottles_ml(
                    float(servings_decimal),
                    bottle_size_ml=float(item.uom),
                    bottles_per_case=12,
                    serving_size_ml=200
                )
                
                # Combine bottles + ml as decimal
                # e.g., 3 bottles + 500ml (of 1000ml bottle) = 3.5
                uom = Decimal(str(item.uom))
                bottles_decimal = Decimal(str(bottles)) + (
                    Decimal(str(ml)) / uom
                )
                bottles_rounded = bottles_decimal.quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                
                return str(cases), str(bottles_rounded)
            
            elif item.subcategory == 'CORDIALS':
                # servings = bottles → cases + bottles
                uom = Decimal(str(item.uom))
                full = int(servings_decimal / uom)  # cases
                partial = int(servings_decimal % uom)  # bottles
                return str(full), str(partial)
            
            elif item.subcategory == 'BIB':
                # servings → boxes + liters
                total_liters = servings_decimal * BIB_SERVING_SIZE
                uom = Decimal(str(item.uom))  # 18 liters/box
                full = int(total_liters / uom)  # boxes
                partial_liters = total_liters % uom  # liters
                partial_rounded = partial_liters.quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                return str(full), str(partial_rounded)
            
            elif item.subcategory == 'BULK_JUICES':
                # servings = bottles (already as bottles)
                # Split into whole + fractional
                full_bottles = int(servings_decimal)
                partial_bottles = servings_decimal - full_bottles
                partial_rounded = partial_bottles.quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                return str(full_bottles), str(partial_rounded)
        
        # Handle other categories
        uom = Decimal(str(item.uom))
        full = int(servings_decimal / uom)
        partial = servings_decimal % uom
        
        if category == 'B':
            # Bottled Beer: cases + bottles (whole numbers)
            partial_display = str(int(round(float(partial))))
        elif category == 'D':
            # Draught: kegs + pints (2 decimals)
            partial_rounded = partial.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            partial_display = str(partial_rounded)
        else:
            # Spirits/Wine: bottles + fractional (2 decimals)
            partial_rounded = partial.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            partial_display = str(partial_rounded)
        
        return str(full), partial_display
    
    def get_opening_display_full_units(self, obj):
        """Opening stock display full units (kegs/cases/bottles)"""
        full, _ = self._calculate_display_units(obj.opening_qty, obj.item)
        return full
    
    def get_opening_display_partial_units(self, obj):
        """Opening stock display partial units (pints/bottles/fractional)"""
        _, partial = self._calculate_display_units(obj.opening_qty, obj.item)
        return partial
    
    def get_expected_display_full_units(self, obj):
        """Expected stock display full units"""
        full, _ = self._calculate_display_units(obj.expected_qty, obj.item)
        return full
    
    def get_expected_display_partial_units(self, obj):
        """Expected stock display partial units"""
        _, partial = self._calculate_display_units(obj.expected_qty, obj.item)
        return partial
    
    def get_counted_display_full_units(self, obj):
        """Counted stock display full units"""
        full, _ = self._calculate_display_units(obj.counted_qty, obj.item)
        return full
    
    def get_counted_display_partial_units(self, obj):
        """Counted stock display partial units"""
        _, partial = self._calculate_display_units(obj.counted_qty, obj.item)
        return partial
    
    def get_variance_display_full_units(self, obj):
        """Variance display full units"""
        full, _ = self._calculate_display_units(obj.variance_qty, obj.item)
        return full
    
    def get_variance_display_partial_units(self, obj):
        """Variance display partial units"""
        _, partial = self._calculate_display_units(obj.variance_qty, obj.item)
        return partial
    
    def get_case_cost(self, obj):
        """Calculate case/dozen cost (valuation_cost × UOM)"""
        from decimal import Decimal
        # For items sold by dozen/case, calculate full case cost
        if obj.item.size and 'Doz' in obj.item.size:
            case_cost = obj.valuation_cost * obj.item.uom
            return str(case_cost)
        # For other items, return None (not applicable)
        return None
    
    def get_bottle_cost(self, obj):
        """Calculate bottle cost for spirits only (valuation_cost × UOM)
        
        Spirits are sold by shots/servings, so:
        - valuation_cost = cost per shot/serving
        - bottle_cost = cost per full bottle (valuation_cost × shots per bottle)
        
        Wine is NOT included - wine is sold by bottle, not by serving.
        """
        from decimal import Decimal
        # Only for spirits (S) - calculate full bottle cost
        category = obj.item.category.code
        if category == 'S':
            bottle_cost = obj.valuation_cost * obj.item.uom
            return str(bottle_cost)
        # For other items (including wine), return None
        return None


class StocktakeSerializer(serializers.ModelSerializer):
    """
    Complete stocktake serializer with all period data.
    Stocktake is an editable view of a Period - includes snapshots,
    period info, and stocktake lines for counting.
    """
    lines = StocktakeLineSerializer(many=True, read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    is_locked = serializers.BooleanField(read_only=True)
    total_lines = serializers.SerializerMethodField()
    
    # Period information (Stocktake belongs to a Period)
    period_id = serializers.SerializerMethodField()
    period_name = serializers.SerializerMethodField()
    period_is_closed = serializers.SerializerMethodField()
    
    # Snapshot data (same as Period - opening/closing stock for all items)
    snapshots = serializers.SerializerMethodField()
    snapshot_ids = serializers.SerializerMethodField()
    
    # Summary fields
    total_items = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    total_counted_value = serializers.SerializerMethodField()
    total_variance_value = serializers.SerializerMethodField()
    # Profitability fields
    total_cogs = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    gross_profit_percentage = serializers.SerializerMethodField()
    pour_cost_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Stocktake
        fields = [
            'id', 'hotel', 'period_start', 'period_end',
            'status', 'is_locked', 'created_at', 'approved_at',
            'approved_by', 'approved_by_name', 'notes',
            # Period connection
            'period_id', 'period_name', 'period_is_closed',
            # Snapshot data (same as period)
            'snapshots', 'snapshot_ids',
            # Stocktake lines (counted data)
            'lines', 'total_lines',
            # Summary
            'total_items', 'total_value', 'total_counted_value',
            'total_variance_value',
            # Profitability
            'total_cogs',
            'total_revenue',
            'gross_profit_percentage',
            'pour_cost_percentage'
        ]
        read_only_fields = ['hotel', 'status', 'approved_at', 'approved_by']
    
    def get_total_cogs(self, obj):
        return obj.total_cogs

    def get_total_revenue(self, obj):
        return obj.total_revenue

    def get_gross_profit_percentage(self, obj):
        return obj.gross_profit_percentage

    def get_pour_cost_percentage(self, obj):
        return obj.pour_cost_percentage

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return (
                f"{obj.approved_by.first_name} "
                f"{obj.approved_by.last_name}"
            ).strip()
        return None

    def get_total_lines(self, obj):
        return obj.lines.count()
    
    def get_period_id(self, obj):
        """Get the Period ID this stocktake belongs to"""
        period = StockPeriod.objects.filter(
            hotel=obj.hotel,
            start_date=obj.period_start,
            end_date=obj.period_end
        ).first()
        return period.id if period else None
    
    def get_period_name(self, obj):
        """Get the Period name (e.g., 'November 2025')"""
        period = StockPeriod.objects.filter(
            hotel=obj.hotel,
            start_date=obj.period_start,
            end_date=obj.period_end
        ).first()
        return period.period_name if period else None
    
    def get_period_is_closed(self, obj):
        """Check if the period is closed"""
        period = StockPeriod.objects.filter(
            hotel=obj.hotel,
            start_date=obj.period_start,
            end_date=obj.period_end
        ).first()
        return period.is_closed if period else False
    
    def get_snapshots(self, obj):
        """
        Get all snapshots for this stocktake's period.
        Same data as Period - shows opening/closing stock for all items.
        """
        period = StockPeriod.objects.filter(
            hotel=obj.hotel,
            start_date=obj.period_start,
            end_date=obj.period_end
        ).first()
        
        if not period:
            return []
        
        snapshots = StockSnapshot.objects.filter(
            period=period
        ).select_related('item', 'item__category').order_by(
            'item__category__code', 'item__name'
        )
        return StockSnapshotNestedSerializer(snapshots, many=True).data
    
    def get_snapshot_ids(self, obj):
        """Get list of all snapshot IDs for this stocktake's period"""
        period = StockPeriod.objects.filter(
            hotel=obj.hotel,
            start_date=obj.period_start,
            end_date=obj.period_end
        ).first()
        
        if not period:
            return []
        
        return list(
            StockSnapshot.objects.filter(period=period)
            .values_list('id', flat=True)
        )
    
    def get_total_items(self, obj):
        """Count of items in this stocktake"""
        return obj.lines.count()
    
    def get_total_value(self, obj):
        """Total expected stock value (calculated from lines)"""
        total = sum(line.expected_value for line in obj.lines.all())
        return str(total)
    
    def get_total_counted_value(self, obj):
        """Total counted stock value (Stock at Cost - matches Excel)"""
        total = sum(line.counted_value for line in obj.lines.all())
        return str(total)
    
    def get_total_variance_value(self, obj):
        """Total variance value (calculated from lines)"""
        total = sum(line.variance_value for line in obj.lines.all())
        return str(total)


class StocktakeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view"""
    is_locked = serializers.BooleanField(read_only=True)
    total_lines = serializers.SerializerMethodField()

    class Meta:
        model = Stocktake
        fields = [
            'id', 'hotel', 'period_start', 'period_end',
            'status', 'is_locked', 'created_at', 'total_lines'
        ]

    def get_total_lines(self, obj):
        return obj.lines.count()


class SaleSerializer(serializers.ModelSerializer):
    """
    Serializer for Sales model.
    Handles sales/consumption tracking independently.
    
    Auto-populates unit_cost and unit_price from StockItem if not provided.
    """
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    category_code = serializers.CharField(
        source='item.category.code', read_only=True
    )
    category_name = serializers.CharField(
        source='item.category.name', read_only=True
    )
    stocktake_period = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    # Make these optional - will be auto-populated from StockItem
    unit_cost = serializers.DecimalField(
        max_digits=10, decimal_places=4, required=False, allow_null=True
    )
    unit_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    
    # Calculated fields from model properties
    gross_profit = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    gross_profit_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    pour_cost_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )

    class Meta:
        model = Sale
        fields = [
            'id', 'stocktake', 'stocktake_period', 'item',
            'item_sku', 'item_name', 'category_code', 'category_name',
            'quantity', 'unit_cost', 'unit_price',
            'total_cost', 'total_revenue',
            'gross_profit', 'gross_profit_percentage', 'pour_cost_percentage',
            'sale_date', 'notes',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'total_cost', 'total_revenue', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        """
        Auto-populate unit_cost and unit_price from StockItem.
        Calculate total_cost and total_revenue automatically.
        
        NEW: Support month parameter - if 'month' is in context,
        use it to set sale_date to first day of that month.
        """
        from datetime import datetime
        
        item = validated_data['item']
        quantity = validated_data['quantity']
        
        # NEW: Handle month parameter from context
        month = self.context.get('month')
        if month:
            # Convert "2025-09" to date(2025, 9, 1)
            year, month_num = map(int, month.split('-'))
            validated_data['sale_date'] = datetime(year, month_num, 1).date()
        
        # Auto-populate unit_cost if not provided
        if 'unit_cost' not in validated_data:
            validated_data['unit_cost'] = item.cost_per_serving
        elif validated_data['unit_cost'] is None:
            validated_data['unit_cost'] = item.cost_per_serving
        
        # Auto-populate unit_price if not provided
        if 'unit_price' not in validated_data:
            validated_data['unit_price'] = item.menu_price
        elif validated_data['unit_price'] is None:
            validated_data['unit_price'] = item.menu_price
        
        # Calculate totals
        unit_cost = validated_data['unit_cost']
        unit_price = validated_data['unit_price']
        
        validated_data['total_cost'] = unit_cost * quantity
        if unit_price:
            validated_data['total_revenue'] = unit_price * quantity
        
        return super().create(validated_data)

    def get_stocktake_period(self, obj):
        """Get stocktake period name for display"""
        if obj.stocktake:
            return (
                f"{obj.stocktake.period_start} to {obj.stocktake.period_end}"
            )
        return None

    def get_created_by_name(self, obj):
        """Get staff full name"""
        if obj.created_by:
            full_name = (
                f"{obj.created_by.first_name} "
                f"{obj.created_by.last_name}"
            ).strip()
            return (
                full_name or obj.created_by.email
                or f"Staff #{obj.created_by.id}"
            )
        return None


class PeriodReopenPermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for PeriodReopenPermission model.
    Manages which staff can reopen closed periods.
    """
    staff_id = serializers.IntegerField(source='staff.id', read_only=True)
    staff_name = serializers.SerializerMethodField()
    staff_email = serializers.CharField(
        source='staff.user.email', read_only=True
    )
    granted_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PeriodReopenPermission
        fields = [
            'id', 'hotel', 'staff', 'staff_id', 'staff_name', 'staff_email',
            'granted_by', 'granted_by_name', 'granted_at',
            'is_active', 'can_grant_to_others', 'notes'
        ]
        read_only_fields = ['granted_by', 'granted_at']
    
    def get_staff_name(self, obj):
        """Get staff member's full name"""
        if obj.staff:
            full_name = (
                f"{obj.staff.first_name} "
                f"{obj.staff.last_name}"
            ).strip()
            return full_name or obj.staff.user.email
        return None
    
    def get_granted_by_name(self, obj):
        """Get name of superuser who granted permission"""
        if obj.granted_by:
            full_name = (
                f"{obj.granted_by.first_name} "
                f"{obj.granted_by.last_name}"
            ).strip()
            return full_name or obj.granted_by.user.email
        return None


class SalesAnalysisSerializer(serializers.Serializer):
    """
    Serializer for combined sales analysis (Stock Items + Cocktails).
    
    FOR ANALYSIS/REPORTING ONLY - does not modify any data.
    Combines stock item sales with cocktail sales for business intelligence.
    
    Structure:
    {
        'period': {...},
        'general_sales': {...},
        'cocktail_sales': {...},
        'combined_sales': {...},
        'breakdown_percentages': {...},
        'category_breakdown': [...]
    }
    """
    # Period information
    period_id = serializers.IntegerField(read_only=True)
    period_name = serializers.CharField(read_only=True)
    period_start = serializers.DateField(read_only=True)
    period_end = serializers.DateField(read_only=True)
    period_is_closed = serializers.BooleanField(read_only=True)
    
    # Stock item sales (from Sale model)
    general_sales = serializers.DictField(read_only=True)
    
    # Cocktail sales (from CocktailConsumption model)
    cocktail_sales = serializers.DictField(read_only=True)
    
    # Combined totals (calculated)
    combined_sales = serializers.DictField(read_only=True)
    
    # Percentage breakdown (stock vs cocktails)
    breakdown_percentages = serializers.DictField(read_only=True)
    
    # Category breakdown (D, B, S, W, M + COCKTAILS)
    category_breakdown = serializers.ListField(read_only=True)
    
    def to_representation(self, instance):
        """
        Convert StockPeriod instance to sales analysis data.
        
        Expected instance format:
        {
            'period': StockPeriod object,
            'include_cocktails': bool (default True),
            'include_category_breakdown': bool (default True)
        }
        """
        from stock_tracker.utils.sales_analysis import (
            combine_sales_data,
            calculate_percentages,
            get_category_breakdown
        )
        from stock_tracker.models import Sale, CocktailConsumption
        from decimal import Decimal
        
        # Extract parameters
        period = instance.get('period')
        include_cocktails = instance.get('include_cocktails', True)
        include_category_breakdown = instance.get(
            'include_category_breakdown', True
        )
        
        # Get matching stocktake
        from stock_tracker.models import Stocktake
        stocktake = Stocktake.objects.filter(
            hotel=period.hotel,
            period_start=period.start_date,
            period_end=period.end_date
        ).first()
        
        # Calculate stock item sales (from Sale model)
        stock_sales = Sale.objects.filter(
            stocktake=stocktake
        ) if stocktake else Sale.objects.none()

        general_revenue = sum(
            sale.total_revenue or Decimal('0') for sale in stock_sales
        )
        general_cost = sum(
            sale.total_cost or Decimal('0') for sale in stock_sales
        )
        general_count = stock_sales.count()
        
        general_sales_data = {
            'revenue': float(general_revenue),
            'cost': float(general_cost),
            'count': general_count,
            'profit': float(general_revenue - general_cost),
            'gp_percentage': (
                round(
                    float(
                        (general_revenue - general_cost) /
                        general_revenue * 100
                    ), 2
                ) if general_revenue > 0 else 0.0
            )
        }
        
        # Calculate cocktail sales (from CocktailConsumption model)
        cocktail_sales_data = {
            'revenue': 0.0,
            'cost': 0.0,
            'count': 0,
            'profit': 0.0,
            'gp_percentage': 0.0
        }
        
        if include_cocktails and stocktake:
            cocktail_consumptions = CocktailConsumption.objects.filter(
                hotel=period.hotel,
                timestamp__gte=period.start_date,
                timestamp__lte=period.end_date
            )
            
            cocktail_revenue = sum(
                consumption.total_revenue or Decimal('0')
                for consumption in cocktail_consumptions
            )
            cocktail_cost = sum(
                consumption.total_cost or Decimal('0')
                for consumption in cocktail_consumptions
            )
            cocktail_count = cocktail_consumptions.count()
            
            cocktail_sales_data = {
                'revenue': float(cocktail_revenue),
                'cost': float(cocktail_cost),
                'count': cocktail_count,
                'profit': float(cocktail_revenue - cocktail_cost),
                'gp_percentage': (
                    round(
                        float(
                            (cocktail_revenue - cocktail_cost) /
                            cocktail_revenue * 100
                        ), 2
                    ) if cocktail_revenue > 0 else 0.0
                )
            }
        
        # Combine sales data
        combined = combine_sales_data(
            general_sales_data, cocktail_sales_data
        )
        
        # Calculate percentages
        percentages = calculate_percentages(
            general_sales_data, cocktail_sales_data
        )
        
        # Get category breakdown
        category_data = []
        if include_category_breakdown:
            category_data = get_category_breakdown(period, include_cocktails)
        
        # Build response
        return {
            'period_id': period.id,
            'period_name': period.period_name,
            'period_start': period.start_date,
            'period_end': period.end_date,
            'period_is_closed': period.is_closed,
            'general_sales': general_sales_data,
            'cocktail_sales': cocktail_sales_data,
            'combined_sales': {
                'total_revenue': float(combined['total_revenue']),
                'total_cost': float(combined['total_cost']),
                'total_count': combined['total_count'],
                'profit': float(combined['profit']),
                'gp_percentage': combined['gp_percentage']
            },
            'breakdown_percentages': percentages,
            'category_breakdown': category_data
        }
