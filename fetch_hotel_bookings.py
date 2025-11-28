#!/usr/bin/env python
"""
Script to fetch and display all bookings for Hotel Killarney
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, Hotel
from django.utils import timezone

def fetch_hotel_bookings():
    try:
        # Get Hotel Killarney (ID 2)
        hotel = Hotel.objects.get(id=2)
        print(f"=== BOOKINGS FOR {hotel.name.upper()} ===")
        print(f"Hotel ID: {hotel.id}")
        print()
        
        # Get all bookings for this hotel
        bookings = RoomBooking.objects.filter(hotel=hotel).order_by('-created_at')
        
        print(f"Total bookings found: {bookings.count()}")
        print()
        
        if bookings.count() == 0:
            print("No bookings found for this hotel.")
            return
        
        # Display booking details
        print("BOOKING DETAILS:")
        print("-" * 100)
        
        for i, booking in enumerate(bookings[:20], 1):
            room_type_name = booking.room_type.name if booking.room_type else "No room type"
            
            print(f"{i}. Booking #{booking.id}")
            print(f"   Guest: {booking.guest_name}")
            print(f"   Email: {booking.guest_email}")
            print(f"   Phone: {booking.guest_phone}")
            print(f"   Room Type: {room_type_name}")
            print(f"   Status: {booking.status}")
            print(f"   Check-in: {booking.check_in}")
            print(f"   Check-out: {booking.check_out}")
            print(f"   Guests: {booking.adults} adults, {booking.children} children")
            print(f"   Total: {booking.total_amount} {booking.currency}")
            print(f"   Payment Provider: {booking.payment_provider or 'None'}")
            print(f"   Payment Reference: {booking.payment_reference or 'None'}")
            print(f"   Paid At: {booking.paid_at.strftime('%Y-%m-%d %H:%M:%S') if booking.paid_at else 'Not paid'}")
            print(f"   Created: {booking.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if booking.special_requests:
                print(f"   Special Requests: {booking.special_requests}")
            
            if booking.promo_code:
                print(f"   Promo Code: {booking.promo_code}")
            
            print()
        
        if bookings.count() > 20:
            print(f"... and {bookings.count() - 20} more bookings")
        
        # Status summary
        print("\n=== BOOKING STATUS SUMMARY ===")
        status_counts = {}
        payment_counts = {}
        
        for booking in bookings:
            # Count by status
            status = booking.status
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts[status] = 1
            
            # Count by payment provider
            payment = booking.payment_provider or 'No Payment'
            if payment in payment_counts:
                payment_counts[payment] += 1
            else:
                payment_counts[payment] = 1
        
        print("By Status:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        print("\nBy Payment Provider:")
        for payment, count in payment_counts.items():
            print(f"  {payment}: {count}")
            
    except Hotel.DoesNotExist:
        print("Hotel with ID 2 not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_hotel_bookings()