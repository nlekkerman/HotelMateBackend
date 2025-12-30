"""
Guest Cancellation Service

Handles Stripe-safe guest cancellation using BookingManagementToken.
Provides idempotent, financially-correct booking cancellation with proper
Stripe authorization void/refund integration.
"""

import logging
import stripe
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from hotel.services.cancellation import CancellationCalculator
from hotel.models import GuestBookingToken

logger = logging.getLogger(__name__)


def _revoke_guest_tokens(booking, reason):
    """
    Revoke all active guest tokens for a booking.
    
    Args:
        booking: RoomBooking instance
        reason: Revocation reason string
    """
    try:
        # Revoke all active guest tokens for this booking
        tokens_updated = GuestBookingToken.objects.filter(
            booking=booking,
            status='ACTIVE'
        ).update(
            status='REVOKED',
            revoked_at=timezone.now(),
            revoked_reason=reason
        )
        
        if tokens_updated > 0:
            logger.info(f"Revoked {tokens_updated} guest tokens for booking {booking.booking_id}: {reason}")
        
    except Exception as e:
        logger.error(f"Failed to revoke guest tokens for booking {booking.booking_id}: {e}")
        # Don't fail the entire cancellation if token revocation fails


class GuestCancellationError(Exception):
    """Base exception for guest cancellation errors."""
    pass


class StripeOperationError(GuestCancellationError):
    """Exception for Stripe operation failures."""
    pass


def cancel_booking_with_token(*, booking, token_obj, reason="Guest cancellation via management link") -> dict:
    """
    Cancel a booking using BookingManagementToken with Stripe-safe operations.
    
    Args:
        booking: RoomBooking instance
        token_obj: BookingManagementToken instance
        reason: Cancellation reason string
    
    Returns:
        dict: Cancellation result with fee_amount, refund_amount, description, etc.
        
    Raises:
        GuestCancellationError: For business logic violations
        StripeOperationError: For Stripe API failures
    """
    
    # 1. VALIDATION: Check if booking can be cancelled
    if booking.status not in ["PENDING_PAYMENT", "PENDING_APPROVAL", "CONFIRMED"]:
        # If already cancelled, return idempotent success
        if booking.status == "CANCELLED" or booking.cancelled_at is not None:
            return _build_idempotent_response(booking)
        
        # Block other invalid statuses
        raise GuestCancellationError(
            f"Booking cannot be cancelled. Current status: {booking.status}"
        )
    
    # 2. CANCELLATION CALCULATION: Always recalculate server-side
    try:
        calculator = CancellationCalculator(booking)
        cancellation_result = calculator.calculate()
    except Exception as e:
        logger.exception(f"CancellationCalculator failed for booking {booking.booking_id}")
        raise GuestCancellationError("Unable to calculate cancellation fees")
    
    # 3. ATOMIC PROCESSING: Stripe first, then DB updates
    try:
        with transaction.atomic():
            # Step 3a: Handle Stripe operations FIRST
            refund_reference = _handle_stripe_operations(booking, cancellation_result)
            
            # Step 3b: Update booking fields after successful Stripe operations
            booking.status = "CANCELLED"
            booking.cancelled_at = timezone.now()
            booking.cancellation_reason = reason
            booking.cancellation_fee = cancellation_result["fee_amount"]
            booking.refund_amount = cancellation_result["refund_amount"]
            
            # Set refund reference if Stripe refund was created
            if refund_reference:
                booking.refund_reference = refund_reference
                booking.refund_processed_at = timezone.now()
            
            booking.save()
            
            # Step 3c: Revoke guest booking tokens after cancellation
            _revoke_guest_tokens(booking, "Booking cancelled")
            
            # Step 3d: Mark token as used
            token_obj.record_action("CANCEL")
            token_obj.used_at = timezone.now()
            token_obj.save()
            
            # Step 3d: Send cancellation confirmation email
            try:
                _send_cancellation_confirmation_email(booking, cancellation_result)
            except Exception as e:
                logger.warning(f"Failed to send cancellation email for {booking.booking_id}: {e}")
                # Don't fail the cancellation if email fails
            
            # Step 3e: Send real-time notifications (both FCM and Pusher via NotificationManager)
            try:
                from notifications.notification_manager import notification_manager
                notification_manager.realtime_booking_cancelled(booking, reason)
                logger.info(f"NotificationManager sent cancellation notifications for {booking.booking_id}")
            except Exception as e:
                logger.warning(f"NotificationManager failed for {booking.booking_id}: {e}")
                # Don't fail the cancellation if notifications fail
            
    except StripeOperationError:
        # Re-raise Stripe errors without wrapping
        raise
    except Exception as e:
        logger.exception(f"Transaction failed for booking {booking.booking_id}")
        raise GuestCancellationError("Failed to process cancellation")
    
    # 4. BUILD RESPONSE
    return {
        "fee_amount": cancellation_result["fee_amount"],
        "refund_amount": cancellation_result["refund_amount"],
        "description": cancellation_result["description"],
        "applied_rule": cancellation_result.get("applied_rule", ""),
        "refund_reference": refund_reference or "",
        "cancelled_at": booking.cancelled_at.isoformat()
    }


