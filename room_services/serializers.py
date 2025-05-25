from rest_framework import serializers
from .models import (
    RoomServiceItem, Order, OrderItem,
    BreakfastItem, BreakfastOrder, BreakfastOrderItem
)

# RoomServiceItem Serializer
class RoomServiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomServiceItem
        fields = '__all__'

# OrderItem Serializer (nested)
class OrderItemSerializer(serializers.ModelSerializer):
    item = RoomServiceItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=RoomServiceItem.objects.all(),
        source='item',
        write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'item', 'item_id', 'quantity', 'notes']

# Order Serializer with nested items
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True)

    class Meta:
        model = Order
        fields = ['id', 'room_number', 'status', 'created_at', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('orderitem_set')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('orderitem_set', [])
        instance.room_number = validated_data.get('room_number', instance.room_number)
        instance.status = validated_data.get('status', instance.status)
        instance.save()

        if items_data:
            instance.orderitem_set.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)

        return instance

# BreakfastItem Serializer
class BreakfastItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakfastItem
        fields = '__all__'

# BreakfastOrderItem Serializer (nested)
class BreakfastOrderItemSerializer(serializers.ModelSerializer):
    item = BreakfastItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=BreakfastItem.objects.all(),
        source='item',
        write_only=True
    )

    class Meta:
        model = BreakfastOrderItem
        fields = ['id', 'item', 'item_id', 'quantity']

# BreakfastOrder Serializer with nested items
class BreakfastOrderSerializer(serializers.ModelSerializer):
    items = BreakfastOrderItemSerializer(source='breakfastorderitem_set', many=True)

    class Meta:
        model = BreakfastOrder
        fields = ['id', 'room_number', 'status', 'created_at', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('breakfastorderitem_set')
        order = BreakfastOrder.objects.create(**validated_data)
        for item_data in items_data:
            BreakfastOrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('breakfastorderitem_set', [])
        instance.room_number = validated_data.get('room_number', instance.room_number)
        instance.status = validated_data.get('status', instance.status)
        instance.save()

        if items_data:
            instance.breakfastorderitem_set.all().delete()
            for item_data in items_data:
                BreakfastOrderItem.objects.create(order=instance, **item_data)

        return instance
