# COMPLETE ROSTER CRUD IMPLEMENTATION PLAN

## 🚀 **IMPLEMENTATION ROADMAP**

Based on the analysis, here's exactly what you need to implement for complete roster CRUD with advanced copy operations:

## 📁 **FILE STRUCTURE ADDITIONS**

```
HotelMateBackend/
├── attendance/
│   ├── serializers_advanced.py        # ← NEW FILE (Advanced copy serializers)
│   ├── views_copy_advanced.py          # ← NEW FILE (Advanced copy operations)
│   ├── views_bulk_operations.py        # ← NEW FILE (Bulk CRUD operations)
│   ├── utils_roster_validation.py      # ← NEW FILE (Advanced validation)
│   ├── utils_conflict_resolution.py    # ← NEW FILE (Conflict resolution)
│   └── tasks_roster_optimization.py    # ← NEW FILE (Background tasks)
```

---

## 🔧 **1. ADVANCED COPY SERIALIZERS**

### **Create `attendance/serializers_advanced.py`**

```python
from rest_framework import serializers
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError


class CopyDepartmentDaySerializer(serializers.Serializer):
    """Copy entire department's roster for a specific day to multiple target dates"""
    department_slug = serializers.CharField(
        help_text="Department slug to copy from"
    )
    source_date = serializers.DateField(
        help_text="Source date to copy shifts from"
    )
    target_dates = serializers.ListField(
        child=serializers.DateField(),
        help_text="List of target dates to copy shifts to"
    )
    include_roles = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="Only copy shifts for these roles (optional)"
    )
    exclude_staff = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Exclude these staff IDs from copying"
    )
    preserve_locations = serializers.BooleanField(
        default=True,
        help_text="Preserve original shift locations"
    )
    check_availability = serializers.BooleanField(
        default=True,
        help_text="Check staff availability before copying"
    )
    
    def validate_target_dates(self, value):
        """Validate target dates are not in the past"""
        today = datetime.now().date()
        for date in value:
            if date < today:
                raise ValidationError(f"Target date {date} cannot be in the past")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        source_date = data.get('source_date')
        target_dates = data.get('target_dates', [])
        
        # Prevent copying to source date
        if source_date in target_dates:
            raise ValidationError("Cannot copy to the same date as source")
        
        # Limit number of target dates to prevent abuse
        if len(target_dates) > 30:
            raise ValidationError("Cannot copy to more than 30 target dates at once")
        
        return data


class CopyDepartmentWeekSerializer(serializers.Serializer):
    """Copy entire department's roster for a week to multiple target periods"""
    department_slug = serializers.CharField()
    source_period_id = serializers.IntegerField()
    target_period_ids = serializers.ListField(child=serializers.IntegerField())
    copy_options = serializers.DictField(
        required=False,
        help_text="Additional copy options: roles, locations, etc."
    )
    preserve_shift_patterns = serializers.BooleanField(default=True)
    skip_weekends = serializers.BooleanField(default=False)
    
    def validate_target_period_ids(self, value):
        """Limit bulk operations"""
        if len(value) > 10:
            raise ValidationError("Cannot copy to more than 10 periods at once")
        return value


class CopyByRoleSerializer(serializers.Serializer):
    """Copy all shifts for a specific role across departments"""
    role_slug = serializers.CharField()
    source_date = serializers.DateField()
    target_date = serializers.DateField()
    departments = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Limit to specific departments (optional)"
    )
    include_locations = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Only copy shifts at these locations"
    )


class CopyByLocationSerializer(serializers.Serializer):
    """Copy all shifts for a specific location"""
    location_id = serializers.IntegerField()
    source_period_id = serializers.IntegerField()
    target_period_id = serializers.IntegerField()
    department_filter = serializers.CharField(
        required=False,
        help_text="Only copy for specific department"
    )


class CopyMultiDaySerializer(serializers.Serializer):
    """Copy one day to multiple target dates with advanced filtering"""
    source_date = serializers.DateField()
    target_dates = serializers.ListField(child=serializers.DateField())
    departments = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Filter by departments"
    )
    staff_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Filter by specific staff members"
    )
    locations = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Filter by locations"
    )
    exclude_weekends = serializers.BooleanField(default=False)
    exclude_holidays = serializers.BooleanField(default=False)
    
    def validate(self, data):
        """Advanced validation"""
        target_dates = data.get('target_dates', [])
        exclude_weekends = data.get('exclude_weekends', False)
        
        if exclude_weekends:
            # Filter out weekends (Saturday=5, Sunday=6)
            filtered_dates = [d for d in target_dates if d.weekday() < 5]
            if len(filtered_dates) != len(target_dates):
                data['target_dates'] = filtered_dates
        
        return data


class CopyWeekdaysOnlySerializer(serializers.Serializer):
    """Copy only specific weekdays between periods"""
    source_period_id = serializers.IntegerField()
    target_period_id = serializers.IntegerField()
    weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        help_text="0=Monday, 6=Sunday"
    )
    departments = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    
    def validate_weekdays(self, value):
        """Validate weekday selection"""
        if not value:
            raise ValidationError("At least one weekday must be selected")
        if len(set(value)) != len(value):
            raise ValidationError("Duplicate weekdays not allowed")
        return sorted(set(value))


class CopyWithAdjustmentSerializer(serializers.Serializer):
    """Copy shifts with time adjustments"""
    source_date = serializers.DateField()
    target_date = serializers.DateField()
    time_adjustment_minutes = serializers.IntegerField(
        help_text="Minutes to shift all times (can be negative)"
    )
    departments = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    validate_business_hours = serializers.BooleanField(
        default=True,
        help_text="Ensure adjusted times fall within business hours"
    )
    
    def validate_time_adjustment_minutes(self, value):
        """Limit time adjustments to reasonable ranges"""
        if abs(value) > 720:  # 12 hours
            raise ValidationError("Time adjustment cannot exceed 12 hours")
        return value


class SmartCopySerializer(serializers.Serializer):
    """Intelligent copying with availability and workload checking"""
    source_period_id = serializers.IntegerField()
    target_period_id = serializers.IntegerField()
    check_availability = serializers.BooleanField(default=True)
    resolve_overlaps = serializers.BooleanField(default=True)
    balance_workload = serializers.BooleanField(default=False)
    max_hours_per_staff = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=60,
        help_text="Maximum hours per staff member per week"
    )
    priority_departments = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Departments to prioritize during conflict resolution"
    )
    auto_assign_alternatives = serializers.BooleanField(
        default=False,
        help_text="Automatically assign alternative staff if conflicts occur"
    )


class BulkShiftUpdateSerializer(serializers.Serializer):
    """Bulk update multiple shifts"""
    shift_ids = serializers.ListField(child=serializers.IntegerField())
    updates = serializers.DictField(
        help_text="Fields to update: location, start_time, end_time, etc."
    )
    
    def validate_shift_ids(self, value):
        """Limit bulk operations"""
        if len(value) > 100:
            raise ValidationError("Cannot update more than 100 shifts at once")
        return value
    
    def validate_updates(self, value):
        """Validate allowed update fields"""
        allowed_fields = {
            'location_id', 'shift_start', 'shift_end', 
            'break_start', 'break_end', 'notes',
            'expected_hours', 'shift_type'
        }
        
        invalid_fields = set(value.keys()) - allowed_fields
        if invalid_fields:
            raise ValidationError(f"Invalid update fields: {invalid_fields}")
        
        return value


class SwapShiftsSerializer(serializers.Serializer):
    """Swap shifts between two staff members"""
    staff_a_id = serializers.IntegerField()
    staff_b_id = serializers.IntegerField()
    shift_date = serializers.DateField()
    validate_skills = serializers.BooleanField(
        default=True,
        help_text="Validate staff have required skills for swapped shifts"
    )
    validate_availability = serializers.BooleanField(default=True)
    
    def validate(self, data):
        """Validate staff are different"""
        if data.get('staff_a_id') == data.get('staff_b_id'):
            raise ValidationError("Cannot swap shifts with the same staff member")
        return data


class ConflictResolutionSerializer(serializers.Serializer):
    """Resolve scheduling conflicts"""
    period_id = serializers.IntegerField()
    resolution_strategy = serializers.ChoiceField(
        choices=[
            ('auto', 'Automatic Resolution'),
            ('prioritize_senior', 'Prioritize Senior Staff'),
            ('prioritize_department', 'Prioritize Specific Department'),
            ('manual', 'Provide Manual Resolution')
        ]
    )
    priority_department = serializers.CharField(
        required=False,
        help_text="Department to prioritize (if using prioritize_department strategy)"
    )
    manual_resolutions = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Manual conflict resolutions"
    )


class BulkDeleteSerializer(serializers.Serializer):
    """Bulk delete shifts by criteria"""
    criteria = serializers.ChoiceField(
        choices=[
            ('date_range', 'Delete by date range'),
            ('department', 'Delete by department'),
            ('staff', 'Delete by staff member'),
            ('location', 'Delete by location'),
            ('shift_ids', 'Delete specific shifts')
        ]
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    department_slug = serializers.CharField(required=False)
    staff_id = serializers.IntegerField(required=False)
    location_id = serializers.IntegerField(required=False)
    shift_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    confirm_deletion = serializers.BooleanField(
        default=False,
        help_text="Must be true to proceed with deletion"
    )
    
    def validate(self, data):
        """Validate deletion criteria"""
        criteria = data.get('criteria')
        
        if criteria == 'date_range':
            if not data.get('start_date') or not data.get('end_date'):
                raise ValidationError("start_date and end_date required for date_range criteria")
        elif criteria == 'department':
            if not data.get('department_slug'):
                raise ValidationError("department_slug required for department criteria")
        elif criteria == 'staff':
            if not data.get('staff_id'):
                raise ValidationError("staff_id required for staff criteria")
        elif criteria == 'location':
            if not data.get('location_id'):
                raise ValidationError("location_id required for location criteria")
        elif criteria == 'shift_ids':
            if not data.get('shift_ids'):
                raise ValidationError("shift_ids required for shift_ids criteria")
        
        if not data.get('confirm_deletion'):
            raise ValidationError("confirm_deletion must be true to proceed")
        
        return data
```

