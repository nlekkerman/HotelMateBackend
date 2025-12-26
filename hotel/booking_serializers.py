"""
Booking-related serializers for availability, pricing, and reservations.
Public endpoints - no authentication required.
"""
from decimal import Decimal
from rest_framework import serializers
from .models import RoomBooking, PricingQuote, BookingOptions, BookingGuest
from rooms.models import RoomType


class BookingOptionsSerializer(serializers.ModelSerializer):
    """Serializer for booking call-to-action options"""
    class Meta:
        model = BookingOptions
        fields = [
            'primary_cta_label',
            'primary_cta_url',
            'secondary_cta_label',
            'secondary_cta_phone',
            'terms_url',
            'policies_url'
        ]


class BookingGuestSerializer(serializers.ModelSerializer):
    """Serializer for booking party members"""
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
            'precheckin_payload',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_full_name(self, obj):
        return obj.full_name


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer for room type marketing information"""
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = RoomType
        fields = [
            'id',
            'code',
            'name',
            'short_description',
            'max_occupancy',
            'bed_setup',
            'photo_url',
            'starting_price_from',
            'currency',
            'booking_code',
            'booking_url',
            'availability_message'
        ]
        read_only_fields = ['id']

    def get_photo_url(self, obj):
        """Return photo URL or None"""
        if obj.photo:
            return obj.photo.url
        return None


class PricingQuoteSerializer(serializers.ModelSerializer):
    """Serializer for PricingQuote model"""
    room_type_name = serializers.CharField(
        source='room_type.name',
        read_only=True
    )
    
    class Meta:
        model = PricingQuote
        fields = [
            'quote_id',
            'hotel',
            'room_type',
            'room_type_name',
            'check_in',
            'check_out',
            'adults',
            'children',
            'base_price_per_night',
            'number_of_nights',
            'subtotal',
            'taxes',
            'fees',
            'discount',
            'total',
            'currency',
            'promo_code',
            'created_at',
            'valid_until',
        ]
        read_only_fields = ['quote_id', 'created_at']


class RoomBookingListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing room bookings.
    Returns key booking information for list views.
    """
    room_type_name = serializers.CharField(
        source='room_type.name',
        read_only=True
    )
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    nights = serializers.SerializerMethodField()
    assigned_room_number = serializers.SerializerMethodField()

    class Meta:
        model = RoomBooking
        fields = [
            'id',
            'booking_id',
            'confirmation_number',
            'hotel_name',
            'room_type_name',
            'primary_email',
            'primary_phone',
            'booker_type',
            'assigned_room_number',
            'check_in',
            'check_out',
            'nights',
            'total_amount',
            'currency',
            'status',
            'checked_in_at',
            'checked_out_at',
            'created_at',
            'paid_at',
        ]
        read_only_fields = fields

    def get_assigned_room_number(self, obj):
        return obj.assigned_room.room_number if obj.assigned_room else None

    def get_nights(self, obj):
        return obj.nights


class RoomBookingDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual booking views.
    Includes all booking information including special requests
    and internal notes.
    """
    guest_name = serializers.SerializerMethodField()
    room_type_name = serializers.CharField(
        source='room_type.name',
        read_only=True
    )
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    hotel_preset = serializers.SerializerMethodField()
    nights = serializers.SerializerMethodField()
    cancellation_details = serializers.SerializerMethodField()
    room_photo_url = serializers.SerializerMethodField()
    booking_summary = serializers.SerializerMethodField()
    assigned_room_number = serializers.SerializerMethodField()
    party = serializers.SerializerMethodField()

    class Meta:
        model = RoomBooking
        fields = [
            'id',
            'booking_id',
            'confirmation_number',
            'hotel_name',
            'hotel_preset',
            'room_type_name',
            'room_photo_url',
            'guest_name',
            'booker_type',
            'booker_first_name',
            'booker_last_name',
            'booker_email',
            'booker_phone',
            'booker_company',
            'assigned_room',
            'assigned_room_number',
            'check_in',
            'check_out',
            'nights',
            'total_amount',
            'currency',
            'status',
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
            'cancellation_details',
            'booking_summary',
            'party',
            'party_complete',
            'party_missing_count',
        ]
        read_only_fields = [
            'id', 'booking_id', 'confirmation_number', 'hotel_name', 'hotel_preset',
            'room_type_name', 'guest_name', 'assigned_room_number', 'created_at', 'updated_at',
            'nights', 'party_complete', 'party_missing_count'
        ]

    def get_guest_name(self, obj):
        return obj.primary_guest_name
        
    def get_assigned_room_number(self, obj):
        return obj.assigned_room.room_number if obj.assigned_room else None

    def get_nights(self, obj):
        return obj.nights

    def get_hotel_preset(self, obj):
        """Get hotel's public page preset (1-5) for styling"""
        try:
            return obj.hotel.public_page.global_style_variant or 1
        except:
            return 1
    
    def get_cancellation_details(self, obj):
        """Parse cancellation information from special_requests field"""
        if obj.status != 'CANCELLED' or not obj.special_requests:
            return None
        
        # Parse cancellation info from special_requests
        cancellation_section = "--- BOOKING CANCELLED ---"
        if cancellation_section not in obj.special_requests:
            return {
                "cancelled_date": "Not specified",
                "cancelled_by": "Staff",
                "cancellation_reason": "No reason provided"
            }
        
        # Extract cancellation details
        try:
            cancel_text = obj.special_requests.split(cancellation_section)[1]
            lines = [line.strip() for line in cancel_text.split('\n') if line.strip()]
            
            cancelled_date = "Not specified"
            cancelled_by = "Staff"
            cancellation_reason = "No reason provided"
            
            for line in lines:
                if line.startswith("Date:"):
                    cancelled_date = line.replace("Date:", "").strip()
                elif line.startswith("Cancelled by:"):
                    cancelled_by = line.replace("Cancelled by:", "").strip()
                elif line.startswith("Reason:"):
                    cancellation_reason = line.replace("Reason:", "").strip()
            
            return {
                "cancelled_date": cancelled_date,
                "cancelled_by": cancelled_by,
                "cancellation_reason": cancellation_reason
            }
        except:
            return {
                "cancelled_date": "Not specified",
                "cancelled_by": "Staff", 
                "cancellation_reason": "No reason provided"
            }
    
    def get_room_photo_url(self, obj):
        """Get room type photo URL"""
        if obj.room_type and obj.room_type.photo:
            return obj.room_type.photo.url
        return None
    
    def get_booking_summary(self, obj):
        """Generate booking summary for modal display"""
        # Calculate stay duration
        stay_duration = obj.nights
        
        # Format dates nicely
        check_in_formatted = obj.check_in.strftime('%B %d, %Y')
        check_out_formatted = obj.check_out.strftime('%B %d, %Y')
        
        # Guest count summary - derive from party
        party_count = obj.party.filter(is_staying=True).count()
        guest_count = f"{party_count} guest"
        if party_count != 1:
            guest_count += "s"
        
        # Payment status
        payment_status = "Paid" if obj.paid_at else "Pending"
        if obj.payment_provider:
            payment_status += f" via {obj.payment_provider.title()}"
        
        return {
            "stay_duration": f"{stay_duration} night" + ("s" if stay_duration > 1 else ""),
            "check_in_formatted": check_in_formatted,
            "check_out_formatted": check_out_formatted,
            "guest_count": guest_count,
            "payment_status": payment_status,
            "total_formatted": f"{obj.currency} {obj.total_amount}",
            "created_formatted": obj.created_at.strftime('%B %d, %Y at %I:%M %p'),
            "room_description": obj.room_type.short_description if obj.room_type else ""
        }
    
    def get_party(self, obj):
        """Get booking party information grouped by role using canonical serializer"""
        from .canonical_serializers import BookingPartyGroupedSerializer
        return BookingPartyGroupedSerializer().to_representation(obj)


