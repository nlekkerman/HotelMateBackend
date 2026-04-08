"""
Staff-only serializers for managing hotel content and settings.
Requires staff authentication and same-hotel permission.
"""
from rest_framework import serializers
from django.db import models
from .models import (
    HotelAccessConfig,
    PublicElementItem,
    PublicElement,
    PublicSection,
    GalleryContainer,
    GalleryImage,
    Preset,
    RoomsSection
)
from rooms.models import RoomType


class HotelAccessConfigStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for access configuration"""
    
    def validate_approval_cutoff_day_offset(self, value):
        """Validate day offset is only 0 or 1"""
        if value not in [0, 1]:
            raise serializers.ValidationError("Day offset must be 0 (same day) or 1 (next day)")
        return value
    
    def validate_late_checkout_grace_minutes(self, value):
        """Validate grace minutes is non-negative and within sane max"""
        if value < 0:
            raise serializers.ValidationError("Grace minutes cannot be negative")
        if value > 720:  # 12 hours max
            raise serializers.ValidationError("Grace minutes cannot exceed 720 (12 hours)")
        return value
    
    def validate_standard_checkout_time(self, value):
        """Validate checkout time is a valid time"""
        if not value:
            raise serializers.ValidationError("Checkout time is required")
        return value
    
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
            # Time control fields
            'standard_checkout_time',
            'late_checkout_grace_minutes', 
            'approval_sla_minutes',
            'approval_cutoff_time',
            'approval_cutoff_day_offset',
        ]


SUPPORTED_CURRENCIES = {
    'EUR', 'USD', 'GBP', 'CHF', 'SEK', 'NOK', 'DKK', 'PLN', 'CZK',
    'HUF', 'RON', 'BGN', 'HRK', 'ISK', 'TRY', 'RUB', 'AUD', 'CAD',
    'NZD', 'JPY', 'CNY', 'INR', 'BRL', 'ZAR', 'AED', 'SGD', 'HKD',
    'THB', 'MXN', 'ARS', 'COP', 'KRW', 'MYR', 'PHP', 'IDR', 'TWD',
}


class RoomTypeStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for room types — canonical staff serializer"""
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

    def validate_starting_price_from(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

    def validate_max_occupancy(self, value):
        if value < 1:
            raise serializers.ValidationError("Max occupancy must be at least 1")
        if value > 50:
            raise serializers.ValidationError("Max occupancy cannot exceed 50")
        return value

    def validate_currency(self, value):
        if value and value.upper() not in SUPPORTED_CURRENCIES:
            raise serializers.ValidationError(
                f"Unsupported currency '{value}'. Must be one of: {', '.join(sorted(SUPPORTED_CURRENCIES))}"
            )
        return value.upper() if value else value

    def validate_code(self, value):
        """Ensure code is unique per hotel (when provided)"""
        if not value:
            return value
        request = self.context.get('request')
        if request and hasattr(request.user, 'staff_profile'):
            hotel = request.user.staff_profile.hotel
            qs = RoomType.objects.filter(hotel=hotel, code=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    f"A room type with code '{value}' already exists for this hotel"
                )
        return value


class PublicElementItemStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for public element items"""
    class Meta:
        model = PublicElementItem
        fields = [
            'id',
            'element',
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
    """Staff CRUD for public elements"""
    items = PublicElementItemStaffSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PublicElement
        fields = [
            'id',
            'section',
            'element_type',
            'title',
            'subtitle',
            'body',
            'image_url',
            'settings',
            'items',
            'item_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_item_count(self, obj):
        return obj.items.count()


class PublicSectionStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for public sections"""
    element = PublicElementStaffSerializer(read_only=True)
    layout_preset = serializers.PrimaryKeyRelatedField(
        queryset=Preset.objects.filter(target_type='section'),
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
            'element',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GalleryImageStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for individual gallery images"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryImage
        fields = [
            'id',
            'gallery',
            'image',
            'image_url',
            'alt_text',
            'caption',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """Get Cloudinary URL for image"""
        if obj.image:
            return obj.image.url
        return None


class GalleryContainerStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for gallery containers"""
    images = GalleryImageStaffSerializer(many=True, read_only=True)
    image_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryContainer
        fields = [
            'id',
            'section',
            'title',
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


class RoomsSectionStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for rooms section configuration"""
    class Meta:
        model = RoomsSection
        fields = [
            'id',
            'section',
            'subtitle',
            'description',
            'style_variant',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'section', 'created_at', 'updated_at']
