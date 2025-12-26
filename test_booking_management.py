#!/usr/bin/env python
"""
Test script for booking management and cancellation functionality
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

try:
    django.setup()
    
    from hotel.models import RoomBooking, BookingManagementToken
    from hotel.services.booking_management import (
        generate_booking_management_token,
        cancel_booking_programmatically
    )
    
    def test_booking_management():
        """Test booking management token generation and cancellation"""
        
        # Find a test booking
        booking = RoomBooking.objects.filter(
            status__in=['CONFIRMED', 'PENDING_PAYMENT', 'PENDING_APPROVAL'],
            cancelled_at__isnull=True
        ).first()
        
        if not booking:
            print("❌ No active bookings found for testing")
            return
        
        print(f"🧪 Testing with booking: {booking.booking_id}")
        print(f"   Status: {booking.status}")
        print(f"   Guest: {booking.primary_guest_name}")
        print(f"   Hotel: {booking.hotel.name}")
        
        # Test token generation
        try:
            raw_token, token = generate_booking_management_token(booking)
            print(f"✅ Token generated: {raw_token[:20]}...")
            print(f"   Token valid: {token.is_valid}")
            print(f"   Token expires: Never (status-based)")
        except Exception as e:
            print(f"❌ Token generation failed: {e}")
            return
        
        # Test token validity
        print(f"\n🔍 Token Validity Checks:")
        print(f"   Is valid: {token.is_valid}")
        print(f"   Is expired: {token.is_expired}")
        print(f"   Is revoked: {token.revoked_at is not None}")
        print(f"   Used for cancellation: {token.is_used_for_cancellation}")
        
        # Test cancellation (only if user confirms)
        print(f"\n⚠️  Would you like to test cancellation? This will cancel the booking!")
        print(f"   Booking ID: {booking.booking_id}")
        print(f"   This action cannot be undone!")
        
        # Don't actually cancel for safety - just show what would happen
        print(f"\n🛡️  Skipping actual cancellation for safety")
        print(f"   To test cancellation, call:")
        print(f"   cancel_booking_programmatically(booking, 'Test cancellation')")
    
    def show_booking_tokens():
        """Show existing booking management tokens"""
        tokens = BookingManagementToken.objects.select_related(
            'booking', 'booking__hotel'
        ).order_by('-created_at')[:5]
        
        print(f"\n📋 Recent Booking Management Tokens:")
        for token in tokens:
            print(f"   {token.booking.booking_id} - {token.booking.hotel.name}")
            print(f"   Valid: {token.is_valid}, Used: {token.is_used_for_cancellation}")
            print(f"   Actions: {len(token.actions_performed)}")
            print(f"   Created: {token.created_at}")
            print("   ---")
    
    if __name__ == "__main__":
        print("=== Booking Management Test ===\n")
        
        show_booking_tokens()
        test_booking_management()
        
except Exception as e:
    print(f"❌ Setup error: {e}")