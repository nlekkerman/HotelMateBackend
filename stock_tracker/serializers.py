from rest_framework import serializers
from .models import StockCategory, StockItem, Stock, StockInventory, StockMovement
from staff.serializers import StaffSerializer  # Assuming you have a StaffSerializer defined

class StockCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCategory
        fields = ['id', 'hotel', 'name', 'slug']

class StockItemSerializer(serializers.ModelSerializer):
    is_below_alert = serializers.SerializerMethodField()

    class Meta:
        model = StockItem
        fields = [
            'id',
            'hotel',
            'name',
            'sku',
            'active_stock_item', 
            'quantity',
            'alert_quantity',  # NEW FIELD
            'is_below_alert',  # Optional: boolean for alert status
        ]

    def get_is_below_alert(self, obj):
        return obj.quantity < obj.alert_quantity


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
    item = serializers.SerializerMethodField()  # or a nested serializer returning name

    class Meta:
        model = StockMovement
        fields = ['id', 'hotel', 'stock', 'item', 'staff_name', 'direction', 'quantity', 'timestamp']

    def get_staff_name(self, obj):
        staff = obj.staff
        if not staff:
            return "—"

        # If 'staff' is a User instance (has no attribute 'user'), use username directly
        if hasattr(staff, 'username') and not hasattr(staff, 'user'):
            # staff is already a User instance
            return staff.username or "—"

        # If staff is Staff instance
        full_name = f"{getattr(staff, 'first_name', '')} {getattr(staff, 'last_name', '')}".strip()
        if full_name:
            return full_name

        # fallback to related user username if exists
        user = getattr(staff, 'user', None)
        if user and hasattr(user, 'username'):
            return user.username

        return "—"

    

    def get_item(self, obj):
        # Return only the name of the item, or a dict with name
        if obj.item:
            return {"name": obj.item.name}
        return {"name": "—"}
