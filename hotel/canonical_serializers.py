"""
Phase 4: Canonical serializers for stable API contracts
These serializers define the locked output shapes for staff booking management.
"""

from rest_framework import serializers
from .models import RoomBooking, BookingGuest
from guests.models import Guest
from rooms.models import Room, RoomType


class BookingPartyGuestSerializer(serializers.ModelSerializer):
    """Single booking party member serializer."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BookingGuest
        fields = [
            'id',
            'role',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone',
            'is_staying',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'full_name']
    
    def get_full_name(self, obj):
        return obj.full_name


class BookingPartyGroupedSerializer(serializers.Serializer):
    """
    Canonical booking party serializer with guaranteed structure.
    Always returns primary + companions + total_count.
    """
    
    def to_representation(self, booking):
        """
        Convert a RoomBooking to grouped party representation.
        
        Args:
            booking: RoomBooking instance
            
        Returns:
            dict: {
                "primary": {...} or null,
                "companions": [...],
                "total_count": int
            }
        """
        party_members = booking.party.all().select_related('booking').order_by('role', 'created_at')
        
        primary_guest = None
        companions = []
        
        for member in party_members:
            member_data = BookingPartyGuestSerializer(member).data
            
            if member.role == 'PRIMARY':
                primary_guest = member_data
            else:
                companions.append(member_data)
        
        return {
            'primary': primary_guest,
            'companions': companions,
            'total_count': len(party_members)
        }


class InHouseGuestSerializer(serializers.ModelSerializer):
    """Minimal in-house guest serializer for UI display."""
    full_name = serializers.SerializerMethodField()
    room_number = serializers.SerializerMethodField()
    
    class Meta:
        model = Guest
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'guest_type',
            'id_pin',
            'room_number',
            'check_in_date',
            'check_out_date',
        ]
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_room_number(self, obj):
        return obj.room.room_number if obj.room else None


class InHouseGuestsGroupedSerializer(serializers.Serializer):
    """
    Canonical in-house guests serializer with guaranteed structure.
    Groups guests by type: primary, companions, walkins.
    """
    
    def to_representation(self, booking):
        """
        Convert a RoomBooking to grouped in-house guests representation.
        
        Args:
            booking: RoomBooking instance
            
        Returns:
            dict: {
                "primary": {...} or null,
                "companions": [...],
                "walkins": [...],
                "total_count": int
            }
        """
        # Only return in-house guests if booking is checked in
        if not booking.assigned_room or not booking.checked_in_at:
            return {
                'primary': None,
                'companions': [],
                'walkins': [],
                'total_count': 0
            }
        
        guests = booking.guests.all().select_related('room', 'primary_guest').order_by('guest_type', 'first_name')
        
        primary_guest = None
        companions = []
        walkins = []
        
        for guest in guests:
            guest_data = InHouseGuestSerializer(guest).data
            
            if guest.guest_type == 'PRIMARY':
                primary_guest = guest_data
            elif guest.guest_type == 'COMPANION':
                companions.append(guest_data)
            elif guest.guest_type == 'WALKIN':
                walkins.append(guest_data)
        
        return {
            'primary': primary_guest,
            'companions': companions,
            'walkins': walkins,
            'total_count': len(guests)
        }


class StaffRoomBookingListSerializer(serializers.ModelSerializer):
    """
    Canonical booking list serializer for staff endpoints.
    Returns minimal data needed for list views.
    """
    nights = serializers.SerializerMethodField()
    assigned_room_number = serializers.SerializerMethodField()
    booker_summary = serializers.SerializerMethodField()
    primary_guest_name = serializers.SerializerMethodField()
    party_total_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomBooking
        fields = [
            'booking_id',
            'confirmation_number',
            'status',
            'check_in',
            'check_out',
            'nights',
            'assigned_room_number',
            'booker_type',
            'booker_summary',
            'primary_guest_name',
            'party_total_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_nights(self, obj):
        return obj.nights
    
    def get_assigned_room_number(self, obj):
        return obj.assigned_room.room_number if obj.assigned_room else None
    
    def get_booker_summary(self, obj):
        """Generate human-readable booker summary."""
        if obj.booker_type == 'COMPANY':
            return obj.booker_company or 'Company Booking'
        elif obj.booker_type == 'INDIVIDUAL':
            return f"{obj.booker_first_name} {obj.booker_last_name}".strip() or 'Individual Booking'
        else:
            return obj.booker_type.replace('_', ' ').title()
    
    def get_primary_guest_name(self, obj):
        return obj.primary_guest_name
    
    def get_party_total_count(self, obj):
        return obj.party.count()


class StaffRoomBookingDetailSerializer(serializers.ModelSerializer):
    """
    Canonical booking detail serializer for staff endpoints.
    Returns all data needed for booking detail views without additional fetches.
    """
    nights = serializers.SerializerMethodField()
    
    # Booker object
    booker = serializers.SerializerMethodField()
    
    # Primary guest object (from RoomBooking primary_* fields)
    primary_guest = serializers.SerializerMethodField()
    
    # Party grouped
    party = serializers.SerializerMethodField()
    
    # In-house guests grouped
    in_house = serializers.SerializerMethodField()
    
    # Assigned room summary
    room = serializers.SerializerMethodField()
    
    # Computed flags
    flags = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomBooking
        fields = [
            'booking_id',
            'confirmation_number',
            'status',
            'check_in',
            'check_out',
            'nights',
            'adults',
            'children',
            'total_amount',
            'currency',
            'special_requests',
            'promo_code',
            'payment_reference',
            'payment_provider',
            'paid_at',
            'checked_in_at',
            'checked_out_at',
            'created_at',
            'updated_at',
            'internal_notes',
            'booker',
            'primary_guest',
            'party',
            'in_house',
            'room',
            'flags',
        ]
        read_only_fields = fields
    
    def get_nights(self, obj):
        return obj.nights
    
    def get_booker(self, obj):
        """Return booker information object."""
        return {
            'type': obj.booker_type,
            'first_name': obj.booker_first_name or '',
            'last_name': obj.booker_last_name or '',
            'company': obj.booker_company or '',
            'email': obj.booker_email or '',
            'phone': obj.booker_phone or '',
        }
    
    def get_primary_guest(self, obj):
        """Return primary guest information from booking primary_* fields."""
        return {
            'first_name': obj.primary_first_name or '',
            'last_name': obj.primary_last_name or '',
            'email': obj.primary_email or '',
            'phone': obj.primary_phone or '',
        }
    
    def get_party(self, obj):
        """Return grouped party information."""
        serializer = BookingPartyGroupedSerializer()
        return serializer.to_representation(obj)
    
    def get_in_house(self, obj):
        """Return grouped in-house guests information."""
        serializer = InHouseGuestsGroupedSerializer()
        return serializer.to_representation(obj)
    
    def get_room(self, obj):
        """Return assigned room summary."""
        if not obj.assigned_room:
            return None
        
        room = obj.assigned_room
        return {
            'room_number': room.room_number,
            'is_occupied': room.is_occupied,
            'is_active': room.is_active,
            'is_out_of_order': room.is_out_of_order,
            'room_type_id': room.room_type.id if room.room_type else None,
            'room_type_name': room.room_type.name if room.room_type else None,
        }
    
    def get_flags(self, obj):
        """Return computed action flags."""
        is_checked_in = (
            obj.assigned_room is not None and 
            obj.checked_in_at is not None and 
            obj.checked_out_at is None
        )
        
        can_check_in = (
            obj.status == 'CONFIRMED' and 
            not is_checked_in and
            obj.checked_out_at is None
        )
        
        can_check_out = (
            is_checked_in and 
            obj.checked_out_at is None
        )
        
        can_edit_party = (
            obj.status not in ('CANCELLED', 'COMPLETED') and 
            obj.checked_out_at is None
        )
        
        return {
            'is_checked_in': is_checked_in,
            'can_check_in': can_check_in,
            'can_check_out': can_check_out,
            'can_edit_party': can_edit_party,
        }