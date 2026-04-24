#!/usr/bin/env python
"""
Test the fixed OverstayStatusView to verify it handles multiple incidents correctly.
"""
import os
import sys
import django
from datetime import datetime, date, time, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import OverstayIncident, RoomBooking, Hotel
from django.utils import timezone

def test_api_fix():
    """Test the API fix works correctly."""
    print("🔍 Testing OverstayStatusView fix...")
    
    # Get the booking we know has multiple incidents
    try:
        booking = RoomBooking.objects.get(booking_id='BK-NOWAYHOT-2026-0001')
        hotel = booking.hotel
        print(f"✓ Found booking: {booking.booking_id}")
        
        # Check all incidents for this booking
        incidents = OverstayIncident.objects.filter(booking=booking).order_by('-detected_at')
        print(f"✓ Found {incidents.count()} incidents:")
        
        for incident in incidents:
            print(f"  - {incident.status} incident detected at {incident.detected_at}")
        
        # Test the OLD query (broken)
        old_incident = OverstayIncident.objects.filter(booking=booking).first()
        print(f"\n❌ OLD query (.first() without ordering):")
        print(f"  Returns: {old_incident.status} incident from {old_incident.detected_at}")
        
        # Test the NEW query (fixed)
        new_incident = (OverstayIncident.objects
            .filter(booking=booking, status__in=['OPEN', 'ACKED'])
            .order_by('-detected_at', '-id')
            .first()
        )
        print(f"\n✅ NEW query (with status filter and ordering):")
        if new_incident:
            print(f"  Returns: {new_incident.status} incident from {new_incident.detected_at}")
        else:
            print(f"  Returns: No active incidents")
            
        # Test the API endpoint
        from hotel.overstay_views import OverstayStatusView
        from django.test import RequestFactory
        from django.contrib.auth.models import User
        
        # Get or create a user
        user, created = User.objects.get_or_create(
            username='test', 
            defaults={'email': 'test@example.com'}
        )
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user
        
        view = OverstayStatusView()
        response = view.get(request, hotel.slug, booking.booking_id)
        
        print(f"\n🎯 API Response (status {response.status_code}):")
        if response.status_code == 200:
            data = response.data
            print(f"  is_overstay: {data['is_overstay']}")
            print(f"  incident_state: {data['incident_state']}")
            if 'overstay' in data:
                overstay = data['overstay']
                print(f"  overstay status: {overstay['status']}")
                print(f"  detected_at: {overstay['detected_at']}")
                print(f"  hours_overdue: {overstay['hours_overdue']}")
            
            # Verify the fix
            if data['incident_state'] == 'ACTIVE' and 'overstay' in data:
                if data['overstay']['status'] == 'OPEN':
                    print("✅ SUCCESS: API now returns OPEN incident correctly!")
                    return True
                else:
                    print("❌ ISSUE: API returned active incident but not OPEN status")
                    return False
            else:
                print("❌ ISSUE: API still not returning active incident")
                return False
        else:
            print(f"❌ API ERROR: {response.data}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_api_fix()
    sys.exit(0 if success else 1)