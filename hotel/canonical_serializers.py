"""
Phase 4: Canonical serializers for stable API contracts
These serializers define the locked output shapes for staff booking management.
"""

from rest_framework import serializers
from .models import RoomBooking, BookingGuest
from guests.models import Guest
from rooms.models import Room, RoomType


class BookingPartyGuestSerializer(serializers.ModelSerializer):
    """Single booking party member serializer with precheckin data."""
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
            'precheckin_payload',  # Add guest-level precheckin data
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
        party_list = booking.party.all().select_related('booking').order_by('role', 'created_at')
        
        primary_guest = None
        companions = []
        
        for member in party_list:
            member_data = BookingPartyGuestSerializer(member).data
            
            if member.role == 'PRIMARY':
                primary_guest = member_data
            else:
                companions.append(member_data)
        
        return {
            'primary': primary_guest,
            'companions': companions,
            'total_count': len(party_list)
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
    room_number = serializers.SerializerMethodField()  # NEW: canonical room number for list
    booker_summary = serializers.SerializerMethodField()
    guest_display_name = serializers.SerializerMethodField()
    party_primary_full_name = serializers.SerializerMethodField()  # NEW: primary name explicitly
    party_total_count = serializers.SerializerMethodField()
    party_status_display = serializers.SerializerMethodField()
    
    # Survey operational flags (Tier 1 Backend Hardening)
    survey_sent = serializers.ReadOnlyField()
    survey_completed = serializers.ReadOnlyField()
    survey_rating = serializers.ReadOnlyField()
    survey_response = serializers.SerializerMethodField()
    
    # NEW: Time control warning fields
    is_approval_due_soon = serializers.SerializerMethodField()
    is_approval_overdue = serializers.SerializerMethodField()
    approval_overdue_minutes = serializers.SerializerMethodField()
    approval_risk_level = serializers.SerializerMethodField()
    
    checkout_deadline_at = serializers.SerializerMethodField()
    is_overstay = serializers.SerializerMethodField()
    overstay_minutes = serializers.SerializerMethodField()
    overstay_risk_level = serializers.SerializerMethodField()
    
    # Staff seen tracking fields
    staff_seen_by_display = serializers.SerializerMethodField()
    is_new_for_staff = serializers.SerializerMethodField()

    class Meta:
        model = RoomBooking
        fields = [
            'booking_id',
            'confirmation_number',
            'status',
            'check_in',
            'check_out',
            'nights',

            # assignment / room
            'assigned_room_number',
            'room_number',  # NEW

            # check-in/out truth for badges
            'checked_in_at',     # NEW
            'checked_out_at',    # NEW

            # booker / guest display
            'booker_type',
            'booker_summary',
            'guest_display_name',
            'party_primary_full_name',  # NEW

            # emails
            'primary_email',
            'booker_email',

            # party meta
            'party_total_count',
            'party_complete',
            'party_missing_count',
            'party_status_display',

            # precheckin + pricing
            'precheckin_submitted_at',
            'total_amount',
            'currency',
            
            # survey flags (Tier 1 Backend Hardening)
            'survey_sent',
            'survey_completed', 
            'survey_rating',
            'survey_sent_at',
            'survey_response',
            
            # Time control fields (model + computed)
            'approval_deadline_at',
            'is_approval_due_soon',
            'is_approval_overdue',
            'approval_overdue_minutes',
            'approval_risk_level',
            'checkout_deadline_at',
            'is_overstay',
            'overstay_minutes',
            'overstay_risk_level',
            
            # Staff seen tracking
            'staff_seen_at',
            'staff_seen_by',
            'staff_seen_by_display',
            'is_new_for_staff',

            # timestamps
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_nights(self, obj):
        return obj.nights

    def get_assigned_room_number(self, obj):
        return obj.assigned_room.room_number if obj.assigned_room else None

    def get_room_number(self, obj):
        # Canonical: if assigned_room exists, use it (matches your business logic)
        return obj.assigned_room.room_number if obj.assigned_room else None

    def get_booker_summary(self, obj):
        if obj.booker_type == 'COMPANY':
            return obj.booker_company or 'Company Booking'
        elif obj.booker_type == 'INDIVIDUAL':
            return f"{obj.booker_first_name} {obj.booker_last_name}".strip() or 'Individual Booking'
        else:
            return obj.booker_type.replace('_', ' ').title()

    def get_party_primary_full_name(self, obj):
        primary_guest = obj.party.filter(role='PRIMARY').first()
        return primary_guest.full_name if primary_guest else None

    def get_guest_display_name(self, obj):
        # keep your existing behavior, but now you also expose party_primary_full_name
        primary_guest = obj.party.filter(role='PRIMARY').first()
        return primary_guest.full_name if primary_guest else "Guest Information Pending"

    def get_party_total_count(self, obj):
        return obj.party.count()

    def get_party_status_display(self, obj):
        if obj.party_complete:
            return "✅ Complete"
        missing = obj.party_missing_count
        return f"⚠️ Missing {missing} guest" if missing == 1 else f"⚠️ Missing {missing} guests"
    
    def get_survey_response(self, obj):
        """Return survey response summary for list view."""
        # Always return survey data if it exists
        if not hasattr(obj, 'survey_response') or obj.survey_response is None:
            return None
            
        # Return survey data for list view
        return {
            'submitted_at': obj.survey_response.submitted_at,
            'overall_rating': obj.survey_response.overall_rating,
            # Note: payload not included in list view for performance
        }
    
    # NEW: Time control warning methods
    def get_is_approval_due_soon(self, obj):
        """Check if approval deadline is approaching."""
        from apps.booking.services.booking_deadlines import get_approval_risk_level
        return get_approval_risk_level(obj) == 'DUE_SOON'
    
    def get_is_approval_overdue(self, obj):
        """Check if approval deadline has passed."""
        from apps.booking.services.booking_deadlines import is_approval_overdue
        return is_approval_overdue(obj)
    
    def get_approval_overdue_minutes(self, obj):
        """Get minutes approval is overdue."""
        from apps.booking.services.booking_deadlines import get_approval_overdue_minutes
        return get_approval_overdue_minutes(obj)
    
    def get_approval_risk_level(self, obj):
        """Get approval risk level for staff warnings."""
        from apps.booking.services.booking_deadlines import get_approval_risk_level
        return get_approval_risk_level(obj)
    
    def get_checkout_deadline_at(self, obj):
        """Get checkout deadline with grace period."""
        from apps.booking.services.stay_time_rules import compute_checkout_deadline
        try:
            return compute_checkout_deadline(obj)
        except Exception:
            return None
    
    def get_is_overstay(self, obj):
        """Check if booking is in overstay."""
        from apps.booking.services.stay_time_rules import is_overstay
        return is_overstay(obj)
    
    def get_overstay_minutes(self, obj):
        """Get minutes in overstay."""
        from apps.booking.services.stay_time_rules import get_overstay_minutes
        return get_overstay_minutes(obj)
    
    def get_overstay_risk_level(self, obj):
        """Get overstay risk level for staff warnings."""
        from apps.booking.services.stay_time_rules import get_overstay_risk_level
        return get_overstay_risk_level(obj)

    def get_staff_seen_by_display(self, obj):
        """Get display name for staff member who first saw this booking."""
        if obj.staff_seen_by:
            return {
                'id': obj.staff_seen_by.id,
                'name': f"{obj.staff_seen_by.first_name} {obj.staff_seen_by.last_name}".strip() or obj.staff_seen_by.user.username
            }
        return None

    def get_is_new_for_staff(self, obj):
        """Check if booking is new (not yet seen by any staff member)."""
        return obj.staff_seen_at is None


class StaffRoomBookingDetailSerializer(serializers.ModelSerializer):
    """
    Canonical booking detail serializer for staff endpoints.
    Returns all data needed for booking detail views without additional fetches.
    """
    nights = serializers.SerializerMethodField()
    
    # Booker object
    booker = serializers.SerializerMethodField()
    
    # Party grouped
    party = serializers.SerializerMethodField()
    
    # In-house guests grouped
    in_house = serializers.SerializerMethodField()
    
    # Assigned room summary
    room = serializers.SerializerMethodField()
    
    # Computed flags
    flags = serializers.SerializerMethodField()
    
    # Survey operational flags (Tier 1 Backend Hardening)
    survey_sent = serializers.ReadOnlyField()
    survey_completed = serializers.ReadOnlyField()
    survey_rating = serializers.ReadOnlyField()
    survey_response = serializers.SerializerMethodField()
    
    # NEW: Time control warning fields
    is_approval_due_soon = serializers.SerializerMethodField()
    is_approval_overdue = serializers.SerializerMethodField()
    approval_overdue_minutes = serializers.SerializerMethodField()
    approval_risk_level = serializers.SerializerMethodField()
    
    checkout_deadline_at = serializers.SerializerMethodField()
    is_overstay = serializers.SerializerMethodField()
    overstay_minutes = serializers.SerializerMethodField()
    overstay_risk_level = serializers.SerializerMethodField()
    
    # Staff seen tracking fields
    staff_seen_by_display = serializers.SerializerMethodField()
    is_new_for_staff = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomBooking
        fields = [
            'booking_id',
            'confirmation_number',
            'status',
            'check_in',
            'check_out',
            'nights',
            'adults',                   # Occupancy info needed for expected vs recorded display
            'children',                 # Occupancy info needed for expected vs recorded display
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
            'precheckin_submitted_at',  # Add precheckin completion timestamp
            'precheckin_payload',       # Add booking-level precheckin data
            'party_complete',           # Party completion status (authoritative)
            'party_missing_count',      # Number of missing party members (authoritative)
            
            # Survey operational flags (Tier 1 Backend Hardening)
            'survey_sent',
            'survey_completed',
            'survey_rating',
            'survey_sent_at',
            'survey_response',
            
            # Time control fields (model + computed)
            'approval_deadline_at',
            'is_approval_due_soon',
            'is_approval_overdue',
            'approval_overdue_minutes',
            'approval_risk_level',
            'checkout_deadline_at',
            'is_overstay',
            'overstay_minutes',
            'overstay_risk_level',
            
            # Staff seen tracking
            'staff_seen_at',
            'staff_seen_by',
            'staff_seen_by_display',
            'is_new_for_staff',
            
            'booker',
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
    
    def get_party(self, obj):
        """Return grouped party information."""
        serializer = BookingPartyGroupedSerializer()
        return serializer.to_representation(obj)
    
    def get_in_house(self, obj):
        """Return grouped in-house guests information."""
        if not obj.checked_in_at:
            return None
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
    
    def get_survey_response(self, obj):
        """Return full survey response data if available."""
        # Always return survey data if it exists  
        if not hasattr(obj, 'survey_response') or obj.survey_response is None:
            return None
            
        # Return full survey response payload for detail view
        return {
            'submitted_at': obj.survey_response.submitted_at,
            'overall_rating': obj.survey_response.overall_rating,
            'payload': obj.survey_response.payload,  # Full survey data (comments, individual ratings, etc.)
        }
    
    # NEW: Time control warning methods
    def get_is_approval_due_soon(self, obj):
        """Check if approval deadline is approaching."""
        from apps.booking.services.booking_deadlines import get_approval_risk_level
        return get_approval_risk_level(obj) == 'DUE_SOON'
    
    def get_is_approval_overdue(self, obj):
        """Check if approval deadline has passed."""
        from apps.booking.services.booking_deadlines import is_approval_overdue
        return is_approval_overdue(obj)
    
    def get_approval_overdue_minutes(self, obj):
        """Get minutes approval is overdue."""
        from apps.booking.services.booking_deadlines import get_approval_overdue_minutes
        return get_approval_overdue_minutes(obj)
    
    def get_approval_risk_level(self, obj):
        """Get approval risk level for staff warnings."""
        from apps.booking.services.booking_deadlines import get_approval_risk_level
        return get_approval_risk_level(obj)
    
    def get_checkout_deadline_at(self, obj):
        """Get checkout deadline with grace period."""
        from apps.booking.services.stay_time_rules import compute_checkout_deadline
        try:
            return compute_checkout_deadline(obj)
        except Exception:
            return None
    
    def get_is_overstay(self, obj):
        """Check if booking is in overstay."""
        from apps.booking.services.stay_time_rules import is_overstay
        return is_overstay(obj)
    
    def get_overstay_minutes(self, obj):
        """Get minutes in overstay."""
        from apps.booking.services.stay_time_rules import get_overstay_minutes
        return get_overstay_minutes(obj)
    
    def get_overstay_risk_level(self, obj):
        """Get overstay risk level for staff warnings."""
        from apps.booking.services.stay_time_rules import get_overstay_risk_level
        return get_overstay_risk_level(obj)    def get_staff_seen_by_display(self, obj):
        """Get display name for staff member who first saw this booking."""
        if obj.staff_seen_by:
            return {
                'id': obj.staff_seen_by.id,
                'name': f"{obj.staff_seen_by.first_name} {obj.staff_seen_by.last_name}".strip() or obj.staff_seen_by.user.username
            }
        return None

    def get_is_new_for_staff(self, obj):
        """Check if booking is new (not yet seen by any staff member)."""
        return obj.staff_seen_at is None
        d e f   g e t _ s t a f f _ s e e n _ b y _ d i s p l a y ( s e l f ,   o b j ) : 
 
                 " " " G e t   d i s p l a y   n a m e   f o r   s t a f f   m e m b e r   w h o   f i r s t   s a w   t h i s   b o o k i n g . " " " 
 
                 i f   o b j . s t a f f _ s e e n _ b y : 
 
                         r e t u r n   { 
 
                                 ' i d ' :   o b j . s t a f f _ s e e n _ b y . i d , 
 
                                 ' n a m e ' :   f " { o b j . s t a f f _ s e e n _ b y . f i r s t _ n a m e }   { o b j . s t a f f _ s e e n _ b y . l a s t _ n a m e } " . s t r i p ( )   o r   o b j . s t a f f _ s e e n _ b y . u s e r . u s e r n a m e 
 
                         } 
 
                 r e t u r n   N o n e 
 
 
 
         d e f   g e t _ i s _ n e w _ f o r _ s t a f f ( s e l f ,   o b j ) : 
 
                 " " " C h e c k   i f   b o o k i n g   i s   n e w   ( n o t   y e t   s e e n   b y   a n y   s t a f f   m e m b e r ) . " " " 
 
                 r e t u r n   o b j . s t a f f _ s e e n _ a t   i s   N o n e 
 
 