from rest_framework import serializers
from .models import (
    Hotel,
    HotelAccessConfig,
    BookingOptions,
    HotelPublicSettings,
    Offer,
    LeisureActivity,
    RoomBooking,
    PricingQuote
)
from rooms.models import RoomType
import re


class HotelAccessConfigSerializer(serializers.ModelSerializer):
    """Serializer for HotelAccessConfig - portal settings"""
    class Meta:
        model = HotelAccessConfig
        fields = [
            'guest_portal_enabled',
            'staff_portal_enabled',
        ]


class HotelPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer for Hotel with branding and portal config.
    Used for guest/staff portal discovery.
    """
    logo_url = serializers.SerializerMethodField()
    guest_base_path = serializers.CharField(read_only=True)
    staff_base_path = serializers.CharField(read_only=True)
    guest_portal_enabled = serializers.BooleanField(
        source='access_config.guest_portal_enabled',
        read_only=True
    )
    staff_portal_enabled = serializers.BooleanField(
        source='access_config.staff_portal_enabled',
        read_only=True
    )

    class Meta:
        model = Hotel
        fields = [
            'id',
            'name',
            'slug',
            'city',
            'country',
            'short_description',
            'logo_url',
            'guest_base_path',
            'staff_base_path',
            'guest_portal_enabled',
            'staff_portal_enabled',
        ]

    def get_logo_url(self, obj):
        """Return logo URL or None"""
        if obj.logo:
            return obj.logo.url
        return None


class HotelSerializer(serializers.ModelSerializer):
    """Standard Hotel serializer for admin/internal use"""
    class Meta:
        model = Hotel
        fields = ['id', 'name', 'slug', 'subdomain', 'logo']
        extra_kwargs = {
            'slug': {'required': True}
        }


class BookingOptionsSerializer(serializers.ModelSerializer):
    """Serializer for booking call-to-action options"""
    class Meta:
        model = BookingOptions
        fields = [
            'primary_cta_label',
            'primary_cta_url',
            'secondary_cta_label',
            'secondary_cta_phone',
            'terms_url',
            'policies_url'
        ]


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer for room type marketing information"""
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = RoomType
        fields = [
            'code',
            'name',
            'short_description',
            'max_occupancy',
            'bed_setup',
            'photo_url',
            'starting_price_from',
            'currency',
            'booking_code',
            'booking_url',
            'availability_message'
        ]

    def get_photo_url(self, obj):
        """Return photo URL or None"""
        if obj.photo:
            return obj.photo.url
        return None


class OfferSerializer(serializers.ModelSerializer):
    """Serializer for hotel offers and packages"""
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'title',
            'short_description',
            'details_html',
            'valid_from',
            'valid_to',
            'tag',
            'book_now_url',
            'photo_url'
        ]

    def get_photo_url(self, obj):
        """Return photo URL or None"""
        if obj.photo:
            return obj.photo.url
        return None


