from rest_framework import serializers
from .models import Booking, BookingCategory


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
