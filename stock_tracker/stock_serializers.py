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
        return obj.items.count()


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for stock locations (Bar, Cellar, Storage, etc.)"""
    class Meta:
        model = Location
        fields = ['id', 'hotel', 'name', 'location_type', 'description', 'is_active']
        read_only_fields = ['hotel']


class StockPeriodSerializer(serializers.ModelSerializer):
    """Serializer for stock periods (Weekly, Monthly, Quarterly, Yearly)"""
    period_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = StockPeriod
        fields = [
            'id', 'hotel', 'period_type', 'start_date', 'end_date',
            'year', 'month', 'quarter', 'week', 'period_name'
        ]
        read_only_fields = ['hotel', 'period_name']


class StockItemSerializer(serializers.ModelSerializer):
    """Serializer for stock items with profitability calculations"""
    category_code = serializers.CharField(source='category.code', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    # Calculated fields from model properties
    total_units = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
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
    gp_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    markup_percentage = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )
    pour_cost_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )

    class Meta:
        model = StockItem
        fields = [
            'id', 'hotel', 'sku', 'name', 
            'category', 'category_code', 'category_name',
            'size', 'size_value', 'size_unit', 'uom', 
            'unit_cost', 'current_full_units', 'current_partial_units',
            'menu_price', 'created_at', 'updated_at',
            # Calculated fields
            'total_units', 'total_stock_value', 'cost_per_serving',
            'gross_profit_per_serving', 'gp_percentage', 
            'markup_percentage', 'pour_cost_percentage'
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
    total_units = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    
    class Meta:
        model = StockSnapshot
        fields = [
            'id', 'hotel', 'item', 'item_sku', 'item_name', 
            'category_code', 'period', 'period_name',
            'closing_full_units', 'closing_partial_units', 'total_units',
            'unit_cost', 'cost_per_serving', 'closing_stock_value',
            'created_at'
        ]
        read_only_fields = ['hotel', 'created_at']


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for stock movements (purchases, sales, waste, transfers, adjustments)"""
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = [
            'id', 'hotel', 'item', 'item_sku', 'item_name', 
            'movement_type', 'full_units', 'partial_units', 'total_units',
            'unit_cost', 'total_value', 'reference', 'notes',
            'staff', 'staff_name', 'timestamp'
        ]
        read_only_fields = ['hotel', 'timestamp', 'staff', 'total_value']

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
    
    # Calculated fields
    counted_total = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    expected_total = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    variance_units = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    counted_value = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    expected_value = serializers.DecimalField(
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
            'opening_full_units', 'opening_partial_units',
            'purchases_full', 'purchases_partial',
            'sales_full', 'sales_partial',
            'waste_full', 'waste_partial',
            'counted_full_units', 'counted_partial_units',
            'counted_total', 'expected_total', 'variance_units',
            'unit_cost', 'counted_value', 'expected_value', 'variance_value'
        ]
        read_only_fields = [
            'opening_full_units', 'opening_partial_units',
            'purchases_full', 'purchases_partial',
            'sales_full', 'sales_partial',
            'waste_full', 'waste_partial', 'unit_cost'
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
