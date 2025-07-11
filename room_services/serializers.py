from rest_framework import serializers
from .models import (
    RoomServiceItem, Order, OrderItem,
    BreakfastItem, BreakfastOrder, BreakfastOrderItem
)
from hotel.models import Hotel
from notifications.utils import notify_porters_of_room_service_order
import logging

logger = logging.getLogger(__name__)

# RoomServiceItem Serializer
class RoomServiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomServiceItem
        fields = '__all__'  # includes hotel, is_on_stock, etc.


# OrderItem Serializer (nested)
class OrderItemSerializer(serializers.ModelSerializer):
    item = RoomServiceItemSerializer(read_only=True)
    item_price = serializers.DecimalField(source='item.price', max_digits=8, decimal_places=2, read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=RoomServiceItem.objects.all(),
        source='item',
        write_only=True
    )
    hotel = serializers.PrimaryKeyRelatedField(
        queryset=Hotel.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'item', 'item_id','item_price', 'quantity', 'notes', 'hotel']


# Order Serializer with nested items
class OrderSerializer(serializers.ModelSerializer):
    hotel = serializers.PrimaryKeyRelatedField(queryset=Order.objects.values_list('hotel', flat=True), required=False, allow_null=True)
    items = OrderItemSerializer(source='orderitem_set', many=True)
    total_price = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = ['id', 'hotel', 'room_number', 'status', 'created_at','total_price', 'items']

    def get_total_price(self, obj):
        return obj.total_price
    
    def create(self, validated_data):
        items_data = validated_data.pop('orderitem_set')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            # Ensure hotel is set on OrderItem from parent Order if missing
            if not item_data.get('hotel'):
                item_data['hotel'] = order.hotel
            OrderItem.objects.create(order=order, **item_data)

        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('orderitem_set', [])
        instance.room_number = validated_data.get('room_number', instance.room_number)
        instance.status = validated_data.get('status', instance.status)
        instance.hotel = validated_data.get('hotel', instance.hotel)
        instance.save()

        if items_data:
            instance.orderitem_set.all().delete()
            for item_data in items_data:
                if not item_data.get('hotel'):
                    item_data['hotel'] = instance.hotel
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

    def validate_item(self, item):
        hotel = self.context.get('hotel')
        if hotel and item.hotel_id != hotel.id:
            raise serializers.ValidationError("This breakfast item does not belong to your hotel.")
        return item


# BreakfastOrder Serializer with nested items
class BreakfastOrderSerializer(serializers.ModelSerializer):
    hotel = serializers.PrimaryKeyRelatedField(
        queryset=Hotel.objects.all(),
        required=False,
        allow_null=True,
        default=None
    )
    delivery_time = serializers.CharField(allow_blank=True, required=False)
    items = BreakfastOrderItemSerializer(source='breakfastorderitem_set', many=True)

    class Meta:
        model = BreakfastOrder
        fields = ['id', 'hotel', 'room_number', 'status', 'created_at', 'delivery_time', 'items']

    def validate(self, data):
        if not data.get('hotel'):
            hotel = self.context.get('hotel')
            if hotel:
                data['hotel'] = hotel
        return data

    
    def create(self, validated_data):
        items_data = validated_data.pop('breakfastorderitem_set', [])

        # Ensure hotel is always assigned
        hotel = self.context.get('hotel')
        if not hotel:
            raise serializers.ValidationError("Missing hotel context")
        validated_data['hotel'] = hotel

        order = BreakfastOrder.objects.create(**validated_data)

        for item_data in items_data:
            BreakfastOrderItem.objects.create(order=order, **item_data)

        return order

    
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('breakfastorderitem_set', [])
        instance.room_number = validated_data.get('room_number', instance.room_number)
        instance.status = validated_data.get('status', instance.status)
        instance.hotel = validated_data.get('hotel', instance.hotel)
        instance.delivery_time = validated_data.get('delivery_time', instance.delivery_time)
        instance.save()

        if items_data:
            instance.breakfastorderitem_set.all().delete()
            for item_data in items_data:
                # ❌ Do not pass 'hotel'
                BreakfastOrderItem.objects.create(order=instance, **item_data)
        return instance
