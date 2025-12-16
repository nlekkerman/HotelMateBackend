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
        
        # Generate idempotency key
        idempotency_key = generate_idempotency_key(
            booking_id,
            guest_email
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
            # Get canonical booking totals from model
            total_amount = booking.total_amount
            currency = (booking.currency or "EUR").lower()

            
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
            
            # Create Stripe Checkout Session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                customer_email=guest_data['email'],
                metadata={
                    'booking_id': booking_id,
                    'hotel_slug': hotel_data['slug'],
                    'guest_name': guest_data['name'],
                    'check_in': dates_data['check_in'],
                    'check_out': dates_data['check_out'],
                },
                payment_intent_data={
                    'description': f"Booking {booking_id} at {hotel_data['name']}",
                },
            )
            
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
            
            # Booking data is already in DB, no need to cache
            
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
        
        # Check if this webhook event has already been processed
        event_id = event['id']
        
        if is_webhook_processed(event_id):
            print(f"Webhook event {event_id} already processed, skipping")
            return Response({
                'status': 'success',
                'message': 'Event already processed'
            }, status=status.HTTP_200_OK)
        
        # Mark event as processed
        mark_webhook_processed(event_id)
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Extract booking info from metadata
            booking_id = session['metadata'].get('booking_id')
            hotel_slug = session['metadata'].get('hotel_slug')
            guest_name = session['metadata'].get('guest_name')
            check_in = session['metadata'].get('check_in')
            check_out = session['metadata'].get('check_out')
            customer_email = session.get('customer_email')
            amount_total = session.get('amount_total', 0) / 100
            currency = session.get('currency', 'eur').upper()
            
            # Send confirmation email to guest
            if customer_email:
                try:
                    email_subject = f"Booking Confirmation - {booking_id}"
                    email_message = f"""
Dear {guest_name},

Your booking has been confirmed!

Booking Details:
- Booking ID: {booking_id}
- Check-in: {check_in}
- Check-out: {check_out}
- Total Paid: {currency} {amount_total:.2f}

Your payment has been successfully processed.

You can view your booking details at:
https://hotelsmates.com/booking/confirmation/{booking_id}

If you have any questions, please contact the hotel directly.

Best regards,
HotelsMates Team
"""
                    
                    send_mail(
                        subject=email_subject,
                        message=email_message,
                        from_email=f"HotelsMates <{settings.EMAIL_HOST_USER}>",
                        recipient_list=[customer_email],
                        fail_silently=False,
                    )
                    
                    print(f"Confirmation email sent to {customer_email}")
                    
                except Exception as e:
                    print(f"Failed to send email: {e}")
            
            # TODO: Update booking status in database to CONFIRMED (Phase 2)
            # TODO: Notify hotel staff (Phase 2)
            
            print(f"Payment successful for booking {booking_id}")
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)


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
