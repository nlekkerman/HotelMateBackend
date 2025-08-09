from datetime import datetime, timedelta, time as dtime
from staff.models import Department, Role
from django.utils.timezone import make_aware
from rest_framework import serializers
from staff.serializers import StaffMinimalSerializer, DepartmentSerializer
from .models import (
    StaffFace, ClockLog, RosterPeriod, StaffRoster,
    StaffAvailability, ShiftTemplate, RosterRequirement,
    ShiftLocation, DailyPlan, DailyPlanEntry,
)


# ─────────────────────────────
# Face / Clock
# ─────────────────────────────

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


# ─────────────────────────────
# Roster
# ─────────────────────────────

class RosterPeriodSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RosterPeriod
        fields = [
            'id', 'title', 'hotel', 'start_date', 'end_date',
            'created_by', 'created_by_name', 'published'
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return None


class ShiftLocationSerializer(serializers.ModelSerializer):
    hotel = serializers.PrimaryKeyRelatedField(read_only=True)
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    hotel_slug = serializers.SlugRelatedField(
        source="hotel", slug_field="slug", read_only=True
    )

    class Meta:
        model = ShiftLocation
        fields = ["id", "name", "color", "hotel", "hotel_name", "hotel_slug"]
        read_only_fields = ["hotel", "hotel_name", "hotel_slug"]


class StaffRosterSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField(read_only=True)
    period_title = serializers.CharField(source='period.title', read_only=True)
    location = ShiftLocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=ShiftLocation.objects.all(),
        source="location",
        write_only=True,
        required=False,
        allow_null=True
    )
    department = serializers.SlugRelatedField(
        queryset=Department.objects.all(),
        slug_field='slug',
        required=True,
    )
    department_name = serializers.CharField(source='department.name', read_only=True)
    class Meta:
        model = StaffRoster
        fields = [
            'id', 'hotel', 'staff', 'staff_name', 'department', 'period', 'period_title',
            'shift_date', 'shift_start', 'shift_end',
            'break_start', 'break_end', 'department', 'department_name',
            'shift_type', 'is_split_shift', 'is_night_shift',
            'expected_hours', 'approved_by', 'notes',
            'created_at', 'updated_at', 'location', 'location_id'
        ]
        extra_kwargs = {
            'hotel': {'required': True},
            'staff': {'required': True},
            'department': {'required': True},
            'period': {'required': True},
            'shift_date': {'required': True},
            'shift_start': {'required': True},
            'shift_end': {'required': True},
            'approved_by': {'read_only': True},  # set in create/update
            'break_start': {'required': False, 'allow_null': True},
            'break_end': {'required': False, 'allow_null': True},
            'expected_hours': {'required': False, 'allow_null': True},
            'notes': {'required': False, 'allow_blank': True},
        }

    # ---------- helpers ----------

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}" if obj.staff else None

    def _calc_expected_hours(self, data):
        """
        Calculate total worked hours (as Decimal hours) considering night shift wrap
        and optional break deduction.
        """
        shift_date = data['shift_date']
        start = data['shift_start']
        end = data['shift_end']

        # Build datetimes
        start_dt = datetime.combine(shift_date, start)
        end_dt = datetime.combine(shift_date, end)

        # Night shift -> crosses midnight
        if end <= start:
            end_dt += timedelta(days=1)

        total = end_dt - start_dt

        # Break
        bs, be = data.get('break_start'), data.get('break_end')
        if bs and be:
            bs_dt = datetime.combine(shift_date, bs)
            be_dt = datetime.combine(shift_date, be)
            # If break also crosses midnight (rare), adjust
            if be <= bs:
                be_dt += timedelta(days=1)
            total -= max(timedelta(0), be_dt - bs_dt)

        # Convert to hours with 2 decimals
        hours = round(total.total_seconds() / 3600.0, 2)
        return hours

    # ---------- validation ----------

    def validate(self, attrs):
        """
        - Ensure hotel == period.hotel
        - Ensure (optional) location.hotel == hotel
        - Ensure shift_end logically after shift_start unless night shift
        - Ensure break is inside the shift window (basic sanity)
        - Auto-set expected_hours if not provided
        - Auto-set is_night_shift if shift crosses midnight
        """
        hotel = attrs.get('hotel') or getattr(self.instance, 'hotel', None)
        period = attrs.get('period') or getattr(self.instance, 'period', None)
        location = attrs.get('location') or getattr(self.instance, 'location', None)

        # Hotel / period consistency
        if hotel and period and hotel != period.hotel:
            raise serializers.ValidationError(
                "Hotel mismatch: period.hotel and hotel must be identical."
            )

        # Hotel / location consistency
        if hotel and location and location.hotel_id != hotel.id:
            raise serializers.ValidationError(
                "Location must belong to the same hotel as the shift."
            )

        start = attrs.get('shift_start') or getattr(self.instance, 'shift_start', None)
        end = attrs.get('shift_end') or getattr(self.instance, 'shift_end', None)
        is_night = attrs.get('is_night_shift', getattr(self.instance, 'is_night_shift', False))

        if start and end:
            if end <= start:
                # Shift crosses midnight, mark as night shift automatically
                attrs['is_night_shift'] = True
            else:
                # Normal shift, ensure is_night_shift is False if not explicitly set
                attrs['is_night_shift'] = False

        # Break sanity (coarse)
        bs, be = attrs.get('break_start'), attrs.get('break_end')
        if (bs and not be) or (be and not bs):
            raise serializers.ValidationError(
                "Both break_start and break_end must be provided, or neither."
            )

        # Auto-calc expected_hours if not provided
        if (
            attrs.get('expected_hours') in (None, '')
            and all(k in attrs for k in ('shift_date', 'shift_start', 'shift_end'))
        ):
            attrs['expected_hours'] = self._calc_expected_hours(attrs)

        return attrs

    # ---------- create / update ----------

    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            staff = getattr(request.user, 'staff_profile', None)
            if staff:
                validated_data['approved_by'] = staff
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request:
            staff = getattr(request.user, 'staff_profile', None)
            if staff:
                validated_data.setdefault('approved_by', staff)
        return super().update(instance, validated_data)


