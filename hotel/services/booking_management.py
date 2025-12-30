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
from django.core.mail import send_mail
from django.utils.html import strip_tags

from hotel.models import RoomBooking, BookingManagementToken


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
    subject = f"📋 Booking Request Received (NOT CONFIRMED) - {booking.confirmation_number}"
    html_content = render_to_string('emails/booking_management.html', context)
    
    # Send email
    try:
        # Create plain text version from HTML
        plain_message = strip_tags(html_content)
        
        success = send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_content,
            from_email=f"{booking.hotel.name} <{settings.EMAIL_HOST_USER}>",
            recipient_list=[recipient_email],
            fail_silently=False,
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


def payment_stage(booking):
    """
    Classify payment stage from existing booking fields.
    
    Returns one of: NONE, SESSION_CREATED, AUTHORIZED, CAPTURED
    
    Based on canonical field mappings:
    - NONE: payment_reference empty AND paid_at is null
    - SESSION_CREATED: payment_reference startswith "cs_" (Stripe Checkout Session ID)
    - AUTHORIZED: payment_reference startswith "pi_" AND paid_at is null (PaymentIntent authorized)
    - CAPTURED: paid_at is not null (payment completed)
    """
    # CAPTURED: payment completed (highest priority)
    if booking.paid_at is not None:
        return "CAPTURED"
    
    # Check payment_reference for session/intent indicators
    payment_ref = booking.payment_reference or ""
    
    if payment_ref.startswith("pi_"):
        # PaymentIntent authorized but not captured
        return "AUTHORIZED"
    elif payment_ref.startswith("cs_"):
        # Checkout Session created
        return "SESSION_CREATED"
    
    # No payment activity
    return "NONE"


def cancel_booking(booking, reason="Booking cancelled", actor="System"):
    """
    Smart cancellation service using payment_stage() to determine correct Stripe actions.
    
    Args:
        booking: RoomBooking instance
        reason: Cancellation reason
        actor: Who/what cancelled the booking
        
    Returns:
        dict: Cancellation result with actions taken
    """
    from django.utils import timezone
    from notifications.notification_manager import notification_manager
    import logging
    
    logger = logging.getLogger(__name__)
    result = {"booking_id": booking.booking_id, "actions": []}
    
    # Determine payment stage
    stage = payment_stage(booking)
    result["payment_stage"] = stage
    
    # Process cancellation atomically
    with transaction.atomic():
        # Update booking status
        booking.status = 'CANCELLED'
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = reason
        booking.save(update_fields=['status', 'cancelled_at', 'cancellation_reason'])
        result["actions"].append("DB_CANCELLED")
        
        # Handle Stripe actions based on payment stage
        if stage == "NONE":
            # No payment to handle
            result["actions"].append("NO_PAYMENT_ACTION")
            
        elif stage in ["SESSION_CREATED", "AUTHORIZED"]:
            # Void/expire session or cancel authorization
            try:
                if stage == "SESSION_CREATED" and booking.payment_reference.startswith("cs_"):
                    # Stripe session - expires automatically, no action needed
                    result["actions"].append("SESSION_EXPIRES_AUTOMATICALLY")
                elif stage == "AUTHORIZED" and booking.payment_intent_id:
                    # Cancel PaymentIntent authorization
                    import stripe
                    from django.conf import settings
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    
                    stripe.PaymentIntent.cancel(booking.payment_intent_id)
                    result["actions"].append("PAYMENT_INTENT_CANCELLED")
                    logger.info(f"Cancelled Stripe PaymentIntent {booking.payment_intent_id}")
            except Exception as e:
                result["actions"].append(f"STRIPE_ERROR: {str(e)}")
                logger.error(f"Failed to cancel Stripe payment for booking {booking.booking_id}: {e}")
                
        elif stage == "CAPTURED":
            # Refund captured payment
            try:
                # Calculate refund based on cancellation policy
                calculator = CancellationCalculator(booking)
                cancellation_result = calculator.calculate()
                
                refund_amount = cancellation_result['refund_amount']
                result["cancellation_fee"] = cancellation_result['fee_amount']
                result["refund_amount"] = refund_amount
                
                if refund_amount > 0:
                    # Process Stripe refund
                    import stripe
                    from django.conf import settings
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    
                    # Find charge ID from payment intent
                    if booking.payment_intent_id:
                        payment_intent = stripe.PaymentIntent.retrieve(booking.payment_intent_id)
                        if payment_intent.charges.data:
                            charge_id = payment_intent.charges.data[0].id
                            
                            # Create refund
                            refund = stripe.Refund.create(
                                charge=charge_id,
                                amount=int(refund_amount * 100),  # Convert to cents
                                reason='requested_by_customer'
                            )
                            
                            # Update booking record
                            booking.refund_amount = refund_amount
                            booking.refund_processed_at = timezone.now()
                            booking.refund_reference = refund.id
                            booking.save(update_fields=['refund_amount', 'refund_processed_at', 'refund_reference'])
                            
                            result["actions"].append(f"REFUND_PROCESSED: {refund.id}")
                            logger.info(f"Processed refund {refund.id} for booking {booking.booking_id}")
                else:
                    result["actions"].append("NO_REFUND_DUE")
                    
            except Exception as e:
                result["actions"].append(f"REFUND_ERROR: {str(e)}")
                logger.error(f"Failed to process refund for booking {booking.booking_id}: {e}")
        
        # Emit realtime events after commit
        transaction.on_commit(
            lambda: emit_cancellation_events(booking, reason, actor)
        )
        
    return result


def emit_cancellation_events(booking, reason, actor):
    """
    Emit cancellation events to both staff and guest channels.
    Called after transaction commit for realtime safety.
    """
    from notifications.notification_manager import notification_manager
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Staff channel event
        notification_manager.realtime_booking_cancelled(booking, reason)
        
        # Guest channel event
        notification_manager.realtime_guest_booking_cancelled(
            booking=booking,
            cancelled_at=booking.cancelled_at,
            cancellation_reason=reason
        )
        
        logger.info(f"Emitted cancellation events for booking {booking.booking_id}")
    except Exception as e:
        logger.error(f"Failed to emit cancellation events for booking {booking.booking_id}: {e}")
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