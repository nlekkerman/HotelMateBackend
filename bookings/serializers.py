from rest_framework import serializers
from .models import Booking, BookingCategory, Seats, BookingSubcategory, Restaurant

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

# 1) Nested serializer for Restaurant to expose id & name
class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["id", "name"]

# 2) Nested serializer for Seats
class SeatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seats
        fields = ["total", "adults", "children", "infants"]
# 3) Your BookingSerializer, fixed:
class BookingSerializer(serializers.ModelSerializer):
    # Keep your existing nested category detail
    category_detail = BookingCategorySerializer(source="category", read_only=True)
    # Add nested restaurant (id + name)
    restaurant = RestaurantSerializer(read_only=True)
    # Add nested seats
    seats = SeatsSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "hotel",
            "category",
            "category_detail",
            "date",
            "time",
            "note",
            "created_at",
            "restaurant",
            "seats",
        ]

class BookingCreateSerializer(serializers.ModelSerializer):
    seats = SeatsSerializer()

    class Meta:
        model = Booking
        fields = ['hotel', 'category', 'restaurant', 'date', 'time', 'note', 'seats']

    def create(self, validated_data):
        seats_data = validated_data.pop('seats')
        booking = Booking.objects.create(**validated_data)
        Seats.objects.create(booking=booking, **seats_data)
        return booking

