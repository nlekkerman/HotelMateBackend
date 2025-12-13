"""
Phase 2 Tests: Booking Assignment Endpoints
Tests for assign-room (check-in) and checkout operations.
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from .models import Hotel, RoomBooking
from rooms.models import Room, RoomType
from guests.models import Guest
from staff.models import Staff, Role, Department


class BookingAssignmentTestCase(TestCase):
    """Test suite for Phase 2 booking assignment functionality."""
    
    def setUp(self):
        """Set up test data for each test."""
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel"
        )
        
        # Create room type
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            code="STD",
            max_occupancy=2
        )
        
        # Create room
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_number=101,
            room_type=self.room_type,
            is_active=True,
            is_out_of_order=False,
            is_occupied=False
        )
        
        # Create confirmed booking
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status="CONFIRMED"
        )
        
        # Create staff user
        self.user = User.objects.create_user(
            username="staff@test.com",
            email="staff@test.com",
            password="testpass123"
        )
        
        # Create role and department
        self.role = Role.objects.create(name="Receptionist", slug="receptionist")
        self.department = Department.objects.create(name="Front Desk", slug="front-desk")
        
        # Create staff profile
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

    @patch('notifications.notification_manager.NotificationManager.realtime_booking_checked_in')
    @patch('notifications.notification_manager.NotificationManager.realtime_room_occupancy_updated')
    def test_assign_room_success(self, mock_room_notify, mock_booking_notify):
        """Test successful room assignment (check-in)."""
        url = reverse('staff-booking-assign-room', kwargs={
            'slug': self.hotel.slug,
            'booking_id': self.booking.booking_id
        })
        
        data = {'room_number': self.room.room_number}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify booking updated
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.assigned_room, self.room)
        self.assertIsNotNone(self.booking.checked_in_at)
        
        # Verify room occupied
        self.room.refresh_from_db()
        self.assertTrue(self.room.is_occupied)
        
        # Verify PRIMARY guest created
        guest = Guest.objects.get(booking=self.booking, guest_type='PRIMARY')
        self.assertEqual(guest.first_name, "John")
        self.assertEqual(guest.last_name, "Doe")
        self.assertEqual(guest.room, self.room)
        
        # Verify notifications called
        mock_booking_notify.assert_called_once()
        mock_room_notify.assert_called_once()

    def test_assign_room_booking_not_confirmed(self):
        """Test assignment fails if booking not confirmed."""
        self.booking.status = 'PENDING_PAYMENT'
        self.booking.save()
        
        url = reverse('staff-booking-assign-room', kwargs={
            'slug': self.hotel.slug,
            'booking_id': self.booking.booking_id
        })
        
        data = {'room_number': self.room.room_number}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("CONFIRMED", str(response.data))

    def test_assign_room_occupied_room(self):
        """Test assignment fails if room already occupied."""
        self.room.is_occupied = True
        self.room.save()
        
        url = reverse('staff-booking-assign-room', kwargs={
            'slug': self.hotel.slug,
            'booking_id': self.booking.booking_id
        })
        
        data = {'room_number': self.room.room_number}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("occupied", str(response.data))

    @patch('notifications.notification_manager.NotificationManager.realtime_booking_checked_out')
    @patch('notifications.notification_manager.NotificationManager.realtime_room_occupancy_updated')
    def test_checkout_success(self, mock_room_notify, mock_booking_notify):
        """Test successful checkout."""
        # First assign room
        self.booking.assigned_room = self.room
        self.booking.checked_in_at = timezone.now()
        self.booking.save()
        
        # Create guest
        guest = Guest.objects.create(
            hotel=self.hotel,
            first_name="John",
            last_name="Doe",
            room=self.room,
            booking=self.booking,
            guest_type='PRIMARY'
        )
        
        self.room.is_occupied = True
        self.room.save()
        
        url = reverse('staff-booking-checkout', kwargs={
            'slug': self.hotel.slug,
            'booking_id': self.booking.booking_id
        })
        
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify booking updated
        self.booking.refresh_from_db()
        self.assertIsNotNone(self.booking.checked_out_at)
        self.assertEqual(self.booking.status, 'COMPLETED')
        
        # Verify room freed
        self.room.refresh_from_db()
        self.assertFalse(self.room.is_occupied)
        
        # Verify guest detached from room
        guest.refresh_from_db()
        self.assertIsNone(guest.room)
        
        # Verify notifications called
        mock_booking_notify.assert_called_once()
        mock_room_notify.assert_called_once()

    def test_idempotent_assign_room(self):
        """Test that assigning same room twice is idempotent."""
        # First assignment
        url = reverse('staff-booking-assign-room', kwargs={
            'slug': self.hotel.slug,
            'booking_id': self.booking.booking_id
        })
        
        data = {'room_number': self.room.room_number}
        
        response1 = self.client.post(url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second assignment (should be idempotent)
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Should still have only one PRIMARY guest
        guests = Guest.objects.filter(booking=self.booking, guest_type='PRIMARY')
        self.assertEqual(guests.count(), 1)

    def test_assign_room_no_room_number(self):
        """Test assignment fails without room_number."""
        url = reverse('staff-booking-assign-room', kwargs={
            'slug': self.hotel.slug,
            'booking_id': self.booking.booking_id
        })
        
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("room_number", str(response.data))