---

## 🔧 **2. ADVANCED COPY OPERATIONS VIEWSET**

### **Create `attendance/views_copy_advanced.py`**

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models import StaffRoster, RosterPeriod, ShiftLocation
from .serializers_advanced import (
    CopyDepartmentDaySerializer, CopyDepartmentWeekSerializer,
    CopyByRoleSerializer, CopyByLocationSerializer,
    CopyMultiDaySerializer, CopyWeekdaysOnlySerializer,
    CopyWithAdjustmentSerializer, SmartCopySerializer
)
from .utils_roster_validation import (
    validate_copy_operation, check_availability_conflicts,
    validate_workload_limits, check_skill_requirements
)
from .utils_conflict_resolution import (
    detect_scheduling_conflicts, resolve_conflicts_automatically,
    suggest_alternative_assignments
)
from staff.models import Staff, Department, Role
from hotel.models import Hotel

logger = logging.getLogger(__name__)


class AdvancedCopyRosterViewSet(viewsets.ViewSet):
    """
    Advanced roster copying operations with intelligent conflict resolution
    """
    
    def _get_hotel(self, hotel_slug):
        """Get hotel object from slug"""
        return get_object_or_404(Hotel, slug=hotel_slug)
    
    def _log_copy_operation(self, hotel, operation_type, performed_by, **kwargs):
        """Log copy operation for audit trail"""
        from .views import log_roster_operation
        log_roster_operation(
            hotel=hotel,
            operation_type=operation_type,
            performed_by=performed_by,
            **kwargs
        )
    
    @action(detail=False, methods=['post'])
    def copy_department_day(self, request, hotel_slug=None):
        """
        Copy entire department's roster for a specific day to multiple target dates
        
        POST /api/staff/hotel/{hotel_slug}/attendance/advanced-copy/copy-department-day/
        """
        serializer = CopyDepartmentDaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        hotel = self._get_hotel(hotel_slug)
        data = serializer.validated_data
        
        department_slug = data['department_slug']
        source_date = data['source_date']
        target_dates = data['target_dates']
        include_roles = data.get('include_roles', [])
        exclude_staff = data.get('exclude_staff', [])
        preserve_locations = data.get('preserve_locations', True)
        check_availability = data.get('check_availability', True)
        
        # Get department
        department = get_object_or_404(Department, slug=department_slug)
        
        # Get source shifts
        source_shifts_query = StaffRoster.objects.filter(
            hotel=hotel,
            shift_date=source_date,
            staff__department=department
        )
        
        # Apply role filter
        if include_roles:
            source_shifts_query = source_shifts_query.filter(
                staff__role__slug__in=include_roles
            )
        
        # Apply staff exclusion
        if exclude_staff:
            source_shifts_query = source_shifts_query.exclude(
                staff_id__in=exclude_staff
            )
        
        source_shifts = list(source_shifts_query.select_related(
            'staff', 'location', 'period'
        ))
        
        if not source_shifts:
            return Response(
                {"detail": f"No shifts found for {department_slug} on {source_date}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate operation
        validation_result = validate_copy_operation(
            source_shifts=source_shifts,
            target_dates=target_dates,
            hotel=hotel,
            check_availability=check_availability
        )
        
        if not validation_result['is_valid']:
            return Response(
                {"detail": validation_result['error'], "warnings": validation_result.get('warnings', [])},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_shifts_created = 0
        conflicts_detected = []
        
        with transaction.atomic():
            for target_date in target_dates:
                # Find target period
                target_period = RosterPeriod.objects.filter(
                    hotel=hotel,
                    start_date__lte=target_date,
                    end_date__gte=target_date
                ).first()
                
                if not target_period:
                    conflicts_detected.append(f"No roster period found for {target_date}")
                    continue
                
                # Check if target period is locked
                if target_period.is_finalized:
                    conflicts_detected.append(f"Cannot copy to finalized period containing {target_date}")
                    continue
                
                # Create new shifts for this date
                new_shifts = []
                for shift in source_shifts:
                    # Check for availability conflicts if enabled
                    if check_availability:
                        availability_conflict = check_availability_conflicts(
                            staff=shift.staff,
                            date=target_date,
                            start_time=shift.shift_start,
                            end_time=shift.shift_end
                        )
                        
                        if availability_conflict:
                            conflicts_detected.append(
                                f"Staff {shift.staff} not available on {target_date} "
                                f"{shift.shift_start}-{shift.shift_end}: {availability_conflict}"
                            )
                            continue
                    
                    # Create new shift
                    new_shift = StaffRoster(
                        hotel=hotel,
                        staff=shift.staff,
                        department=shift.department,
                        period=target_period,
                        shift_date=target_date,
                        shift_start=shift.shift_start,
                        shift_end=shift.shift_end,
                        break_start=shift.break_start,
                        break_end=shift.break_end,
                        expected_hours=shift.expected_hours,
                        shift_type=shift.shift_type,
                        is_night_shift=shift.is_night_shift,
                        location=shift.location if preserve_locations else None,
                        notes=f"Copied from {source_date}"
                    )
                    new_shifts.append(new_shift)
                
                # Bulk create shifts for this date
                if new_shifts:
                    try:
                        StaffRoster.objects.bulk_create(new_shifts, ignore_conflicts=True)
                        new_shifts_created += len(new_shifts)
                    except Exception as e:
                        conflicts_detected.append(f"Error creating shifts for {target_date}: {str(e)}")
        
        # Log operation
        self._log_copy_operation(
            hotel=hotel,
            operation_type='copy_department_day',
            performed_by=getattr(request.user, 'staff_profile', None),
            success=new_shifts_created > 0,
            affected_shifts_count=new_shifts_created,
            operation_details={
                'department': department_slug,
                'source_date': source_date.isoformat(),
                'target_dates': [d.isoformat() for d in target_dates],
                'conflicts': len(conflicts_detected)
            }
        )
        
        return Response({
            'shifts_created': new_shifts_created,
            'conflicts_detected': conflicts_detected,
            'source_shifts_count': len(source_shifts),
            'target_dates_processed': len(target_dates)
        }, status=status.HTTP_201_CREATED if new_shifts_created > 0 else status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def copy_department_week(self, request, hotel_slug=None):
        """
        Copy entire department's roster for a week to multiple target periods
        """
        serializer = CopyDepartmentWeekSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        hotel = self._get_hotel(hotel_slug)
        data = serializer.validated_data
        
        department_slug = data['department_slug']
        source_period_id = data['source_period_id']
        target_period_ids = data['target_period_ids']
        copy_options = data.get('copy_options', {})
        skip_weekends = data.get('skip_weekends', False)
        
        department = get_object_or_404(Department, slug=department_slug)
        source_period = get_object_or_404(RosterPeriod, id=source_period_id, hotel=hotel)
        
        # Get source shifts
        source_shifts_query = StaffRoster.objects.filter(
            hotel=hotel,
            period=source_period,
            staff__department=department
        )
        
        # Apply weekend filter if requested
        if skip_weekends:
            source_shifts_query = source_shifts_query.exclude(
                shift_date__week_day__in=[1, 7]  # Sunday=1, Saturday=7 in Django
            )
        
        source_shifts = list(source_shifts_query.select_related('staff', 'location'))
        
        if not source_shifts:
            return Response(
                {"detail": f"No shifts found for {department_slug} in source period"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_shifts_created = 0
        conflicts_detected = []
        
        with transaction.atomic():
            for target_period_id in target_period_ids:
                target_period = get_object_or_404(RosterPeriod, id=target_period_id, hotel=hotel)
                
                if target_period.is_finalized:
                    conflicts_detected.append(f"Target period {target_period.title} is finalized")
                    continue
                
                # Calculate date offset
                date_offset = (target_period.start_date - source_period.start_date).days
                
                new_shifts = []
                for shift in source_shifts:
                    new_date = shift.shift_date + timedelta(days=date_offset)
                    
                    # Ensure new date falls within target period
                    if target_period.start_date <= new_date <= target_period.end_date:
                        new_shift = StaffRoster(
                            hotel=hotel,
                            staff=shift.staff,
                            department=shift.department,
                            period=target_period,
                            shift_date=new_date,
                            shift_start=shift.shift_start,
                            shift_end=shift.shift_end,
                            break_start=shift.break_start,
                            break_end=shift.break_end,
                            expected_hours=shift.expected_hours,
                            shift_type=shift.shift_type,
                            is_night_shift=shift.is_night_shift,
                            location=shift.location,
                            notes=f"Copied from {source_period.title}"
                        )
                        new_shifts.append(new_shift)
                
                # Bulk create shifts
                if new_shifts:
                    try:
                        StaffRoster.objects.bulk_create(new_shifts, ignore_conflicts=True)
                        new_shifts_created += len(new_shifts)
                    except Exception as e:
                        conflicts_detected.append(f"Error copying to {target_period.title}: {str(e)}")
        
        return Response({
            'shifts_created': new_shifts_created,
            'conflicts_detected': conflicts_detected,
            'source_shifts_count': len(source_shifts),
            'target_periods_processed': len(target_period_ids)
        }, status=status.HTTP_201_CREATED if new_shifts_created > 0 else status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def copy_by_role(self, request, hotel_slug=None):
        """
        Copy all shifts for a specific role across departments
        """
        serializer = CopyByRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        hotel = self._get_hotel(hotel_slug)
        data = serializer.validated_data
        
        role_slug = data['role_slug']
        source_date = data['source_date']
        target_date = data['target_date']
        departments = data.get('departments', [])
        include_locations = data.get('include_locations', [])
        
        role = get_object_or_404(Role, slug=role_slug)
        
        # Get source shifts
        source_shifts_query = StaffRoster.objects.filter(
            hotel=hotel,
            shift_date=source_date,
            staff__role=role
        )
        
        # Apply department filter
        if departments:
            source_shifts_query = source_shifts_query.filter(
                staff__department__slug__in=departments
            )
        
        # Apply location filter
        if include_locations:
            source_shifts_query = source_shifts_query.filter(
                location_id__in=include_locations
            )
        
        source_shifts = list(source_shifts_query.select_related('staff', 'location', 'department'))
        
        if not source_shifts:
            return Response(
                {"detail": f"No shifts found for role {role_slug} on {source_date}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Find target period
        target_period = RosterPeriod.objects.filter(
            hotel=hotel,
            start_date__lte=target_date,
            end_date__gte=target_date
        ).first()
        
        if not target_period:
            return Response(
                {"detail": f"No roster period found for target date {target_date}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_shifts = []
        for shift in source_shifts:
            new_shift = StaffRoster(
                hotel=hotel,
                staff=shift.staff,
                department=shift.department,
                period=target_period,
                shift_date=target_date,
                shift_start=shift.shift_start,
                shift_end=shift.shift_end,
                break_start=shift.break_start,
                break_end=shift.break_end,
                expected_hours=shift.expected_hours,
                shift_type=shift.shift_type,
                is_night_shift=shift.is_night_shift,
                location=shift.location,
                notes=f"Role-based copy from {source_date}"
            )
            new_shifts.append(new_shift)
        
        with transaction.atomic():
            StaffRoster.objects.bulk_create(new_shifts, ignore_conflicts=True)
        
        return Response({
            'shifts_created': len(new_shifts),
            'role': role_slug,
            'source_date': source_date,
            'target_date': target_date
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def copy_multi_day(self, request, hotel_slug=None):
        """
        Copy one day to multiple target dates with advanced filtering
        """
        serializer = CopyMultiDaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        hotel = self._get_hotel(hotel_slug)
        data = serializer.validated_data
        
        source_date = data['source_date']
        target_dates = data['target_dates']
        departments = data.get('departments', [])
        staff_ids = data.get('staff_ids', [])
        locations = data.get('locations', [])
        
        # Build source query
        source_shifts_query = StaffRoster.objects.filter(
            hotel=hotel,
            shift_date=source_date
        )
        
        if departments:
            source_shifts_query = source_shifts_query.filter(
                staff__department__slug__in=departments
            )
        
        if staff_ids:
            source_shifts_query = source_shifts_query.filter(
                staff_id__in=staff_ids
            )
        
        if locations:
            source_shifts_query = source_shifts_query.filter(
                location_id__in=locations
            )
        
        source_shifts = list(source_shifts_query.select_related('staff', 'location', 'department'))
        
        if not source_shifts:
            return Response(
                {"detail": f"No shifts found matching criteria on {source_date}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        total_created = 0
        date_results = []
        
        with transaction.atomic():
            for target_date in target_dates:
                # Find target period
                target_period = RosterPeriod.objects.filter(
                    hotel=hotel,
                    start_date__lte=target_date,
                    end_date__gte=target_date
                ).first()
                
                if not target_period:
                    date_results.append({
                        'date': target_date.isoformat(),
                        'success': False,
                        'error': 'No roster period found'
                    })
                    continue
                
                # Create shifts for this date
                new_shifts = []
                for shift in source_shifts:
                    new_shift = StaffRoster(
                        hotel=hotel,
                        staff=shift.staff,
                        department=shift.department,
                        period=target_period,
                        shift_date=target_date,
                        shift_start=shift.shift_start,
                        shift_end=shift.shift_end,
                        break_start=shift.break_start,
                        break_end=shift.break_end,
                        expected_hours=shift.expected_hours,
                        shift_type=shift.shift_type,
                        is_night_shift=shift.is_night_shift,
                        location=shift.location,
                        notes=f"Multi-day copy from {source_date}"
                    )
                    new_shifts.append(new_shift)
                
                try:
                    StaffRoster.objects.bulk_create(new_shifts, ignore_conflicts=True)
                    total_created += len(new_shifts)
                    date_results.append({
                        'date': target_date.isoformat(),
                        'success': True,
                        'shifts_created': len(new_shifts)
                    })
                except Exception as e:
                    date_results.append({
                        'date': target_date.isoformat(),
                        'success': False,
                        'error': str(e)
                    })
        
        return Response({
            'total_shifts_created': total_created,
            'source_shifts_count': len(source_shifts),
            'date_results': date_results
        }, status=status.HTTP_201_CREATED if total_created > 0 else status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def smart_copy(self, request, hotel_slug=None):
        """
        Intelligent copying with availability and workload checking
        """
        serializer = SmartCopySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        hotel = self._get_hotel(hotel_slug)
        data = serializer.validated_data
        
        source_period_id = data['source_period_id']
        target_period_id = data['target_period_id']
        check_availability = data.get('check_availability', True)
        resolve_overlaps = data.get('resolve_overlaps', True)
        balance_workload = data.get('balance_workload', False)
        max_hours_per_staff = data.get('max_hours_per_staff')
        auto_assign_alternatives = data.get('auto_assign_alternatives', False)
        
        source_period = get_object_or_404(RosterPeriod, id=source_period_id, hotel=hotel)
        target_period = get_object_or_404(RosterPeriod, id=target_period_id, hotel=hotel)
        
        # Get all shifts from source period
        source_shifts = list(StaffRoster.objects.filter(
            period=source_period
        ).select_related('staff', 'department', 'location'))
        
        if not source_shifts:
            return Response(
                {"detail": "No shifts found in source period"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate date offset
        date_offset = (target_period.start_date - source_period.start_date).days
        
        # Smart copy logic
        successful_copies = []
        conflicts_resolved = []
        unavailable_staff = []
        workload_exceeded = []
        
        with transaction.atomic():
            for shift in source_shifts:
                new_date = shift.shift_date + timedelta(days=date_offset)
                
                # Skip if new date is outside target period
                if not (target_period.start_date <= new_date <= target_period.end_date):
                    continue
                
                # Check availability if enabled
                if check_availability:
                    availability_check = check_availability_conflicts(
                        staff=shift.staff,
                        date=new_date,
                        start_time=shift.shift_start,
                        end_time=shift.shift_end
                    )
                    
                    if availability_check:
                        unavailable_staff.append({
                            'staff': f"{shift.staff}",
                            'date': new_date.isoformat(),
                            'conflict': availability_check
                        })
                        
                        if auto_assign_alternatives:
                            # Try to find alternative staff
                            alternative_staff = suggest_alternative_assignments(
                                original_staff=shift.staff,
                                shift_date=new_date,
                                shift_start=shift.shift_start,
                                shift_end=shift.shift_end,
                                department=shift.department,
                                hotel=hotel
                            )
                            
                            if alternative_staff:
                                shift.staff = alternative_staff
                                conflicts_resolved.append({
                                    'original_staff': f"{shift.staff}",
                                    'alternative_staff': f"{alternative_staff}",
                                    'date': new_date.isoformat()
                                })
                            else:
                                continue
                        else:
                            continue
                
                # Check workload limits if enabled
                if balance_workload and max_hours_per_staff:
                    current_workload = validate_workload_limits(
                        staff=shift.staff,
                        period=target_period,
                        additional_hours=shift.expected_hours or 0,
                        max_hours=max_hours_per_staff
                    )
                    
                    if not current_workload['within_limits']:
                        workload_exceeded.append({
                            'staff': f"{shift.staff}",
                            'current_hours': current_workload['current_hours'],
                            'would_exceed_by': current_workload['excess_hours']
                        })
                        continue
                
                # Create the new shift
                new_shift = StaffRoster(
                    hotel=hotel,
                    staff=shift.staff,
                    department=shift.department,
                    period=target_period,
                    shift_date=new_date,
                    shift_start=shift.shift_start,
                    shift_end=shift.shift_end,
                    break_start=shift.break_start,
                    break_end=shift.break_end,
                    expected_hours=shift.expected_hours,
                    shift_type=shift.shift_type,
                    is_night_shift=shift.is_night_shift,
                    location=shift.location,
                    notes=f"Smart copy from {source_period.title}"
                )
                
                try:
                    new_shift.save()
                    successful_copies.append({
                        'staff': f"{shift.staff}",
                        'date': new_date.isoformat(),
                        'shift_time': f"{shift.shift_start}-{shift.shift_end}"
                    })
                except Exception as e:
                    # Handle overlap conflicts if resolve_overlaps is enabled
                    if resolve_overlaps and "unique constraint" in str(e).lower():
                        resolution = resolve_conflicts_automatically(
                            conflicted_shift=new_shift,
                            existing_shifts=StaffRoster.objects.filter(
                                staff=shift.staff,
                                shift_date=new_date
                            )
                        )
                        
                        if resolution['resolved']:
                            conflicts_resolved.append(resolution)
                        else:
                            unavailable_staff.append({
                                'staff': f"{shift.staff}",
                                'date': new_date.isoformat(),
                                'conflict': 'Unresolved scheduling conflict'
                            })
        
        # Log the smart copy operation
        self._log_copy_operation(
            hotel=hotel,
            operation_type='smart_copy',
            performed_by=getattr(request.user, 'staff_profile', None),
            success=len(successful_copies) > 0,
            affected_shifts_count=len(successful_copies),
            source_period=source_period,
            target_period=target_period,
            operation_details={
                'conflicts_resolved': len(conflicts_resolved),
                'unavailable_staff': len(unavailable_staff),
                'workload_exceeded': len(workload_exceeded)
            }
        )
        
        return Response({
            'successful_copies': len(successful_copies),
            'conflicts_resolved': conflicts_resolved,
            'unavailable_staff': unavailable_staff,
            'workload_exceeded': workload_exceeded,
            'summary': {
                'source_period': source_period.title,
                'target_period': target_period.title,
                'total_source_shifts': len(source_shifts),
                'successful_copies': len(successful_copies),
                'success_rate': f"{(len(successful_copies) / len(source_shifts) * 100):.1f}%"
            }
        }, status=status.HTTP_201_CREATED)
```

This is the first part of the implementation. The file structure would continue with:

1. **Bulk Operations ViewSet** (`views_bulk_operations.py`)
2. **Advanced Validation Utilities** (`utils_roster_validation.py`) 
3. **Conflict Resolution Utilities** (`utils_conflict_resolution.py`)
4. **URL Pattern Updates** (`urls.py` additions)
5. **Frontend Integration Examples**

Would you like me to continue with the next parts of the implementation?