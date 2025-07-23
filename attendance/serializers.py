from rest_framework import serializers
from .models import StaffFace, ClockLog


class StaffFaceSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    hotel_slug = serializers.CharField(source='hotel.slug', read_only=True)

    class Meta:
        model = StaffFace
        fields = ['id', 'staff', 'staff_name', 'hotel', 'hotel_slug', 'image', 'created_at']

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"


class ClockLogSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    hotel_slug = serializers.CharField(source='hotel.slug', read_only=True)

    class Meta:
        model = ClockLog
        fields = [
            'id', 'staff', 'staff_name', 'hotel', 'hotel_slug',
            'time_in', 'time_out', 'verified_by_face', 'location_note'
        ]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"
