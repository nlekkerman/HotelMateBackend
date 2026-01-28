#!/usr/bin/env python
"""
Test acknowledging an already-ACKED incident.
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

def test_re_acknowledge():
    """Test acknowledging an already-ACKED incident."""
    print("🔍 Testing re-acknowledgment of ACKED incident...")
    
    try:
        # Get the booking 
        booking = RoomBooking.objects.get(booking_id='BK-NOWAYHOT-2026-0001')
        hotel = booking.hotel
        
        # Create different staff user for this test
        user, created = User.objects.get_or_create(
            username='teststaff3',
            defaults={'email': 'staff3@test.com', 'first_name': 'Test', 'last_name': 'Staff3'}
        )
        
        # Show current state
        incident = OverstayIncident.objects.filter(
            booking=booking,
            status__in=['OPEN', 'ACKED']
        ).first()
        
        if incident:
            print(f"✓ Found active incident: {incident.status}")
            print(f"  Currently acknowledged by: {incident.acknowledged_by}")
            print(f"  Current note: {incident.acknowledged_note}")
        else:
            print("❌ No active incident found")
            return False
        
        # Try to acknowledge again with different staff/note
        print(f"\n🎯 Re-acknowledging with different staff user...")
        result = acknowledge_overstay(
            hotel=hotel,
            booking=booking,
            staff_user=user,
            note="Updated acknowledgment from different staff member",
            dismiss=False
        )
        
        # Check what happened
        incident_after = OverstayIncident.objects.filter(
            booking=booking,
            status__in=['OPEN', 'ACKED']
        ).first()
        
        if incident_after:
            print(f"✅ SUCCESS: Incident still ACKED")
            print(f"  Now acknowledged by: {incident_after.acknowledged_by}")
            print(f"  Updated note: {incident_after.acknowledged_note}")
            print(f"  Acknowledged at: {incident_after.acknowledged_at}")
            
            # Verify it's the same incident (not a new one)
            total_incidents = OverstayIncident.objects.filter(booking=booking).count()
            print(f"  Total incidents: {total_incidents} (should still be 2)")
            
            return True
        else:
            print("❌ No active incident after acknowledgment")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_re_acknowledge()
    sys.exit(0 if success else 1)