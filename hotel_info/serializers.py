from rest_framework import serializers
from .models import HotelInfo

class HotelInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelInfo
        fields = '__all__'
