from rest_framework import serializers
from common.models import ThemePreference


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


# HotelThemeSerializer removed - HotelPublicSettings model deleted
