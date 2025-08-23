from rest_framework import serializers
from .models import Room
from hotel.models import Hotel
from guests.serializers import GuestSerializer

class RoomSerializer(serializers.ModelSerializer):
    guests_in_room = GuestSerializer(many=True, read_only=True)
    hotel = serializers.PrimaryKeyRelatedField(queryset=Hotel.objects.all())  # or use a nested serializer if you want details
    hotel_slug = serializers.SlugRelatedField(
        source='hotel',
        read_only=True,
        slug_field='slug'
    )
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)

    class Meta:
        model = Room
        fields = [
            'id',
            'hotel',
            'hotel_name',
            'room_number',
            'hotel_slug',
            'guests_in_room',
            'guest_id_pin',
            'guests',
            'is_occupied',
            'room_service_qr_code',
            'in_room_breakfast_qr_code',
            'dinner_booking_qr_code',
            'chat_pin_qr_code',
        ]
