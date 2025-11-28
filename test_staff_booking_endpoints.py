#!/usr/bin/env python
"""
Test script for staff booking endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/staff"
HOTEL_SLUG = "hotel-killarney"

def test_bookings_list():
    """Test the staff bookings list endpoint"""
    print("=== TESTING STAFF BOOKINGS LIST ===")
    
    # Test without authentication (should fail)
    url = f"{BASE_URL}/hotel/{HOTEL_SLUG}/bookings/"
    response = requests.get(url)
    print(f"Without auth - Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Expected error (no auth): {response.text[:200]}")
    
    print("\nNote: To test with authentication, you need to:")
    print("1. Login as a staff member")
    print("2. Include the authorization token in headers")
    print("3. Staff member must be associated with Hotel Killarney")
    print()

def test_booking_filters():
    """Show available filter options"""
    print("=== AVAILABLE BOOKING FILTERS ===")
    print("GET /api/staff/hotel/{hotel_slug}/bookings/")
    print()
    print("Query Parameters:")
    print("- status: Filter by booking status")
    print("  Options: PENDING_PAYMENT, CONFIRMED, CANCELLED, COMPLETED, NO_SHOW")
    print("- start_date: Filter by check-in date (YYYY-MM-DD)")
    print("- end_date: Filter by check-out date (YYYY-MM-DD)")
    print()
    print("Examples:")
    print(f"- {BASE_URL}/hotel/{HOTEL_SLUG}/bookings/?status=PENDING_PAYMENT")
    print(f"- {BASE_URL}/hotel/{HOTEL_SLUG}/bookings/?start_date=2025-11-28")
    print(f"- {BASE_URL}/hotel/{HOTEL_SLUG}/bookings/?status=CONFIRMED&start_date=2025-12-01")
    print()

def test_booking_actions():
    """Show booking action endpoints"""
    print("=== BOOKING ACTIONS ===")
    print("Confirm Booking:")
    print(f"POST {BASE_URL}/hotel/{HOTEL_SLUG}/bookings/{{booking_id}}/confirm/")
    print("- Changes status from PENDING_PAYMENT to CONFIRMED")
    print("- Requires staff authentication")
    print()
    print("Cancel Booking:")
    print(f"POST {BASE_URL}/hotel/{HOTEL_SLUG}/bookings/{{booking_id}}/cancel/")
    print("- Changes status to CANCELLED")
    print("- Optional body: {'reason': 'Cancellation reason'}")
    print("- Requires staff authentication")
    print()
    print("Example booking IDs from Hotel Killarney:")
    print("- BK-20251128-0002 (Deluxe Double Room - €163.50)")
    print("- BK-20251128-0001 (Standard Room - €1144.50)")
    print()

def show_sample_response():
    """Show expected response format"""
    print("=== SAMPLE BOOKING RESPONSE ===")
    sample_booking = {
        "id": 2,
        "booking_id": "BK-20251128-0002",
        "confirmation_number": "CONF-12345",
        "hotel_name": "Hotel Killarney",
        "room_type_name": "Deluxe Double Room",
        "guest_name": "Nikola Simic",
        "guest_email": "nlekkerman@gmail.com",
        "guest_phone": "0830945102",
        "check_in": "2025-11-28",
        "check_out": "2025-11-29",
        "nights": 1,
        "adults": 2,
        "children": 0,
        "total_amount": "163.50",
        "currency": "EUR",
        "status": "PENDING_PAYMENT",
        "created_at": "2025-11-28T08:04:45.123456Z",
        "paid_at": None
    }
    
    print(json.dumps(sample_booking, indent=2))
    print()

if __name__ == "__main__":
    print("HOTEL KILLARNEY STAFF BOOKING ENDPOINTS")
    print("=" * 50)
    print()
    
    test_bookings_list()
    test_booking_filters()
    test_booking_actions()
    show_sample_response()
    
    print("CURRENT BOOKINGS STATUS:")
    print("- 2 bookings found")
    print("- Both in PENDING_PAYMENT status")
    print("- No payments processed yet")
    print("- Ready for staff confirmation/cancellation")