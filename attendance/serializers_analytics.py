# attendance/serializers_analytics.py
from rest_framework import serializers

# ---- Queries ----
class PeriodQuerySerializer(serializers.Serializer):
    start = serializers.DateField()
    end = serializers.DateField()
    department = serializers.CharField(required=False, allow_blank=True, allow_null=True)

# ---- Period / overall ----
class StaffRosterAnalyticsRowSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    department = serializers.CharField()
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()
    avg_shift_length = serializers.FloatField()

class DepartmentRosterAnalyticsRowSerializer(serializers.Serializer):
    department = serializers.CharField()
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()
    avg_shift_length = serializers.FloatField()
    unique_staff = serializers.IntegerField()

class RosterKpiSerializer(serializers.Serializer):
    total_rostered_hours = serializers.FloatField()
    total_shifts = serializers.IntegerField()
    avg_shift_length = serializers.FloatField()
    unique_staff = serializers.IntegerField()

# ---- Daily ----
class DailyTotalsRowSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()

class DailyDepartmentRowSerializer(serializers.Serializer):
    date = serializers.DateField()
    department = serializers.CharField()
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()
    unique_staff = serializers.IntegerField()

class DailyStaffRowSerializer(serializers.Serializer):
    date = serializers.DateField()
    staff_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    department = serializers.CharField()
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()

# ---- Weekly ----
class WeeklyTotalsRowSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    week = serializers.IntegerField()
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()
    unique_staff = serializers.IntegerField()

class WeeklyDepartmentRowSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    week = serializers.IntegerField()
    department = serializers.CharField()
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()
    unique_staff = serializers.IntegerField()

class WeeklyStaffRowSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    week = serializers.IntegerField()
    staff_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    department = serializers.CharField()
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()
