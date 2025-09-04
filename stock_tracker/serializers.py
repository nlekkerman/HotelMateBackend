from rest_framework import serializers
from .models import StockCategory, StockItem, Stock, StockInventory, StockItemType, StockMovement
from staff.serializers import StaffSerializer

class StockCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCategory
        fields = ['id', 'hotel', 'name', 'slug']


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
            'id',
            'hotel',
            'name',
            'sku',
            'active_stock_item', 
            'quantity',
            'stock_in_bar',
            'total_available',
            'alert_quantity',
            'is_below_alert',
            'volume_per_unit',
            'unit',
            'type',
        ]

    def get_is_below_alert(self, obj):
        return obj.total_available < obj.alert_quantity

    def get_type(self, obj):
        return obj.type.name if obj.type else None

    def get_total_available(self, obj):
        return obj.total_available


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


class StockSerializer(serializers.ModelSerializer):
    # drop `source=`—DRF will use the field name by default
    inventory_lines = StockInventorySerializer(
        many=True,
        help_text="List of items + quantities in this stock"
    )

    class Meta:
        model = Stock
        fields = ['id', 'hotel', 'category', 'inventory_lines']

    def create(self, validated_data):
        lines_data = validated_data.pop('inventory_lines', [])
        stock = Stock.objects.create(**validated_data)
        for line in lines_data:
            # here, line['item'] must be an ID
            StockInventory.objects.create(
                stock=stock,
                item_id=line['item_id'],
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
                item_id=line['item_id'],
                quantity=line['quantity']
            )
        return instance


class StockMovementSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    item = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = [
            'id',
            'hotel',
            'item',
            'staff_name',
            'direction',
            'quantity',
            'timestamp',
        ]

    def get_staff_name(self, obj):
        staff = obj.staff
        if not staff:
            return "—"

        # User instance directly
        if hasattr(staff, 'username') and not hasattr(staff, 'user'):
            return staff.username or "—"

        # Staff model with first/last name
        full_name = f"{getattr(staff, 'first_name', '')} {getattr(staff, 'last_name', '')}".strip()
        if full_name:
            return full_name

        # fallback → related user.username
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
                "quantity_bar": obj.item.stock_in_bar,  # ✅ NEW
            }
        return {"id": None, "name": "—"}


class StockAnalyticsSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    item_name = serializers.CharField()
    opening_stock = serializers.DecimalField(max_digits=10, decimal_places=2)
    added = serializers.DecimalField(max_digits=10, decimal_places=2)
    moved_to_bar = serializers.DecimalField(max_digits=10, decimal_places=2)
    closing_stock = serializers.DecimalField(max_digits=10, decimal_places=2)


class StockItemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockItemType
        fields = ["id", "name", "slug"]