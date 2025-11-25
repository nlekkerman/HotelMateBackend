from rest_framework import serializers
from .models import (
    Hotel,
    HotelAccessConfig,
    BookingOptions,
    RoomBooking,
    PricingQuote,
    PublicSection,
    PublicElement,
    PublicElementItem,
)
from rooms.models import RoomType


# ============================================================================
# CORE SERIALIZERS
# ============================================================================

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
    Used for guest/staff portal discovery and landing page.
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
            'id',
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
        read_only_fields = ['id']

    def get_photo_url(self, obj):
        """Return photo URL or None"""
        if obj.photo:
            return obj.photo.url
        return None


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
# STAFF CRUD SERIALIZERS
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
            'created_at',
            'valid_until',
        ]
        read_only_fields = ['quote_id', 'created_at']


# ============================================================================
# PUBLIC PAGE STRUCTURE SERIALIZERS
# ============================================================================

class PublicElementItemSerializer(serializers.ModelSerializer):
    """Serializer for individual items within elements"""
    class Meta:
        model = PublicElementItem
        fields = [
            'id',
            'title',
            'subtitle',
            'body',
            'image_url',
            'badge',
            'cta_label',
            'cta_url',
            'sort_order',
            'is_active',
            'meta',
        ]
        read_only_fields = ['id']


class PublicElementSerializer(serializers.ModelSerializer):
    """Serializer for elements with their items"""
    items = PublicElementItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = PublicElement
        fields = [
            'id',
            'element_type',
            'title',
            'subtitle',
            'body',
            'image_url',
            'settings',
            'items',
        ]
        read_only_fields = ['id']


class PublicSectionSerializer(serializers.ModelSerializer):
    """Serializer for sections with their element"""
    element = PublicElementSerializer(read_only=True)
    
    class Meta:
        model = PublicSection
        fields = [
            'id',
            'hotel',
            'position',
            'is_active',
            'name',
            'element',
        ]
        read_only_fields = ['id']


# ============================================================================
# STAFF BUILDER SERIALIZERS (for Super Staff Admin)
# ============================================================================

class PublicElementItemStaffSerializer(serializers.ModelSerializer):
    """Staff serializer for individual items - includes timestamps"""
    class Meta:
        model = PublicElementItem
        fields = [
            'id',
            'title',
            'subtitle',
            'body',
            'image_url',
            'badge',
            'cta_label',
            'cta_url',
            'sort_order',
            'is_active',
            'meta',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublicElementStaffSerializer(serializers.ModelSerializer):
    """Staff serializer for elements - includes timestamps and all items"""
    items = PublicElementItemStaffSerializer(many=True, read_only=True)
    
    class Meta:
        model = PublicElement
        fields = [
            'id',
            'element_type',
            'title',
            'subtitle',
            'body',
            'image_url',
            'settings',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublicSectionStaffSerializer(serializers.ModelSerializer):
    """Staff serializer for sections - includes timestamps"""
    element = PublicElementStaffSerializer(read_only=True)
    
    class Meta:
        model = PublicSection
        fields = [
            'id',
            'hotel',
            'position',
            'is_active',
            'name',
            'element',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
