from rest_framework import serializers
from .models import Guest

class GuestSerializer(serializers.ModelSerializer):
    hotel_slug = serializers.SlugField(source='hotel.slug', read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    room_number = serializers.IntegerField(source='room.room_number', read_only=True)
    room_label = serializers.SerializerMethodField()
    in_house = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()  # 👈 Add this line

    def get_room_label(self, obj):
        if obj.room and obj.hotel:
            return f"Room {obj.room.room_number} at {obj.hotel.name}"
        return ""
    
    def get_in_house(self, obj):
        return obj.in_house

    def get_full_name(self, obj):  # 👈 Define this method
        return f"{obj.first_name} {obj.last_name}".strip()

    class Meta:
        model = Guest
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',  # 👈 Include this
            'id_pin',
            'check_in_date',
            'check_out_date',
            'days_booked',
            'hotel', 'hotel_slug', 'hotel_name',
            'room', 'room_number', 'room_label',
            'in_house',
        ]
        read_only_fields = [
            'hotel_slug', 'hotel_name',
            'room_number', 'room_label',
            'in_house', 'full_name'  # 👈 Mark as read-only
        ]
