#!/usr/bin/env python
"""
Debug script to check real booking payment status and simulate webhook processing.
Use this to debug why real bookings aren't getting their status updated.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, RoomBooking
from django.utils import timezone


def check_booking_status(booking_id):
    """Check the current status of a specific booking"""
    print(f"🔍 Checking booking {booking_id}...")
    
    try:
        booking = RoomBooking.objects.get(booking_id=booking_id)
        print(f"📋 Current state:")
        print(f"   Status: {booking.status}")
        print(f"   Payment Provider: '{booking.payment_provider}'")
        print(f"   Payment Reference: '{booking.payment_reference}'")
        print(f"   Paid At: {booking.paid_at}")
        print(f"   Total Amount: {booking.total_amount}")
        print(f"   Hotel: {booking.hotel.name} ({booking.hotel.slug})")
        
        if booking.payment_reference:
            print(f"\n✅ Payment reference exists: {booking.payment_reference}")
            print("   → This means a Stripe session was created")
            
            if booking.paid_at:
                print(f"✅ Payment confirmed at: {booking.paid_at}")
                print("   → Webhook was processed successfully")
            else:
                print("❌ No paid_at timestamp")
                print("   → Webhook may not have been called or failed")
                
                # Check if we can find webhook logs
                print("\n🔧 To debug webhook:")
                print("   1. Check Heroku logs: heroku logs --tail -a your-app-name")
                print("   2. Check Stripe dashboard for webhook deliveries")
                print("   3. Verify webhook endpoint URL in Stripe dashboard")
        else:
            print("❌ No payment reference")
            print("   → No Stripe session was created yet")
            
        return booking
        
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking {booking_id} not found")
        return None


def simulate_webhook_for_booking(booking_id, session_id=None, payment_intent_id=None):
    """Manually simulate webhook processing for a booking"""
    print(f"\n🔧 Simulating webhook for booking {booking_id}...")
    
    try:
        booking = RoomBooking.objects.get(booking_id=booking_id)
        
        if booking.paid_at:
            print(f"ℹ️  Booking already paid at {booking.paid_at}")
            return booking
            
        # Simulate what the webhook would do
        from django.db import transaction
        
        with transaction.atomic():
            booking = RoomBooking.objects.select_for_update().get(booking_id=booking_id)
            
            # Update payment info
            booking.payment_provider = 'stripe'
            booking.payment_reference = payment_intent_id or session_id or f'manual_{booking_id}'
            booking.paid_at = timezone.now()
            booking.status = 'CONFIRMED'
            
            booking.save(update_fields=[
                'payment_provider', 'payment_reference', 'paid_at', 'status'
            ])
            
            print(f"✅ Manually updated booking:")
            print(f"   Status: {booking.status}")
            print(f"   Paid At: {booking.paid_at}")
            print(f"   Reference: {booking.payment_reference}")
            
        return booking
        
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking {booking_id} not found")
        return None


def list_pending_bookings():
    """List all bookings that are still pending payment but have payment references"""
    print("🔍 Looking for bookings with payment sessions but no confirmation...")
    
    pending_with_refs = RoomBooking.objects.filter(
        status='PENDING_PAYMENT',
        payment_reference__isnull=False
    ).exclude(payment_reference='')
    
    print(f"Found {pending_with_refs.count()} bookings with payment refs but still pending:")
    
    for booking in pending_with_refs[:10]:  # Limit to 10 for readability
        print(f"   📋 {booking.booking_id}: ref={booking.payment_reference[:20]}...")
        
    return pending_with_refs


def main():
    """Interactive debugging menu"""
    print("🚀 Stripe Payment Status Debugger")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Check specific booking status")
        print("2. List pending bookings with payment refs")
        print("3. Simulate webhook for specific booking")
        print("4. Exit")
        
        try:
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1':
                booking_id = input("Enter booking ID (e.g., BK-2025-0005): ").strip()
                if booking_id:
                    check_booking_status(booking_id)
                    
            elif choice == '2':
                list_pending_bookings()
                
            elif choice == '3':
                booking_id = input("Enter booking ID: ").strip()
                session_id = input("Enter Stripe session ID (optional): ").strip()
                payment_intent = input("Enter payment intent ID (optional): ").strip()
                
                if booking_id:
                    simulate_webhook_for_booking(
                        booking_id, 
                        session_id if session_id else None,
                        payment_intent if payment_intent else None
                    )
                    
            elif choice == '4':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Quick check for the specific booking mentioned
    if len(sys.argv) > 1:
        booking_id = sys.argv[1]
        check_booking_status(booking_id)
    else:
        main()