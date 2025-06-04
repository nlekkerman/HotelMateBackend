from rest_framework import serializers
from .models import Booking, BookingCategory, Seats


class BookingCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = BookingCategory
        fields = ['id', 'name', 'parent', 'subcategories']

    def get_subcategories(self, obj):
        children = obj.subcategories.all()
        return BookingCategorySerializer(children, many=True).data


class BookingSerializer(serializers.ModelSerializer):
    category_detail = BookingCategorySerializer(source='category', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'hotel', 'name', 'category', 'category_detail', 'date', 'time', 'note', 'created_at']


class SeatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seats
        fields = ['total', 'adults', 'children', 'infants']

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