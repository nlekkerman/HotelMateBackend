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
    CancellationPolicy,
    CancellationPolicyTier,
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


class BookingGuestInline(admin.StackedInline):
    """Inline editor for BookingGuest (party members) - Multi-row format"""
    model = BookingGuest
    extra = 0
    verbose_name_plural = 'Booking Party'
    fields = (
        'comprehensive_guest_display',
        ('first_name', 'last_name'),
        ('email', 'phone'),
        'is_staying',
        'comprehensive_precheckin_display'
    )
    readonly_fields = ('comprehensive_guest_display', 'comprehensive_precheckin_display')
    ordering = ['role', 'created_at']
    
    def comprehensive_guest_display(self, obj):
        """Display comprehensive guest information in multi-row format"""
        # Guest basic info with role
        if obj.role == 'PRIMARY':
            role_badge = '<span style="background:#28a745;color:white;padding:2px 8px;border-radius:3px;font-weight:bold;">👑 PRIMARY GUEST</span>'
        else:
            role_badge = '<span style="background:#6c757d;color:white;padding:2px 8px;border-radius:3px;">👥 COMPANION</span>'
        
        # Contact info
        contact_info = f"📧 {obj.email or 'No email'} | 📞 {obj.phone or 'No phone'}"
        
        # Staying status
        staying_status = "🛏️ Staying" if obj.is_staying else "🚪 Not staying"
        
        # Build comprehensive display
        html_parts = [
            f'<div style="margin-bottom:8px;">{role_badge}</div>',
            f'<div style="margin-bottom:4px;"><strong>{obj.first_name} {obj.last_name}</strong></div>',
            f'<div style="margin-bottom:4px;color:#666;">{contact_info}</div>',
            f'<div style="color:#666;">{staying_status}</div>'
        ]
        
        return format_html(''.join(html_parts))
    comprehensive_guest_display.short_description = 'Guest Information'
    
    def comprehensive_precheckin_display(self, obj):
        """Display all precheckin data in multi-row format"""
        if not obj.precheckin_payload:
            return format_html('<div style="background:#f8d7da;color:#721c24;font-style:italic;padding:8px;border-radius:4px;border:1px solid #f5c6cb;">❌ No precheckin data submitted</div>')
        
        # Get all precheckin data
        nationality = obj.precheckin_payload.get('nationality')
        country_res = obj.precheckin_payload.get('country_of_residence')
        
        html_parts = ['<div style="background:#e8f5e8;padding:10px;border-radius:4px;margin:5px 0;border:1px solid #c3e6cb;">']
        html_parts.append('<div style="color:#155724;font-weight:bold;margin-bottom:8px;font-size:14px;">✅ Precheckin Data Submitted</div>')
        
        # Display nationality information prominently
        if nationality:
            html_parts.append(f'<div style="margin-bottom:4px;color:#212529;font-size:13px;"><strong style="color:#000000;">🌍 Nationality:</strong> <span style="color:#495057;font-weight:600;">{nationality}</span></div>')
        
        if country_res and country_res != nationality:
            html_parts.append(f'<div style="margin-bottom:4px;color:#212529;font-size:13px;"><strong style="color:#0056b3;">🏠 Residence:</strong> <span style="color:#495057;font-weight:600;">{country_res}</span></div>')
        
        # Display other precheckin fields
        other_data = []
        for key, value in obj.precheckin_payload.items():
            if value and key not in ['nationality', 'country_of_residence']:
                field_name = key.replace('_', ' ').title()
                other_data.append(f'<div style="margin-bottom:2px;"><strong>{field_name}:</strong> {value}</div>')
        
        if other_data:
            html_parts.append('<div style="margin-top:8px;padding-top:8px;border-top:1px solid #dee2e6;">')
            html_parts.extend(other_data)
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return format_html(''.join(html_parts))
    comprehensive_precheckin_display.short_description = 'Precheckin Information'
    
    def get_readonly_fields(self, request, obj=None):
        """Make PRIMARY guest data read-only but allow companion editing"""
        readonly = list(self.readonly_fields)
        if obj and hasattr(obj, 'role') and obj.role == 'PRIMARY':
            # For PRIMARY guests, make all basic fields read-only
            readonly.extend(['first_name', 'last_name', 'email', 'phone', 'is_staying'])
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of PRIMARY guests"""
        if obj and hasattr(obj, 'role') and obj.role == 'PRIMARY':
            return False
        return super().has_delete_permission(request, obj)
    
    class Media:
        css = {
            'all': ('admin/css/custom_inline.css',)
        }
        js = ('admin/js/collapse_inlines.js',)


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
        'assigned_room_display',
        'room_move_info',
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
        'assigned_room_display',
        'room_assigned_at',
        'room_assigned_by',
        'room_moved_at',
        'room_moved_by',
        'room_moved_from',
        'party_status_display',
        'precheckin_status_display',
        'precheckin_data_display',
        'cancellation_policy_info_display',
        'cancellation_details_formatted',
        'cancelled_by_display',
        'cancellation_date_display',
        'cancellation_reason_display',
        'cancellation_policy_display',
        'cancellation_fee_display',
        'refund_amount_display',
        'refund_processed_display'
    )

    def room_move_info(self, obj):
        """Display room move information in list view"""
        if obj.room_moved_at and obj.room_moved_from:
            return format_html(
                '🔄 {} → {} <br/><small>📅 {}</small>',
                obj.room_moved_from.room_number,
                obj.assigned_room.room_number if obj.assigned_room else 'None',
                obj.room_moved_at.strftime('%m/%d %H:%M')
            )
        return "-"
    room_move_info.short_description = "Room Move"

    def cancellation_info(self, obj):
        """Display cancellation info in list view using actual database fields"""
        if obj.status == 'CANCELLED':
            info_parts = []
            if obj.cancelled_at:
                info_parts.append(f"📅 {obj.cancelled_at.strftime('%m/%d')}")  
            if obj.cancellation_fee and obj.cancellation_fee > 0:
                info_parts.append(f"💰 €{obj.cancellation_fee}")
            if obj.refund_amount and obj.refund_amount > 0:
                info_parts.append(f"💳 €{obj.refund_amount}")
            
            if info_parts:
                return f"❌ {' • '.join(info_parts)}"
            else:
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
        """Display who cancelled the booking using actual database field"""
        if obj.status != 'CANCELLED':
            return "-"
        
        # Use actual cancellation_reason field instead of parsing special_requests
        if obj.cancellation_reason:
            # Extract who cancelled from the reason string if it contains that info
            if 'staff cancellation' in obj.cancellation_reason.lower():
                return "Staff"
            elif 'guest cancellation' in obj.cancellation_reason.lower():
                return "Guest"  
            elif 'token' in obj.cancellation_reason.lower():
                return "Guest (via token)"
            elif 'admin' in obj.cancellation_reason.lower():
                return "Staff (admin)"
            else:
                return "Staff"  # Default for most cancellations
        
        return "Unknown"
    cancelled_by_display.short_description = "Cancelled By"

    def cancellation_date_display(self, obj):
        """Display cancellation date using actual database field"""
        if obj.cancelled_at:
            return obj.cancelled_at.strftime('%Y-%m-%d %H:%M:%S')
        return "-"
    cancellation_date_display.short_description = "Cancelled Date"

    def cancellation_reason_display(self, obj):
        """Display cancellation reason using actual database field"""
        if obj.cancellation_reason:
            return obj.cancellation_reason
        return "No reason provided"
    cancellation_reason_display.short_description = "Cancellation Reason"
    
    def cancellation_policy_display(self, obj):
        """Display cancellation policy information"""
        if obj.cancellation_policy_snapshot:
            policy_data = obj.cancellation_policy_snapshot
            template = policy_data.get('template', 'Unknown')
            hours_before = policy_data.get('hours_before_checkin', 'N/A')
            penalty_type = policy_data.get('penalty_type', 'N/A')
            
            formatted_lines = [
                f"📋 Template: {template}",
                f"⏰ Hours before check-in: {hours_before}",
                f"💸 Penalty type: {penalty_type}"
            ]
            
            if penalty_type == 'PERCENTAGE' and 'penalty_percentage' in policy_data:
                formatted_lines.append(f"📊 Penalty: {policy_data['penalty_percentage']}%")
            elif penalty_type == 'FIXED' and 'penalty_amount' in policy_data:
                formatted_lines.append(f"💰 Penalty: €{policy_data['penalty_amount']}")
                
            return '\n'.join(formatted_lines)
        elif obj.cancellation_policy:
            # Fall back to direct policy relation
            policy = obj.cancellation_policy
            return f"📋 {policy.template} policy (ID: {policy.id})"
        else:
            return "No policy set"
    cancellation_policy_display.short_description = "Cancellation Policy"
    
    def cancellation_fee_display(self, obj):
        """Display cancellation fee from database field"""
        if obj.cancellation_fee is not None:
            return f"€{obj.cancellation_fee}"
        return "-"
    cancellation_fee_display.short_description = "Cancellation Fee"
    
    def refund_amount_display(self, obj):
        """Display refund amount from database field"""
        if obj.refund_amount is not None:
            return f"€{obj.refund_amount}"
        return "-"
    refund_amount_display.short_description = "Refund Amount"
    
    def refund_processed_display(self, obj):
        """Display when refund was processed"""
        if obj.refund_processed_at:
            return obj.refund_processed_at.strftime('%Y-%m-%d %H:%M:%S')
        return "-"
    refund_processed_display.short_description = "Refund Processed At"
    
    def cancellation_policy_info_display(self, obj):
        """Display cancellation policy information for any booking status"""
        policy_info = []
        
        # Check for direct policy relation first
        if obj.cancellation_policy:
            policy = obj.cancellation_policy
            policy_info.append(f"📋 Policy: {policy.name} ({policy.code})")
            policy_info.append(f"🏷️ Template: {policy.template_type}")
            
            if policy.free_until_hours:
                policy_info.append(f"⏰ Free until: {policy.free_until_hours} hours before check-in")
            
            if policy.penalty_type and policy.penalty_type != 'NONE':
                penalty_desc = ""
                if policy.penalty_type == 'FIXED' and policy.penalty_amount:
                    penalty_desc = f"€{policy.penalty_amount}"
                elif policy.penalty_type == 'PERCENTAGE' and policy.penalty_percentage:
                    penalty_desc = f"{policy.penalty_percentage}%"
                elif policy.penalty_type == 'FIRST_NIGHT':
                    penalty_desc = "First night cost"
                elif policy.penalty_type == 'FULL_STAY':
                    penalty_desc = "Full stay cost"
                else:
                    penalty_desc = policy.penalty_type
                policy_info.append(f"💰 Penalty: {penalty_desc}")
            else:
                policy_info.append("💰 Penalty: No penalty")
                
        # Check for policy snapshot (for older bookings or bookings with snapshotted policies)
        elif hasattr(obj, 'cancellation_policy_snapshot') and obj.cancellation_policy_snapshot:
            policy_data = obj.cancellation_policy_snapshot
            policy_info.append("📸 Snapshot Policy (from booking time):")
            
            template = policy_data.get('template_type', policy_data.get('template', 'Unknown'))
            policy_info.append(f"🏷️ Template: {template}")
            
            free_hours = policy_data.get('free_until_hours', policy_data.get('hours_before_checkin'))
            if free_hours:
                policy_info.append(f"⏰ Free until: {free_hours} hours before check-in")
            
            penalty_type = policy_data.get('penalty_type', 'Unknown')
            if penalty_type and penalty_type != 'NONE':
                penalty_desc = ""
                if penalty_type == 'FIXED' and 'penalty_amount' in policy_data:
                    penalty_desc = f"€{policy_data['penalty_amount']}"
                elif penalty_type == 'PERCENTAGE' and 'penalty_percentage' in policy_data:
                    penalty_desc = f"{policy_data['penalty_percentage']}%"
                elif penalty_type == 'FIRST_NIGHT':
                    penalty_desc = "First night cost"
                elif penalty_type == 'FULL_STAY':
                    penalty_desc = "Full stay cost"
                else:
                    penalty_desc = penalty_type
                policy_info.append(f"💰 Penalty: {penalty_desc}")
        else:
            policy_info.append("❌ No cancellation policy set")
            
        if policy_info:
            return '\n'.join(policy_info)
        else:
            return "No policy information available"
    cancellation_policy_info_display.short_description = "Cancellation Policy"
    
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
    
    def assigned_room_display(self, obj):
        """Display assigned room information"""
        if obj.assigned_room:
            room_info = f"Room {obj.assigned_room.room_number}"
            if obj.checked_in_at:
                # Guest is checked in
                return format_html(
                    '<span style="color: green;">🏨 {} <br><small>✅ Checked In</small></span>', 
                    room_info
                )
            else:
                # Room assigned but not checked in
                return format_html(
                    '<span style="color: blue;">🔑 {} <br><small>⏳ Assigned</small></span>', 
                    room_info
                )
        else:
            # No room assigned
            if obj.status == 'CONFIRMED':
                return format_html('<span style="color: orange;">❌ No Room<br><small>⚠ Needs Assignment</small></span>')
            else:
                return format_html('<span style="color: gray;">-</span>')
    assigned_room_display.short_description = "Assigned Room"
    
    def precheckin_status_display(self, obj):
        """Display precheckin completion status"""
        if obj.precheckin_submitted_at:
            return format_html('<span style="color: green;">✅ Completed<br><small>{}</small></span>', 
                             obj.precheckin_submitted_at.strftime('%Y-%m-%d %H:%M'))
        else:
            return format_html('<span style="color: gray;">⏳ Not submitted</span>')
    precheckin_status_display.short_description = "Pre-check-in"
    
    def precheckin_data_display(self, obj):
        """Display comprehensive party precheckin data in multi-row format"""
        # Check if any guest has precheckin data
        guests_with_data = obj.party.filter(precheckin_payload__isnull=False).exclude(precheckin_payload={})
        
        if not guests_with_data.exists():
            return format_html('<div style="background:#f8d7da;color:#721c24;font-style:italic;padding:8px;border-radius:4px;border:1px solid #f5c6cb;">❌ No precheckin data from any party member</div>')
        
        html_parts = ['<div style="background:#e8f5e8;padding:12px;border-radius:6px;margin:5px 0;border:1px solid #c3e6cb;">']
        html_parts.append(f'<div style="color:#155724;font-weight:bold;margin-bottom:12px;font-size:14px;">✅ Precheckin Data Summary ({guests_with_data.count()} guests completed)</div>')
        
        # Display data for each guest who completed precheckin
        for guest in guests_with_data.order_by('role', 'created_at'):
            role_label = "👑 PRIMARY" if guest.role == 'PRIMARY' else "👥 COMPANION"
            guest_name = f"{guest.first_name} {guest.last_name}"
            
            html_parts.append(f'<div style="margin-bottom:10px;padding:8px;border-left:3px solid #007bff;background:white;">')
            html_parts.append(f'<div style="font-weight:bold;margin-bottom:6px;color:#000000;">{role_label} - {guest_name}</div>')
            
            # Display nationality and residence prominently
            nationality = guest.precheckin_payload.get('nationality')
            country_res = guest.precheckin_payload.get('country_of_residence')
            
            if nationality:
                html_parts.append(f'<div style="margin-bottom:3px;color:#212529;font-size:12px;"><strong style="color:#0056b3;">🌍 Nationality:</strong> <span style="color:#495057;font-weight:600;">{nationality}</span></div>')
            
            if country_res and country_res != nationality:
                html_parts.append(f'<div style="margin-bottom:3px;color:#212529;font-size:12px;"><strong style="color:#0056b3;">🏠 Residence:</strong> <span style="color:#495057;font-weight:600;">{country_res}</span></div>')
            
            # Display other precheckin data
            other_fields = []
            for key, value in guest.precheckin_payload.items():
                if value and key not in ['nationality', 'country_of_residence']:
                    field_name = key.replace('_', ' ').title()
                    if isinstance(value, bool):
                        value_str = "✅ Yes" if value else "❌ No"
                    else:
                        value_str = str(value)
                    other_fields.append(f'<div style="margin-bottom:2px;font-size:0.9em;color:#666;">• <strong>{field_name}:</strong> {value_str}</div>')
            
            if other_fields:
                html_parts.extend(other_fields)
            
            html_parts.append('</div>')
        
        # Show booking-level precheckin data if exists
        if obj.precheckin_payload:
            html_parts.append('<div style="margin-top:12px;padding-top:8px;border-top:1px solid #dee2e6;">')
            html_parts.append('<div style="font-weight:bold;margin-bottom:6px;">📋 Booking-Level Data</div>')
            
            for key, value in obj.precheckin_payload.items():
                field_name = key.replace('_', ' ').title()
                if isinstance(value, bool):
                    value_str = "✅ Yes" if value else "❌ No"
                else:
                    value_str = str(value) if value else "Not provided"
                html_parts.append(f'<div style="margin-bottom:2px;font-size:0.9em;">• <strong>{field_name}:</strong> {value_str}</div>')
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return format_html(''.join(html_parts))
    precheckin_data_display.short_description = "Complete Precheckin Data"
    
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
        ('Room Assignment', {
            'fields': ('assigned_room', 'assigned_room_display', 'room_assigned_at', 'room_assigned_by'),
            'description': 'Physical room assignment and check-in status'
        }),
        ('Room Move History', {
            'fields': (
                ('room_moved_at', 'room_moved_by'),
                'room_moved_from',
                'room_move_reason',
                'room_move_notes'
            ),
            'classes': ('collapse',),
            'description': 'Room move audit trail for in-house guests (only visible if room was moved)'
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
        ('Cancellation Policy', {
            'fields': (
                'cancellation_policy_info_display',
            ),
            'description': 'Cancellation policy attached to this booking'
        }),
        ('Cancellation Details', {
            'fields': (
                ('cancelled_by_display', 'cancellation_date_display'),
                'cancellation_reason_display',
                'cancellation_policy_display', 
                ('cancellation_fee_display', 'refund_amount_display'),
                'refund_processed_display',
                'cancellation_details_formatted'  # Keep legacy formatted view for reference
            ),
            'classes': ('collapse',),
            'description': 'Cancellation details including policy, fees, and refunds (only visible for cancelled bookings)'
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
        """Show cancellation details section only for cancelled bookings"""
        fieldsets = list(self.fieldsets)
        
        if obj and obj.status == 'CANCELLED':
            # Show both policy info and cancellation details for cancelled bookings
            return fieldsets
        else:
            # Show only policy info, hide cancellation details for non-cancelled bookings
            return [fs for fs in fieldsets if fs[0] != 'Cancellation Details']


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


# Cancellation Policy Admin
class CancellationPolicyTierInline(admin.TabularInline):
    model = CancellationPolicyTier
    extra = 0
    fields = ('hours_before_checkin', 'penalty_type', 'penalty_amount', 'penalty_percentage')
    ordering = ['-hours_before_checkin']  # Show highest hours first (earliest deadlines)


@admin.register(CancellationPolicy)
class CancellationPolicyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'hotel',
        'name',
        'code', 
        'template_type',
        'free_until_hours',
        'penalty_display',
        'is_active',
        'created_at'
    )
    list_filter = ('hotel', 'template_type', 'penalty_type', 'is_active', 'created_at')
    search_fields = ('hotel__name', 'name', 'code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hotel', 'name', 'code', 'description', 'template_type', 'is_active')
        }),
        ('Policy Settings', {
            'fields': (
                'free_until_hours',
                'penalty_type', 
                'penalty_amount',
                'penalty_percentage',
                'no_show_penalty_type'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [CancellationPolicyTierInline]
    
    def penalty_display(self, obj):
        """Display penalty information"""
        if obj.penalty_type == 'NONE':
            return "No penalty"
        elif obj.penalty_type == 'FIXED' and obj.penalty_amount:
            return f"€{obj.penalty_amount}"
        elif obj.penalty_type == 'PERCENTAGE' and obj.penalty_percentage:
            return f"{obj.penalty_percentage}%"
        elif obj.penalty_type == 'FIRST_NIGHT':
            return "First night cost"
        elif obj.penalty_type == 'FULL_STAY':
            return "Full stay cost"
        else:
            return obj.penalty_type
    penalty_display.short_description = "Penalty"
    
    def get_queryset(self, request):
        """Filter by hotel if user has hotel scope"""
        qs = super().get_queryset(request)
        # Add hotel filtering logic here if needed
        return qs


@admin.register(CancellationPolicyTier) 
class CancellationPolicyTierAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'policy',
        'hours_before_checkin', 
        'penalty_type',
        'penalty_display'
    )
    list_filter = ('policy__hotel', 'penalty_type')
    search_fields = ('policy__hotel__name',)
    
    def penalty_display(self, obj):
        """Display penalty information for tier"""
        if obj.penalty_type == 'NONE':
            return "No penalty"
        elif obj.penalty_type == 'FIXED' and obj.penalty_amount:
            return f"€{obj.penalty_amount}"
        elif obj.penalty_type == 'PERCENTAGE' and obj.penalty_percentage:
            return f"{obj.penalty_percentage}%"
        elif obj.penalty_type == 'FIRST_NIGHT':
            return "First night cost"
        elif obj.penalty_type == 'FULL_STAY':
            return "Full stay cost"
        else:
            return obj.penalty_type
    penalty_display.short_description = "Penalty"
