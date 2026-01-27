#!/usr/bin/env python
"""
Check existing OverstayIncidents for audit.
"""
import os
import sys
import django
from datetime import datetime, date, time, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import OverstayIncident, RoomBooking
from room_bookings.services.overstay import compute_checkout_deadline_at
from django.utils import timezone

def main():
    """Check existing incidents."""
    incidents = OverstayIncident.objects.all()
    print(f"Found {incidents.count()} OverstayIncidents:")
    
    for incident in incidents:
        print(f"\nIncident {incident.id}:")
        print(f"  Booking: {incident.booking.booking_id}")
        print(f"  Status: {incident.status}")
        print(f"  Detected at: {incident.detected_at}")
        print(f"  Expected checkout: {incident.expected_checkout_date}")
        
        booking = incident.booking
        print(f"  Booking status: {booking.status}")
        print(f"  Checked in: {booking.checked_in_at}")
        print(f"  Checked out: {booking.checked_out_at}")
        
        # Calculate current overstay status
        try:
            deadline_utc = compute_checkout_deadline_at(booking)
            now = timezone.now()
            if now > deadline_utc:
                mins_overdue = int((now - deadline_utc).total_seconds() / 60)
                print(f"  Current deadline: {deadline_utc}")
                print(f"  Current overdue: {mins_overdue} minutes")
            else:
                print(f"  Not currently overdue (deadline: {deadline_utc})")
        except Exception as e:
            print(f"  Error calculating deadline: {e}")
            
if __name__ == "__main__":
    main()