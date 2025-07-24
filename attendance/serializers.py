from rest_framework import serializers
from .models import (
    StaffFace, ClockLog, RosterPeriod, StaffRoster,
    StaffAvailability, ShiftTemplate, RosterRequirement
)


class StaffFaceSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    hotel_slug = serializers.CharField(source='hotel.slug', read_only=True)

    class Meta:
        model = StaffFace
        fields = ['id', 'staff', 'staff_name', 'hotel', 'hotel_slug', 'image', 'encoding', 'created_at']

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"


class ClockLogSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    hotel_slug = serializers.CharField(source='hotel.slug', read_only=True)

    class Meta:
        model = ClockLog
        fields = [
            'id', 'staff', 'staff_name', 'hotel', 'hotel_slug',
            'time_in', 'time_out', 'verified_by_face', 'location_note', 'auto_clock_out'
        ]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"


class RosterPeriodSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RosterPeriod
        fields = ['id', 'title', 'hotel', 'start_date', 'end_date', 'created_by', 'created_by_name', 'published']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return None


class StaffRosterSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    period_title = serializers.CharField(source='period.title', read_only=True)

    class Meta:
        model = StaffRoster
        fields = [
            'id', 'hotel', 'staff', 'staff_name', 'department', 'period', 'period_title',
            'shift_date', 'shift_start', 'shift_end',
            'break_start', 'break_end',
            'shift_type', 'is_split_shift', 'is_night_shift',
            'expected_hours', 'approved_by', 'notes',
            'created_at', 'updated_at'
        ]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"


class StaffAvailabilitySerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = StaffAvailability
        fields = ['id', 'staff', 'staff_name', 'date', 'available', 'reason']

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"


class ShiftTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTemplate
        fields = ['id', 'hotel', 'name', 'start_time', 'end_time', 'is_night']


class RosterRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = RosterRequirement
        fields = ['id', 'period', 'department', 'role', 'date', 'required_count']
        read_only_fields = ['id', 'created_at', 'updated_at']