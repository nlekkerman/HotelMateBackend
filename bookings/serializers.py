from rest_framework import serializers
from django.shortcuts import get_object_or_404
from datetime import datetime

from .models import (Booking, BookingCategory, Seats, BookingSubcategory,
                     Restaurant, RestaurantBlueprint, BlueprintArea,
                     DiningTable, BlueprintObjectType, BlueprintObject,
                     BookingTable,
                     TableShape)

from rooms.serializers import RoomSerializer
from guests.serializers import GuestSerializer
class BookingSubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingSubcategory
        fields = ["id", "name", "slug"]


# 2) Now we serialize BookingCategory and nest the subcategory:
class BookingCategorySerializer(serializers.ModelSerializer):
    # nest the one BookingSubcategory instance as a dict
    subcategory = BookingSubcategorySerializer(read_only=True)

    class Meta:
        model = BookingCategory
        fields = ["id", "name", "hotel", "subcategory"]



class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            "id",
            "name",
            "slug",
            "hotel",
            "capacity",
            "description",
            "opening_time",
            "closing_time",
            "is_active",
            "max_bookings_per_hour",
            "max_group_size",
            "taking_bookings",
        ]
        read_only_fields = ["id", "slug"]  # slug can be auto-generated if you like


# 2) Nested serializer for Seats
class SeatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seats
        fields = ["total", "adults", "children", "infants"]


class DiningTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningTable
        fields = '__all__'

    def validate(self, data):
        shape = data.get('shape')
        width = data.get('width')
        height = data.get('height')
        radius = data.get('radius')

        if shape in [TableShape.RECT, TableShape.OVAL]:
            if width is None or height is None:
                raise serializers.ValidationError("RECT/OVAL tables require width and height.")
        elif shape == TableShape.CIRCLE:
            if radius is None:
                raise serializers.ValidationError("CIRCLE tables require a radius.")
        return data

class BookingTableSerializer(serializers.ModelSerializer):
    table = DiningTableSerializer(read_only=True)
    table_id = serializers.PrimaryKeyRelatedField(
        queryset=DiningTable.objects.all(), write_only=True
    )

    class Meta:
        model = BookingTable
        fields = ['id', 'booking', 'table', 'table_id']

# 3) Your BookingSerializer, fixed:
class BookingSerializer(serializers.ModelSerializer):
    category_detail = BookingCategorySerializer(source="category", read_only=True)
    restaurant = RestaurantSerializer(read_only=True)
    seats = SeatsSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    guest = GuestSerializer(read_only=True)
    booking_tables = BookingTableSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "hotel",
            "category",
            "category_detail",
            "date",
            "start_time",
            "end_time",
            "note",
            "created_at",
            "restaurant",
            "voucher_code",
            "seats",
            "room",
            "guest",
            "seen",
            "booking_tables",
        ]

# -------------------------
# Booking (Create/Update)
# -------------------------
class BookingCreateSerializer(serializers.ModelSerializer):
  
    adults = serializers.IntegerField(write_only=True, required=False, default=1)
    children = serializers.IntegerField(write_only=True, required=False, default=0)
    infants = serializers.IntegerField(write_only=True, required=False, default=0)

    class Meta:
        model = Booking
        fields = [
            'hotel', 'category', 'restaurant', 'voucher_code',
            'date', 'start_time', 'end_time', 'note', 'room', 'guest',
            'adults', 'children', 'infants'
        ]

    
    def create(self, validated_data):
        tables = validated_data.pop('assigned_tables', [])

        # Seats
        seats_data = {
            'adults': validated_data.pop('adults', 0),
            'children': validated_data.pop('children', 0),
            'infants': validated_data.pop('infants', 0),
        }
        seats_data['total'] = seats_data['adults'] + seats_data['children'] + seats_data['infants']

        # Auto-assign guest from room
        room = validated_data.get("room")
        if "guest" not in validated_data and room:
            validated_data["guest"] = room.guests.first()

        booking = Booking.objects.create(**validated_data)
        Seats.objects.create(booking=booking, **seats_data)

        for table in tables:
            BookingTable.objects.create(booking=booking, table=table)

        return booking

class BlueprintAreaSerializer(serializers.ModelSerializer):
    tables = DiningTableSerializer(many=True, read_only=True)

    class Meta:
        model = BlueprintArea
        fields = ['id', 'name', 'x', 'y', 'width', 'height', 'z_index', 'tables']


class RestaurantBlueprintSerializer(serializers.ModelSerializer):
    areas = BlueprintAreaSerializer(many=True, read_only=True)
    background_image = serializers.ImageField(required=False, allow_null=True)
    restaurant_slug = serializers.CharField(source='restaurant.slug', read_only=True)
    hotel_slug = serializers.CharField(source='restaurant.hotel.slug', read_only=True)
    restaurant = serializers.PrimaryKeyRelatedField(
        queryset=Restaurant.objects.all(),
        write_only=True,
        required=False
    )
    class Meta:
        model = RestaurantBlueprint
        fields = [
            "id",
            "hotel_slug",
            "restaurant",
            "restaurant_slug", 
            "width",
            "height",
            "grid_size",
            "background_image",
            "areas",
        ]

# -------------------------
# BlueprintObjectType Serializer
# -------------------------
class BlueprintObjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlueprintObjectType
        fields = ['id', 'name', 'icon', 'default_width', 'default_height']
        read_only_fields = ['id']


# -------------------------
# BlueprintObject Serializer
# -------------------------
class BlueprintObjectSerializer(serializers.ModelSerializer):
    type = BlueprintObjectTypeSerializer(read_only=True)
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=BlueprintObjectType.objects.all(), write_only=True
    )
    blueprint_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = BlueprintObject
        fields = ['id', 'blueprint_id', 'type', 'type_id', 'name', 'x', 'y', 'width', 'height', 'rotation', 'z_index']
        read_only_fields = ['id']

    def create(self, validated_data):
        blueprint_id = validated_data.pop('blueprint_id')
        blueprint = get_object_or_404(RestaurantBlueprint, pk=blueprint_id)
        validated_data['blueprint'] = blueprint

        obj_type = validated_data.pop('type_id')
        validated_data['type'] = obj_type

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'blueprint_id' in validated_data:
            blueprint_id = validated_data.pop('blueprint_id')
            instance.blueprint = get_object_or_404(RestaurantBlueprint, pk=blueprint_id)

        if 'type_id' in validated_data:
            instance.type = validated_data.pop('type_id')

        return super().update(instance, validated_data)



