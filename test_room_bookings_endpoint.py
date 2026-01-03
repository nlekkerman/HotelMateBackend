#!/usr/bin/env python
"""
Test script to verify guest_token appears in room-bookings endpoint response.
This is the endpoint that the frontend actually uses.
"""
import os
import sys
import django

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking
from hotel.booking_views import PublicRoomBookingDetailView
from django.test import RequestFactory
from unittest.mock import Mock

def test_room_bookings_endpoint():
    """Test the actual room-bookings endpoint that frontend calls"""
    print("🧪 Testing PublicRoomBookingDetailView for room-bookings endpoint...")
    
    # Get our test booking
    booking = RoomBooking.objects.get(booking_id='BK-2026-0001')
    print(f"   Booking: {booking.booking_id}")
    print(f"   Check-in: {booking.checked_in_at}")
    print(f"   Check-out: {booking.checked_out_at}")
    print(f"   Room: {booking.assigned_room}")
    print(f"   Should include guest_token: {booking.checked_in_at and not booking.checked_out_at}")
    print()
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get(f'/api/public/hotel/hotel-killarney/room-bookings/{booking.booking_id}/')
    
    # Create view instance and call it
    view = PublicRoomBookingDetailView()
    response = view.get(request, 'hotel-killarney', booking.booking_id)
    
    print("📋 Response data structure:")
    response_data = response.data
    
    # Check if guest_token is in the response
    if 'guest_token' in response_data:
        token = response_data['guest_token']
        print(f"✅ guest_token found: {token[:20]}...")
        print(f"   Token length: {len(token) if token else 0}")
    else:
        print("❌ guest_token NOT found in response")
        print("   Available fields:")
        for key in sorted(response_data.keys()):
            print(f"     - {key}")
    
    print()
    print("📄 Full response structure:")
    for key, value in response_data.items():
        if isinstance(value, dict):
            print(f"   {key}: {{...}}")
        elif isinstance(value, list):
            print(f"   {key}: [{len(value)} items]")
        else:
            print(f"   {key}: {value}")

if __name__ == '__main__':
    test_room_bookings_endpoint()