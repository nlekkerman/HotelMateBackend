"""
Payment processing views for hotel bookings using Stripe.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
import stripe

from .payment_cache import (
    generate_idempotency_key,
    store_payment_session,
    get_payment_session,
    store_booking_metadata,
    get_booking_metadata,
    get_idempotency_session,
    store_idempotency_session,
    is_webhook_processed,
    mark_webhook_processed,
)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class CreatePaymentSessionView(APIView):
    """
    Create a Stripe Checkout session for a booking.
    
    POST /api/public/hotel/<hotel_slug>/room-bookings/<booking_id>/payment/session/
    
    Request body:
    - success_url: URL to redirect after successful payment
    - cancel_url: URL to redirect if payment is cancelled
    """
    permission_classes = [AllowAny]
    
    def post(self, request, booking_id, hotel_slug):
        # Validate hotel slug is provided
        if not hotel_slug:
            return Response(
                {"detail": "Hotel slug is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Load booking from database
        from .models import Hotel, RoomBooking
        
        # Load booking from database (get_object_or_404 handles Http404 automatically)
        hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
        booking = get_object_or_404(
            RoomBooking,
            booking_id=booking_id,
            hotel=hotel
        )
        
        # Validate booking can accept payment
        if booking.status not in ['PENDING_PAYMENT']:
            return Response(
                {"detail": f"Booking is {booking.status}, cannot process payment"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        guest_email = booking.primary_email
        if not guest_email:
            return Response(
                {"detail": "Booking has no guest email"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate stable idempotency key (no date rotation)
        total_amount = booking.total_amount
        currency = (booking.currency or "EUR").lower()
        
        idempotency_key = generate_idempotency_key(
            booking_id,
            guest_email,
            total_amount,
            currency
        )
        
        # Check if session already exists for this idempotency key
        existing_session_id = get_idempotency_session(idempotency_key)
        
        if existing_session_id:
            try:
                # Return existing session
                existing_session = stripe.checkout.Session.retrieve(
                    existing_session_id
                )
                
                # Check if session is already paid
                if existing_session.payment_status == 'paid':
                    return Response({
                        'session_id': existing_session.id,
                        'payment_url': None,
                        'status': 'paid',
                        'amount': str(Decimal(existing_session.amount_total) / 100),
                        'currency': existing_session.currency.upper(),
                        'message': 'Booking already paid'
                    }, status=status.HTTP_200_OK)
                
                # Check if session is still valid (not expired)
                if existing_session.status == 'open':
                    return Response({
                        'session_id': existing_session.id,
                        'payment_url': existing_session.url,
                        'status': 'existing',
                        'amount': str(Decimal(existing_session.amount_total) / 100),
                        'currency': existing_session.currency.upper(),
                        'message': 'Returning existing payment session'
                    }, status=status.HTTP_200_OK)
            except stripe.error.StripeError:
                # If session doesn't exist anymore, create new one
                pass
        
        # Get URLs from request
        success_url = request.data.get(
            'success_url',
            'https://hotelsmates.com/booking/success'
        )
        cancel_url = request.data.get(
            'cancel_url',
            'https://hotelsmates.com/booking/cancelled'
        )
        
        try:
            # Get canonical booking totals from model (already set above for idempotency)

            
            # Convert total to cents/smallest currency unit (Decimal-safe)
            amount = int((Decimal(total_amount) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            
            # Extract booking details for Stripe session
            hotel_data = {
                'name': hotel.name,
                'slug': hotel.slug
            }
            
            # Null-safe room_type access
            room_type = booking.room_type
            room_name = room_type.name if room_type else "Room Booking"
            room_photo = room_type.photo.url if (room_type and room_type.photo) else None
            
            room_data = {
                'type': room_name,
                'photo': room_photo
            }
            dates_data = {
                'check_in': booking.check_in.isoformat(),
                'check_out': booking.check_out.isoformat(),
                'nights': booking.nights
            }
            guest_data = {
                'name': booking.primary_guest_name,
                'email': booking.primary_email
            }
            
            # Create line items for Stripe
            line_items = [{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': f"{hotel_data['name']} - {room_data['type']}",
                        'description': (
                            f"Check-in: {dates_data['check_in']}, "
                            f"Check-out: {dates_data['check_out']} "
                            f"({dates_data['nights']} nights)"
                        ),
                        'images': [room_data['photo']] if room_data['photo'] else [],
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }]
            
            # Create Stripe Checkout Session with proper URL parameter joining
            sep = "&" if "?" in success_url else "?"
            success_url_with_session = f"{success_url}{sep}session_id={{CHECKOUT_SESSION_ID}}"
            
            print(f"📍 CREATING PAYMENT SESSION - File: {__file__}, Function: CreatePaymentSessionView.post")
            print(f"📋 Session metadata: booking_id={booking_id}, hotel_slug={hotel_data['slug']}")
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=success_url_with_session,
                cancel_url=cancel_url,
                customer_email=guest_data['email'],
                metadata={
                    'booking_id': booking_id,
                    'hotel_slug': hotel_data['slug'],
                    'guest_name': guest_data['name'],
                    'guest_email': guest_data['email'],
                    'total_amount': str(total_amount),
                    'currency': currency,
                    'check_in': dates_data['check_in'],
                    'check_out': dates_data['check_out'],
                },
                # 🔑 KEY CHANGE: Manual capture for authorize-then-capture flow
                payment_intent_data={
                    'capture_method': 'manual',
                    'description': f"Hotel booking {booking_id} - {hotel_data['name']}",
                },
            )
            
            print(f"✅ Payment session created: {session.id} for booking {booking_id}")
            
            # Store session in cache with idempotency key
            store_idempotency_session(idempotency_key, session.id)
            
            # Store payment session data
            session_data = {
                'session_id': session.id,
                'booking_id': booking_id,
                'idempotency_key': idempotency_key,
                'amount': str(total_amount),
                'currency': currency.upper(),
                'status': 'created',
            }
            store_payment_session(booking_id, session_data)
            
            # ✅ IMMEDIATELY persist payment reference to booking
            booking.payment_provider = "stripe"
            booking.payment_reference = session.id  # Store session ID as reference
            booking.save(update_fields=['payment_provider', 'payment_reference'])
            
            print(f"Payment session created for booking {booking_id}: {session.id}")
            
            return Response({
                'session_id': session.id,
                'payment_url': session.url,
                'status': 'created',
                'amount': str(total_amount),
                'currency': currency.upper(),
            }, status=status.HTTP_200_OK)
            
        except stripe.error.StripeError as e:
            return Response(
                {
                    'detail': 'Payment session creation failed',
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'detail': 'An error occurred',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StripeWebhookView(APIView):
    """
    Handle Stripe webhook events for payment confirmation.
    
    POST /api/public/hotel/room-bookings/stripe-webhook/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return Response(
                {'detail': 'Invalid payload'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except stripe.error.SignatureVerificationError:
            return Response(
                {'detail': 'Invalid signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # DB idempotency check: get_or_create with status-based retry logic
        event_id = event['id']
        event_type = event['type']
        
        from django.db import IntegrityError
        from .models import StripeWebhookEvent
        
        webhook_event, created = StripeWebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={'event_type': event_type, 'status': 'RECEIVED'}
        )
        
        # Handle rare case where Stripe resends same ID with different event_type
        if not created and webhook_event.event_type != event_type:
            webhook_event.event_type = event_type
            webhook_event.save(update_fields=['event_type'])
        
        if not created and webhook_event.status == 'PROCESSED':
            print(f"Webhook event {event_id} already processed, skipping")
            return Response({
                'status': 'already_processed'
            }, status=status.HTTP_200_OK)
        
        # If FAILED or RECEIVED, reprocess
        
        # Handle the event with proper error handling
        try:
            if event['type'] == 'checkout.session.completed':
                self.process_checkout_completed(event, webhook_event)
                webhook_event.status = 'PROCESSED'
        except Exception as e:
            webhook_event.status = 'FAILED'
            webhook_event.error_message = str(e)[:1000]  # Truncate long errors
            print(f"❌ Webhook processing failed: {str(e)}")
            # ❗ CRITICAL: Still return 200 to prevent Stripe retry storms
        finally:
            webhook_event.save()
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    
    def process_checkout_completed(self, event, webhook_event):
        """Process checkout.session.completed event with authorization flow"""
        session = event['data']['object']
        
        # Extract session details
        session_id = session['id']
        payment_intent_id = session.get('payment_intent')
        
        # Extract booking info from metadata
        booking_id = session['metadata'].get('booking_id')
        hotel_slug = session['metadata'].get('hotel_slug')
        
        # Update webhook event record with context
        webhook_event.checkout_session_id = session_id
        webhook_event.payment_intent_id = payment_intent_id
        webhook_event.booking_id = booking_id
        webhook_event.hotel_slug = hotel_slug
            
        
        print(f"📍 WEBHOOK PROCESSING - checkout.session.completed")
        print(f"Processing session {session_id}, booking_id: {booking_id}")
        
        # PAYMENT STATE VALIDATION (CRITICAL) - Updated for authorize-capture flow
        payment_intent = None
        
        # ✅ FIXED: Handle both manual and automatic capture modes properly
        if payment_intent_id:
            # Retrieve PaymentIntent to check its status
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            print(f"Payment Intent status: {payment_intent['status']}")
            
            # For authorize-capture flow: expect 'requires_capture' and 'unpaid' session
            if payment_intent['status'] == 'requires_capture':
                if session['payment_status'] != 'unpaid':
                    raise ValueError(
                        f"Manual capture mode: Expected 'unpaid' session, got '{session['payment_status']}'"
                    )
                print("✅ Manual capture mode: Payment authorized, awaiting capture")
            elif payment_intent['status'] == 'succeeded':
                if session['payment_status'] != 'paid':
                    raise ValueError(
                        f"Auto capture mode: Expected 'paid' session, got '{session['payment_status']}'"
                    )
                print("✅ Auto capture mode: Payment completed immediately")
            else:
                raise ValueError(
                    f"Unexpected PaymentIntent status: {payment_intent['status']}"
                )
        else:
            # Fallback: handle sessions without payment_intent_id
            if session['payment_status'] == 'paid':
                print("✅ Payment completed (no PaymentIntent)")
            elif session['payment_status'] == 'unpaid':
                print("✅ Payment authorized (no PaymentIntent, manual capture mode)")
            else:
                raise ValueError(f"Unexpected payment_status: {session['payment_status']}")
        
        # ✅ ATOMIC AUTHORIZATION PROCESSING
        from .models import RoomBooking, Hotel
        
        with transaction.atomic():
            # Locate booking reliably - prefer metadata, fallback to payment_reference lookup
            booking = None
            
            if booking_id and hotel_slug:
                try:
                    booking = RoomBooking.objects.select_for_update().get(
                        booking_id=booking_id,
                        hotel__slug=hotel_slug
                    )
                    print(f"Found booking by metadata: {booking_id}")
                except RoomBooking.DoesNotExist:
                    print(f"Booking not found by metadata: {booking_id}")
            
            # Fallback: hotel-scoped lookup by payment_reference (session_id or payment_intent_id)
            if not booking:
                qs = RoomBooking.objects.select_for_update().all()
                if hotel_slug:
                    qs = qs.filter(hotel__slug=hotel_slug)
                
                # Search for both session_id and payment_intent_id since payment_reference changes
                search_refs = [session_id]
                if payment_intent_id:
                    search_refs.append(payment_intent_id)
                
                booking = qs.filter(payment_reference__in=search_refs).first()
                if booking:
                    print(f"Found booking by payment_reference: {booking.booking_id}")
                    booking_id = booking.booking_id  # Update for logging
                else:
                    raise Exception(f"No booking found for session {session_id} / PI {payment_intent_id}")
            
            # Idempotency check: skip if already authorized/decided or paid
            if booking.status in ('PENDING_APPROVAL', 'CONFIRMED', 'DECLINED') or booking.payment_authorized_at:
                print(f"Booking {booking_id} already processed ({booking.status}), skipping")
                booking_updated = False
            else:
                try:
                    # 🚨 CRITICAL: Set authorization state, NOT confirmed
                    booking.payment_provider = 'stripe'
                    booking.payment_intent_id = payment_intent_id  
                    booking.payment_reference = payment_intent_id or session_id
                    booking.payment_authorized_at = timezone.now()
                    booking.status = 'PENDING_APPROVAL'  # NOT CONFIRMED!
                    
                    # DO NOT SET paid_at (only set during capture)
                    
                    booking.save(update_fields=[
                        'payment_provider', 'payment_intent_id', 'payment_reference',
                        'payment_authorized_at', 'status'
                    ])
                    
                    print(f"✅ Booking {booking_id} payment authorized (pending staff approval)")
                    
                    # Refresh and log final persisted values
                    booking.refresh_from_db()
                    print(f"📋 WEBHOOK DB UPDATE COMPLETE - File: {__file__}")
                    print(f"📋 Final state - Status: {booking.status}, Paid: {booking.paid_at}, Provider: {booking.payment_provider}, Ref: {booking.payment_reference}")
                    print(f"📋 Booking ID: {booking.booking_id}, Hotel: {booking.hotel.slug if booking.hotel else 'None'}")
                    
                    booking_updated = True
                    
                    # 🚨 MISSING: Emit Pusher event for PENDING_APPROVAL status change
                    try:
                        from notifications.notification_manager import notification_manager
                        notification_manager.realtime_booking_updated(booking)
                        print(f"📡 Pusher event sent for booking {booking_id} -> PENDING_APPROVAL")
                        
                        # Send guest-scoped realtime event (payment required)
                        from django.db import transaction
                        transaction.on_commit(
                            lambda: notification_manager.realtime_guest_booking_payment_required(
                                booking=booking,
                                reason="Hotel accepted booking - payment required"
                            )
                        )
                    except Exception as e:
                        print(f"❌ Failed to send Pusher event for booking {booking_id}: {e}")
                    
                except Exception as e:
                    print(f"❌ Failed to process payment for booking {booking_id or 'unknown'}: {e}")
                    booking_updated = False
                    # Don't return error - webhook should still return 200 to Stripe
            
        # Extract email data from session metadata
        customer_email = session['metadata'].get('guest_email')
        guest_name = session['metadata'].get('guest_name')
        check_in = session['metadata'].get('check_in')
        check_out = session['metadata'].get('check_out')
        currency = session['metadata'].get('currency', 'EUR').upper()
        amount_total = float(session['metadata'].get('total_amount', 0))
        
        # Send authorization email only if DB update succeeded
        if booking_updated and customer_email:
            try:
                # Generate booking management token for secure access
                from hotel.services.booking_management import generate_booking_management_token
                raw_token, token_obj = generate_booking_management_token(booking)
                
                # Get hotel slug for the URL
                hotel_slug = booking.hotel.slug
                
                # Build secure management URL
                management_url = f"https://hotelsmates.com/booking/status/{hotel_slug}/{booking_id}?token={raw_token}"
                
                email_subject = f"Payment authorized — awaiting hotel confirmation ({booking_id})"
                email_message = f"""
Dear {guest_name or 'Guest'},

We have authorized your payment!

Booking Details:
- Booking ID: {booking_id}
- Check-in: {check_in}
- Check-out: {check_out}
- Amount authorized: {currency} {amount_total:.2f}

Your payment authorization has been successfully processed. Your booking is now awaiting hotel confirmation.

No charge will be captured unless the hotel accepts your booking. If not accepted, the authorization will be released by your bank.

You can view your booking status and manage your reservation at:
{management_url}

This secure link allows you to:
- View your booking details and status
- Cancel your booking if needed (subject to cancellation policy)
- Check cancellation fees before confirming

Important: Keep this link secure - it provides access to your booking management.

If you have any questions, please contact the hotel directly.

Best regards,
HotelsMates Team
"""
                
                sent = send_mail(
                    subject=email_subject,
                    message=email_message,
                    from_email=f"HotelsMates <{settings.EMAIL_HOST_USER}>",
                    recipient_list=[customer_email],
                    fail_silently=False,
                )
                
                print(f"📧 send_mail returned {sent} for {customer_email}")
                
            except Exception as e:
                print(f"Failed to send payment confirmation email: {e}")
        
        print(f"Webhook processing complete for booking {booking_id}")


class VerifyPaymentView(APIView):
    """
    Verify payment status for a booking.
    
    GET /api/public/hotel/<hotel_slug>/room-bookings/<booking_id>/payment/verify/?session_id=<session_id>
    """
    permission_classes = [AllowAny]
    
    def get(self, request, booking_id, hotel_slug):
        # Validate hotel slug is provided
        if not hotel_slug:
            return Response(
                {"detail": "Hotel slug is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'detail': 'session_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Retrieve the session from Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            
            return Response({
                'booking_id': booking_id,
                'payment_status': session.payment_status,
                'amount_total': session.amount_total / 100,
                'currency': session.currency.upper(),
                'customer_email': session.customer_email,
                'metadata': session.metadata,
            }, status=status.HTTP_200_OK)
            
        except stripe.error.StripeError as e:
            return Response(
                {
                    'detail': 'Failed to verify payment',
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
