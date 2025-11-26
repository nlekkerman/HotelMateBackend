# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Hotel,
    HotelAccessConfig,
    BookingOptions,
    RoomBooking,
    PricingQuote,
    Preset,
    HotelPublicPage,
    PublicSection,
    PublicElement,
    PublicElementItem,
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
        'guest_name',
        'hotel',
        'room_type',
        'check_in',
        'check_out',
        'status',
        'total_amount',
        'created_at'
    )
    list_filter = ('status', 'hotel', 'check_in', 'created_at')
    search_fields = (
        'booking_id',
        'confirmation_number',
        'guest_email',
        'guest_first_name',
        'guest_last_name'
    )
    readonly_fields = (
        'booking_id',
        'confirmation_number',
        'created_at',
        'updated_at',
        'nights'
    )
    
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
                'guest_first_name',
                'guest_last_name',
                'guest_email',
                'guest_phone'
            )
        }),
        ('Occupancy', {
            'fields': ('adults', 'children')
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
        ('Additional Information', {
            'fields': ('special_requests', 'internal_notes')
        }),
    )


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
