from rest_framework import serializers
from .models import (
    StockCategory, StockItem, Stock, StockInventory, StockItemType,
    StockMovement, StockPeriod, StockPeriodItem
)
from staff.serializers import StaffSerializer


# ----------------------
# STOCK CATEGORY
# ----------------------
class StockCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCategory
        fields = ['id', 'hotel', 'name', 'slug']


# ----------------------
# STOCK ITEM
# ----------------------
class StockItemSerializer(serializers.ModelSerializer):
    is_below_alert = serializers.SerializerMethodField()
    volume_per_unit = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    type = serializers.SerializerMethodField()
    total_available = serializers.SerializerMethodField()

    class Meta:
        model = StockItem
        fields = [
            'id', 'hotel', 'name', 'sku', 'active_stock_item',
            'quantity', 'stock_in_bar', 'total_available',
            'alert_quantity', 'is_below_alert',
            'volume_per_unit', 'unit', 'type',
        ]

    def get_is_below_alert(self, obj):
        return obj.total_available < obj.alert_quantity

    def get_type(self, obj):
        return obj.type.name if obj.type else None

    def get_total_available(self, obj):
        return obj.total_available


# ----------------------
# STOCK INVENTORY
# ----------------------
class StockInventorySerializer(serializers.ModelSerializer):
    item = StockItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        source='item',
        write_only=True
    )

    class Meta:
        model = StockInventory
        fields = ['item', 'item_id', 'quantity']


# ----------------------
# STOCK
# ----------------------
class StockSerializer(serializers.ModelSerializer):
    inventory_lines = StockInventorySerializer(many=True)

    class Meta:
        model = Stock
        fields = ['id', 'hotel', 'category', 'inventory_lines']

    def create(self, validated_data):
        lines_data = validated_data.pop('inventory_lines', [])
        stock = Stock.objects.create(**validated_data)
        for line in lines_data:
            StockInventory.objects.create(
                stock=stock,
                item_id=line['item_id'].id if hasattr(line['item_id'], 'id') else line['item_id'],
                quantity=line['quantity']
            )
        return stock

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('inventory_lines', [])
        instance.category = validated_data.get('category', instance.category)
        instance.save()
        instance.inventory_lines.all().delete()
        for line in lines_data:
            StockInventory.objects.create(
                stock=instance,
                item_id=line['item_id'].id if hasattr(line['item_id'], 'id') else line['item_id'],
                quantity=line['quantity']
            )
        return instance


# ----------------------
# STOCK MOVEMENT
# ----------------------
class StockMovementSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    item = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = ['id', 'hotel', 'item', 'staff_name', 'direction', 'quantity', 'timestamp']

    def get_staff_name(self, obj):
        staff = obj.staff
        if not staff:
            return "—"
        if hasattr(staff, 'username'):
            return getattr(staff, 'username', "—")
        full_name = f"{getattr(staff, 'first_name', '')} {getattr(staff, 'last_name', '')}".strip()
        if full_name:
            return full_name
        user = getattr(staff, 'user', None)
        if user and hasattr(user, 'username'):
            return user.username
        return "—"

    def get_item(self, obj):
        if obj.item:
            return {
                "id": obj.item.id,
                "name": obj.item.name,
                "quantity_storage": obj.item.quantity,
                "quantity_bar": obj.item.stock_in_bar,
            }
        return {"id": None, "name": "—"}


# ----------------------
# STOCK ANALYTICS
# ----------------------
class StockAnalyticsSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    item_name = serializers.CharField()
    opening_storage = serializers.DecimalField(max_digits=10, decimal_places=2)
    opening_bar = serializers.DecimalField(max_digits=10, decimal_places=2)
    added = serializers.DecimalField(max_digits=10, decimal_places=2)
    moved_to_bar = serializers.DecimalField(max_digits=10, decimal_places=2)
    sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    waste = serializers.DecimalField(max_digits=10, decimal_places=2)
    closing_storage = serializers.DecimalField(max_digits=10, decimal_places=2)
    closing_bar = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_closing_stock = serializers.DecimalField(max_digits=10, decimal_places=2)


# ----------------------
# STOCK ITEM TYPE
# ----------------------
class StockItemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockItemType
        fields = ["id", "name", "slug"]


# ----------------------
# STOCK PERIOD ITEM
# ----------------------
class StockPeriodItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)

    class Meta:
        model = StockPeriodItem
        fields = [
            "id", "item", "item_name",
            "opening_storage", "opening_bar",
            "added", "moved_to_bar", "sales", "waste",
            "closing_storage", "closing_bar", "total_closing_stock",
        ]


# ----------------------
# STOCK PERIOD
# ----------------------
class StockPeriodSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    items = StockPeriodItemSerializer(many=True, read_only=True)

    class Meta:
        model = StockPeriod
        fields = ["id", "hotel", "hotel_name", "start_date", "end_date", "created_at", "items"]
        read_only_fields = ["hotel", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        period = StockPeriod.objects.create(**validated_data)
        for item_data in items_data:
            StockPeriodItem.objects.create(period=period, **item_data)
        return period
