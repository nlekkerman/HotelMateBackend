"""
Payment processing views for hotel bookings using Stripe.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
import stripe

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class CreatePaymentSessionView(APIView):
    """
    Create a Stripe Checkout session for a booking.
    
    POST /api/bookings/<booking_id>/payment/session/
    
    Request body:
    - success_url: URL to redirect after successful payment
    - cancel_url: URL to redirect if payment is cancelled
    """
    permission_classes = [AllowAny]
    
    def post(self, request, booking_id):
        # Get URLs from request
        success_url = request.data.get(
            'success_url',
            'https://hotelsmates.com/booking/success'
        )
        cancel_url = request.data.get(
            'cancel_url',
            'https://hotelsmates.com/booking/cancelled'
        )
        
        # For Phase 1, we'll accept booking data in the request
        # In Phase 2, this would load from database
        booking_data = request.data.get('booking', {})
        
        if not booking_data:
            return Response(
                {"detail": "Booking data is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Extract pricing info
            pricing = booking_data.get('pricing', {})
            total = pricing.get('total', '0')
            currency = pricing.get('currency', 'EUR').lower()
            
            # Convert total to cents/smallest currency unit
            amount = int(float(total) * 100)
            
            # Extract booking details
            hotel = booking_data.get('hotel', {})
            room = booking_data.get('room', {})
            dates = booking_data.get('dates', {})
            guest = booking_data.get('guest', {})
            
            # Create line items for Stripe
            line_items = [{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': f"{hotel.get('name')} - {room.get('type')}",
                        'description': (
                            f"Check-in: {dates.get('check_in')}, "
                            f"Check-out: {dates.get('check_out')} "
                            f"({dates.get('nights')} nights)"
                        ),
                        'images': [room.get('photo')] if room.get('photo') else [],
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
                customer_email=guest.get('email'),
                metadata={
                    'booking_id': booking_id,
                    'hotel_slug': hotel.get('slug'),
                    'guest_name': guest.get('name'),
                    'check_in': dates.get('check_in'),
                    'check_out': dates.get('check_out'),
                },
                payment_intent_data={
                    'description': f"Booking {booking_id} at {hotel.get('name')}",
                },
            )
            
            return Response({
                'session_id': session.id,
                'payment_url': session.url,
                'status': 'created',
                'amount': total,
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
    
    POST /api/bookings/stripe-webhook/
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
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Extract booking info from metadata
            booking_id = session['metadata'].get('booking_id')
            
            # TODO: Update booking status in database to CONFIRMED
            # TODO: Send confirmation email to guest
            # TODO: Notify hotel staff
            
            print(f"Payment successful for booking {booking_id}")
            print(f"Session: {session}")
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)


class VerifyPaymentView(APIView):
    """
    Verify payment status for a booking.
    
    GET /api/bookings/<booking_id>/payment/verify/?session_id=<session_id>
    """
    permission_classes = [AllowAny]
    
    def get(self, request, booking_id):
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
