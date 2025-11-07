from rest_framework import serializers
from .models import (
    StockCategory,
    StockItem,
    StockPeriod,
    StockSnapshot,
    StockMovement,
    Location,
    Stocktake,
    StocktakeLine
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
    
    # Profitability metrics from item
    gp_percentage = serializers.SerializerMethodField()
    markup_percentage = serializers.SerializerMethodField()
    pour_cost_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = StockSnapshot
        fields = [
            'id', 'item', 'closing_full_units', 'closing_partial_units',
            'total_servings', 'closing_stock_value',
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
    
    class Meta:
        model = StockPeriod
        fields = [
            'id', 'hotel', 'period_type', 'start_date', 'end_date',
            'year', 'month', 'quarter', 'week', 'period_name', 'is_closed'
        ]
        read_only_fields = ['hotel', 'period_name']


class StockPeriodDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for single period with all snapshots
    (like Stocktake)
    """
    period_name = serializers.CharField(read_only=True)
    snapshots = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    
    class Meta:
        model = StockPeriod
        fields = [
            'id', 'hotel', 'period_type', 'start_date', 'end_date',
            'year', 'month', 'quarter', 'week', 'period_name', 'is_closed',
            'snapshots', 'total_items', 'total_value'
        ]
        read_only_fields = ['hotel', 'period_name']
    
    def get_snapshots(self, obj):
        """Get all snapshots for this period"""
        snapshots = StockSnapshot.objects.filter(
            period=obj
        ).select_related('item', 'item__category').order_by(
            'item__category__code', 'item__name'
        )
        return StockSnapshotNestedSerializer(snapshots, many=True).data
    
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
    (purchases, sales, waste, transfers, adjustments)
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
    """Serializer for stocktake lines"""
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    category_code = serializers.CharField(
        source='item.category.code', read_only=True
    )
    category_name = serializers.CharField(
        source='item.category.name', read_only=True
    )
    
    # Calculated fields from model properties
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

    class Meta:
        model = StocktakeLine
        fields = [
            'id', 'stocktake', 'item', 'item_sku', 'item_name',
            'category_code', 'category_name',
            'opening_qty', 'purchases', 'sales', 'waste',
            'transfers_in', 'transfers_out', 'adjustments',
            'counted_full_units', 'counted_partial_units',
            'counted_qty', 'expected_qty', 'variance_qty',
            'valuation_cost', 'expected_value', 'counted_value',
            'variance_value'
        ]
        read_only_fields = [
            'opening_qty', 'purchases', 'sales', 'waste',
            'transfers_in', 'transfers_out', 'adjustments', 'valuation_cost'
        ]


class StocktakeSerializer(serializers.ModelSerializer):
    lines = StocktakeLineSerializer(many=True, read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    is_locked = serializers.BooleanField(read_only=True)
    total_lines = serializers.SerializerMethodField()

    class Meta:
        model = Stocktake
        fields = [
            'id', 'hotel', 'period_start', 'period_end',
            'status', 'is_locked', 'created_at', 'approved_at',
            'approved_by', 'approved_by_name', 'notes',
            'lines', 'total_lines'
        ]
        read_only_fields = ['hotel', 'status', 'approved_at', 'approved_by']

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return (
                f"{obj.approved_by.first_name} "
                f"{obj.approved_by.last_name}"
            ).strip()
        return None

    def get_total_lines(self, obj):
        return obj.lines.count()


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