class PublicRoomBookingDetailSerializer(serializers.ModelSerializer):
    """
    Public serializer for room booking details exposed to external systems.
    Only includes public-safe fields as defined in the API contracts.
    """
    hotel_info = serializers.SerializerMethodField()
    room_info = serializers.SerializerMethodField()
    dates_info = serializers.SerializerMethodField()
    guests_info = serializers.SerializerMethodField()
    guest_info = serializers.SerializerMethodField()
    pricing_info = serializers.SerializerMethodField()
    payment_url = serializers.SerializerMethodField()
    payment_required = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    cancellation_preview = serializers.SerializerMethodField()

    class Meta:
        model = RoomBooking
        fields = [
            'booking_id',
            'confirmation_number', 
            'status',
            'created_at',
            'hotel_info',
            'room_info',
            'dates_info',
            'guests_info',
            'guest_info',
            'special_requests',
            'pricing_info',
            'promo_code',
            'payment_required',
            'payment_url',
            'can_cancel',
            'cancellation_preview',
        ]
        read_only_fields = fields
    
    def get_hotel_info(self, obj):
        """Hotel information"""
        return {
            "name": obj.hotel.name,
            "slug": obj.hotel.slug,
            "phone": getattr(obj.hotel, 'phone', '+353 64 663 1555'),  # Default fallback
            "email": getattr(obj.hotel, 'email', 'info@hotelkillarney.ie')  # Default fallback
        }
    
    def get_room_info(self, obj):
        """Room type information"""
        return {
            "type": obj.room_type.name,
            "code": obj.room_type.code,
            "photo": obj.room_type.photo.url if obj.room_type.photo else None
        }
    
    def get_dates_info(self, obj):
        """Booking dates information"""
        return {
            "check_in": obj.check_in.strftime('%Y-%m-%d'),
            "check_out": obj.check_out.strftime('%Y-%m-%d'),
            "nights": obj.nights
        }
    
    def get_guests_info(self, obj):
        """Guest count information"""
        return {
            "adults": obj.adults,
            "children": obj.children,
            "total": obj.adults + obj.children
        }
    
    def get_guest_info(self, obj):
        """Primary guest information (public-safe fields only)"""
        return {
            "name": obj.primary_guest_name,
            "email": obj.primary_email,
            "phone": obj.primary_phone
        }
    
    def get_pricing_info(self, obj):
        """Pricing information"""
        # For public API, calculate basic breakdown if needed
        subtotal = obj.total_amount * Decimal('0.917')  # Reverse VAT calculation
        taxes = obj.total_amount - subtotal
        
        return {
            "subtotal": f"{subtotal:.2f}",
            "taxes": f"{taxes:.2f}",
            "discount": "0.00",  # No discount info in current model
            "total": f"{obj.total_amount:.2f}",
            "currency": obj.currency
        }
    
    def get_payment_url(self, obj):
        """Payment session URL for pending bookings"""
        request = self.context.get('request')
        if request and obj.status == 'PENDING_PAYMENT':
            hotel_slug = obj.hotel.slug
            booking_id = obj.booking_id
            return f"/api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/payment/session/"
        return None
    
    def get_payment_required(self, obj):
        """Check if payment is required for this booking"""
        # "needs payment" if pending and not marked paid
        return (obj.status == "PENDING_PAYMENT") and (obj.paid_at is None)
    
    def get_can_cancel(self, obj):
        """Check if booking can be cancelled"""
        return obj.status in ['CONFIRMED', 'PENDING_PAYMENT', 'PENDING_APPROVAL'] and not obj.cancelled_at
    
    def get_cancellation_preview(self, obj):
        """Get cancellation fee preview if booking can be cancelled"""
        if not self.get_can_cancel(obj):
            return None
            
        try:
            from hotel.services.cancellation import CancellationCalculator
            calculator = CancellationCalculator(obj)
            result = calculator.calculate()
            return {
                'fee_amount': str(result['fee_amount']),
                'refund_amount': str(result['refund_amount']),
                'description': result['description'],
                'applied_rule': result.get('applied_rule', '')
            }
        except Exception:
            return None
    
    def get_can_cancel(self, obj):
        """Check if booking can be cancelled"""
        return obj.status in ['CONFIRMED', 'PENDING_PAYMENT', 'PENDING_APPROVAL'] and not obj.cancelled_at
    
    def get_cancellation_preview(self, obj):
        """Get cancellation fee preview if booking can be cancelled"""
        if not self.get_can_cancel(obj):
            return None
            
        try:
            from hotel.services.cancellation import CancellationCalculator
            calculator = CancellationCalculator(obj)
            result = calculator.calculate()
            return {
                'fee_amount': str(result['fee_amount']),
                'refund_amount': str(result['refund_amount']),
                'description': result['description'],
                'applied_rule': result.get('applied_rule', '')
            }
        except Exception:
            return None
    
    def to_representation(self, instance):
        """Custom representation to match expected API format"""
        data = super().to_representation(instance)
        
        # Restructure to match expected format
        result = {
            "booking_id": data['booking_id'],
            "confirmation_number": data['confirmation_number'],
            "status": data['status'],
            "created_at": data['created_at'],
            "hotel": data['hotel_info'],
            "room": data['room_info'],
            "dates": data['dates_info'],
            "guests": data['guests_info'],
            "guest": data['guest_info'],
            "special_requests": data['special_requests'] or "",
            "pricing": data['pricing_info'],
            "promo_code": data['promo_code'],
            "payment_required": data['status'] == 'PENDING_PAYMENT',
            "payment_url": data['payment_url'],
            "can_cancel": data['can_cancel'],
            "cancellation_preview": data['cancellation_preview']
        }
        
        return result
