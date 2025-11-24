from rest_framework import serializers
from common.models import ThemePreference
from hotel.models import HotelPublicSettings


class ThemePreferenceSerializer(serializers.ModelSerializer):
    hotel_slug = serializers.SlugRelatedField(
        source="hotel", slug_field="slug", read_only=True
    )

    class Meta:
        model = ThemePreference
        fields = (
            "id",
            "hotel_slug",
            "main_color",
            "secondary_color",
            "button_color",
            "button_text_color",
            "button_hover_color",
            "text_color",
            "background_color",
            "border_color",
            "link_color",
            "link_hover_color",
        )


class HotelThemeSerializer(serializers.ModelSerializer):
    """Public serializer for hotel theme/branding from HotelPublicSettings"""
    hotel_slug = serializers.CharField(source='hotel.slug', read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)

    class Meta:
        model = HotelPublicSettings
        fields = (
            'hotel_slug',
            'hotel_name',
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'button_color',
            'theme_mode',
        )
