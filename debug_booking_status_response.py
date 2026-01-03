#!/usr/bin/env python
"""
Debug the actual BookingStatusView response to see why guest_token isn't being returned
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import RequestFactory
from django.http import QueryDict
from hotel.public_views import BookingStatusView
from hotel.models import RoomBooking, BookingManagementToken
import hashlib

def test_actual_booking_status_response():
    """Simulate the actual BookingStatusView API call"""
    
    booking_id = "BK-2026-0001"
    hotel_slug = "hotel-killarney"
    
    try:
        booking = RoomBooking.objects.get(booking_id=booking_id)
        print(f"📋 Testing BookingStatusView for: {booking.booking_id}")
        print(f"   Check-in: {booking.checked_in_at}")
        print(f"   Check-out: {booking.checked_out_at}")
        print(f"   Room: {booking.assigned_room}")
        print(f"   Should generate guest_token: {booking.checked_in_at and not booking.checked_out_at}")
        
        # Get a management token to use (we need one for the view to work)
        mgmt_tokens = BookingManagementToken.objects.filter(booking=booking)
        
        if mgmt_tokens.count() > 0:
            # Create a dummy raw token (we can't get the real one)
            test_raw_token = "test_mgmt_token_123"
            
            # Create request factory
            factory = RequestFactory()
            
            # Create the request that matches frontend call
            request = factory.get(
                f'/api/public/hotels/{hotel_slug}/booking/status/{booking_id}/',
                {'token': test_raw_token}
            )
            
            # Manually test the _get_or_create_guest_token method
            view = BookingStatusView()
            
            print(f"\n🔧 Testing guest token generation directly...")
            guest_token = view._get_or_create_guest_token(booking)
            
            if guest_token:
                print(f"✅ Guest token generated: {guest_token[:20]}...")
            else:
                print(f"❌ No guest token generated")
                
            # Test the condition that should trigger guest_token inclusion
            condition_check = booking.checked_in_at and not booking.checked_out_at
            print(f"\n🧪 Condition check for guest_token inclusion:")
            print(f"   booking.checked_in_at: {booking.checked_in_at}")
            print(f"   booking.checked_out_at: {booking.checked_out_at}")
            print(f"   not booking.checked_out_at: {not booking.checked_out_at}")
            print(f"   Final condition: {condition_check}")
            
            if condition_check and guest_token:
                print(f"✅ Should include guest_token in response")
                
                # Simulate what the response should look like
                response_preview = {
                    'booking': {
                        'id': booking.booking_id,
                        'status': booking.status,
                        'checked_in_at': booking.checked_in_at.isoformat() if booking.checked_in_at else None,
                        'checked_out_at': booking.checked_out_at.isoformat() if booking.checked_out_at else None,
                        'assigned_room_number': booking.assigned_room.room_number if booking.assigned_room else None
                    },
                    'guest_token': guest_token
                }
                print(f"\n📄 Expected response structure:")
                print(f"   guest_token: {response_preview['guest_token'][:20]}...")
                print(f"   checked_in_at: {response_preview['booking']['checked_in_at']}")
                print(f"   assigned_room_number: {response_preview['booking']['assigned_room_number']}")
                
            else:
                print(f"❌ Should NOT include guest_token")
                print(f"   Condition: {condition_check}")
                print(f"   Token: {bool(guest_token)}")
                
        else:
            print("❌ No management tokens found for testing")
            
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking {booking_id} not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_actual_booking_status_response()