# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Hotel,
    HotelAccessConfig,
    BookingOptions,
    Offer,
    LeisureActivity
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


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'hotel',
        'tag',
        'valid_from',
        'valid_to',
        'is_active',
        'sort_order',
        'photo_preview'
    )
    list_filter = ('hotel', 'is_active', 'tag', 'valid_from')
    search_fields = ('title', 'short_description', 'hotel__name')
    list_editable = ('is_active', 'sort_order')
    ordering = ('sort_order', '-created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hotel', 'title', 'tag', 'photo')
        }),
        ('Description', {
            'fields': ('short_description', 'details_text', 'details_html')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('Booking', {
            'fields': ('book_now_url',)
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


@admin.register(LeisureActivity)
class LeisureActivityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'hotel',
        'category',
        'is_active',
        'sort_order',
        'image_preview'
    )
    list_filter = ('hotel', 'category', 'is_active')
    search_fields = ('name', 'short_description', 'hotel__name')
    list_editable = ('is_active', 'sort_order')
    ordering = ('category', 'sort_order', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hotel', 'name', 'category', 'icon')
        }),
        ('Description', {
            'fields': ('short_description', 'details_html')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px;"/>',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Image"
