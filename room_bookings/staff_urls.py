"""
Room Bookings Staff URLs - Phase 2
All room booking staff endpoints under:
/api/staff/hotel/{hotel_slug}/room-bookings/

Imports business logic from hotel.staff_views - NO code duplication.
"""

from django.urls import path

# Import views from hotel.staff_views (business logic stays there)
from hotel.staff_views import (
    StaffBookingsListView,
    StaffBookingDetailView, 
    StaffBookingConfirmView,
    StaffBookingCancelView,
    BookingAssignmentView,
    BookingPartyManagementView,
)

urlpatterns = [
    # List all room bookings for the hotel
    path(
        '',
        StaffBookingsListView.as_view(),
        name='room-bookings-staff-list'
    ),
    
    # Get detailed information about a specific booking
    path(
        '<str:booking_id>/',
        StaffBookingDetailView.as_view(),
        name='room-bookings-staff-detail'
    ),
    
    # Confirm a booking (change status to CONFIRMED)
    path(
        '<str:booking_id>/confirm/',
        StaffBookingConfirmView.as_view(),
        name='room-bookings-staff-confirm'
    ),
    
    # Cancel a booking with cancellation reason
    path(
        '<str:booking_id>/cancel/',
        StaffBookingCancelView.as_view(),
        name='room-bookings-staff-cancel'
    ),
    
    # Assign room to booking (check-in process)
    path(
        '<str:booking_id>/assign-room/',
        BookingAssignmentView.as_view(),
        {'action': 'assign-room'},
        name='room-bookings-staff-assign-room'
    ),
    
    # Checkout booking (end stay)
    path(
        '<str:booking_id>/checkout/',
        BookingAssignmentView.as_view(),
        {'action': 'checkout'},
        name='room-bookings-staff-checkout'
    ),
    
    # Get booking party information
    path(
        '<str:booking_id>/party/',
        BookingPartyManagementView.as_view(),
        name='room-bookings-staff-party'
    ),
    
    # Update booking party companions list
    path(
        '<str:booking_id>/party/companions/',
        BookingPartyManagementView.as_view(),
        {'action': 'companions'},
        name='room-bookings-staff-party-companions'
    ),
]