# ─────────────────────────────
# Availability / Templates / Requirements
# ─────────────────────────────

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
    department = serializers.SlugRelatedField(
        queryset=Department.objects.all(),
        slug_field='slug',
        required=True,
    )
    department_name = serializers.CharField(source='department.name', read_only=True)

    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = RosterRequirement
        fields = ['id', 'period', 'department', 'department_name', 'role', 'role_name', 'date', 'required_count']
        read_only_fields = ['id']

class DailyPlanEntrySerializer(serializers.ModelSerializer):
    hotel_slug = serializers.CharField(source='staff.hotel.slug', read_only=True)
    staff_name = serializers.SerializerMethodField()
    staff_department = serializers.CharField(source='staff.department.name', read_only=True)
    shift_start = serializers.TimeField(source='roster.shift_start', format='%H:%M', read_only=True)
    shift_end = serializers.TimeField(source='roster.shift_end', format='%H:%M', read_only=True)
    location_name = serializers.CharField(source='location.name', default='No Location', read_only=True)

    class Meta:
        model = DailyPlanEntry
        fields = [
            'id',
            'hotel_slug',
            'staff_name',
            'staff_department',
            'shift_start',
            'shift_end',
            'location_name',
        ]

    def get_staff_name(self, obj):
        staff = obj.staff
        if staff:
            return f"{staff.first_name} {staff.last_name}"
        return None

class DailyPlanSerializer(serializers.ModelSerializer):
    entries = DailyPlanEntrySerializer(many=True)

    class Meta:
        model = DailyPlan
        fields = ['id', 'hotel', 'hotel_name', 'date', 'entries']

    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    entries = DailyPlanEntrySerializer(many=True, read_only=True)

    class Meta:
        model = DailyPlan
        fields = ['id', 'hotel', 'hotel_name', 'date', 'created_at', 'updated_at', 'entries']
        

class CopyShiftSerializer(serializers.Serializer):
    shift_id = serializers.IntegerField()
    target_date = serializers.DateField()

class CopyDaySerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()
    source_date = serializers.DateField()
    target_date = serializers.DateField()

class CopyDayAllSerializer(serializers.Serializer):
    source_date = serializers.DateField()
    target_date = serializers.DateField()

class CopyWeekSerializer(serializers.Serializer):
    source_period_id = serializers.IntegerField()
    target_period_id = serializers.IntegerField()

class CopyWeekStaffSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()
    source_period_id = serializers.IntegerField()
    target_period_id = serializers.IntegerField()