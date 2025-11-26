from rest_framework import serializers
from django.db import models
from .models import (
    Hotel,
    HotelAccessConfig,
    BookingOptions,
    RoomBooking,
    PricingQuote,
    Preset,
    PublicSection,
    PublicElement,
    PublicElementItem,
    HeroSection,
    GalleryContainer,
    GalleryImage,
    ListContainer,
    Card,
    NewsItem,
    ContentBlock,
)
from rooms.models import RoomType
from common.cloudinary_utils import get_cloudinary_url


# ============================================================================
# PRESET SERIALIZERS
# ============================================================================

class PresetSerializer(serializers.ModelSerializer):
    """Serializer for presets - used for section layouts, card styles, image styles, etc."""
    class Meta:
        model = Preset
        fields = [
            'id',
            'target_type',
            'section_type',
            'key',
            'name',
            'description',
            'is_default',
            'config',
        ]
        read_only_fields = ['id']


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
    layout_preset = PresetSerializer(read_only=True)
    layout_preset_id = serializers.PrimaryKeyRelatedField(
        queryset=Preset.objects.filter(target_type='section'),
        source='layout_preset',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = PublicSection
        fields = [
            'id',
            'hotel',
            'position',
            'is_active',
            'name',
            'layout_preset',
            'layout_preset_id',
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
            'element',  # REQUIRED - which element this item belongs to
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
    
    def validate_element(self, value):
        """Ensure element exists"""
        if not value:
            raise serializers.ValidationError("Element is required.")
        return value


class PublicElementStaffSerializer(serializers.ModelSerializer):
    """Staff serializer for elements - includes timestamps and all items"""
    items = PublicElementItemStaffSerializer(many=True, read_only=True)
    
    class Meta:
        model = PublicElement
        fields = [
            'id',
            'section',  # REQUIRED - which section this element belongs to
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
    
    def validate_section(self, value):
        """Ensure section exists and belongs to accessible hotel"""
        if not value:
            raise serializers.ValidationError("Section is required.")
        return value


class PublicSectionStaffSerializer(serializers.ModelSerializer):
    """Staff serializer for sections - includes timestamps and all section-specific data"""
    element = PublicElementStaffSerializer(read_only=True)
    
    # Include section-specific data (will be added after serializers are defined)
    hero_data = serializers.SerializerMethodField()
    galleries = serializers.SerializerMethodField()
    lists = serializers.SerializerMethodField()
    news_items = serializers.SerializerMethodField()
    section_type = serializers.SerializerMethodField()
    
    class Meta:
        model = PublicSection
        fields = [
            'id',
            'hotel',
            'position',
            'is_active',
            'name',
            'section_type',
            'element',
            'hero_data',
            'galleries',
            'lists',
            'news_items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_section_type(self, obj):
        """Infer section type from related data"""
        if hasattr(obj, 'hero_data'):
            return 'hero'
        elif obj.galleries.exists():
            return 'gallery'
        elif obj.lists.exists():
            return 'list'
        elif obj.news_items.exists():
            return 'news'
        return 'unknown'
    
    def get_hero_data(self, obj):
        """Return hero data if exists"""
        if hasattr(obj, 'hero_data'):
            # Import here to avoid circular import
            # HeroSectionSerializer is defined below
            data = {
                'id': obj.hero_data.id,
                'section': obj.hero_data.section_id,
                'hero_title': obj.hero_data.hero_title,
                'hero_text': obj.hero_data.hero_text,
                'hero_image_url': obj.hero_data.hero_image.url if obj.hero_data.hero_image else None,
                'hero_logo_url': obj.hero_data.hero_logo.url if obj.hero_data.hero_logo else None,
                'created_at': obj.hero_data.created_at,
                'updated_at': obj.hero_data.updated_at,
            }
            return data
        return None
    
    def get_galleries(self, obj):
        """Return galleries if exist"""
        galleries = obj.galleries.all()
        if galleries.exists():
            # Inline serialization to avoid circular import
            return [{
                'id': g.id,
                'section': g.section_id,
                'name': g.name,
                'sort_order': g.sort_order,
                'image_count': g.images.count(),
                'images': [{
                    'id': img.id,
                    'gallery': img.gallery_id,
                    'image_url': img.image.url if img.image else None,
                    'caption': img.caption,
                    'alt_text': img.alt_text,
                    'sort_order': img.sort_order,
                } for img in g.images.all()]
            } for g in galleries]
        return []
    
    def get_lists(self, obj):
        """Return lists if exist"""
        lists = obj.lists.all()
        if lists.exists():
            # Inline serialization to avoid circular import
            return [{
                'id': lst.id,
                'section': lst.section_id,
                'title': lst.title,
                'sort_order': lst.sort_order,
                'card_count': lst.cards.count(),
                'cards': [{
                    'id': card.id,
                    'list_container': card.list_container_id,
                    'title': card.title,
                    'subtitle': card.subtitle,
                    'description': card.description,
                    'image_url': card.image.url if card.image else None,
                    'sort_order': card.sort_order,
                } for card in lst.cards.all()]
            } for lst in lists]
        return []
    
    def get_news_items(self, obj):
        """Return news items if exist"""
        news_items = obj.news_items.all()
        if news_items.exists():
            # Inline serialization to avoid circular import
            return [{
                'id': news.id,
                'section': news.section_id,
                'title': news.title,
                'date': news.date,
                'summary': news.summary,
                'sort_order': news.sort_order,
                'block_count': news.content_blocks.count(),
                'content_blocks': [{
                    'id': block.id,
                    'news_item': block.news_item_id,
                    'block_type': block.block_type,
                    'body': block.body,
                    'image_url': block.image.url if block.image else None,
                    'image_position': block.image_position,
                    'image_caption': block.image_caption,
                    'sort_order': block.sort_order,
                } for block in news.content_blocks.all()]
            } for news in news_items]
        return []


# ============================================================================
# NEW SECTION TYPE SERIALIZERS
# ============================================================================

# --- Hero Section Serializers ---

class HeroSectionSerializer(serializers.ModelSerializer):
    """Serializer for Hero section data"""
    hero_image_url = serializers.SerializerMethodField()
    hero_logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = HeroSection
        fields = [
            'id',
            'section',
            'hero_title',
            'hero_text',
            'hero_image',
            'hero_image_url',
            'hero_logo',
            'hero_logo_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_hero_image_url(self, obj):
        return get_cloudinary_url(obj.hero_image)
    
    def get_hero_logo_url(self, obj):
        return get_cloudinary_url(obj.hero_logo)


# --- Gallery Section Serializers ---

class GalleryImageSerializer(serializers.ModelSerializer):
    """Serializer for individual gallery images"""
    image_url = serializers.SerializerMethodField()
    image_style_preset = PresetSerializer(read_only=True)
    image_style_preset_id = serializers.PrimaryKeyRelatedField(
        queryset=Preset.objects.filter(target_type='image'),
        source='image_style_preset',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = GalleryImage
        fields = [
            'id',
            'gallery',
            'image',
            'image_url',
            'caption',
            'alt_text',
            'image_style_preset',
            'image_style_preset_id',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        return get_cloudinary_url(obj.image)


class GalleryContainerSerializer(serializers.ModelSerializer):
    """Serializer for gallery container with nested images"""
    images = GalleryImageSerializer(many=True, read_only=True)
    image_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryContainer
        fields = [
            'id',
            'section',
            'name',
            'sort_order',
            'images',
            'image_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_count(self, obj):
        return obj.images.count()


class BulkGalleryImageUploadSerializer(serializers.Serializer):
    """Serializer for bulk image upload to a gallery"""
    gallery = serializers.PrimaryKeyRelatedField(
        queryset=GalleryContainer.objects.all()
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        min_length=1,
        max_length=20
    )
    
    def create(self, validated_data):
        gallery = validated_data['gallery']
        images = validated_data['images']
        
        # Get current max sort_order
        max_order = gallery.images.aggregate(
            models.Max('sort_order')
        )['sort_order__max'] or -1
        
        created_images = []
        for idx, image in enumerate(images):
            gallery_image = GalleryImage.objects.create(
                gallery=gallery,
                image=image,
                sort_order=max_order + idx + 1
            )
            created_images.append(gallery_image)
        
        return created_images


# --- List/Card Section Serializers ---

class CardSerializer(serializers.ModelSerializer):
    """Serializer for individual cards"""
    image_url = serializers.SerializerMethodField()
    style_preset = PresetSerializer(read_only=True)
    style_preset_id = serializers.PrimaryKeyRelatedField(
        queryset=Preset.objects.filter(target_type='card'),
        source='style_preset',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Card
        fields = [
            'id',
            'list_container',
            'title',
            'subtitle',
            'description',
            'image',
            'image_url',
            'style_preset',
            'style_preset_id',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        return get_cloudinary_url(obj.image)


class ListContainerSerializer(serializers.ModelSerializer):
    """Serializer for list container with nested cards"""
    cards = CardSerializer(many=True, read_only=True)
    card_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ListContainer
        fields = [
            'id',
            'section',
            'title',
            'sort_order',
            'cards',
            'card_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_card_count(self, obj):
        return obj.cards.count()


# --- News Section Serializers ---

class ContentBlockSerializer(serializers.ModelSerializer):
    """Serializer for content blocks (text or image)"""
    image_url = serializers.SerializerMethodField()
    block_preset = PresetSerializer(read_only=True)
    block_preset_id = serializers.PrimaryKeyRelatedField(
        queryset=Preset.objects.filter(target_type='news_block'),
        source='block_preset',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = ContentBlock
        fields = [
            'id',
            'news_item',
            'block_type',
            'body',
            'image',
            'image_url',
            'image_position',
            'image_caption',
            'block_preset',
            'block_preset_id',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        return get_cloudinary_url(obj.image)
    
    def validate(self, data):
        """Validate that text blocks have body and image blocks have image"""
        block_type = data.get('block_type')
        
        if block_type == 'text' and not data.get('body'):
            raise serializers.ValidationError({
                'body': 'Text blocks must have body content'
            })
        
        if block_type == 'image' and not data.get('image'):
            raise serializers.ValidationError({
                'image': 'Image blocks must have an image'
            })
        
        return data


class NewsItemSerializer(serializers.ModelSerializer):
    """Serializer for news items with nested content blocks"""
    content_blocks = ContentBlockSerializer(many=True, read_only=True)
    block_count = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsItem
        fields = [
            'id',
            'section',
            'title',
            'date',
            'summary',
            'sort_order',
            'content_blocks',
            'block_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_block_count(self, obj):
        return obj.content_blocks.count()


# ============================================================================
# ENHANCED PUBLIC SECTION SERIALIZERS (with typed data)
# ============================================================================

class PublicSectionDetailSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer that includes section-specific data
    based on section type (hero, gallery, list, news)
    """
    element = PublicElementSerializer(read_only=True)
    
    # Section-specific nested data
    hero_data = HeroSectionSerializer(read_only=True)
    galleries = GalleryContainerSerializer(many=True, read_only=True)
    lists = ListContainerSerializer(many=True, read_only=True)
    news_items = NewsItemSerializer(many=True, read_only=True)
    
    # Helper fields
    section_type = serializers.SerializerMethodField()
    
    class Meta:
        model = PublicSection
        fields = [
            'id',
            'hotel',
            'position',
            'is_active',
            'name',
            'section_type',
            'element',
            'hero_data',
            'galleries',
            'lists',
            'news_items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_section_type(self, obj):
        """Infer section type from related data"""
        if hasattr(obj, 'hero_data'):
            return 'hero'
        elif obj.galleries.exists():
            return 'gallery'
        elif obj.lists.exists():
            return 'list'
        elif obj.news_items.exists():
            return 'news'
        elif hasattr(obj, 'element'):
            return obj.element.element_type
        return 'unknown'
