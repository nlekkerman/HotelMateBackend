"""
Checkout Ghost Guest Bug Reproduction Test

Test for the specific bug where guests become "orphaned" (booking=NULL but still in room)
and checkout fails to clear the room because it only looks for guests with BOTH booking AND room.
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from hotel.models import Hotel, RoomBooking
from rooms.models import Room, RoomType
from guests.models import Guest
from staff.models import Staff, Role, Department


class CheckoutGhostGuestBugTest(TestCase):
    """Test for the Room 337 ghost guest checkout bug scenario."""
    
    def setUp(self):
        """Set up test data for ghost guest bug reproduction."""
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel Ghost Bug",
            slug="test-hotel-ghost"
        )
        
        # Create room type
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            code="STD",
            max_occupancy=2
        )
        
        # Create the infamous Room 337
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_number="337",
            room_type=self.room_type,
            is_active=True,
            is_out_of_order=False,
            is_occupied=True,  # Room shows as occupied
            room_status="OCCUPIED"
        )
        
        # Create confirmed booking with room assigned
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            booker_type="SELF",
            adults=2,
            children=0,
            total_amount=200.00,
            status="CONFIRMED",
            assigned_room=self.room,  # Room is properly assigned
            checked_in_at=timezone.now()  # Booking is checked in
        )
        
        # Create staff user and profile
        self.user = User.objects.create_user(
            username="staff@test.com",
            email="staff@test.com",
            password="testpass123"
        )
        
        self.role = Role.objects.create(name="Receptionist", slug="receptionist")
        self.department = Department.objects.create(name="Front Desk", slug="front-desk")
        
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            role=self.role,
            department=self.department,
            first_name="Staff",
            last_name="Member"
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('notifications.notification_manager.NotificationManager.realtime_booking_checked_out')
    @patch('notifications.notification_manager.NotificationManager.realtime_room_occupancy_updated')
    def test_checkout_with_ghost_guests_room_337_bug(self, mock_room_notify, mock_booking_notify):
        """
        EXACT REPRODUCTION: Room 337 ghost guest checkout bug.
        
        Scenario: 
        - Booking guests have room=NULL (corrupted state)
        - Ghost guests in room have booking=NULL (orphaned state)
        - Old checkout logic finds 0 guests and leaves room occupied
        - NEW checkout logic finds ALL affected guests and clears room
        """
        
        # === CREATE THE CORRUPTED STATE ===
        
        # 1. Create booking guest with room=NULL (corrupted - should have room assigned)
        booking_guest = Guest.objects.create(
            hotel=self.hotel,
            first_name="John",
            last_name="Doe",
            booking=self.booking,  # Linked to booking
            room=None,  # ❌ CORRUPTED: Should be self.room but got disconnected
            guest_type='PRIMARY'
        )
        
        # 2. Create orphaned ghost guest in room with booking=NULL (invalid state)
        ghost_guest = Guest.objects.create(
            hotel=self.hotel,
            first_name="Ghost",
            last_name="Guest",
            booking=None,  # ❌ ORPHANED: No booking link
            room=self.room,  # Still assigned to room
            guest_type='PRIMARY'
        )
        
        # === VERIFY CORRUPTED STATE SETUP ===
        
        # Verify the corrupted state exists
        self.assertEqual(Guest.objects.filter(booking=self.booking, room=self.room).count(), 0, 
                        "Old query should find 0 guests (this is the bug!)")
        self.assertEqual(Guest.objects.filter(booking=self.booking).count(), 1,
                        "Should have 1 booking guest")
        self.assertEqual(Guest.objects.filter(room=self.room, booking__isnull=True).count(), 1,
                        "Should have 1 orphaned ghost guest in room")
        self.assertTrue(self.room.is_occupied, "Room should be marked as occupied")
        
        # === ATTEMPT CHECKOUT ===
        
        url = f'/api/staff/hotels/{self.hotel.slug}/room-bookings/{self.booking.booking_id}/check-out/'
        
        response = self.client.post(url)
        
        # === VERIFY CHECKOUT SUCCESS ===
        
        self.assertEqual(response.status_code, status.HTTP_200_OK, 
                        f"Checkout should succeed. Response: {response.data}")
        
        # === VERIFY COMPLETE ROOM CLEANUP ===
        
        # Critical: NO guests should remain in the room
        remaining_guests = Guest.objects.filter(room=self.room)
        self.assertEqual(remaining_guests.count(), 0, 
                        "Room 337 should have ZERO guests after checkout - no more ghosts!")
        
        # Verify booking guest was detached from room (room set to None)
        booking_guest.refresh_from_db()
        self.assertIsNone(booking_guest.room, "Booking guest should have room=None after checkout")
        
        # Verify ghost guest was detached from room (room set to None)  
        ghost_guest.refresh_from_db()
        self.assertIsNone(ghost_guest.room, "Ghost guest should have room=None after checkout")
        
        # === VERIFY BOOKING COMPLETION ===
        
        self.booking.refresh_from_db()
        self.assertIsNotNone(self.booking.checked_out_at, "Booking should have checked_out_at timestamp")
        self.assertEqual(self.booking.status, 'COMPLETED', "Booking should be COMPLETED")
        
        # === VERIFY ROOM STATE ===
        
        self.room.refresh_from_db()
        self.assertFalse(self.room.is_occupied, "Room should not be occupied after checkout")
        self.assertEqual(self.room.room_status, 'CHECKOUT_DIRTY', "Room should be CHECKOUT_DIRTY")
        
        # === VERIFY NOTIFICATIONS ===
        
        mock_booking_notify.assert_called_once()
        mock_room_notify.assert_called_once()

    def test_checkout_normal_case_still_works(self):
        """Verify normal checkout (non-corrupted state) still works correctly."""
        
        # Create normal guest properly linked to both booking and room
        normal_guest = Guest.objects.create(
            hotel=self.hotel,
            first_name="Normal",
            last_name="Guest", 
            booking=self.booking,
            room=self.room,
            guest_type='PRIMARY'
        )
        
        # Execute checkout
        url = f'/api/staff/hotels/{self.hotel.slug}/room-bookings/{self.booking.booking_id}/check-out/'
        response = self.client.post(url)
        
        # Verify success
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify guest detached
        normal_guest.refresh_from_db()
        self.assertIsNone(normal_guest.room)
        
        # Verify no guests in room
        remaining_guests = Guest.objects.filter(room=self.room)
        self.assertEqual(remaining_guests.count(), 0)

    def test_checkout_idempotent_with_ghost_guests(self):
        """Checkout should be idempotent even with ghost guests."""
        
        # Create ghost guest
        ghost_guest = Guest.objects.create(
            hotel=self.hotel,
            first_name="Ghost",
            last_name="Idempotent",
            booking=None,
            room=self.room,
            guest_type='PRIMARY'
        )
        
        # First checkout
        url = f'/api/staff/hotels/{self.hotel.slug}/room-bookings/{self.booking.booking_id}/check-out/'
        response1 = self.client.post(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second checkout (should be idempotent)
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify still no guests in room
        remaining_guests = Guest.objects.filter(room=self.room)
        self.assertEqual(remaining_guests.count(), 0)