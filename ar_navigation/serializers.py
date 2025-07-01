# ar_navigation/serializers.py

from rest_framework import serializers
from .models import ARAnchor

class ARAnchorSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ARAnchor
        fields = [
            "id",
            "name",
            "floor",
            "image_url",
            "position_hint",
            "instruction",
            "order",
            "marker_type",
            "next_anchor",
        ]

    def get_image_url(self, obj):
        return obj.image.url if obj.image else ""
