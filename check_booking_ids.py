#!/usr/bin/env python
"""
Check for duplicate booking IDs and help diagnose the race condition issue.
"""
import os
import sys
import django

# Set up Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking
from django.db.models import Count
from collections import Counter

def check_duplicate_booking_ids():
    """Check for and report duplicate booking IDs"""
    print("🔍 Checking for duplicate booking IDs...")
    
    # Find bookings with duplicate booking_id
    duplicates = (
        RoomBooking.objects
        .values('booking_id')
        .annotate(count=Count('booking_id'))
        .filter(count__gt=1)
        .order_by('-count')
    )
    
    if duplicates:
        print(f"❌ Found {len(duplicates)} booking IDs with duplicates:")
        for dup in duplicates:
            booking_id = dup['booking_id']
            count = dup['count']
            print(f"  - {booking_id}: {count} bookings")
            
            # Show details of each duplicate booking
            bookings = RoomBooking.objects.filter(booking_id=booking_id).order_by('id')
            for i, booking in enumerate(bookings):
                print(f"    {i+1}. ID: {booking.id}, Hotel: {booking.hotel.slug}, "
                      f"Created: {booking.created_at}, Status: {booking.status}")
    else:
        print("✅ No duplicate booking IDs found")
    
    # Check for the specific problematic ID
    problematic_id = "BK-2026-0004"
    problematic_bookings = RoomBooking.objects.filter(booking_id=problematic_id)
    
    print(f"\n🎯 Checking specific ID: {problematic_id}")
    if problematic_bookings.exists():
        print(f"Found {problematic_bookings.count()} booking(s) with ID {problematic_id}:")
        for booking in problematic_bookings:
            print(f"  - Booking ID: {booking.id}, Hotel: {booking.hotel.slug}, "
                  f"Status: {booking.status}, Created: {booking.created_at}")
    else:
        print(f"No bookings found with ID {problematic_id}")

def check_booking_id_sequences():
    """Check booking ID sequences for 2026"""
    print("\n📊 Checking 2026 booking ID sequences...")
    
    bookings_2026 = RoomBooking.objects.filter(
        booking_id__startswith='BK-2026-'
    ).order_by('booking_id')
    
    if not bookings_2026:
        print("No 2026 bookings found")
        return
    
    # Extract sequence numbers
    sequences = []
    for booking in bookings_2026:
        try:
            sequence_part = booking.booking_id.split('-')[2]  # BK-2026-0004 -> 0004
            sequence = int(sequence_part.lstrip('0') or '0')
            sequences.append(sequence)
        except (ValueError, IndexError):
            print(f"⚠️ Invalid booking ID format: {booking.booking_id}")
    
    if sequences:
        sequences.sort()
        print(f"Found {len(sequences)} bookings for 2026:")
        print(f"  Sequence range: {min(sequences)} to {max(sequences)}")
        print(f"  Total bookings: {len(sequences)}")
        
        # Check for gaps or duplicates in sequences
        sequence_counts = Counter(sequences)
        duplicates = [seq for seq, count in sequence_counts.items() if count > 1]
        
        if duplicates:
            print(f"  ❌ Duplicate sequences: {duplicates}")
        
        # Show recent bookings
        print("\n📋 Recent 2026 bookings:")
        recent_bookings = bookings_2026.order_by('-created_at')[:5]
        for booking in recent_bookings:
            print(f"  - {booking.booking_id}: {booking.hotel.slug}, "
                  f"{booking.status}, {booking.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    check_duplicate_booking_ids()
    check_booking_id_sequences()