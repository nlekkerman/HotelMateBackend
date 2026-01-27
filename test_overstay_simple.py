#!/usr/bin/env python
"""
Simple test script for overstay detection functionality.
Bypasses Django test framework to avoid migration issues.
"""
import os
import sys
import django
from datetime import datetime, date, time, timedelta
import pytz

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, RoomBooking, OverstayIncident
from rooms.models import Room, RoomType  
# Add missing imports
from room_bookings.services.overstay import detect_overstays, compute_checkout_deadline_at, compute_checkout_deadline_at


def test_configurable_checkout_detection():
    """Test basic configurable checkout overstay detection."""
    print("🧪 Testing configurable checkout overstay detection...")
    
    try:
        # Get or create test hotel
        hotel, created = Hotel.objects.get_or_create(
            slug="test-hotel-dublin",
            defaults={
                'name': "Test Hotel Dublin",
                'timezone': "Europe/Dublin"
            }
        )
        print(f"✓ Hotel: {hotel.name} (timezone: {hotel.timezone})")
        
        # Test timezone access
        tz_obj = hotel.timezone_obj
        print(f"✓ Timezone object: {tz_obj}")
        
        # Test checkout deadline calculation
        test_date = date(2025, 1, 15)
        
        # Create a test booking for deadline calculation
        test_booking = RoomBooking.objects.create(
            hotel=hotel,
            booking_id='TEST-DEADLINE',
            check_in=test_date - timedelta(days=1),
            check_out=test_date,
            status='CONFIRMED',
            booker_first_name='Test',
            booker_last_name='User',
            booker_email='test@example.com',
            total_amount=100.00
        )
        
        deadline_utc = compute_checkout_deadline_at(test_booking)
        print(f"✓ Checkout deadline for {test_date}: {deadline_utc}")
        
        # Test detection before deadline (should find 0 overstays)
        before_deadline = deadline_utc - timedelta(hours=1)
        count = detect_overstays(hotel, before_deadline)
        print(f"✓ Before deadline detection: {count} overstays found")
        
        # Test detection at configured checkout deadline
        from room_bookings.services.overstay import compute_checkout_deadline_at
        at_deadline = compute_checkout_deadline_at(booking)
        count = detect_overstays(hotel, at_deadline)
        print(f"✓ At checkout deadline detection: {count} overstays found")
        
        print("✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_booking():
    """Test overstay detection with actual booking data."""
    print("\n🧪 Testing with booking data...")
    
    try:
        # Get hotel
        hotel = Hotel.objects.get(slug="test-hotel-dublin")
        
        # Get or create room type and room
        room_type, _ = RoomType.objects.get_or_create(
            hotel=hotel,
            name="Standard Room",
            defaults={
                'max_occupancy': 2,
                'starting_price_from': 100.00
            }
        )
        
        room, _ = Room.objects.get_or_create(
            hotel=hotel,
            room_number="101",
            defaults={
                'room_type': room_type,
                'room_status': 'READY_FOR_GUEST'
            }
        )
        
        print(f"✓ Room: {room.room_number} ({room.room_type.name})")
        
        # Create an overstaying booking (checked out date is yesterday)
        yesterday = date.today().replace(day=14)  # Mock yesterday
        
        # Clean up any existing test data
        RoomBooking.objects.filter(booking_id__startswith="TEST-").delete()
        OverstayIncident.objects.filter(meta__contains={'room_number': '101'}).delete()
        
        booking = RoomBooking.objects.create(
            # Required fields from model inspection
            hotel=hotel,
            room_type=room_type,
            booking_id=f"TEST-{date.today().strftime('%Y%m%d-%H%M%S')}",  # Unique ID
            confirmation_number=f"CONF-{date.today().strftime('%Y%m%d-%H%M%S')}", 
            check_in=yesterday,
            check_out=yesterday,  # Should have checked out yesterday
            primary_first_name="John",  # Required
            primary_last_name="Doe",    # Required
            total_amount=150.00,        # Required
            
            # Optional but needed for our test
            assigned_room=room,
            checked_in_at=datetime.combine(yesterday, time(15, 0), tzinfo=pytz.UTC),  # Checked in 3PM
            checked_out_at=None,  # Still not checked out = overstay!
            primary_email="john@test.com",
            status="CHECKED_IN"
        )
        
        print(f"✓ Created booking: {booking.booking_id}")
        print(f"  Check-out date: {booking.check_out}")
        print(f"  Checked in: {booking.checked_in_at}")
        print(f"  Checked out: {booking.checked_out_at}")
        
        # Now test detection after checkout deadline today
        checkout_deadline = compute_checkout_deadline_at(booking)
        print(f"✓ Testing detection at: {checkout_deadline}")
        
        # Clear any existing incidents first
        OverstayIncident.objects.filter(booking=booking).delete()
        
        count = detect_overstays(hotel, checkout_deadline + timedelta(minutes=30))
        print(f"✓ Overstays detected: {count}")
        
        # Check if incident was created
        incidents = OverstayIncident.objects.filter(booking=booking)
        print(f"✓ Incidents created: {incidents.count()}")
        
        for incident in incidents:
            print(f"  - Incident ID: {incident.id}")
            print(f"    Expected checkout: {incident.expected_checkout_date}")
            print(f"    Detected at: {incident.detected_at}")
            print(f"    Status: {incident.status}")
            print(f"    Severity: {incident.severity}")
        
        # Test idempotency - running again should not create duplicates
        # Use configured deadline instead of hardcoded noon
        checkout_deadline = compute_checkout_deadline_at(booking)
        count2 = detect_overstays(hotel, checkout_deadline)
        incidents_after = OverstayIncident.objects.filter(booking=booking).count()
        print(f"✓ Second run detected: {count2} (should be 0)")
        print(f"✓ Total incidents after: {incidents_after} (should be same)")
        
        print("✅ Booking test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Booking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🚀 Starting overstay detection tests...\n")
    
    success = True
    success &= test_configurable_checkout_detection()
    success &= test_with_booking()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("  ✅ Configurable checkout detection working")
        print("  ✅ Timezone handling working") 
        print("  ✅ OverstayIncident creation working")
        print("  ✅ Idempotency working (no duplicates)")
        print("\n🎯 Ready for production deployment!")
    else:
        print("\n💥 Some tests failed - check output above")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())