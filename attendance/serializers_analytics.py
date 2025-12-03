from rest_framework import serializers

# ---- Queries ----
class PeriodQuerySerializer(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False) 
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    department = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate(self, data):
        # Allow both start/end and start_date/end_date formats
        start = data.get('start') or data.get('start_date')
        end = data.get('end') or data.get('end_date')
        
        if not start:
            raise serializers.ValidationError("Either 'start' or 'start_date' is required")
        if not end:
            raise serializers.ValidationError("Either 'end' or 'end_date' is required")
            
        # Normalize to start/end format
        data['start'] = start
        data['end'] = end
        
        return data

# ---- Period / overall ----
class StaffRosterAnalyticsRowSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    dept_id = serializers.IntegerField(required=False)
    department_name = serializers.CharField(required=False)
    department_slug = serializers.CharField(required=False)
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()
    avg_shift_length = serializers.FloatField()

class DepartmentRosterAnalyticsRowSerializer(serializers.Serializer):
    dept_id = serializers.IntegerField()  # corrected to match data key
    department_name = serializers.CharField()
    department_slug = serializers.CharField()
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
    dept_id = serializers.IntegerField()
    department_name = serializers.CharField()
    department_slug = serializers.CharField()
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()
    unique_staff = serializers.IntegerField()

class DailyStaffRowSerializer(serializers.Serializer):
    date = serializers.DateField()
    staff_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    dept_id = serializers.IntegerField(required=False)
    department_name = serializers.CharField(required=False)
    department_slug = serializers.CharField(required=False)
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
    dept_id = serializers.IntegerField()
    department_name = serializers.CharField()
    department_slug = serializers.CharField()
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()
    unique_staff = serializers.IntegerField()

class WeeklyStaffRowSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    week = serializers.IntegerField()
    staff_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    dept_id = serializers.IntegerField(required=False)
    department_name = serializers.CharField(required=False)
    department_slug = serializers.CharField(required=False)
    total_rostered_hours = serializers.FloatField()
    shifts_count = serializers.IntegerField()
