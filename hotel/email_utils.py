"""
Email utilities for hotel bookings.
"""
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_booking_confirmation_email(booking):
    """
    Send confirmation email to guest when booking is confirmed.
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Prepare email context
        context = {
            'guest_name': booking.guest_name,
            'hotel_name': booking.hotel.name,
            'booking_id': booking.booking_id,
            'confirmation_number': booking.confirmation_number,
            'room_type': booking.room_type.name,
            'check_in': booking.check_in.strftime('%B %d, %Y'),
            'check_out': booking.check_out.strftime('%B %d, %Y'),
            'nights': booking.nights,
            'adults': booking.adults,
            'children': booking.children,
            'total_amount': booking.total_amount,
            'currency': booking.currency,
            'special_requests': booking.special_requests,
            'hotel_phone': booking.hotel.phone,
            'hotel_email': booking.hotel.email,
        }
        
        # Email subject
        subject = f"Your booking at {booking.hotel.name} is confirmed"
        
        # Email body (plain text)
        message = f"""
Dear {booking.guest_name},

Your booking at {booking.hotel.name} has been confirmed!

Booking Details:
----------------
Confirmation Number: {booking.confirmation_number}
Booking ID: {booking.booking_id}

Room: {booking.room_type.name}
Check-in: {context['check_in']}
Check-out: {context['check_out']}
Nights: {booking.nights}
Guests: {booking.adults} adult(s), {booking.children} child(ren)

Total Amount: {booking.currency} {booking.total_amount}

"""
        
        if booking.special_requests:
            message += f"\nSpecial Requests: {booking.special_requests}\n"
        
        message += f"""
Contact Information:
-------------------
Hotel Phone: {booking.hotel.phone if booking.hotel.phone else 'N/A'}
Hotel Email: {booking.hotel.email if booking.hotel.email else 'N/A'}

We look forward to welcoming you!

Best regards,
{booking.hotel.name} Team
"""
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.guest_email],
            fail_silently=False,
        )
        
        logger.info(
            f"Confirmation email sent successfully for booking "
            f"{booking.booking_id} to {booking.guest_email}"
        )
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send confirmation email for booking "
            f"{booking.booking_id}: {str(e)}"
        )
        return False
