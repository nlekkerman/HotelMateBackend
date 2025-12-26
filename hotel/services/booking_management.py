"""
Booking Management Service

Handles creation of secure booking management tokens and email sending.
Allows guests to view and manage their bookings via secure links.
"""
import hashlib
import secrets
from datetime import timedelta
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings

from hotel.models import RoomBooking, BookingManagementToken
from notifications.email_service import send_html_email


def generate_booking_management_token(booking: RoomBooking) -> tuple[str, BookingManagementToken]:
    """
    Generate a secure booking management token for a booking.
    Token remains valid until booking is completed, cancelled, or declined.
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        tuple: (raw_token, BookingManagementToken instance)
    """
    # Generate secure random token
    raw_token = secrets.token_urlsafe(32)
    
    # Create token hash for database storage
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Set expires_at to checkout date (for reference, but validity is status-based)
    expires_at = timezone.make_aware(
        timezone.datetime.combine(booking.check_out, timezone.datetime.min.time())
    ) + timedelta(days=1)  # Day after checkout
    
    # Create token record
    token = BookingManagementToken.objects.create(
        booking=booking,
        token_hash=token_hash,
        expires_at=expires_at  # Keep for reference, but validity is status-based
    )
    
    return raw_token, token


def send_booking_management_email(booking: RoomBooking, raw_token: str, recipient_email: str = None) -> bool:
    """
    Send booking management email with secure link.
    
    Args:
        booking: RoomBooking instance
        raw_token: Raw token string (not hashed)
        recipient_email: Email to send to (defaults to booking primary email)
    
    Returns:
        bool: Success status
    """
    if not recipient_email:
        recipient_email = booking.primary_email
    
    if not recipient_email:
        raise ValueError("No recipient email provided")
    
    # Build management URL with hotel slug, booking ID, and token
    base_url = getattr(settings, 'FRONTEND_BASE_URL', 'https://hotelsmates.com')
    management_url = f"{base_url}/booking/status/{booking.hotel.slug}/{booking.booking_id}?token={raw_token}"
    
    # Prepare email context
    context = {
        'booking': booking,
        'hotel': booking.hotel,
        'management_url': management_url,
        'guest_name': booking.primary_guest_name
    }
    
    # Render email templates
    subject = f"Manage Your Booking - {booking.confirmation_number}"
    html_content = render_to_string('emails/booking_management.html', context)
    
    # Send email
    try:
        success = send_html_email(
            recipient_email=recipient_email,
            subject=subject,
            html_content=html_content,
            sender_name=booking.hotel.name
        )
        
        if success:
            # Update token with sent email
            token = BookingManagementToken.objects.filter(
                booking=booking,
                token_hash=hashlib.sha256(raw_token.encode()).hexdigest()
            ).first()
            
            if token:
                token.sent_to_email = recipient_email
                token.save()
        
        return success
        
    except Exception as e:
        print(f"Failed to send booking management email: {e}")
        return False


def create_and_send_booking_management_token(booking: RoomBooking, recipient_email: str = None) -> bool:
    """
    High-level function to create token and send management email.
    
    Args:
        booking: RoomBooking instance
        recipient_email: Email to send to (defaults to booking primary email)
    
    Returns:
        bool: Success status
    """
    try:
        # Generate token
        raw_token, token = generate_booking_management_token(booking)
        
        # Send email
        success = send_booking_management_email(booking, raw_token, recipient_email)
        
        if success:
            print(f"✅ Booking management email sent for {booking.booking_id}")
        else:
            print(f"❌ Failed to send booking management email for {booking.booking_id}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error creating booking management token: {e}")
        return False


def get_booking_management_url(booking_id: str, raw_token: str) -> str:
    """
    Generate the frontend URL for booking management.
    
    Args:
        booking_id: Booking ID (e.g., 'BK-2025-0023')
        raw_token: Raw token string
    
    Returns:
        str: Complete management URL
    """
    base_url = getattr(settings, 'FRONTEND_BASE_URL', 'https://hotelsmates.com')
    return f"{base_url}/booking/status/{booking_id}?token={raw_token}"


def cancel_booking_programmatically(booking: RoomBooking, reason: str = "Cancelled by system", cancelled_by: str = "System") -> dict:
    """
    Cancel a booking programmatically (for system/admin use).
    
    Args:
        booking: RoomBooking instance
        reason: Cancellation reason
        cancelled_by: Who/what cancelled the booking
    
    Returns:
        dict: Cancellation result with fee information
    """
    from django.utils import timezone
    from django.db import transaction
    from hotel.services.cancellation import CancellationCalculator
    
    # Check if booking can be cancelled
    if booking.status not in ['CONFIRMED', 'PENDING_PAYMENT', 'PENDING_APPROVAL']:
        raise ValueError(f"Booking {booking.booking_id} cannot be cancelled (status: {booking.status})")
    
    if booking.cancelled_at:
        raise ValueError(f"Booking {booking.booking_id} is already cancelled")
    
    # Calculate cancellation fees
    calculator = CancellationCalculator(booking)
    cancellation_result = calculator.calculate()
    
    # Process cancellation atomically
    with transaction.atomic():
        booking.status = 'CANCELLED'
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = reason
        booking.cancellation_fee = cancellation_result['fee_amount']
        booking.refund_amount = cancellation_result['refund_amount']
        booking.save()
        
        # Mark all management tokens as used
        BookingManagementToken.objects.filter(
            booking=booking,
            used_at__isnull=True
        ).update(used_at=timezone.now())
    
    return {
        'success': True,
        'booking_id': booking.booking_id,
        'cancelled_at': booking.cancelled_at.isoformat(),
        'cancellation_fee': str(booking.cancellation_fee),
        'refund_amount': str(booking.refund_amount),
        'description': cancellation_result['description'],
        'cancelled_by': cancelled_by
    }