"""
Public-facing serializers for hotel discovery and public pages.
No authentication required.
"""
from rest_framework import serializers
from decimal import Decimal
from .models import (
    Hotel,
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
    Preset,
    RoomsSection
)
from .base_serializers import PresetSerializer
from common.cloudinary_utils import get_cloudinary_url
from rooms.models import RoomType, RatePlan, RoomTypeRatePlan
from hotel.services.pricing import get_or_create_default_rate_plan


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
            'style_variant',
            'layout_preset',
            'layout_preset_id',
            'element',
        ]
        read_only_fields = ['id']


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
            'style_variant',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_hero_image_url(self, obj):
        return get_cloudinary_url(obj.hero_image)
    
    def get_hero_logo_url(self, obj):
        return get_cloudinary_url(obj.hero_logo)


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
            'style_variant',
            'sort_order',
            'images',
            'image_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_count(self, obj):
        return obj.images.count()


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
            'style_variant',
            'sort_order',
            'cards',
            'card_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_card_count(self, obj):
        return obj.cards.count()


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
        """Validate text blocks have body and image blocks have image"""
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
            'style_variant',
            'sort_order',
            'content_blocks',
            'block_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_block_count(self, obj):
        return obj.content_blocks.count()


class RoomTypeRatePlanVariantSerializer(serializers.ModelSerializer):
    """Serializer for individual room type + rate plan combinations"""
    room_type_id = serializers.SerializerMethodField()
    room_type_name = serializers.SerializerMethodField()
    room_type_code = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()
    max_occupancy = serializers.SerializerMethodField()
    bed_setup = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    availability_message = serializers.SerializerMethodField()
    
    rate_plan_name = serializers.CharField(source='rate_plan.name')
    rate_plan_code = serializers.CharField(source='rate_plan.code')
    rate_plan_description = serializers.CharField(source='rate_plan.description')
    is_refundable = serializers.BooleanField(source='rate_plan.is_refundable')
    
    current_price = serializers.SerializerMethodField()
    original_price = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()
    has_discount = serializers.SerializerMethodField()
    booking_cta_url = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomTypeRatePlan
        fields = [
            'id',
            'room_type_id',
            'room_type_name', 
            'room_type_code',
            'short_description',
            'max_occupancy',
            'bed_setup',
            'photo',
            'currency',
            'availability_message',
            'rate_plan_name',
            'rate_plan_code', 
            'rate_plan_description',
            'is_refundable',
            'current_price',
            'original_price',
            'price_display',
            'discount_percent',
            'has_discount',
            'booking_cta_url',
        ]
    
    def get_room_type_id(self, obj):
        return obj.room_type.id
    
    def get_room_type_name(self, obj):
        return obj.room_type.name
    
    def get_room_type_code(self, obj):
        return obj.room_type.code or obj.room_type.name
    
    def get_short_description(self, obj):
        return obj.room_type.short_description
    
    def get_max_occupancy(self, obj):
        return obj.room_type.max_occupancy
    
    def get_bed_setup(self, obj):
        return obj.room_type.bed_setup
    
    def get_photo(self, obj):
        """Return photo URL if available"""
        return get_cloudinary_url(obj.room_type.photo)
    
    def get_currency(self, obj):
        return obj.room_type.currency
    
    def get_availability_message(self, obj):
        return obj.room_type.availability_message
    
    def get_current_price(self, obj):
        """Get current price from RoomTypeRatePlan or fallback to starting_price_from"""
        if obj.base_price:
            return float(obj.base_price)
        return float(obj.room_type.starting_price_from)
    
    def get_original_price(self, obj):
        """Get original room type starting price for comparison"""
        return float(obj.room_type.starting_price_from)
    
    def get_discount_percent(self, obj):
        """Calculate discount percentage"""
        return float(obj.rate_plan.default_discount_percent)
    
    def get_has_discount(self, obj):
        """Check if this rate plan has a discount"""
        return obj.rate_plan.default_discount_percent > 0
    
    def get_price_display(self, obj):
        """Get formatted price display with currency symbol"""
        current_price = self.get_current_price(obj)
        currency_symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£'
        }
        symbol = currency_symbols.get(obj.room_type.currency, obj.room_type.currency)
        return f"{symbol}{current_price:.0f}"
    
    def get_booking_cta_url(self, obj):
        """Generate booking URL with room type code and rate plan"""
        hotel_slug = obj.room_type.hotel.slug
        room_code = obj.room_type.code or obj.room_type.name
        rate_code = obj.rate_plan.code
        return f"/public/booking/{hotel_slug}?room_type_code={room_code}&rate_plan_code={rate_code}"


