"""
Base serializers for hotel models.
Admin/internal use only.
"""
from rest_framework import serializers
from .models import Hotel, HotelAccessConfig, Preset, HotelPublicPage


class PresetSerializer(serializers.ModelSerializer):
    """Serializer for presets - used for section layouts, card styles, etc."""
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


class HotelAccessConfigSerializer(serializers.ModelSerializer):
    """Serializer for HotelAccessConfig - portal settings"""
    class Meta:
        model = HotelAccessConfig
        fields = [
            'guest_portal_enabled',
            'staff_portal_enabled',
        ]


class HotelSerializer(serializers.ModelSerializer):
    """Standard Hotel serializer for admin/internal use"""
    class Meta:
        model = Hotel
        fields = ['id', 'name', 'slug', 'subdomain', 'logo']
        extra_kwargs = {
            'slug': {'required': True}
        }


class HotelPublicPageSerializer(serializers.ModelSerializer):
    """Serializer for HotelPublicPage with global style variant"""
    class Meta:
        model = HotelPublicPage
        fields = [
            'id',
            'hotel',
            'global_style_variant',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
