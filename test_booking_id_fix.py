#!/usr/bin/env python
"""
Test the booking ID generation fix by creating a test booking.
"""
import os
import sys
import django

# Set up Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, RoomBooking
from rooms.models import RoomType
from datetime import date, timedelta

def test_booking_id_generation():
    """Test that booking ID generation works correctly"""
    print("🧪 Testing booking ID generation...")
    
    # Get a hotel for testing
    hotel = Hotel.objects.filter(is_active=True).first()
    if not hotel:
        print("❌ No active hotels found for testing")
        return
        
    print(f"Using hotel: {hotel.name} ({hotel.slug})")
    
    # Get a room type for testing
    room_type = hotel.room_types.filter(is_active=True).first()
    if not room_type:
        print("❌ No active room types found for testing")
        return
        
    print(f"Using room type: {room_type.name}")
    
    # Check current booking IDs for 2026
    current_bookings = RoomBooking.objects.filter(
        booking_id__startswith='BK-2026-'
    ).order_by('booking_id')
    
    print(f"\n📋 Current 2026 bookings:")
    for booking in current_bookings:
        print(f"  - {booking.booking_id}: {booking.status}")
    
    # Test ID generation without saving
    test_booking = RoomBooking(
        hotel=hotel,
        room_type=room_type,
        check_in=date.today() + timedelta(days=1),
        check_out=date.today() + timedelta(days=2),
        primary_first_name="Test",
        primary_last_name="User",
        primary_email="test@example.com",
        primary_phone="+1234567890",
        booker_type="SELF",
        adults=2,
        children=0,
        total_amount=100.00,
        currency="EUR",
        status="PENDING_PAYMENT"
    )
    
    # Test the ID generation method directly
    new_booking_id = test_booking._generate_unique_booking_id()
    new_confirmation_number = test_booking._generate_unique_confirmation_number()
    
    print(f"\n✨ Generated IDs:")
    print(f"  Booking ID: {new_booking_id}")
    print(f"  Confirmation Number: {new_confirmation_number}")
    
    # Verify these IDs are indeed unique
    existing_booking = RoomBooking.objects.filter(booking_id=new_booking_id).exists()
    existing_confirmation = RoomBooking.objects.filter(confirmation_number=new_confirmation_number).exists()
    
    print(f"\n🔍 Uniqueness check:")
    print(f"  Booking ID {new_booking_id} exists: {existing_booking}")
    print(f"  Confirmation {new_confirmation_number} exists: {existing_confirmation}")
    
    if not existing_booking and not existing_confirmation:
        print("✅ Both IDs are unique - fix is working!")
    else:
        print("❌ ID collision detected - fix needs more work")

if __name__ == "__main__":
    test_booking_id_generation()