from datetime import datetime, timedelta, time as dtime
from staff.models import Department, Role
from django.utils.timezone import make_aware
from rest_framework import serializers
from staff.serializers import StaffMinimalSerializer, DepartmentSerializer
from .models import (
    StaffFace, ClockLog, RosterPeriod, StaffRoster,
    StaffAvailability, ShiftTemplate, RosterRequirement,
    ShiftLocation, DailyPlan, DailyPlanEntry, FaceAuditLog,
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
    department = serializers.SerializerMethodField()  # Add this

    # write-only FK setter
    roster_shift_id = serializers.PrimaryKeyRelatedField(
        source='roster_shift',
        queryset=StaffRoster.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    # read-only lightweight representation
    roster_shift = serializers.SerializerMethodField(read_only=True)

    # Add staff image field
    staff_image = serializers.SerializerMethodField()
    
    class Meta:
        model = ClockLog
        fields = [
            'id', 'staff', 'staff_name', 'staff_image', 'hotel', 'hotel_slug',
            'time_in', 'time_out', 'verified_by_face', 'location_note', 'auto_clock_out',
            'hours_worked', 'department',
            'roster_shift_id',  # input
            'roster_shift',     # output
            # PHASE 4: Unrostered approval and warning fields
            'is_unrostered', 'is_approved', 'is_rejected',
            'break_warning_sent', 'overtime_warning_sent', 'hard_limit_warning_sent',
            'long_session_ack_mode',
            # Break tracking fields
            'is_on_break', 'break_start', 'break_end', 'total_break_minutes',
        ]

    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"

    def get_department(self, obj):
        if obj.staff and obj.staff.department:
            return {
                'name': obj.staff.department.name,
                'slug': obj.staff.department.slug,
            }
        return {'name': 'N/A', 'slug': None}
    
    def get_staff_image(self, obj):
        """Get staff face image from face registration"""
        try:
            from .models import StaffFace
            staff_face = StaffFace.objects.get(staff=obj.staff, is_active=True)
            return staff_face.get_image_url()
        except StaffFace.DoesNotExist:
            return None

    def get_roster_shift(self, obj):
        shift = obj.roster_shift
        if not shift:
            return None
        return {
            "id": shift.id,
            "date": shift.shift_date,
            "start": shift.shift_start,
            "end": shift.shift_end,
            "location": getattr(shift.location, "name", None),
            "department": getattr(shift.department, "name", None),
        }

# ─────────────────────────────
# Roster
# ─────────────────────────────

class RosterPeriodSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    finalized_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RosterPeriod
        fields = [
            'id', 'title', 'hotel', 'start_date', 'end_date',
            'created_by', 'created_by_name', 'published',
            # PHASE 4: Finalization fields
            'is_finalized', 'finalized_by', 'finalized_by_name', 'finalized_at'
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return None
    
    def get_finalized_by_name(self, obj):
        if obj.finalized_by:
            return f"{obj.finalized_by.first_name} {obj.finalized_by.last_name}"
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
        Calculate total worked hours using centralized overnight shift logic.
        """
        from .views import calculate_shift_hours, shift_to_datetime_range
        
        shift_date = data['shift_date']
        start = data['shift_start']
        end = data['shift_end']

        # Use centralized calculation
        total_hours = calculate_shift_hours(shift_date, start, end)

        # Deduct break time if provided
        bs, be = data.get('break_start'), data.get('break_end')
        if bs and be:
            # Calculate break duration using same logic
            break_hours = calculate_shift_hours(shift_date, bs, be)
            total_hours = max(0, total_hours - break_hours)

        return total_hours

    # ---------- validation ----------

    def validate(self, attrs):
        """
        Comprehensive validation using centralized overnight shift utilities.
        """
        from .views import (
            is_overnight_shift, validate_shift_duration, 
            validate_overnight_shift_end_time
        )
        
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

        shift_date = attrs.get('shift_date') or getattr(self.instance, 'shift_date', None)
        start = attrs.get('shift_start') or getattr(self.instance, 'shift_start', None)
        end = attrs.get('shift_end') or getattr(self.instance, 'shift_end', None)

        if start and end and shift_date:
            # Validate shift duration doesn't exceed maximum
            try:
                validate_shift_duration(shift_date, start, end, max_hours=12.0)
            except ValueError as e:
                raise serializers.ValidationError(str(e))
            
            # Validate overnight shift end times are reasonable
            try:
                validate_overnight_shift_end_time(start, end, max_end_hour=6)
            except ValueError as e:
                raise serializers.ValidationError(str(e))
            
            # Auto-set is_night_shift based on time crossing midnight
            attrs['is_night_shift'] = is_overnight_shift(start, end)

        # Break validation
        bs, be = attrs.get('break_start'), attrs.get('break_end')
        if (bs and not be) or (be and not bs):
            raise serializers.ValidationError(
                "Both break_start and break_end must be provided, or neither."
            )
        
        # Validate break duration if provided
        if bs and be and shift_date:
            try:
                validate_shift_duration(shift_date, bs, be, max_hours=2.0)
            except ValueError as e:
                raise serializers.ValidationError(f"Break duration error: {e}")

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


# ─────────────────────────────
# PHASE 4: Approval & Alert Serializers
# ─────────────────────────────

class UnrosteredConfirmSerializer(serializers.Serializer):
    """Serializer for confirming unrostered clock-in"""
    staff_id = serializers.IntegerField()
    confirmed = serializers.BooleanField(default=True)


class ClockLogApprovalSerializer(serializers.ModelSerializer):
    """Minimal serializer for approval actions"""
    staff_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ClockLog
        fields = [
            'id', 'staff', 'staff_name', 'time_in', 
            'is_unrostered', 'is_approved', 'is_rejected'
        ]
        read_only_fields = ['id', 'staff', 'staff_name', 'time_in', 'is_unrostered']
    
    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"


class AlertActionSerializer(serializers.Serializer):
    """Serializer for break/overtime alert actions"""
    action = serializers.ChoiceField(choices=[
        ('stay', 'Stay clocked in'),
        ('clock_out', 'Clock out now')
    ])
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class PeriodFinalizationSerializer(serializers.Serializer):
    """Serializer for period finalization validation"""
    confirm = serializers.BooleanField(default=False)
    force = serializers.BooleanField(
        default=False, 
        help_text="Force finalization even with unresolved logs (admin only)"
    )


# ─────────────────────────────
# Enhanced Face Recognition Serializers  
# ─────────────────────────────

import base64
import io
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from .utils import (
    validate_face_encoding, generate_face_registration_response,
    create_face_audit_log
)


class Base64ImageField(serializers.Field):
    """
    Custom field to handle base64 image data and convert to file objects for Cloudinary.
    """
    
    def to_internal_value(self, data):
        """Convert base64 string to Django file object."""
        if not isinstance(data, str):
            raise serializers.ValidationError("Image data must be a base64 string")
        
        if not data.startswith('data:image/'):
            raise serializers.ValidationError("Image data must be a valid base64 data URL")
        
        try:
            # Parse the data URL: data:image/jpeg;base64,/9j/4AAQ...
            header, encoded_data = data.split(',', 1)
            
            # Extract image format from header
            format_part = header.split(';')[0].split('/')[-1]
            if format_part.lower() not in ['jpeg', 'jpg', 'png', 'webp']:
                raise serializers.ValidationError("Unsupported image format")
            
            # Decode base64 data
            decoded_data = base64.b64decode(encoded_data)
            
            # Create PIL Image to validate
            image = Image.open(io.BytesIO(decoded_data))
            
            # Validate image size (max 10MB)
            if len(decoded_data) > 10 * 1024 * 1024:
                raise serializers.ValidationError("Image file too large. Maximum size is 10MB.")
            
            # Create InMemoryUploadedFile object for Cloudinary
            image_file = InMemoryUploadedFile(
                file=io.BytesIO(decoded_data),
                field_name='image',
                name=f'face_image.{format_part}',
                content_type=f'image/{format_part}',
                size=len(decoded_data),
                charset=None
            )
            
            return image_file
            
        except Exception as e:
            raise serializers.ValidationError(f"Invalid image data: {str(e)}")
    
    def to_representation(self, value):
        """Return the Cloudinary URL for the image."""
        if value:
            try:
                return value.url
            except Exception:
                return str(value)
        return None


class FaceRegistrationSerializer(serializers.Serializer):
    """
    Serializer for face registration with Cloudinary image upload and encoding validation.
    """
    image = Base64ImageField(
        help_text="Base64 encoded image data (data:image/jpeg;base64,...)"
    )
    encoding = serializers.ListField(
        child=serializers.FloatField(),
        help_text="128-dimensional face encoding vector",
        allow_empty=False
    )
    staff_id = serializers.IntegerField(
        required=False,
        help_text="Target staff ID (optional, defaults to requesting user)"
    )
    consent_given = serializers.BooleanField(
        default=True,
        help_text="Explicit consent for face data processing"
    )
    
    def validate_encoding(self, value):
        """Validate face encoding format."""
        is_valid, error_message = validate_face_encoding(value)
        if not is_valid:
            raise serializers.ValidationError(error_message)
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        request = self.context.get('request')
        hotel = self.context.get('hotel')
        
        if not request or not hotel:
            raise serializers.ValidationError("Missing request context")
        
        # Determine target staff
        staff_id = data.get('staff_id')
        if staff_id:
            # Admin registering for another staff member
            from staff.models import Staff
            try:
                target_staff = Staff.objects.get(id=staff_id, hotel=hotel)
                data['target_staff'] = target_staff
            except Staff.DoesNotExist:
                raise serializers.ValidationError("Invalid staff ID for this hotel")
        else:
            # Self-registration
            if not hasattr(request.user, 'staff_profile'):
                raise serializers.ValidationError("User does not have staff profile")
            data['target_staff'] = request.user.staff_profile
        
        return data
    
    def create(self, validated_data):
        """Create or update staff face data with Cloudinary storage."""
        target_staff = validated_data['target_staff']
        hotel = self.context['hotel']
        request = self.context['request']
        performing_staff = getattr(request.user, 'staff_profile', None)
        
        # Delete existing face data if any
        StaffFace.objects.filter(staff=target_staff).delete()
        
        # Create new face data
        staff_face = StaffFace.objects.create(
            hotel=hotel,
            staff=target_staff,
            image=validated_data['image'],  # Will be uploaded to Cloudinary
            encoding=validated_data['encoding'],
            consent_given=validated_data.get('consent_given', True),
            registered_by=performing_staff,
            is_active=True
        )
        
        # Update staff profile
        target_staff.has_registered_face = True
        target_staff.save(update_fields=['has_registered_face'])
        
        # Create audit log
        create_face_audit_log(
            hotel=hotel,
            staff=target_staff,
            action='REGISTERED',
            performed_by=performing_staff,
            consent_given=validated_data.get('consent_given', True),
            request=request
        )
        
        return staff_face


class FaceClockInSerializer(serializers.Serializer):
    """
    Serializer for face recognition clock-in/out with enhanced safety features.
    """
    image = Base64ImageField(
        required=False,
        allow_null=True,
        help_text="Base64 encoded face image for recognition (optional if encoding provided)"
    )
    encoding = serializers.ListField(
        child=serializers.FloatField(),
        help_text="128-dimensional face encoding vector for matching"
    )
    location_note = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Optional location or note for this clock action"
    )
    force_action = serializers.ChoiceField(
        choices=[
            ('clock_in', 'Force Clock In'), 
            ('clock_out', 'Force Clock Out'),
            ('start_break', 'Start Break'),
            ('end_break', 'End Break'),
            ('resume_shift', 'Resume Shift')
        ],
        required=False,
        help_text="Force specific clock action (optional)"
    )
    is_kiosk_mode = serializers.BooleanField(
        required=False,
        default=False,
        help_text="True if this is a shared kiosk device (auto-refresh after actions)"
    )
    
    def validate_encoding(self, value):
        """Validate face encoding format."""
        is_valid, error_message = validate_face_encoding(value)
        if not is_valid:
            raise serializers.ValidationError(error_message)
        return value


class StaffFaceEnhancedSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer for StaffFace model with security considerations.
    Excludes sensitive biometric encoding data from API responses.
    """
    staff_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    public_id = serializers.SerializerMethodField()
    encoding_length = serializers.SerializerMethodField()
    registered_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffFace
        fields = [
            'id', 'staff', 'staff_name', 'hotel', 
            'image_url', 'public_id', 'encoding_length',
            'is_active', 'consent_given', 'registered_by_name',
            'created_at', 'updated_at'
        ]
        # Exclude sensitive biometric data from serialization
        # encoding field is intentionally excluded for privacy
    
    def get_staff_name(self, obj):
        return obj.staff.user.get_full_name()
    
    def get_image_url(self, obj):
        return obj.get_image_url()
    
    def get_public_id(self, obj):
        return obj.get_public_id()
    
    def get_encoding_length(self, obj):
        return len(obj.encoding) if obj.encoding else 0
    
    def get_registered_by_name(self, obj):
        if obj.registered_by:
            return obj.registered_by.user.get_full_name()
        return None


class FaceRevocationSerializer(serializers.Serializer):
    """
    Serializer for face data revocation with audit trail.
    """
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional reason for revocation"
    )
    staff_id = serializers.IntegerField(
        required=False,
        help_text="Target staff ID (optional, defaults to requesting user)"
    )
    
    def validate(self, data):
        """Validate revocation request."""
        request = self.context.get('request')
        hotel = self.context.get('hotel')
        
        if not request or not hotel:
            raise serializers.ValidationError("Missing request context")
        
        # Determine target staff
        staff_id = data.get('staff_id')
        if staff_id:
            # Admin revoking for another staff member
            from staff.models import Staff
            try:
                target_staff = Staff.objects.get(id=staff_id, hotel=hotel)
                data['target_staff'] = target_staff
            except Staff.DoesNotExist:
                raise serializers.ValidationError("Invalid staff ID for this hotel")
        else:
            # Self-revocation
            if not hasattr(request.user, 'staff_profile'):
                raise serializers.ValidationError("User does not have staff profile")
            data['target_staff'] = request.user.staff_profile
        
        # Check if staff has face data to revoke
        try:
            face_data = StaffFace.objects.get(staff=data['target_staff'], is_active=True)
            data['face_data'] = face_data
        except StaffFace.DoesNotExist:
            raise serializers.ValidationError("No active face data found for this staff member")
        
        return data
    
    def create(self, validated_data):
        """Revoke face data and update audit trail."""
        face_data = validated_data['face_data']
        request = self.context['request']
        performing_staff = getattr(request.user, 'staff_profile', None)
        
        # Revoke the face data (calls model method with audit log)
        face_data.revoke(
            performed_by=performing_staff,
            reason=validated_data.get('reason')
        )
        
        # Update staff profile
        face_data.staff.has_registered_face = False
        face_data.staff.save(update_fields=['has_registered_face'])
        
        return face_data


class FaceAuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for face audit log entries.
    """
    staff_name = serializers.SerializerMethodField()
    performed_by_name = serializers.SerializerMethodField()
    hotel_slug = serializers.CharField(source='hotel.slug', read_only=True)
    
    class Meta:
        model = FaceAuditLog
        fields = [
            'id', 'hotel_slug', 'staff', 'staff_name', 'action',
            'performed_by', 'performed_by_name', 'reason', 'consent_given',
            'client_ip', 'created_at'
        ]
        # Exclude user_agent from API response for brevity
    
    def get_staff_name(self, obj):
        return obj.staff.user.get_full_name()
    
    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.user.get_full_name()
        return None