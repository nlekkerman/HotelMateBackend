from rest_framework import serializers
from .models import StaffFace, ClockLog


class StaffFaceSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.__str__', read_only=True)
    hotel_slug = serializers.CharField(source='hotel.slug', read_only=True)

    class Meta:
        model = StaffFace
        fields = ['id', 'staff', 'staff_name', 'hotel', 'hotel_slug', 'image', 'created_at']


class ClockLogSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.__str__', read_only=True)
    hotel_slug = serializers.CharField(source='hotel.slug', read_only=True)

    class Meta:
        model = ClockLog
        fields = ['id', 'staff', 'staff_name', 'hotel', 'hotel_slug', 'time_in', 'time_out', 'verified_by_face', 'location_note']
