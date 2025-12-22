from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Room, RoomType, RatePlan, RoomTypeRatePlan,
    DailyRate, Promotion, RoomTypeInventory
)


class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'room_number', 'hotel', 'room_type', 'assigned_booking_display', 
        'is_occupied', 'get_guests_count', 'room_status', 'is_active', 
        'is_out_of_order', 'maintenance_required'
    )

    search_fields = ('room_number', 'hotel__name', 'room_type__name')
    list_filter = (
        'is_occupied', 'hotel', 'room_type', 'room_status', 'is_active', 
        'is_out_of_order', 'maintenance_required'
    )
    list_editable = ('room_type', 'room_status', 'is_active')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hotel', 'room_number', 'room_type')
        }),
        ('Current Assignment', {
            'fields': ('assigned_booking_display',),
            'description': 'Current booking assigned to this room'
        }),
        ('Status', {
            'fields': ('is_occupied', 'room_status', 'is_active', 'is_out_of_order')
        }),
        ('Maintenance', {
            'fields': ('maintenance_required', 'maintenance_priority', 'maintenance_notes')
        }),
        ('Turnover Tracking', {
            'fields': ('last_cleaned_at', 'cleaned_by_staff', 'last_inspected_at', 
                      'inspected_by_staff', 'turnover_notes'),
            'classes': ('collapse',),
        }),
        ('Guest Communication', {
            'fields': ('guest_fcm_token',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('assigned_booking_display',)

    def get_guests_count(self, obj):
        return obj.guests_in_room.count()
    get_guests_count.short_description = 'Number of Guests'

    def assigned_booking_display(self, obj):
        """Display which booking is assigned to this room"""
        try:
            # Import here to avoid circular imports
            from hotel.models import RoomBooking
            
            # Find the booking assigned to this room
            booking = RoomBooking.objects.filter(assigned_room=obj).first()
            
            if booking:
                guest_name = f"{booking.primary_first_name} {booking.primary_last_name}"
                booking_id = booking.booking_id
                
                if booking.checked_in_at:
                    # Guest is checked in
                    return format_html(
                        '<span style="color: green;">✅ {}<br><small>{}</small></span>', 
                        guest_name, booking_id
                    )
                else:
                    # Room assigned but not checked in
                    return format_html(
                        '<span style="color: blue;">🔑 {}<br><small>{}</small></span>', 
                        guest_name, booking_id
                    )
            else:
                # No booking assigned
                if obj.is_occupied:
                    return format_html('<span style="color: orange;">⚠ Occupied (no booking)</span>')
                else:
                    return format_html('<span style="color: gray;">🟢 Available</span>')
                    
        except Exception as e:
            return format_html('<span style="color: red;">❌ Error</span>')
    assigned_booking_display.short_description = "Assigned Booking"


admin.site.register(Room, RoomAdmin)


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'hotel',
        'code',
        'starting_price_from',
        'currency',
        'max_occupancy',
        'is_active',
        'sort_order',
        'photo_preview'
    )
    list_filter = ('hotel', 'is_active', 'currency')
    search_fields = ('name', 'code', 'hotel__name')
    list_editable = ('is_active', 'sort_order')
    ordering = ('sort_order', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hotel', 'code', 'name')
        }),
        ('Room Details', {
            'fields': (
                'short_description',
                'max_occupancy',
                'bed_setup',
                'photo'
            )
        }),
        ('Pricing', {
            'fields': ('starting_price_from', 'currency')
        }),
        ('Booking', {
            'fields': (
                'booking_code',
                'booking_url',
                'availability_message'
            )
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order')
        }),
    )

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 50px;"/>',
                obj.photo.url
            )
        return "-"
    photo_preview.short_description = "Photo"


# ============================================================================
# PMS / RATE MANAGEMENT ADMIN
# ============================================================================

@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'hotel',
        'is_refundable',
        'default_discount_percent',
        'is_active'
    )
    list_filter = ('hotel', 'is_active', 'is_refundable')
    search_fields = ('code', 'name', 'hotel__name')
    list_editable = ('is_active',)
    ordering = ('hotel', 'code')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hotel', 'code', 'name', 'description')
        }),
        ('Configuration', {
            'fields': ('is_refundable', 'default_discount_percent', 'is_active')
        }),
    )


@admin.register(RoomTypeRatePlan)
class RoomTypeRatePlanAdmin(admin.ModelAdmin):
    list_display = (
        'room_type',
        'rate_plan',
        'base_price',
        'is_active'
    )
    list_filter = ('is_active', 'rate_plan__hotel')
    search_fields = ('room_type__name', 'rate_plan__code')
    list_editable = ('is_active',)
    raw_id_fields = ('room_type', 'rate_plan')


@admin.register(DailyRate)
class DailyRateAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'room_type',
        'rate_plan',
        'price'
    )
    list_filter = ('date', 'rate_plan__hotel')
    search_fields = ('room_type__name', 'rate_plan__code')
    date_hierarchy = 'date'
    ordering = ('-date',)
    raw_id_fields = ('room_type', 'rate_plan')


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'hotel',
        'discount_percent',
        'discount_fixed',
        'valid_from',
        'valid_until',
        'is_active'
    )
    list_filter = ('hotel', 'is_active', 'valid_from', 'valid_until')
    search_fields = ('code', 'name', 'hotel__name')
    list_editable = ('is_active',)
    date_hierarchy = 'valid_from'
    ordering = ('-valid_until',)
    
    filter_horizontal = ('room_types', 'rate_plans')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hotel', 'code', 'name', 'description')
        }),
        ('Discount Configuration', {
            'fields': ('discount_percent', 'discount_fixed')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Restrictions', {
            'fields': ('room_types', 'rate_plans', 'min_nights', 'max_nights')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(RoomTypeInventory)
class RoomTypeInventoryAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'room_type',
        'total_rooms',
        'stop_sell'
    )
    list_filter = ('stop_sell', 'room_type__hotel', 'room_type')
    search_fields = ('room_type__name',)
    date_hierarchy = 'date'
    ordering = ('-date',)
    list_editable = ('total_rooms', 'stop_sell')
    raw_id_fields = ('room_type',)