class LeisureActivitySerializer(serializers.ModelSerializer):
    """Serializer for leisure activities and facilities"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = LeisureActivity
        fields = [
            'name',
            'category',
            'short_description',
            'details_html',
            'icon',
            'image_url'
        ]

    def get_image_url(self, obj):
        """Return image URL or None"""
        if obj.image:
            return obj.image.url
        return None


class HotelPublicDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for public hotel page.
    Includes all marketing content, location, contact info,
    and nested booking options, room types, offers, activities.
    Now includes public_settings for branding (B2).
    """
    logo_url = serializers.SerializerMethodField()
    hero_image_url = serializers.SerializerMethodField()
    booking_options = BookingOptionsSerializer(read_only=True)
    public_settings = serializers.SerializerMethodField()
    room_types = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()
    leisure_activities = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = [
            # Basic info
            'slug',
            'name',
            'tagline',
            'hero_image_url',
            'logo_url',
            'short_description',
            'long_description',
            # Location
            'city',
            'country',
            'address_line_1',
            'address_line_2',
            'postal_code',
            'latitude',
            'longitude',
            # Contact
            'phone',
            'email',
            'website_url',
            'booking_url',
            # Nested objects
            'booking_options',
            'public_settings',
            'room_types',
            'offers',
            'leisure_activities',
        ]

    def get_logo_url(self, obj):
        """Return logo URL or None"""
        if obj.logo:
            return obj.logo.url
        return None

    def get_hero_image_url(self, obj):
        """Return hero image URL or None"""
        if obj.hero_image:
            return obj.hero_image.url
        return None
    
    def get_public_settings(self, obj):
        """Return public settings if they exist (B2)"""
        try:
            settings = obj.public_settings
            return HotelPublicSettingsPublicSerializer(settings).data
        except HotelPublicSettings.DoesNotExist:
            return None

    def get_room_types(self, obj):
        """Return only active room types"""
        active_room_types = obj.room_types.filter(is_active=True)
        return RoomTypeSerializer(active_room_types, many=True).data

    def get_offers(self, obj):
        """Return only active offers"""
        active_offers = obj.offers.filter(is_active=True)
        return OfferSerializer(active_offers, many=True).data

    def get_leisure_activities(self, obj):
        """Return only active leisure activities"""
        active_activities = obj.leisure_activities.filter(is_active=True)
        return LeisureActivitySerializer(active_activities, many=True).data


class HotelPublicSettingsPublicSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for public hotel settings.
    Used by the public endpoint for rendering hotel pages.
    """
    class Meta:
        model = HotelPublicSettings
        fields = [
            'short_description',
            'long_description',
            'welcome_message',
            'hero_image',
            'gallery',
            'amenities',
            'contact_email',
            'contact_phone',
            'contact_address',
            'website',
            'google_maps_link',
            'logo',
            'favicon',
            'slogan',
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'button_color',
            'button_text_color',
            'button_hover_color',
            'text_color',
            'border_color',
            'link_color',
            'link_hover_color',
            'theme_mode',
        ]
        read_only_fields = fields


class HotelPublicSettingsStaffSerializer(serializers.ModelSerializer):
    """
    Write-enabled serializer for staff to update hotel settings.
    Includes validation for colors and data formats (B4).
    """
    class Meta:
        model = HotelPublicSettings
        fields = [
            'short_description',
            'long_description',
            'welcome_message',
            'hero_image',
            'gallery',
            'amenities',
            'contact_email',
            'contact_phone',
            'contact_address',
            'website',
            'google_maps_link',
            'logo',
            'favicon',
            'slogan',
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'button_color',
            'button_text_color',
            'button_hover_color',
            'text_color',
            'border_color',
            'link_color',
            'link_hover_color',
            'theme_mode',
            'updated_at',
        ]
        read_only_fields = ['updated_at']
    
    def validate_primary_color(self, value):
        return self._validate_hex_color(value, 'primary_color')
    
    def validate_secondary_color(self, value):
        return self._validate_hex_color(value, 'secondary_color')
    
    def validate_accent_color(self, value):
        return self._validate_hex_color(value, 'accent_color')
    
    def validate_background_color(self, value):
        return self._validate_hex_color(value, 'background_color')
    
    def validate_button_color(self, value):
        return self._validate_hex_color(value, 'button_color')
    
    def validate_button_text_color(self, value):
        return self._validate_hex_color(value, 'button_text_color')
    
    def validate_button_hover_color(self, value):
        return self._validate_hex_color(value, 'button_hover_color')
    
    def validate_text_color(self, value):
        return self._validate_hex_color(value, 'text_color')
    
    def validate_border_color(self, value):
        return self._validate_hex_color(value, 'border_color')
    
    def validate_link_color(self, value):
        return self._validate_hex_color(value, 'link_color')
    
    def validate_link_hover_color(self, value):
        return self._validate_hex_color(value, 'link_hover_color')
    
    def _validate_hex_color(self, value, field_name):
        """Validate HEX color format"""
        if value and not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError(
                f'{field_name} must be a valid HEX color (e.g., #3B82F6)'
            )
        return value
    
    def validate_gallery(self, value):
        """Ensure gallery is a list"""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                'gallery must be a list of URLs'
            )
        return value
    
    def validate_amenities(self, value):
        """Ensure amenities is a list"""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                'amenities must be a list of strings'
            )
        return value


class RoomBookingListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing room bookings for staff.
    Returns key booking information for list views.
    """
    guest_name = serializers.SerializerMethodField()
    room_type_name = serializers.CharField(
        source='room_type.name',
        read_only=True
    )
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    nights = serializers.SerializerMethodField()

    class Meta:
        model = RoomBooking
        fields = [
            'id',
            'booking_id',
            'confirmation_number',
            'hotel_name',
            'room_type_name',
            'guest_name',
            'guest_email',
            'guest_phone',
            'check_in',
            'check_out',
            'nights',
            'adults',
            'children',
            'total_amount',
            'currency',
            'status',
            'created_at',
            'paid_at',
        ]
        read_only_fields = fields

    def get_guest_name(self, obj):
        return obj.guest_name

    def get_nights(self, obj):
        return obj.nights


class RoomBookingDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual booking views.
    Includes all booking information including special requests
    and internal notes.
    """
    guest_name = serializers.SerializerMethodField()
    room_type_name = serializers.CharField(
        source='room_type.name',
        read_only=True
    )
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    nights = serializers.SerializerMethodField()

    class Meta:
        model = RoomBooking
        fields = [
            'id',
            'booking_id',
            'confirmation_number',
            'hotel_name',
            'room_type_name',
            'guest_name',
            'guest_first_name',
            'guest_last_name',
            'guest_email',
            'guest_phone',
            'check_in',
            'check_out',
            'nights',
            'adults',
            'children',
            'total_amount',
            'currency',
            'status',
            'special_requests',
            'promo_code',
            'payment_reference',
            'payment_provider',
            'paid_at',
            'created_at',
            'updated_at',
            'internal_notes',
        ]
        read_only_fields = [
            'id', 'booking_id', 'confirmation_number', 'hotel_name',
            'room_type_name', 'guest_name', 'created_at', 'updated_at',
            'nights'
        ]

    def get_guest_name(self, obj):
        return obj.guest_name

    def get_nights(self, obj):
        return obj.nights


# ============================================================================
# STAFF CRUD SERIALIZERS (B1)
# ============================================================================

class HotelAccessConfigStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for access configuration"""
    class Meta:
        model = HotelAccessConfig
        fields = [
            'guest_portal_enabled',
            'staff_portal_enabled',
            'requires_room_pin',
            'room_pin_length',
            'rotate_pin_on_checkout',
            'allow_multiple_guest_sessions',
            'max_active_guest_devices_per_room',
        ]


class OfferStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for offers - includes all fields"""
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'short_description',
            'details_text',
            'details_html',
            'valid_from',
            'valid_to',
            'tag',
            'book_now_url',
            'photo',
            'photo_url',
            'sort_order',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None


class LeisureActivityStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for leisure activities"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LeisureActivity
        fields = [
            'id',
            'name',
            'category',
            'short_description',
            'details_html',
            'icon',
            'image',
            'image_url',
            'sort_order',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


class RoomTypeStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for room types"""
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomType
        fields = [
            'id',
            'code',
            'name',
            'short_description',
            'max_occupancy',
            'bed_setup',
            'photo',
            'photo_url',
            'starting_price_from',
            'currency',
            'booking_code',
            'booking_url',
            'availability_message',
            'sort_order',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None


class PricingQuoteSerializer(serializers.ModelSerializer):
    """Serializer for PricingQuote model"""
    room_type_name = serializers.CharField(
        source='room_type.name',
        read_only=True
    )
    
    class Meta:
        model = PricingQuote
        fields = [
            'quote_id',
            'hotel',
            'room_type',
            'room_type_name',
            'check_in',
            'check_out',
            'adults',
            'children',
            'base_price_per_night',
            'number_of_nights',
            'subtotal',
            'taxes',
            'fees',
            'discount',
            'total',
            'currency',
            'promo_code',
            'applied_offer',
            'created_at',
            'valid_until',
        ]
        read_only_fields = ['quote_id', 'created_at']
