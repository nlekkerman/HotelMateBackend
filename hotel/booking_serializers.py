"""
Booking-related serializers for availability, pricing, and reservations.
Public endpoints - no authentication required.
"""
from rest_framework import serializers
from .models import RoomBooking, PricingQuote, BookingOptions
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
    guest_name = serializers.SerializerMethodField()
    room_type_name = serializers.CharField(
        source='room_type.name',
        read_only=True
    )
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    nights = serializers.SerializerMethodField()

    class Meta:
        model = RoomBooking
        fields = [
            'id',
            'booking_id',
            'confirmation_number',
            'hotel_name',
            'room_type_name',
            'guest_name',
            'guest_email',
            'guest_phone',
            'check_in',
            'check_out',
            'nights',
            'adults',
            'children',
            'total_amount',
            'currency',
            'status',
            'created_at',
            'paid_at',
        ]
        read_only_fields = fields

    def get_guest_name(self, obj):
        return obj.guest_name

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
            'guest_first_name',
            'guest_last_name',
            'guest_email',
            'guest_phone',
            'check_in',
            'check_out',
            'nights',
            'adults',
            'children',
            'total_amount',
            'currency',
            'status',
            'special_requests',
            'promo_code',
            'payment_reference',
            'payment_provider',
            'paid_at',
            'created_at',
            'updated_at',
            'internal_notes',
            'cancellation_details',
            'booking_summary',
        ]
        read_only_fields = [
            'id', 'booking_id', 'confirmation_number', 'hotel_name', 'hotel_preset',
            'room_type_name', 'guest_name', 'created_at', 'updated_at',
            'nights'
        ]

    def get_guest_name(self, obj):
        return obj.guest_name

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
        
        # Guest count summary
        guest_count = f"{obj.adults} adult"
        if obj.adults > 1:
            guest_count += "s"
        if obj.children > 0:
            guest_count += f", {obj.children} child"
            if obj.children > 1:
                guest_count += "ren"
        
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
