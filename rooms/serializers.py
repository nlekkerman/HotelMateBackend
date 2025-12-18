from rest_framework import serializers
from .models import Room, RoomType
from hotel.models import Hotel
from guests.serializers import GuestSerializer


class RoomSerializer(serializers.ModelSerializer):
    guests_in_room = GuestSerializer(many=True, read_only=True)
    hotel = serializers.PrimaryKeyRelatedField(
        queryset=Hotel.objects.all()
    )
    hotel_slug = serializers.SlugRelatedField(
        source='hotel',
        read_only=True,
        slug_field='slug'
    )
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    
    # Phase 1: Grouped guest output
    primary_guest = serializers.SerializerMethodField()
    companions = serializers.SerializerMethodField()
    walkins = serializers.SerializerMethodField()
    
    # Status display fields
    room_status_display = serializers.CharField(
        source='get_room_status_display', read_only=True
    )
    is_bookable = serializers.SerializerMethodField()
    room_type_info = serializers.SerializerMethodField()
    current_price = serializers.SerializerMethodField()

    def get_primary_guest(self, obj):
        primary = obj.guests_in_room.filter(guest_type='PRIMARY').first()
        return GuestSerializer(primary).data if primary else None
    
    def get_companions(self, obj):
        companions = obj.guests_in_room.filter(guest_type='COMPANION')
        return GuestSerializer(companions, many=True).data
    
    def get_walkins(self, obj):
        walkins = obj.guests_in_room.filter(guest_type='WALKIN')
        return GuestSerializer(walkins, many=True).data

    def get_is_bookable(self, obj):
        """Return if room is currently bookable"""
        return (obj.is_active and
                not obj.is_out_of_order and
                obj.room_status in ['AVAILABLE', 'READY_FOR_GUEST'])

    def get_room_type_info(self, obj):
        """Return basic room type information"""
        if obj.room_type:
            return {
                'id': obj.room_type.id,
                'name': obj.room_type.name,
                'max_occupancy': obj.room_type.max_occupancy,
                'starting_price_from': (str(obj.room_type.starting_price_from)
                                       if obj.room_type.starting_price_from else None)
            }
        return None
    
    def get_current_price(self, obj):
        """Get current room price for today's date"""
        if not obj.room_type:
            return None
            
        from django.utils import timezone
        from .models import DailyRate, RatePlan
        
        today = timezone.now().date()
        
        # Try to get daily rate for today
        daily_rate = DailyRate.objects.filter(
            room_type=obj.room_type,
            date=today
        ).first()
        
        if daily_rate:
            return {
                'amount': str(daily_rate.price),
                'currency': obj.room_type.currency,
                'date': str(today),
                'rate_type': 'daily_rate'
            }
        
        # Fallback to room type base price
        if obj.room_type.starting_price_from:
            return {
                'amount': str(obj.room_type.starting_price_from),
                'currency': obj.room_type.currency,
                'date': str(today),
                'rate_type': 'base_price'
            }
            
        return None

    class Meta:
        model = Room
        fields = [
            'id',
            'hotel',
            'hotel_name',
            'room_number',
            'room_type',
            'room_type_info',
            'current_price',
            'hotel_slug',
            'guests_in_room',  # Keep for backward compatibility temporarily
            'primary_guest',   # Phase 1: Grouped output
            'companions',      # Phase 1: Grouped output
            'walkins',         # Phase 1: Grouped output
            'is_occupied',
            # Status fields
            'room_status',
            'room_status_display',
            'is_bookable',
            'is_active',
            'is_out_of_order',
            'maintenance_required',
            'maintenance_priority',
        ]


class RoomStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for rooms (inventory management) - B1"""
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    current_price = serializers.SerializerMethodField()
    
    def get_current_price(self, obj):
        """Get current room price for staff management"""
        if not obj.room_type:
            return None
            
        from django.utils import timezone
        from .models import DailyRate
        
        today = timezone.now().date()
        
        # Try to get daily rate for today
        daily_rate = DailyRate.objects.filter(
            room_type=obj.room_type,
            date=today
        ).first()
        
        if daily_rate:
            return {
                'amount': str(daily_rate.price),
                'currency': obj.room_type.currency,
                'rate_type': 'daily_rate'
            }
        
        # Fallback to room type base price
        if obj.room_type.starting_price_from:
            return {
                'amount': str(obj.room_type.starting_price_from),
                'currency': obj.room_type.currency,
                'rate_type': 'base_price'
            }
            
        return None
    
    class Meta:
        model = Room
        fields = [
            'id',
            'room_number',
            'room_type',
            'room_type_name',
            'current_price',
            'is_occupied',
            'room_status',
            'is_active',
            'is_out_of_order',
            'maintenance_required',
            'maintenance_priority',
        ]
        read_only_fields = [
            'id',
            'room_type_name',
            'current_price',
        ]


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer for room type selection and display"""
    
    class Meta:
        model = RoomType
        fields = [
            'id',
            'name',
            'code',
            'max_occupancy',
            'starting_price_from',
            'currency',
            'is_active',
        ]
