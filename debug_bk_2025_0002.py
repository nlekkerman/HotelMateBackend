#!/usr/bin/env python
"""
Debug script for BK-2025-0002 - investigate why it stays PENDING_PAYMENT
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

def debug_booking_bk_2025_0002():
    """Debug the specific booking BK-2025-0002"""
    from hotel.models import RoomBooking
    
    booking_id = "BK-2025-0002"
    
    print(f"🔍 DEBUGGING BOOKING: {booking_id}")
    print("=" * 60)
    
    try:
        booking = RoomBooking.objects.get(booking_id=booking_id)
        
        print(f"📋 BOOKING DETAILS:")
        print(f"   ID: {booking.booking_id}")
        print(f"   Status: {booking.status}")
        print(f"   Hotel: {booking.hotel.name} ({booking.hotel.slug})")
        print(f"   Created: {booking.created_at}")
        print(f"   Updated: {booking.updated_at}")
        print(f"   Check-in: {booking.check_in}")
        print(f"   Check-out: {booking.check_out}")
        print(f"   Total: {booking.currency} {booking.total_amount}")
        print()
        
        print(f"💳 PAYMENT DETAILS:")
        print(f"   Provider: '{booking.payment_provider}'")
        print(f"   Reference: '{booking.payment_reference}'")
        print(f"   Paid At: {booking.paid_at}")
        print()
        
        print(f"👤 GUEST DETAILS:")
        print(f"   Primary: {booking.primary_first_name} {booking.primary_last_name}")
        print(f"   Email: {booking.primary_email}")
        print(f"   Phone: {booking.primary_phone}")
        print()
        
        # Check if payment reference exists and what it is
        if booking.payment_reference:
            print(f"🔎 STRIPE SESSION INVESTIGATION:")
            print(f"   Reference found: {booking.payment_reference}")
            
            # Try to retrieve Stripe session if reference looks like a session ID
            if booking.payment_reference.startswith('cs_'):
                try:
                    import stripe
                    from django.conf import settings
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    
                    session = stripe.checkout.Session.retrieve(booking.payment_reference)
                    print(f"   Stripe Status: {session.payment_status}")
                    print(f"   Session Mode: {session.mode}")
                    print(f"   Created: {datetime.fromtimestamp(session.created)}")
                    print(f"   Amount Total: {session.amount_total / 100} {session.currency.upper()}")
                    print(f"   Customer Email: {session.customer_email}")
                    
                    if hasattr(session, 'metadata') and session.metadata:
                        print(f"   Metadata:")
                        for key, value in session.metadata.items():
                            print(f"     {key}: {value}")
                    
                    if session.payment_intent:
                        payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
                        print(f"   Payment Intent: {payment_intent.id}")
                        print(f"   Payment Status: {payment_intent.status}")
                        
                except Exception as e:
                    print(f"   ❌ Stripe API Error: {e}")
            else:
                print(f"   Reference doesn't look like Stripe session ID")
        else:
            print(f"❌ NO PAYMENT REFERENCE - Booking never had Stripe session created")
            
        print()
        print(f"🔧 DIAGNOSTIC SUMMARY:")
        
        # Age of booking
        age = datetime.now(booking.created_at.tzinfo) - booking.created_at
        print(f"   Booking Age: {age.days} days, {age.seconds // 3600} hours")
        
        # Payment flow analysis
        if not booking.payment_reference:
            print(f"   Issue: No payment session was ever created")
            print(f"   Action: Guest never reached payment step")
        elif booking.payment_reference and not booking.paid_at:
            print(f"   Issue: Payment session created but payment not completed")
            print(f"   Action: Check Stripe dashboard for session status")
        elif booking.payment_reference and booking.paid_at and booking.status == 'PENDING_PAYMENT':
            print(f"   Issue: Payment completed but status not updated")
            print(f"   Action: Webhook may have failed - check Stripe webhook logs")
        
        print()
        print(f"📞 RECOMMENDED ACTIONS:")
        if not booking.payment_reference:
            print(f"   1. Contact guest - payment link may have expired")
            print(f"   2. Generate new payment session if needed")
        else:
            print(f"   1. Check Stripe dashboard for session {booking.payment_reference}")
            print(f"   2. Check webhook delivery logs in Stripe")
            print(f"   3. If payment completed, manually update booking status")
            
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking {booking_id} not found in database")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_booking_bk_2025_0002()