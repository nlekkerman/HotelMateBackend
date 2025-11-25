from rest_framework import serializers
from .models import (
    Hotel,
    HotelAccessConfig,
    BookingOptions,
    HotelPublicSettings,
    Offer,
    LeisureActivity,
    RoomBooking,
    PricingQuote,
    Gallery,
    GalleryImage
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


class OfferSerializer(serializers.ModelSerializer):
    """Serializer for hotel offers and packages"""
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id',
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
    Prioritizes customizable public_settings over Hotel model fields.
    """
    # Override all Hotel fields to check public_settings first
    name = serializers.SerializerMethodField()
    tagline = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    hero_image_url = serializers.SerializerMethodField()
    landing_page_image_url = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()
    long_description = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    address_line_1 = serializers.SerializerMethodField()
    address_line_2 = serializers.SerializerMethodField()
    postal_code = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    website_url = serializers.SerializerMethodField()
    booking_url = serializers.SerializerMethodField()
    # Nested objects
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
            'landing_page_image_url',
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
        """
        Return logo from public_settings (customizable) or Hotel model
        """
        try:
            settings = obj.public_settings
            if settings.logo:
                return settings.logo
        except HotelPublicSettings.DoesNotExist:
            pass
        # Fallback to Hotel model logo
        if obj.logo:
            return obj.logo.url
        return None

    def get_hero_image_url(self, obj):
        """Return hero image from public_settings or Hotel"""
        try:
            settings = obj.public_settings
            if settings.hero_image:
                return settings.hero_image.url
        except HotelPublicSettings.DoesNotExist:
            pass
        if obj.hero_image:
            return obj.hero_image.url
        return None
    
    def get_landing_page_image_url(self, obj):
        """Return landing page image from public_settings or Hotel"""
        try:
            settings = obj.public_settings
            if settings.landing_page_image:
                return settings.landing_page_image.url
        except HotelPublicSettings.DoesNotExist:
            pass
        if obj.landing_page_image:
            return obj.landing_page_image.url
        return None
    
    def get_name(self, obj):
        """Return custom name from settings or Hotel name"""
        try:
            settings = obj.public_settings
            if settings.name_override:
                return settings.name_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.name
    
    def get_tagline(self, obj):
        """Return custom tagline from settings or Hotel tagline"""
        try:
            settings = obj.public_settings
            if settings.tagline_override:
                return settings.tagline_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.tagline
    
    def get_short_description(self, obj):
        """Return description from settings or Hotel"""
        try:
            settings = obj.public_settings
            if settings.short_description:
                return settings.short_description
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.short_description
    
    def get_long_description(self, obj):
        """Return long description from settings or Hotel"""
        try:
            settings = obj.public_settings
            if settings.long_description:
                return settings.long_description
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.long_description
    
    def get_city(self, obj):
        """Return custom city from settings or Hotel city"""
        try:
            settings = obj.public_settings
            if settings.city_override:
                return settings.city_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.city
    
    def get_country(self, obj):
        """Return custom country from settings or Hotel country"""
        try:
            settings = obj.public_settings
            if settings.country_override:
                return settings.country_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.country
    
    def get_address_line_1(self, obj):
        """Return custom address from settings or Hotel address"""
        try:
            settings = obj.public_settings
            if settings.address_line_1_override:
                return settings.address_line_1_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.address_line_1
    
    def get_address_line_2(self, obj):
        """Return custom address from settings or Hotel address"""
        try:
            settings = obj.public_settings
            if settings.address_line_2_override:
                return settings.address_line_2_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.address_line_2
    
    def get_postal_code(self, obj):
        """Return custom postal code from settings or Hotel"""
        try:
            settings = obj.public_settings
            if settings.postal_code_override:
                return settings.postal_code_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.postal_code
    
    def get_latitude(self, obj):
        """Return custom latitude from settings or Hotel"""
        try:
            settings = obj.public_settings
            if settings.latitude_override is not None:
                return settings.latitude_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.latitude
    
    def get_longitude(self, obj):
        """Return custom longitude from settings or Hotel"""
        try:
            settings = obj.public_settings
            if settings.longitude_override is not None:
                return settings.longitude_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.longitude
    
    def get_phone(self, obj):
        """Return custom phone from settings or Hotel phone"""
        try:
            settings = obj.public_settings
            if settings.phone_override:
                return settings.phone_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.phone
    
    def get_email(self, obj):
        """Return custom email from settings or Hotel email"""
        try:
            settings = obj.public_settings
            if settings.email_override:
                return settings.email_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.email
    
    def get_website_url(self, obj):
        """Return custom website from settings or Hotel website"""
        try:
            settings = obj.public_settings
            if settings.website_url_override:
                return settings.website_url_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.website_url
    
    def get_booking_url(self, obj):
        """Return custom booking URL from settings or Hotel"""
        try:
            settings = obj.public_settings
            if settings.booking_url_override:
                return settings.booking_url_override
        except HotelPublicSettings.DoesNotExist:
            pass
        return obj.booking_url
    
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
    Shows current values from Hotel model with override capability.
    
    Note: Gallery is READ-ONLY here. Use dedicated gallery endpoints:
    - POST /api/staff/hotel/<slug>/settings/gallery/upload/ to add images
    - POST /api/staff/hotel/<slug>/settings/gallery/reorder/ to reorder
    - DELETE /api/staff/hotel/<slug>/settings/gallery/remove/ to delete
    """
    # Image fields - NOT SerializerMethodField to allow uploads
    # CloudinaryField accepts both file uploads and URL strings
    hero_image_url = serializers.SerializerMethodField(read_only=True)
    landing_page_image_url = serializers.SerializerMethodField(read_only=True)
    
    # Display fields showing current effective values
    name_display = serializers.SerializerMethodField()
    tagline_display = serializers.SerializerMethodField()
    hero_image_display = serializers.SerializerMethodField()
    landing_page_image_display = serializers.SerializerMethodField()
    logo_display = serializers.SerializerMethodField()
    city_display = serializers.SerializerMethodField()
    country_display = serializers.SerializerMethodField()
    address_line_1_display = serializers.SerializerMethodField()
    address_line_2_display = serializers.SerializerMethodField()
    postal_code_display = serializers.SerializerMethodField()
    latitude_display = serializers.SerializerMethodField()
    longitude_display = serializers.SerializerMethodField()
    phone_display = serializers.SerializerMethodField()
    email_display = serializers.SerializerMethodField()
    website_url_display = serializers.SerializerMethodField()
    booking_url_display = serializers.SerializerMethodField()
    
    # Galleries - structured gallery system
    galleries = serializers.SerializerMethodField()
    
    class Meta:
        model = HotelPublicSettings
        fields = [
            # Hotel model override fields (editable)
            'name_override',
            'name_display',
            'tagline_override',
            'tagline_display',
            'city_override',
            'city_display',
            'country_override',
            'country_display',
            'address_line_1_override',
            'address_line_1_display',
            'address_line_2_override',
            'address_line_2_display',
            'postal_code_override',
            'postal_code_display',
            'latitude_override',
            'latitude_display',
            'longitude_override',
            'longitude_display',
            'phone_override',
            'phone_display',
            'email_override',
            'email_display',
            'website_url_override',
            'website_url_display',
            'booking_url_override',
            'booking_url_display',
            # Content fields
            'short_description',
            'long_description',
            'welcome_message',
            # Images (writable fields for uploads)
            'hero_image',
            'hero_image_url',
            'hero_image_display',
            'landing_page_image',
            'landing_page_image_url',
            'landing_page_image_display',
            'logo',
            'logo_display',
            'galleries',
            'amenities',
            # Contact (legacy fields)
            'contact_email',
            'contact_phone',
            'contact_address',
            'website',
            'google_maps_link',
            'favicon',
            'slogan',
            # Branding colors
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
        # Galleries is read-only
        read_only_fields = ['updated_at', 'galleries']
    
    def get_galleries(self, obj):
        """Fetch structured galleries with images"""
        galleries = Gallery.objects.filter(
            hotel=obj.hotel
        ).prefetch_related('images')
        return GallerySerializer(galleries, many=True).data
    
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
    
    def get_hero_image_url(self, obj):
        """Return hero_image URL from HotelPublicSettings"""
        if obj.hero_image:
            try:
                return obj.hero_image.url
            except Exception:
                return str(obj.hero_image)
        return None
    
    def get_landing_page_image_url(self, obj):
        """Return landing_page_image URL from HotelPublicSettings"""
        if obj.landing_page_image:
            try:
                return obj.landing_page_image.url
            except Exception:
                return str(obj.landing_page_image)
        return None
    
    def get_hero_image_display(self, obj):
        """
        Return current hero_image or Hotel model fallback
        """
        if obj.hero_image:
            return obj.hero_image.url
        # Fallback to Hotel model
        if obj.hotel.hero_image:
            return obj.hotel.hero_image.url
        return None
    
    def get_logo_display(self, obj):
        """Return current logo or Hotel model fallback"""
        if obj.logo:
            return obj.logo
        if obj.hotel.logo:
            return obj.hotel.logo.url
        return None
    
    def get_name_display(self, obj):
        """Return custom name or Hotel model name"""
        return obj.name_override or obj.hotel.name
    
    def get_tagline_display(self, obj):
        """Return custom tagline or Hotel model tagline"""
        return obj.tagline_override or obj.hotel.tagline
    
    def get_landing_page_image_display(self, obj):
        """Return custom landing image or Hotel model fallback"""
        if obj.landing_page_image:
            return obj.landing_page_image.url
        if obj.hotel.landing_page_image:
            return obj.hotel.landing_page_image.url
        return None
    
    def get_city_display(self, obj):
        """Return custom city or Hotel model city"""
        return obj.city_override or obj.hotel.city
    
    def get_country_display(self, obj):
        """Return custom country or Hotel model country"""
        return obj.country_override or obj.hotel.country
    
    def get_address_line_1_display(self, obj):
        """Return custom address or Hotel model address"""
        return obj.address_line_1_override or obj.hotel.address_line_1
    
    def get_address_line_2_display(self, obj):
        """Return custom address or Hotel model address"""
        return obj.address_line_2_override or obj.hotel.address_line_2
    
    def get_postal_code_display(self, obj):
        """Return custom postal code or Hotel model postal code"""
        return obj.postal_code_override or obj.hotel.postal_code
    
    def get_latitude_display(self, obj):
        """Return custom latitude or Hotel model latitude"""
        if obj.latitude_override is not None:
            return obj.latitude_override
        return obj.hotel.latitude
    
    def get_longitude_display(self, obj):
        """Return custom longitude or Hotel model longitude"""
        if obj.longitude_override is not None:
            return obj.longitude_override
        return obj.hotel.longitude
    
    def get_phone_display(self, obj):
        """Return custom phone or Hotel model phone"""
        return obj.phone_override or obj.hotel.phone
    
    def get_email_display(self, obj):
        """Return custom email or Hotel model email"""
        return obj.email_override or obj.hotel.email
    
    def get_website_url_display(self, obj):
        """Return custom website or Hotel model website"""
        return obj.website_url_override or obj.hotel.website_url
    
    def get_booking_url_display(self, obj):
        """Return custom booking URL or Hotel model booking URL"""
        return obj.booking_url_override or obj.hotel.booking_url


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


# ==================== Gallery Serializers ====================


class GalleryImageSerializer(serializers.ModelSerializer):
    """Serializer for individual gallery images"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryImage
        fields = [
            'id',
            'image',
            'image_url',
            'caption',
            'alt_text',
            'display_order',
            'is_featured',
            'uploaded_at',
        ]
        read_only_fields = ['id', 'uploaded_at', 'image_url']
    
    def get_image_url(self, obj):
        """Return Cloudinary URL"""
        return obj.image_url


class GallerySerializer(serializers.ModelSerializer):
    """Serializer for gallery collections"""
    images = GalleryImageSerializer(many=True, read_only=True)
    image_count = serializers.SerializerMethodField()
    hotel_slug = serializers.CharField(source='hotel.slug', read_only=True)
    
    class Meta:
        model = Gallery
        fields = [
            'id',
            'hotel',
            'hotel_slug',
            'name',
            'category',
            'description',
            'is_active',
            'display_order',
            'image_count',
            'images',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_count(self, obj):
        """Return number of images in gallery"""
        return obj.images.count()


class GalleryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating galleries (no nested images)"""
    
    class Meta:
        model = Gallery
        fields = [
            'id',
            'name',
            'category',
            'description',
            'is_active',
            'display_order',
        ]
        read_only_fields = ['id']


class GalleryImageCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding images to a gallery"""
    
    class Meta:
        model = GalleryImage
        fields = [
            'id',
            'image',
            'caption',
            'alt_text',
            'display_order',
            'is_featured',
        ]
        read_only_fields = ['id']


class GalleryImageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating image details (caption, order, etc.)"""
    
    class Meta:
        model = GalleryImage
        fields = [
            'id',
            'caption',
            'alt_text',
            'display_order',
            'is_featured',
        ]
        read_only_fields = ['id']
