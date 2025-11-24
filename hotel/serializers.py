from rest_framework import serializers
from .models import (
    Hotel,
    HotelAccessConfig,
    BookingOptions,
    HotelPublicSettings,
    Offer,
    LeisureActivity,
    RoomBooking
)
from rooms.models import RoomType


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
    """
    logo_url = serializers.SerializerMethodField()
    hero_image_url = serializers.SerializerMethodField()
    booking_options = BookingOptionsSerializer(read_only=True)
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
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'button_color',
            'theme_mode',
        ]
        read_only_fields = fields


class HotelPublicSettingsStaffSerializer(serializers.ModelSerializer):
    """
    Write-enabled serializer for staff to update hotel settings.
    Used by the staff-only endpoint.
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
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'button_color',
            'theme_mode',
            'updated_at',
        ]
        read_only_fields = ['updated_at']


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
