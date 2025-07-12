# ar_navigation/serializers.py
from rest_framework import serializers
from .models import ARAnchor

class ARAnchorSerializer(serializers.ModelSerializer):
    url = serializers.ReadOnlyField()
    instruction = serializers.CharField(read_only=True)

    class Meta:
        model = ARAnchor
        fields = (
            "id",
            "hotel",
            "restaurant",
            "instruction",
            "url",
            "qr_code_url",
        )
        read_only_fields = ("instruction", "url", "qr_code_url")
