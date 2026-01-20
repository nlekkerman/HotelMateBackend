#!/usr/bin/env python
"""
Test script to verify booking time control services are working correctly.
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append('c:\\Users\\nlekk\\HMB\\HotelMateBackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.utils import timezone
from hotel.models import RoomBooking, Hotel
from apps.booking.services.booking_deadlines import (
    compute_approval_deadline, 
    get_approval_risk_level,
    is_approval_overdue
)
from apps.booking.services.stay_time_rules import (
    compute_checkout_deadline,
    is_overstay, 
    get_overstay_risk_level
)

def test_services():
    """Test the booking time control services."""
    print("🔍 Testing Booking Time Control Services")
    print("=" * 50)
    
    # Test 1: Get a sample booking or create mock data
    bookings = RoomBooking.objects.all()[:1]
    if not bookings:
        print("❌ No bookings found in database for testing")
        return False
    
    booking = bookings[0]
    print(f"📋 Testing with booking: {booking.booking_id}")
    print(f"   Status: {booking.status}")
    print(f"   Hotel: {booking.hotel.name}")
    print(f"   Check-out: {booking.check_out}")
    
    # Test 2: Approval deadline service
    print("\n📅 Testing Approval Deadline Service:")
    try:
        deadline = compute_approval_deadline(booking)
        risk_level = get_approval_risk_level(booking)
        is_overdue = is_approval_overdue(booking)
        
        print(f"✅ compute_approval_deadline: {deadline}")
        print(f"✅ get_approval_risk_level: {risk_level}")
        print(f"✅ is_approval_overdue: {is_overdue}")
    except Exception as e:
        print(f"❌ Approval deadline service error: {e}")
        return False
    
    # Test 3: Stay time rules service
    print("\n🏨 Testing Stay Time Rules Service:")
    try:
        checkout_deadline = compute_checkout_deadline(booking)
        is_overstaying = is_overstay(booking)
        overstay_risk = get_overstay_risk_level(booking)
        
        print(f"✅ compute_checkout_deadline: {checkout_deadline}")
        print(f"✅ is_overstay: {is_overstaying}")
        print(f"✅ get_overstay_risk_level: {overstay_risk}")
    except Exception as e:
        print(f"❌ Stay time rules service error: {e}")
        return False
    
    # Test 4: Hotel configuration access
    print("\n⚙️ Testing Hotel Configuration:")
    try:
        hotel_config = getattr(booking.hotel, 'access_config', None)
        if hotel_config:
            print(f"✅ Hotel has access_config")
            print(f"   Standard checkout time: {hotel_config.standard_checkout_time}")
            print(f"   Grace minutes: {hotel_config.late_checkout_grace_minutes}")
            print(f"   Approval SLA: {hotel_config.approval_sla_minutes} minutes")
        else:
            print("⚠️ Hotel access_config not found - using defaults")
    except Exception as e:
        print(f"❌ Hotel configuration error: {e}")
        return False
    
    # Test 5: Database fields
    print("\n💾 Testing New Database Fields:")
    try:
        print(f"✅ approval_deadline_at: {booking.approval_deadline_at}")
        print(f"✅ expired_at: {booking.expired_at}")
        print(f"✅ auto_expire_reason_code: {booking.auto_expire_reason_code}")
        print(f"✅ overstay_flagged_at: {booking.overstay_flagged_at}")
        print(f"✅ overstay_acknowledged_at: {booking.overstay_acknowledged_at}")
        print(f"✅ refunded_at: {booking.refunded_at}")
        print(f"✅ refund_reference: {booking.refund_reference}")
    except Exception as e:
        print(f"❌ Database fields error: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    success = test_services()
    sys.exit(0 if success else 1)