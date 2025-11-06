from rest_framework import serializers
from .models import (
    StockCategory,
    StockItem,
    StockMovement,
    Stocktake,
    StocktakeLine
)


class StockCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCategory
        fields = ['id', 'hotel', 'name', 'sort_order']


class StockItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )
    bin_name = serializers.CharField(
        source='bin.name',
        read_only=True
    )
    gp_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    is_below_par = serializers.BooleanField(read_only=True)
    pour_cost = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        read_only=True
    )
    pour_cost_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    profit_per_serving = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        read_only=True
    )
    profit_margin_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = StockItem
        fields = [
            'id', 'hotel', 'category', 'category_name', 'sku', 'name',
            'description', 'product_type', 'subtype', 'tag',
            'size', 'size_value', 'size_unit', 'uom', 'base_unit',
            'unit_cost', 'cost_per_base', 'case_cost', 'selling_price',
            'current_qty', 'par_level', 'bin', 'bin_name',
            'vendor', 'country', 'region', 'subregion', 'producer', 'vineyard',
            'abv_percent', 'vintage', 'unit_upc', 'case_upc',
            'serving_size', 'serving_unit', 'menu_price',
            'active', 'hide_on_menu',
            'gp_percentage', 'is_below_par', 'pour_cost',
            'pour_cost_percentage', 'profit_per_serving',
            'profit_margin_percentage'
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = [
            'id', 'hotel', 'item', 'item_sku', 'item_name', 'movement_type',
            'quantity', 'unit_cost', 'reference', 'notes',
            'staff', 'staff_name', 'timestamp'
        ]
        # Make 'staff' read-only so the API sets it from the authenticated user
        # and clients don't need to (and cannot) include an arbitrary staff PK.
        read_only_fields = ['timestamp', 'staff']

    def get_staff_name(self, obj):
        """Get staff full name from Staff model"""
        if obj.staff:
            full_name = (
                f"{obj.staff.first_name} {obj.staff.last_name}".strip()
            )
            # Fallback to email or ID if names not set
            return full_name or obj.staff.email or f"Staff #{obj.staff.id}"
        return None


class StocktakeLineSerializer(serializers.ModelSerializer):
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_description = serializers.CharField(
        source='item.description',
        read_only=True
    )
    category_name = serializers.CharField(
        source='item.category.name',
        read_only=True
    )
    counted_qty = serializers.DecimalField(
        max_digits=15,
        decimal_places=4,
        read_only=True
    )
    expected_qty = serializers.DecimalField(
        max_digits=15,
        decimal_places=4,
        read_only=True
    )
    variance_qty = serializers.DecimalField(
        max_digits=15,
        decimal_places=4,
        read_only=True
    )
    expected_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=4,
        read_only=True
    )
    counted_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=4,
        read_only=True
    )
    variance_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=4,
        read_only=True
    )

    class Meta:
        model = StocktakeLine
        fields = [
            'id', 'stocktake', 'item', 'item_sku', 'item_name',
            'item_description', 'category_name', 'opening_qty',
            'purchases', 'sales', 'waste', 'transfers_in', 'transfers_out',
            'adjustments', 'counted_full_units', 'counted_partial_units',
            'counted_qty', 'expected_qty', 'variance_qty',
            'valuation_cost', 'expected_value', 'counted_value',
            'variance_value'
        ]
        read_only_fields = [
            'opening_qty', 'purchases', 'sales', 'waste',
            'transfers_in', 'transfers_out', 'adjustments',
            'valuation_cost'
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
