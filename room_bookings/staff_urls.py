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
    # Safe Room Assignment System Views
    AvailableRoomsView,
    SafeAssignRoomView,
    UnassignRoomView,
    SafeStaffBookingListView,
    # Pre-check-in functionality
    SendPrecheckinLinkView,
    # Stripe Authorize-Capture Flow Views
    StaffBookingAcceptView,
    StaffBookingDeclineView,
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
    
    # ===== SAFE ROOM ASSIGNMENT SYSTEM ENDPOINTS =====
    
    # Get available rooms for a booking
    path(
        '<str:booking_id>/available-rooms/',
        AvailableRoomsView.as_view(),
        name='room-bookings-available-rooms'
    ),
    
    # Safe room assignment with atomic locking and validation
    path(
        '<str:booking_id>/safe-assign-room/',
        SafeAssignRoomView.as_view(),
        name='room-bookings-safe-assign-room'
    ),
    
    # Unassign room (before check-in only)
    path(
        '<str:booking_id>/unassign-room/',
        UnassignRoomView.as_view(),
        name='room-bookings-unassign-room'
    ),
    
    # Enhanced staff bookings list with assignment filters
    path(
        'safe/',
        SafeStaffBookingListView.as_view(),
        name='room-bookings-safe-staff-list'
    ),
    
    # Send pre-check-in link to guests
    path(
        '<str:booking_id>/send-precheckin-link/',
        SendPrecheckinLinkView.as_view(),
        name='send-precheckin-link'
    ),
    
    # ===== STRIPE AUTHORIZE-CAPTURE FLOW ENDPOINTS =====
    
    # Approve booking (capture authorized payment)
    path(
        '<str:booking_id>/approve/',
        StaffBookingAcceptView.as_view(),
        name='room-bookings-staff-approve'
    ),
    
    # Decline booking (cancel authorization)
    path(
        '<str:booking_id>/decline/',
        StaffBookingDeclineView.as_view(),
        name='room-bookings-staff-decline'
    ),
]