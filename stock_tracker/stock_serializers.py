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
    gp_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = StockItem
        fields = [
            'id', 'hotel', 'category', 'category_name', 'code',
            'description', 'size', 'uom', 'unit_cost', 'selling_price',
            'current_qty', 'base_unit', 'gp_percentage'
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    item_code = serializers.CharField(source='item.code', read_only=True)
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = [
            'id', 'hotel', 'item', 'item_code', 'movement_type',
            'quantity', 'unit_cost', 'reference', 'notes',
            'staff', 'staff_name', 'timestamp'
        ]
        read_only_fields = ['timestamp']

    def get_staff_name(self, obj):
        if obj.staff:
            return f"{obj.staff.first_name} {obj.staff.last_name}".strip()
        return None


class StocktakeLineSerializer(serializers.ModelSerializer):
    item_code = serializers.CharField(source='item.code', read_only=True)
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
            'id', 'stocktake', 'item', 'item_code', 'item_description',
            'category_name', 'opening_qty', 'purchases', 'sales', 'waste',
            'transfers_in', 'transfers_out', 'adjustments',
            'counted_full_units', 'counted_partial_units',
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
        read_only_fields = ['status', 'approved_at', 'approved_by']

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