class RoomTypePublicSerializer(serializers.ModelSerializer):
    """Legacy serializer for simple room type display (backwards compatibility)"""
    photo = serializers.SerializerMethodField()
    booking_cta_url = serializers.SerializerMethodField()
    
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
            'starting_price_from',
            'currency',
            'availability_message',
            'booking_cta_url',
        ]
    
    def get_photo(self, obj):
        """Return photo URL if available"""
        return get_cloudinary_url(obj.photo)
    
    def get_booking_cta_url(self, obj):
        """Generate booking URL with room type code"""
        hotel_slug = obj.hotel.slug
        code = obj.code or obj.name
        return f"/public/booking/{hotel_slug}?room_type_code={code}"


class RoomsSectionSerializer(serializers.ModelSerializer):
    """Serializer for Rooms section with live RoomType data"""
    room_types = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomsSection
        fields = [
            'id',
            'section',
            'subtitle',
            'description',
            'style_variant',
            'room_types',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_room_types(self, obj):
        """Get active room type and rate plan combinations, grouped intelligently"""
        hotel = obj.section.hotel
        
        # Get all active room type + rate plan combinations
        room_type_rate_plans = RoomTypeRatePlan.objects.filter(
            room_type__hotel=hotel,
            room_type__is_active=True,
            rate_plan__is_active=True,
            is_active=True
        ).select_related('room_type', 'rate_plan').order_by(
            'room_type__sort_order', 
            'room_type__name',
            'rate_plan__default_discount_percent'  # Show discounted rates first
        )
        
        # Group by room type to check for multiple pricing
        room_type_groups = {}
        for rtrp in room_type_rate_plans:
            room_type_id = rtrp.room_type.id
            if room_type_id not in room_type_groups:
                room_type_groups[room_type_id] = []
            room_type_groups[room_type_id].append(rtrp)
        
        # Build response: show all variants if multiple pricing, single if same
        result = []
        for room_type_id, variants in room_type_groups.items():
            # Check if there are different prices for this room type
            unique_prices = set()
            for variant in variants:
                price = variant.base_price if variant.base_price else variant.room_type.starting_price_from
                unique_prices.add(price)
            
            if len(unique_prices) > 1:
                # Multiple different prices - show all variants
                for variant in variants:
                    result.append(RoomTypeRatePlanVariantSerializer(variant, context=self.context).data)
            else:
                # Same price for all rate plans - show only the best (most discounted) variant
                best_variant = min(variants, key=lambda x: x.rate_plan.default_discount_percent, reverse=True)
                result.append(RoomTypeRatePlanVariantSerializer(best_variant, context=self.context).data)
        
        return result


class PublicSectionDetailSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer that includes section-specific data
    based on section type (hero, gallery, list, news, rooms)
    """
    element = PublicElementSerializer(read_only=True)
    
    # Section-specific nested data
    hero_data = HeroSectionSerializer(read_only=True)
    galleries = GalleryContainerSerializer(many=True, read_only=True)
    lists = ListContainerSerializer(many=True, read_only=True)
    news_items = NewsItemSerializer(many=True, read_only=True)
    rooms_data = RoomsSectionSerializer(read_only=True)
    
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
            'style_variant',
            'section_type',
            'element',
            'hero_data',
            'galleries',
            'lists',
            'news_items',
            'rooms_data',
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
        elif hasattr(obj, 'rooms_data'):
            return 'rooms'
        elif hasattr(obj, 'element'):
            return obj.element.element_type
        return 'unknown'