def _build_idempotent_response(booking) -> dict:
    """Build response for already-cancelled bookings."""
    return {
        "fee_amount": booking.cancellation_fee or Decimal("0.00"),
        "refund_amount": booking.refund_amount or Decimal("0.00"),
        "description": "Booking was already cancelled",
        "applied_rule": "ALREADY_CANCELLED",
        "refund_reference": getattr(booking, 'refund_reference', '') or "",
        "cancelled_at": booking.cancelled_at.isoformat() if booking.cancelled_at else ""
    }


def _handle_stripe_operations(booking, cancellation_result) -> str:
    """
    Handle Stripe authorization void or refund based on booking state.
    
    Returns:
        str: Refund reference ID if refund was created, empty string otherwise
        
    Raises:
        StripeOperationError: If required Stripe operation fails
    """
    # Skip Stripe operations if not a Stripe booking
    if booking.payment_provider != "stripe" or not booking.payment_intent_id:
        logger.info(f"Skipping Stripe operations for booking {booking.booking_id} - not a Stripe booking")
        return ""
    
    # Missing payment_intent_id - treat as safe fallback
    if not booking.payment_intent_id.strip():
        logger.warning(f"Empty payment_intent_id for Stripe booking {booking.booking_id}")
        return ""
    
    refund_reference = ""
    
    try:
        # CASE A: PENDING_APPROVAL - Void authorization
        if booking.status == "PENDING_APPROVAL" and booking.paid_at is None:
            logger.info(f"Voiding authorization for booking {booking.booking_id}")
            
            stripe.PaymentIntent.cancel(
                booking.payment_intent_id,
                cancellation_reason="requested_by_customer"
            )
            
            logger.info(f"Successfully voided PaymentIntent {booking.payment_intent_id}")
        
        # CASE B: CONFIRMED - Refund captured payment
        elif booking.status == "CONFIRMED" and booking.paid_at is not None:
            refund_amount = cancellation_result["refund_amount"]
            
            # Idempotency check: don't refund if already processed
            if booking.refund_processed_at is not None:
                logger.info(f"Refund already processed for booking {booking.booking_id}")
                return getattr(booking, 'refund_reference', '') or ""
            
            if refund_amount > 0:
                logger.info(f"Creating refund for booking {booking.booking_id}, amount: {refund_amount}")
                
                # Convert to Stripe cents safely
                refund_cents = int(Decimal(str(refund_amount)) * 100)
                idempotency_key = f"guest_cancel_refund:{booking.booking_id}"
                
                refund = stripe.Refund.create(
                    payment_intent=booking.payment_intent_id,
                    amount=refund_cents,
                    idempotency_key=idempotency_key
                )
                
                refund_reference = refund.id
                logger.info(f"Successfully created refund {refund_reference} for booking {booking.booking_id}")
            else:
                logger.info(f"No refund needed for booking {booking.booking_id} - refund amount is 0")
        
        else:
            logger.warning(f"Unexpected Stripe booking state for {booking.booking_id}: status={booking.status}, paid_at={booking.paid_at}")
    
    except stripe.error.StripeError as e:
        logger.exception(f"Stripe operation failed for booking {booking.booking_id}")
        raise StripeOperationError(f"Payment processing failed: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error in Stripe operations for booking {booking.booking_id}")
        raise StripeOperationError(f"Payment processing error: {str(e)}")
    
    return refund_reference


def _send_cancellation_confirmation_email(booking, cancellation_result):
    """Send cancellation confirmation email to guest."""
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        # Prepare email context
        context = {
            'booking': booking,
            'hotel': booking.hotel,
            'cancellation_fee': cancellation_result['fee_amount'],
            'refund_amount': cancellation_result['refund_amount'],
            'description': cancellation_result['description'],
            'refund_reference': cancellation_result.get('refund_reference', ''),
            'cancelled_at': cancellation_result['cancelled_at']
        }
        
        # Email subject
        subject = f"Booking Cancelled - {booking.hotel.name} - {booking.booking_id}"
        
        # Email content (plain text fallback)
        message = f"""
Dear {booking.primary_guest_name},

Your booking has been successfully cancelled.

Booking Details:
- Booking ID: {booking.booking_id}
- Hotel: {booking.hotel.name}
- Check-in: {booking.check_in}
- Check-out: {booking.check_out}

Cancellation Summary:
- Cancellation Fee: €{cancellation_result['fee_amount']}
- Refund Amount: €{cancellation_result['refund_amount']}
- {cancellation_result['description']}

If you have any questions, please contact the hotel directly at {booking.hotel.email}.

Thank you,
{booking.hotel.name}
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=message.strip(),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[booking.primary_email],
            fail_silently=False,
        )
        
        logger.info(f"Cancellation confirmation email sent for booking {booking.booking_id}")
        
    except Exception as e:
        logger.error(f"Failed to send cancellation email for {booking.booking_id}: {e}")
        raise