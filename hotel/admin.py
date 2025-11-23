# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Hotel, HotelAccessConfig


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
            'fields': ('name', 'slug', 'subdomain', 'logo')
        }),
        ('Location & Description', {
            'fields': ('city', 'country', 'short_description')
        }),
        ('Visibility & Ordering', {
            'fields': ('is_active', 'sort_order'),
            'description': 'Control hotel visibility and display order'
        }),
    )
    
    inlines = [HotelAccessConfigInline]

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 50px;"/>',
                obj.logo.url
            )
        return "-"
    logo_preview.short_description = "Logo"


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
