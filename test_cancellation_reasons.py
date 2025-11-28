#!/usr/bin/env python
"""
Test script showing how booking cancellation with reasons works
"""
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking
from django.utils import timezone

def demonstrate_cancellation_reasons():
    print("=== BOOKING CANCELLATION REASON TRACKING ===")
    print()
    
    # Get existing bookings
    bookings = RoomBooking.objects.filter(hotel_id=2, status='PENDING_PAYMENT')
    
    if not bookings.exists():
        print("No pending bookings found to demonstrate cancellation")
        return
    
    booking = bookings.first()
    
    print(f"📋 Sample Booking: {booking.booking_id}")
    print(f"   Guest: {booking.guest_name}")
    print(f"   Room: {booking.room_type.name}")
    print(f"   Status: {booking.status}")
    print(f"   Current special_requests: {booking.special_requests or 'None'}")
    print()
    
    print("🎯 CANCELLATION REASON EXAMPLES:")
    print()
    
    # Example cancellation reasons
    sample_reasons = [
        "Guest requested cancellation due to emergency",
        "No-show - guest didn't arrive",
        "Overbooking situation", 
        "Room maintenance required",
        "Payment failed after multiple attempts",
        "Weather conditions - travel impossible"
    ]
    
    for i, reason in enumerate(sample_reasons, 1):
        print(f"{i}. {reason}")
    print()
    
    print("📝 HOW CANCELLATION TRACKING WORKS:")
    print()
    print("1. Staff selects cancellation reason from predefined list or enters custom reason")
    print("2. System records:")
    print("   - Date and time of cancellation")
    print("   - Staff member who cancelled")  
    print("   - Detailed reason provided")
    print("3. Information is stored in booking.special_requests field")
    print("4. FCM notification sent to guest (if available)")
    print()
    
    # Show what the special_requests field would look like after cancellation
    staff_name = "John Smith"
    reason = "Guest requested cancellation due to emergency"
    current_requests = booking.special_requests or ''
    
    cancellation_info = (
        f"\n\n--- BOOKING CANCELLED ---\n"
        f"Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Cancelled by: {staff_name}\n"
        f"Reason: {reason}"
    )
    
    final_requests = f"{current_requests}{cancellation_info}".strip()
    
    print("📄 EXAMPLE SPECIAL_REQUESTS AFTER CANCELLATION:")
    print("-" * 50)
    print(final_requests)
    print("-" * 50)
    print()
    
    print("🔔 FCM NOTIFICATION DATA:")
    notification_data = {
        "type": "booking_cancellation",
        "booking_id": booking.booking_id,
        "confirmation_number": booking.confirmation_number,
        "hotel_name": booking.hotel.name,
        "cancellation_reason": reason,
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
        "route": "/bookings/cancelled"
    }
    print(json.dumps(notification_data, indent=2))
    print()
    
    print("🎯 API ENDPOINT USAGE:")
    print(f"POST /api/staff/hotel/hotel-killarney/bookings/{booking.booking_id}/cancel/")
    print("Body:")
    print(json.dumps({"reason": reason}, indent=2))
    print()
    
    print("✅ BENEFITS:")
    print("- Full audit trail of who cancelled and why")
    print("- Guest receives immediate notification")
    print("- Reason helps with customer service follow-up")
    print("- Data for analyzing cancellation patterns")

if __name__ == "__main__":
    demonstrate_cancellation_reasons()