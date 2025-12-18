# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Hotel,
    HotelAccessConfig,
    BookingOptions,
    RoomBooking,
    BookingGuest,
    PricingQuote,
    Preset,
    HotelPublicPage,
    PublicSection,
    PublicElement,
    PublicElementItem,
    AttendanceSettings,
)


class HotelAccessConfigInline(admin.StackedInline):
    """Inline editor for HotelAccessConfig"""
    model = HotelAccessConfig
    can_delete = False
    verbose_name_plural = 'Access Configuration'
    fields = (
        ('guest_portal_enabled', 'staff_portal_enabled'),
        ('requires_room_pin', 'room_pin_length'),
        'rotate_pin_on_checkout',
        ('allow_multiple_guest_sessions', 'max_active_guest_devices_per_room'),
    )


class BookingOptionsInline(admin.StackedInline):
    """Inline editor for BookingOptions"""
    model = BookingOptions
    can_delete = False
    verbose_name_plural = 'Booking Options'
    fields = (
        ('primary_cta_label', 'primary_cta_url'),
        ('secondary_cta_label', 'secondary_cta_phone'),
        ('terms_url', 'policies_url'),
    )


class BookingGuestInline(admin.TabularInline):
    """Inline editor for BookingGuest (party members)"""
    model = BookingGuest
    extra = 0
    verbose_name_plural = 'Booking Party'
    fields = ('role_display', 'first_name', 'last_name', 'email', 'phone', 'is_staying', 'guest_precheckin_display')
    readonly_fields = ('role_display', 'guest_precheckin_display')
    ordering = ['role', 'created_at']
    
    def role_display(self, obj):
        """Display role with visual indicator"""
        if obj.role == 'PRIMARY':
            return format_html('<strong>👑 PRIMARY</strong>')
        return '👥 COMPANION'
    role_display.short_description = 'Role'
    
    def guest_precheckin_display(self, obj):
        """Display guest-specific precheckin data"""
        if not obj.precheckin_payload:
            return "-"
        
        formatted = []
        for key, value in obj.precheckin_payload.items():
            if value:  # Only show non-empty values
                formatted.append(f"{key}: {value}")
        
        return ', '.join(formatted) if formatted else "-"
    guest_precheckin_display.short_description = 'Precheckin Data'
    
    def get_readonly_fields(self, request, obj=None):
        """Make PRIMARY guest completely read-only"""
        readonly = list(self.readonly_fields)
        if obj and hasattr(obj, 'role') and obj.role == 'PRIMARY':
            # For PRIMARY guests, make all fields read-only
            readonly.extend(['first_name', 'last_name', 'email', 'phone', 'is_staying'])
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of PRIMARY guests"""
        if obj and hasattr(obj, 'role') and obj.role == 'PRIMARY':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('name',),
        'subdomain': ('name',),
    }
    list_display = (
        'name',
        'city',
        'country',
        'is_active',
        'sort_order',
        'logo_preview',
    )
    list_filter = ('is_active', 'country', 'city')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('name', 'slug', 'subdomain', 'city', 'country')
    ordering = ('sort_order', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'subdomain', 'logo', 'hero_image')
        }),
        ('Marketing Content', {
            'fields': ('tagline', 'short_description', 'long_description'),
            'description': 'Public-facing marketing content'
        }),
        ('Location', {
            'fields': (
                'city', 'country',
                'address_line_1', 'address_line_2', 'postal_code',
                ('latitude', 'longitude')
            )
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'website_url', 'booking_url')
        }),
        ('Visibility & Ordering', {
            'fields': ('is_active', 'sort_order'),
            'description': 'Control hotel visibility and display order'
        }),
    )
    
    inlines = [HotelAccessConfigInline, BookingOptionsInline]

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 50px;"/>',
                obj.logo.url
            )
        return "-"
    logo_preview.short_description = "Logo"


@admin.register(Preset)
class PresetAdmin(admin.ModelAdmin):
    """Admin interface for managing presets"""
    list_display = (
        'name',
        'target_type',
        'section_type',
        'key',
        'is_default',
    )
    list_filter = ('target_type', 'section_type', 'is_default')
    search_fields = ('name', 'key', 'description')
    ordering = ('target_type', 'section_type', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'key', 'description', 'is_default')
        }),
        ('Classification', {
            'fields': ('target_type', 'section_type'),
            'description': 'Defines what type of element this preset applies to'
        }),
        ('Configuration', {
            'fields': ('config',),
            'description': 'JSON configuration for frontend styling and behavior',
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(HotelPublicPage)
class HotelPublicPageAdmin(admin.ModelAdmin):
    """Admin interface for managing hotel public pages"""
    list_display = (
        'hotel',
        'global_style_variant',
        'created_at',
        'updated_at',
    )
    list_filter = ('global_style_variant',)
    search_fields = ('hotel__name', 'hotel__slug')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Hotel', {
            'fields': ('hotel',)
        }),
        ('Global Style', {
            'fields': ('global_style_variant',),
            'description': 'Set a global style preset (1-5) that applies to all sections'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HotelAccessConfig)
class HotelAccessConfigAdmin(admin.ModelAdmin):
    list_display = (
        'hotel',
        'guest_portal_enabled',
        'staff_portal_enabled',
        'requires_room_pin',
    )
    list_filter = (
        'guest_portal_enabled',
        'staff_portal_enabled',
        'requires_room_pin',
    )
    search_fields = ('hotel__name',)
    
    fieldsets = (
        ('Portal Toggles', {
            'fields': ('hotel', 'guest_portal_enabled', 'staff_portal_enabled')
        }),
        ('Room PIN Settings', {
            'fields': (
                'requires_room_pin',
                'room_pin_length',
                'rotate_pin_on_checkout'
            )
        }),
        ('Multi-Device Access', {
            'fields': (
                'allow_multiple_guest_sessions',
                'max_active_guest_devices_per_room'
            )
        }),
    )


@admin.register(RoomBooking)
class RoomBookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_id',
        'confirmation_number',
        'primary_guest_name',
        'hotel',
        'room_type',
        'check_in',
        'check_out',
        'status',
        'party_status_display',
        'precheckin_status_display',
        'total_amount',
        'created_at',
        'cancellation_info'
    )
    list_filter = ('status', 'hotel', 'check_in', 'created_at', 'booker_type')
    search_fields = (
        'booking_id',
        'confirmation_number',
        'primary_email',
        'primary_first_name',
        'primary_last_name',
        'booker_email',
        'booker_first_name',
        'booker_last_name'
    )
    readonly_fields = (
        'booking_id',
        'confirmation_number',
        'created_at',
        'updated_at',
        'nights',
        'party_status_display',
        'precheckin_status_display',
        'precheckin_data_display',
        'cancellation_details_formatted',
        'cancelled_by_display',
        'cancellation_date_display',
        'cancellation_reason_display'
    )

    def cancellation_info(self, obj):
        """Display cancellation info in list view"""
        if obj.status == 'CANCELLED' and obj.special_requests:
            # Handle simple format: "CANCELLATION REASON: payment data wrong"
            if obj.special_requests.startswith('CANCELLATION REASON:'):
                reason = obj.special_requests.replace('CANCELLATION REASON:', '').strip()
                return f"❌ {reason[:30]}..."
            # Handle structured format with "--- BOOKING CANCELLED ---"
            elif '--- BOOKING CANCELLED ---' in obj.special_requests:
                parts = obj.special_requests.split('--- BOOKING CANCELLED ---')
                if len(parts) > 1:
                    lines = parts[1].strip().split('\n')
                    for line in lines:
                        if line.startswith('Reason:'):
                            reason = line.replace('Reason:', '').strip()
                            return f"❌ {reason[:30]}..."
            return "❌ Cancelled"
        return "-"
    cancellation_info.short_description = "Cancellation"

    def cancellation_details_formatted(self, obj):
        """Parse and display formatted cancellation details"""
        if obj.status != 'CANCELLED' or not obj.special_requests:
            return "Not cancelled"
        
        formatted = []
        
        # Handle simple format: "CANCELLATION REASON: payment data wrong"
        if obj.special_requests.startswith('CANCELLATION REASON:'):
            reason = obj.special_requests.replace('CANCELLATION REASON:', '').strip()
            formatted.append(f"📅 Date: {obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            formatted.append(f"👤 Cancelled by: Staff (via admin)")
            formatted.append(f"📝 Reason: {reason}")
            return '\n'.join(formatted)
        
        # Handle structured format with "--- BOOKING CANCELLED ---"
        elif '--- BOOKING CANCELLED ---' in obj.special_requests:
            parts = obj.special_requests.split('--- BOOKING CANCELLED ---')
            if len(parts) < 2:
                return "Cancellation details not available"
            
            cancel_section = parts[1].strip()
            lines = cancel_section.split('\n')
            
            details = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    details[key.strip()] = value.strip()
            
            if 'Date' in details:
                formatted.append(f"📅 Date: {details['Date']}")
            if 'By' in details:
                formatted.append(f"👤 Cancelled by: {details['By']}")  
            if 'Reason' in details:
                formatted.append(f"📝 Reason: {details['Reason']}")
            
            return '\n'.join(formatted) if formatted else "Cancellation details not available"
        
        return "Cancellation details not available"
    cancellation_details_formatted.short_description = "Cancellation Details"

    def cancelled_by_display(self, obj):
        """Display who cancelled the booking"""
        if obj.status != 'CANCELLED' or not obj.special_requests:
            return "-"
        
        # Handle simple format: "CANCELLATION REASON: payment data wrong"
        if obj.special_requests.startswith('CANCELLATION REASON:'):
            return "Staff (via admin)"
        
        # Handle structured format with "--- BOOKING CANCELLED ---"
        elif '--- BOOKING CANCELLED ---' in obj.special_requests:
            parts = obj.special_requests.split('--- BOOKING CANCELLED ---')
            if len(parts) > 1:
                lines = parts[1].strip().split('\n')
                for line in lines:
                    if line.startswith('By:'):
                        return line.replace('By:', '').strip()
        
        return "Unknown"
    cancelled_by_display.short_description = "Cancelled By"

    def cancellation_date_display(self, obj):
        """Display cancellation date"""
        if obj.status != 'CANCELLED' or not obj.special_requests:
            return "-"
        
        # Handle simple format: use updated_at timestamp
        if obj.special_requests.startswith('CANCELLATION REASON:'):
            return obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        
        # Handle structured format with "--- BOOKING CANCELLED ---"
        elif '--- BOOKING CANCELLED ---' in obj.special_requests:
            parts = obj.special_requests.split('--- BOOKING CANCELLED ---')
            if len(parts) > 1:
                lines = parts[1].strip().split('\n')
                for line in lines:
                    if line.startswith('Date:'):
                        return line.replace('Date:', '').strip()
        
        return "Unknown"
    cancellation_date_display.short_description = "Cancelled Date"

    def cancellation_reason_display(self, obj):
        """Display cancellation reason"""
        if obj.status != 'CANCELLED' or not obj.special_requests:
            return "-"
        
        # Handle simple format: "CANCELLATION REASON: payment data wrong"
        if obj.special_requests.startswith('CANCELLATION REASON:'):
            return obj.special_requests.replace('CANCELLATION REASON:', '').strip()
        
        # Handle structured format with "--- BOOKING CANCELLED ---"
        elif '--- BOOKING CANCELLED ---' in obj.special_requests:
            parts = obj.special_requests.split('--- BOOKING CANCELLED ---')
            if len(parts) > 1:
                lines = parts[1].strip().split('\n')
                for line in lines:
                    if line.startswith('Reason:'):
                        return line.replace('Reason:', '').strip()
        
        return "No reason provided"
    cancellation_reason_display.short_description = "Cancellation Reason"
    
    def party_status_display(self, obj):
        """Display party completion status"""
        if obj.party_complete:
            party_count = obj.party.filter(is_staying=True).count()
            return format_html('<span style="color: green;">✅ Complete ({} guests)</span>', party_count)
        else:
            missing = obj.party_missing_count
            current = obj.party.filter(is_staying=True).count()
            expected = obj.adults + obj.children
            return format_html(
                '<span style="color: orange;">⚠ Missing {} ({}/{})</span>', 
                missing, current, expected
            )
    party_status_display.short_description = "Party Status"
    
    def precheckin_status_display(self, obj):
        """Display precheckin completion status"""
        if obj.precheckin_submitted_at:
            return format_html('<span style="color: green;">✅ Completed<br><small>{}</small></span>', 
                             obj.precheckin_submitted_at.strftime('%Y-%m-%d %H:%M'))
        else:
            return format_html('<span style="color: gray;">⏳ Not submitted</span>')
    precheckin_status_display.short_description = "Pre-check-in"
    
    def precheckin_data_display(self, obj):
        """Display formatted precheckin payload data"""
        if not obj.precheckin_payload:
            return "No precheckin data"
        
        formatted = []
        for key, value in obj.precheckin_payload.items():
            # Format field names nicely
            field_name = key.replace('_', ' ').title()
            if isinstance(value, bool):
                value_str = "✅ Yes" if value else "❌ No"
            else:
                value_str = str(value) if value else "Not provided"
            
            formatted.append(f"{field_name}: {value_str}")
        
        return format_html('<br>'.join(formatted)) if formatted else "No precheckin data"
    precheckin_data_display.short_description = "Pre-check-in Data"
    
    # Add the inline for party management
    inlines = [BookingGuestInline]
    
    fieldsets = (
        ('Booking Information', {
            'fields': (
                'booking_id',
                'confirmation_number',
                'status',
                'created_at',
                'updated_at'
            )
        }),
        ('Hotel & Room', {
            'fields': ('hotel', 'room_type', 'check_in', 'check_out')
        }),
        ('Guest Information', {
            'fields': (
                'primary_first_name',
                'primary_last_name',
                'primary_email',
                'primary_phone'
            )
        }),
        ('Occupancy & Party', {
            'fields': ('adults', 'children'),
            'description': 'Expected guest counts - party details managed below in "Booking Party" section'
        }),
        ('Pricing', {
            'fields': ('total_amount', 'currency', 'promo_code')
        }),
        ('Payment', {
            'fields': (
                'payment_provider',
                'payment_reference',
                'paid_at'
            )
        }),
        ('Cancellation Information', {
            'fields': (
                'cancellation_details_formatted',
                'cancelled_by_display', 
                'cancellation_date_display',
                'cancellation_reason_display'
            ),
            'classes': ('collapse',),
            'description': 'Cancellation details (only visible for cancelled bookings)'
        }),
        ('Pre-check-in Information', {
            'fields': (
                'precheckin_status_display',
                'precheckin_data_display'
            ),
            'description': 'Guest-submitted precheckin data (ETA, special requests, nationality, etc.)'
        }),
        ('Additional Information', {
            'fields': ('special_requests', 'internal_notes')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """Show cancellation section only for cancelled bookings"""
        fieldsets = list(self.fieldsets)
        
        if obj and obj.status == 'CANCELLED':
            # Show cancellation section for cancelled bookings
            return fieldsets
        else:
            # Hide cancellation section for non-cancelled bookings
            return [fs for fs in fieldsets if fs[0] != 'Cancellation Information']


@admin.register(PricingQuote)
class PricingQuoteAdmin(admin.ModelAdmin):
    list_display = (
        'quote_id',
        'hotel',
        'room_type',
        'check_in',
        'check_out',
        'total',
        'created_at',
        'valid_until',
        'is_valid'
    )
    list_filter = ('hotel', 'created_at')
    search_fields = ('quote_id',)
    readonly_fields = ('quote_id', 'created_at', 'is_valid')
    
    fieldsets = (
        ('Quote Information', {
            'fields': ('quote_id', 'hotel', 'room_type')
        }),
        ('Dates & Occupancy', {
            'fields': (
                'check_in',
                'check_out',
                'adults',
                'children'
            )
        }),
        ('Pricing Breakdown', {
            'fields': (
                'base_price_per_night',
                'number_of_nights',
                'subtotal',
                'taxes',
                'fees',
                'discount',
                'total',
                'currency'
            )
        }),
        ('Promotions', {
            'fields': ('promo_code',)
        }),
        ('Validity', {
            'fields': ('created_at', 'valid_until')
        }),
    )


class PublicElementInline(admin.StackedInline):
    """Inline editor for PublicElement"""
    model = PublicElement
    can_delete = False
    verbose_name_plural = 'Element'
    fields = (
        'element_type',
        'title',
        'subtitle',
        'body',
        'image_url',
        'settings',
    )
    extra = 0


class PublicElementItemInline(admin.TabularInline):
    """Inline editor for PublicElementItem"""
    model = PublicElementItem
    fields = (
        'title',
        'subtitle',
        'image_url',
        'badge',
        'cta_label',
        'cta_url',
        'sort_order',
        'is_active',
    )
    extra = 0
    ordering = ['sort_order']


@admin.register(PublicSection)
class PublicSectionAdmin(admin.ModelAdmin):
    list_display = (
        'hotel',
        'position',
        'name',
        'element_type_display',
        'is_active',
        'created_at'
    )
    list_filter = ('hotel', 'is_active', 'created_at')
    list_editable = ('position', 'is_active')
    search_fields = ('hotel__name', 'name')
    ordering = ('hotel', 'position')
    
    fieldsets = (
        ('Section Information', {
            'fields': ('hotel', 'name', 'position', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    inlines = [PublicElementInline]

    def element_type_display(self, obj):
        """Display the element type from the related element"""
        if hasattr(obj, 'element'):
            return obj.element.element_type
        return "-"
    element_type_display.short_description = "Element Type"


@admin.register(PublicElement)
class PublicElementAdmin(admin.ModelAdmin):
    list_display = (
        'section',
        'element_type',
        'title',
        'created_at'
    )
    list_filter = ('element_type', 'created_at')
    search_fields = ('section__hotel__name', 'title', 'element_type')
    
    fieldsets = (
        ('Element Information', {
            'fields': ('section', 'element_type')
        }),
        ('Content', {
            'fields': ('title', 'subtitle', 'body', 'image_url', 'settings')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    inlines = [PublicElementItemInline]


@admin.register(PublicElementItem)
class PublicElementItemAdmin(admin.ModelAdmin):
    list_display = (
        'element',
        'title',
        'sort_order',
        'is_active',
        'created_at'
    )
    list_filter = ('is_active', 'created_at')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('element__section__hotel__name', 'title')
    ordering = ('element', 'sort_order')
    
    fieldsets = (
        ('Item Information', {
            'fields': ('element', 'title', 'subtitle')
        }),
        ('Content', {
            'fields': ('body', 'image_url', 'badge')
        }),
        ('Call to Action', {
            'fields': ('cta_label', 'cta_url')
        }),
        ('Display', {
            'fields': ('sort_order', 'is_active', 'meta')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    """Admin interface for managing hotel attendance settings"""
    list_display = (
        'hotel',
        'face_attendance_enabled',
        'face_departments_display',
        'break_warning_hours',
        'overtime_warning_hours',
        'enforce_limits',
    )
    list_filter = ('face_attendance_enabled', 'enforce_limits')
    search_fields = ('hotel__name', 'hotel__slug')
    readonly_fields = ('face_departments_display',)
    
    fieldsets = (
        ('Hotel', {
            'fields': ('hotel',)
        }),
        ('Time Limits & Warnings', {
            'fields': (
                'break_warning_hours',
                'overtime_warning_hours', 
                'hard_limit_hours',
                'enforce_limits',
            ),
            'description': 'Configure shift duration warnings and limits'
        }),
        ('Face Recognition Settings', {
            'fields': (
                'face_attendance_enabled',
                'face_attendance_min_confidence',
                'require_face_consent',
                'allow_face_self_registration',
                'face_data_retention_days',
                'face_attendance_departments',
                'face_departments_display',
            ),
            'description': 'Configure face recognition for attendance tracking'
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Add help text for face_attendance_departments field"""
        form = super().get_form(request, obj, **kwargs)
        if 'face_attendance_departments' in form.base_fields:
            if obj and obj.hotel:
                # Show available departments for this hotel (through staff members)
                from staff.models import Department
                departments = Department.objects.filter(
                    staff_members__hotel=obj.hotel
                ).distinct()
                dept_info = [f"{dept.name} (ID: {dept.id})" for dept in departments]
                help_text = (
                    f'Available departments for {obj.hotel.name}: '
                    f'{", ".join(dept_info) if dept_info else "No departments found"}. '
                    'Enter department IDs as JSON list, e.g., [1, 2, 3]. Leave empty to allow all departments.'
                )
            else:
                help_text = (
                    'JSON list of department IDs that can use face attendance. '
                    'Leave empty to allow all departments. Example: [1, 2, 3]'
                )
            form.base_fields['face_attendance_departments'].help_text = help_text
        return form
    
    def face_departments_display(self, obj):
        """Display department names instead of IDs"""
        if not obj.face_attendance_departments:
            return "All departments allowed"
        
        try:
            from staff.models import Department
            total_departments = Department.objects.count()
            enabled_count = len(obj.face_attendance_departments)
            
            # Check if all departments are enabled
            if enabled_count == total_departments:
                return f"🌟 ALL departments ({enabled_count})"
            
            # Get department names
            departments = Department.objects.filter(
                id__in=obj.face_attendance_departments
            ).values_list('name', flat=True)
            
            dept_names = list(departments)
            
            # Show first few names, then count if too many
            if len(dept_names) <= 3:
                return ", ".join(dept_names)
            else:
                return f"{', '.join(dept_names[:3])} + {len(dept_names) - 3} more"
                
        except Exception as e:
            return f"Error: {str(obj.face_attendance_departments)}"
    
    face_departments_display.short_description = "Allowed Departments"
