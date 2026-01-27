#!/usr/bin/env python
"""
Test the acknowledge_overstay function fix.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, OverstayIncident
from room_bookings.services.overstay import acknowledge_overstay
from django.contrib.auth.models import User
from django.utils import timezone

def test_acknowledge_fix():
    """Test the acknowledge function works with multiple incidents."""
    print("🔍 Testing acknowledge_overstay fix...")
    
    try:
        # Get the booking with multiple incidents
        booking = RoomBooking.objects.get(booking_id='BK-NOWAYHOT-2026-0001')
        hotel = booking.hotel
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='teststaff',
            defaults={'email': 'staff@test.com'}
        )
        
        # Show current incidents
        incidents = OverstayIncident.objects.filter(booking=booking).order_by('-detected_at')
        print(f"✓ Current incidents for {booking.booking_id}:")
        for incident in incidents:
            print(f"  - {incident.status} (detected: {incident.detected_at})")
        
        # Test acknowledge function
        print(f"\n🎯 Testing acknowledge_overstay...")
        result = acknowledge_overstay(
            hotel=hotel,
            booking=booking,
            staff_user=user,
            note="Test acknowledgment from staff",
            dismiss=False
        )
        
        print(f"✅ SUCCESS: acknowledge_overstay completed without error!")
        print(f"Result keys: {list(result.keys())}")
        
        # Check what happened to incidents
        incidents_after = OverstayIncident.objects.filter(booking=booking).order_by('-detected_at')
        print(f"\n📊 Incidents after acknowledgment:")
        for incident in incidents_after:
            status_info = incident.status
            if incident.acknowledged_at:
                status_info += f" (acked: {incident.acknowledged_at})"
            print(f"  - {status_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_acknowledge_fix()
    sys.exit(0 if success else 1)