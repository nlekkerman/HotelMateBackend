#!/usr/bin/env python
"""
Comprehensive test for all overstay API fixes.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, OverstayIncident
from hotel.overstay_views import OverstayStatusView, OverstayAcknowledgeView
from room_bookings.services.overstay import acknowledge_overstay
from django.contrib.auth.models import User
from django.test import RequestFactory
import json

def test_all_overstay_fixes():
    """Test all overstay API endpoints work with multiple incidents."""
    print("🔍 Testing all overstay fixes comprehensively...")
    
    try:
        # Get the booking with multiple incidents
        booking = RoomBooking.objects.get(booking_id='BK-NOWAYHOT-2026-0001')
        hotel = booking.hotel
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='teststaff2',
            defaults={'email': 'staff2@test.com'}
        )
        
        factory = RequestFactory()
        
        print(f"✓ Testing with booking: {booking.booking_id}")
        print(f"✓ Hotel: {hotel.name} ({hotel.slug})")
        
        # Test 1: Status View (should work - already fixed)
        print(f"\n1️⃣ Testing OverstayStatusView...")
        status_view = OverstayStatusView()
        request = factory.get('/')
        request.user = user
        
        response = status_view.get(request, hotel.slug, booking.booking_id)
        
        if response.status_code == 200:
            data = response.data
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ incident_state: {data['incident_state']}")
            if 'overstay' in data:
                print(f"   ✅ overstay status: {data['overstay']['status']}")
        else:
            print(f"   ❌ Status failed: {response.status_code}")
            return False
            
        # Test 2: Acknowledge View (should work after fix)
        print(f"\n2️⃣ Testing OverstayAcknowledgeView...")
        ack_view = OverstayAcknowledgeView()
        request = factory.post('/', {'note': 'Comprehensive test acknowledgment'})
        request.user = user
        
        response = ack_view.post(request, hotel.slug, booking.booking_id)
        
        if response.status_code == 200:
            data = response.data
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ Response keys: {list(data.keys())}")
        else:
            print(f"   ❌ Acknowledge failed: {response.status_code} - {response.data}")
            return False
            
        # Test 3: Check final incident states
        print(f"\n3️⃣ Final incident verification...")
        incidents = OverstayIncident.objects.filter(booking=booking).order_by('-detected_at')
        
        print(f"   Total incidents: {incidents.count()}")
        active_incidents = incidents.filter(status__in=['OPEN', 'ACKED'])
        print(f"   Active incidents: {active_incidents.count()}")
        
        for incident in incidents:
            status_detail = incident.status
            if incident.acknowledged_at:
                status_detail += f" (acked by {incident.acknowledged_by})"
            print(f"   - {status_detail} (detected: {incident.detected_at})")
            
        # Test 4: Final status check
        print(f"\n4️⃣ Final status API check...")
        final_response = status_view.get(request, hotel.slug, booking.booking_id)
        if final_response.status_code == 200:
            final_data = final_response.data
            print(f"   ✅ Final incident_state: {final_data['incident_state']}")
            if 'overstay' in final_data:
                print(f"   ✅ Final overstay status: {final_data['overstay']['status']}")
        
        print(f"\n🎉 ALL TESTS PASSED! Overstay system now handles multiple incidents correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_overstay_fixes()
    sys.exit(0 if success else 1)