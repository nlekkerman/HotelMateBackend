"""
Phase 3 Booking Party Management Tests

Comprehensive test suite for BookingGuest model, party management endpoints,
assign-room party conversion, and related functionality.
"""

import json
from datetime import date, timedelta
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from hotel.models import Hotel, RoomBooking, BookingGuest
from rooms.models import Room, RoomType  
from guests.models import Guest
from staff.models import Staff


class BookingGuestModelTest(TestCase):
    """Test BookingGuest model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            address="123 Test St",
            phone="+1234567890",
            email="test@hotel.com"
        )
        
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Deluxe Room",
            code="DLX",
            max_occupancy=4,
            base_price=100.00
        )
        
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            primary_phone="+1234567890",
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            adults=2,
            children=1,
            total_amount=300.00
        )
    
    def test_booking_guest_creation(self):
        """Test creating BookingGuest instances"""
        # Create PRIMARY guest
        primary_guest = BookingGuest.objects.create(
            booking=self.booking,
            role='PRIMARY',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='+1234567890',
            is_staying=True
        )
        
        # Create COMPANION guest
        companion_guest = BookingGuest.objects.create(
            booking=self.booking,
            role='COMPANION',
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com',
            is_staying=True
        )
        
        # Verify creation
        self.assertEqual(primary_guest.role, 'PRIMARY')
        self.assertEqual(companion_guest.role, 'COMPANION')
        self.assertEqual(primary_guest.full_name, 'John Doe')
        self.assertEqual(companion_guest.full_name, 'Jane Doe')
        
        # Verify booking relationship
        self.assertEqual(self.booking.party_members.count(), 2)
        self.assertTrue(
            self.booking.party_members.filter(role='PRIMARY').exists()
        )
        self.assertTrue(
            self.booking.party_members.filter(role='COMPANION').exists()
        )
    
    def test_unique_primary_constraint(self):
        """Test that only one PRIMARY guest is allowed per booking"""
        # Create first PRIMARY guest
        BookingGuest.objects.create(
            booking=self.booking,
            role='PRIMARY',
            first_name='John',
            last_name='Doe',
            is_staying=True
        )
        
        # Try to create second PRIMARY guest - should fail
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            BookingGuest.objects.create(
                booking=self.booking,
                role='PRIMARY',
                first_name='Jane',
                last_name='Smith',
                is_staying=True
            )
    
    def test_multiple_companions_allowed(self):
        """Test that multiple COMPANIONs are allowed"""
        # Create PRIMARY guest
        BookingGuest.objects.create(
            booking=self.booking,
            role='PRIMARY',
            first_name='John',
            last_name='Doe',
            is_staying=True
        )
        
        # Create multiple COMPANIONs
        BookingGuest.objects.create(
            booking=self.booking,
            role='COMPANION',
            first_name='Jane',
            last_name='Doe',
            is_staying=True
        )
        
        BookingGuest.objects.create(
            booking=self.booking,
            role='COMPANION',
            first_name='Kid',
            last_name='Doe',
            is_staying=True
        )
        
        # Verify all created successfully
        self.assertEqual(self.booking.party_members.count(), 3)
        self.assertEqual(
            self.booking.party_members.filter(role='COMPANION').count(), 2
        )


class BookingPartySyncTest(TestCase):
    """Test RoomBooking primary field sync with BookingGuest"""
    
    def setUp(self):
        """Set up test data"""
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            address="123 Test St",
            phone="+1234567890",
            email="test@hotel.com"
        )
        
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Deluxe Room",
            code="DLX",
            max_occupancy=4,
            base_price=100.00
        )
    
    def test_sync_on_booking_save(self):
        """Test that PRIMARY BookingGuest is synced when booking is saved"""
        booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            primary_phone="+1234567890",
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            adults=2,
            children=0,
            total_amount=200.00
        )
        
        # Verify PRIMARY BookingGuest was auto-created
        primary_guest = booking.party_members.filter(role='PRIMARY').first()
        self.assertIsNotNone(primary_guest)
        self.assertEqual(primary_guest.first_name, "John")
        self.assertEqual(primary_guest.last_name, "Doe")
        self.assertEqual(primary_guest.email, "john@example.com")
        self.assertEqual(primary_guest.phone, "+1234567890")
    
    def test_sync_on_booking_update(self):
        """Test that PRIMARY BookingGuest is updated when booking changes"""
        booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            adults=1,
            children=0,
            total_amount=100.00
        )
        
        # Update booking primary fields
        booking.primary_first_name = "Jane"
        booking.primary_last_name = "Smith"
        booking.primary_email = "jane@example.com"
        booking.save()
        
        # Verify PRIMARY BookingGuest was updated
        primary_guest = booking.party_members.filter(role='PRIMARY').first()
        self.assertEqual(primary_guest.first_name, "Jane")
        self.assertEqual(primary_guest.last_name, "Smith")
        self.assertEqual(primary_guest.email, "jane@example.com")


class PublicBookingPartyAPITest(TestCase):
    """Test public booking API with party support"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            address="123 Test St",
            phone="+1234567890",
            email="test@hotel.com"
        )
        
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Deluxe Room",
            code="DLX",
            max_occupancy=4,
            base_price=100.00
        )
    
    def test_booking_without_party(self):
        """Test booking creation without party list (backward compatibility)"""
        booking_data = {
            "room_type_id": self.room_type.id,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=3)),
            "adults": 2,
            "children": 0,
            "guest_first_name": "John",
            "guest_last_name": "Doe",
            "guest_email": "john@example.com",
            "guest_phone": "+1234567890"
        }
        
        response = self.client.post(
            f'/api/guest/hotels/{self.hotel.slug}/bookings/',
            booking_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify booking created with auto-synced PRIMARY guest
        booking = RoomBooking.objects.get(
            booking_id=response.data['booking_id']
        )
        primary_guest = booking.party_members.filter(role='PRIMARY').first()
        self.assertIsNotNone(primary_guest)
        self.assertEqual(primary_guest.first_name, "John")
        self.assertEqual(primary_guest.last_name, "Doe")
    
    def test_booking_with_party(self):
        """Test booking creation with party list"""
        booking_data = {
            "room_type_id": self.room_type.id,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=3)),
            "adults": 3,
            "children": 1,
            "guest_first_name": "John",
            "guest_last_name": "Doe",
            "guest_email": "john@example.com",
            "guest_phone": "+1234567890",
            "party": [
                {
                    "role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890"
                },
                {
                    "role": "COMPANION",
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "jane@example.com"
                },
                {
                    "role": "COMPANION",
                    "first_name": "Junior",
                    "last_name": "Doe"
                },
                {
                    "role": "COMPANION",
                    "first_name": "Kid",
                    "last_name": "Doe"
                }
            ]
        }
        
        response = self.client.post(
            f'/api/guest/hotels/{self.hotel.slug}/bookings/',
            booking_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify booking and party created
        booking = RoomBooking.objects.get(
            booking_id=response.data['booking_id']
        )
        self.assertEqual(booking.party_members.count(), 4)
        self.assertEqual(
            booking.party_members.filter(role='PRIMARY').count(), 1
        )
        self.assertEqual(
            booking.party_members.filter(role='COMPANION').count(), 3
        )
        
        # Verify auto-normalization (booking fields updated to match PRIMARY)
        primary_guest = booking.party_members.filter(role='PRIMARY').first()
        self.assertEqual(booking.primary_first_name, primary_guest.first_name)
        self.assertEqual(booking.primary_last_name, primary_guest.last_name)
        self.assertEqual(booking.primary_email, primary_guest.email)
    
    def test_booking_party_validation(self):
        """Test party validation rules"""
        # Test multiple PRIMARY guests
        booking_data = {
            "room_type_id": self.room_type.id,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=3)),
            "adults": 2,
            "children": 0,
            "guest_first_name": "John",
            "guest_last_name": "Doe",
            "guest_email": "john@example.com",
            "party": [
                {
                    "role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe"
                },
                {
                    "role": "PRIMARY",
                    "first_name": "Jane",
                    "last_name": "Doe"
                }
            ]
        }
        
        response = self.client.post(
            f'/api/guest/hotels/{self.hotel.slug}/bookings/',
            booking_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("exactly one PRIMARY", response.data['detail'])


class StaffPartyManagementAPITest(TestCase):
    """Test staff party management endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create user and staff
        self.user = User.objects.create_user(
            username='staff',
            password='testpass'
        )
        self.staff = Staff.objects.create(
            user=self.user,
            first_name="Staff",
            last_name="Member",
            role="manager"
        )
        
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            address="123 Test St",
            phone="+1234567890",
            email="test@hotel.com"
        )
        
        # Add staff to hotel
        self.hotel.staff.add(self.staff)
        
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Deluxe Room",
            code="DLX",
            max_occupancy=4,
            base_price=100.00
        )
        
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            adults=2,
            children=0,
            total_amount=200.00
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_get_party_list(self):
        """Test retrieving party list"""
        # Add some companions
        BookingGuest.objects.create(
            booking=self.booking,
            role='COMPANION',
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com',
            is_staying=True
        )
        
        response = self.client.get(
            f'/api/staff/hotels/{self.hotel.slug}/bookings/{self.booking.booking_id}/party/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Verify response structure
        self.assertIn('booking_id', data)
        self.assertIn('primary', data)
        self.assertIn('companions', data)
        self.assertIn('total_party_size', data)
        
        # Verify data
        self.assertEqual(data['booking_id'], self.booking.booking_id)
        self.assertIsNotNone(data['primary'])
        self.assertEqual(len(data['companions']), 1)
        self.assertEqual(data['total_party_size'], 2)
        
        # Verify primary guest data
        self.assertEqual(data['primary']['first_name'], 'John')
        self.assertEqual(data['primary']['last_name'], 'Doe')
        self.assertEqual(data['primary']['role'], 'PRIMARY')
    
    @patch('notifications.notification_manager.NotificationManager.realtime_booking_party_updated')
    def test_update_companions(self, mock_notification):
        """Test updating companions list"""
        companions_data = {
            "companions": [
                {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "jane@example.com"
                },
                {
                    "first_name": "Junior",
                    "last_name": "Doe"
                }
            ]
        }
        
        response = self.client.put(
            f'/api/staff/hotels/{self.hotel.slug}/bookings/{self.booking.booking_id}/party/companions/',
            companions_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify companions were created
        self.assertEqual(
            self.booking.party_members.filter(role='COMPANION').count(), 2
        )
        
        # Verify notification was sent
        mock_notification.assert_called_once()
        
        # Verify response includes updated party
        self.assertEqual(len(response.data['companions']), 2)
    
    def test_prevent_party_edit_after_checkin(self):
        """Test that party cannot be edited after check-in"""
        # Simulate check-in
        from django.utils import timezone
        self.booking.checked_in_at = timezone.now()
        self.booking.save()
        
        companions_data = {
            "companions": [
                {
                    "first_name": "Jane",
                    "last_name": "Doe"
                }
            ]
        }
        
        response = self.client.put(
            f'/api/staff/hotels/{self.hotel.slug}/bookings/{self.booking.booking_id}/party/companions/',
            companions_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot modify party after check-in", response.data['error'])


class AssignRoomPartyConversionTest(TestCase):
    """Test assign-room endpoint with party conversion"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create user and staff
        self.user = User.objects.create_user(
            username='staff',
            password='testpass'
        )
        self.staff = Staff.objects.create(
            user=self.user,
            first_name="Staff",
            last_name="Member",
            role="manager"
        )
        
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            address="123 Test St",
            phone="+1234567890",
            email="test@hotel.com"
        )
        
        # Add staff to hotel
        self.hotel.staff.add(self.staff)
        
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Deluxe Room",
            code="DLX",
            max_occupancy=4,
            base_price=100.00
        )
        
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number=101,
            is_active=True
        )
        
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            adults=3,
            children=0,
            total_amount=300.00,
            status='CONFIRMED'
        )
        
        # Add party members
        BookingGuest.objects.create(
            booking=self.booking,
            role='COMPANION',
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com',
            is_staying=True
        )
        
        BookingGuest.objects.create(
            booking=self.booking,
            role='COMPANION',
            first_name='Junior',
            last_name='Doe',
            is_staying=True
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    @patch('notifications.notification_manager.NotificationManager.realtime_booking_checked_in')
    @patch('notifications.notification_manager.NotificationManager.realtime_room_occupancy_updated')
    def test_assign_room_converts_full_party(self, mock_room_notify, mock_booking_notify):
        """Test that assign-room converts entire party to Guests"""
        assign_data = {"room_number": 101}
        
        response = self.client.post(
            f'/api/staff/hotels/{self.hotel.slug}/bookings/{self.booking.booking_id}/assign-room/',
            assign_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all party members were converted to Guests
        guests = Guest.objects.filter(booking=self.booking)
        self.assertEqual(guests.count(), 3)  # PRIMARY + 2 COMPANIONs
        
        # Verify primary guest
        primary_guest = guests.filter(guest_type='PRIMARY').first()
        self.assertIsNotNone(primary_guest)
        self.assertEqual(primary_guest.first_name, 'John')
        self.assertEqual(primary_guest.room, self.room)
        self.assertIsNone(primary_guest.primary_guest)
        
        # Verify companions
        companions = guests.filter(guest_type='COMPANION')
        self.assertEqual(companions.count(), 2)
        
        for companion in companions:
            self.assertEqual(companion.room, self.room)
            self.assertEqual(companion.primary_guest, primary_guest)
            self.assertIn(companion.first_name, ['Jane', 'Junior'])
        
        # Verify idempotency - each Guest has booking_guest FK
        for guest in guests:
            self.assertIsNotNone(guest.booking_guest)
            self.assertEqual(guest.booking_guest.booking, self.booking)
        
        # Verify notifications were called with party data
        mock_booking_notify.assert_called_once()
        call_args = mock_booking_notify.call_args[0]
        self.assertEqual(len(call_args), 4)  # booking, room, primary_guest, party_guests
        self.assertEqual(len(call_args[3]), 3)  # All party members
        
        # Verify response includes party data
        self.assertIn('party', response.data)
        party_data = response.data['party']
        self.assertIsNotNone(party_data['primary'])
        self.assertEqual(len(party_data['companions']), 2)
    
    def test_idempotent_assign_room(self):
        """Test that repeated assign-room calls are idempotent"""
        assign_data = {"room_number": 101}
        
        # First assign
        response1 = self.client.post(
            f'/api/staff/hotels/{self.hotel.slug}/bookings/{self.booking.booking_id}/assign-room/',
            assign_data,
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Get initial guests
        initial_guests = list(Guest.objects.filter(booking=self.booking))
        initial_count = len(initial_guests)
        
        # Second assign (should be idempotent)
        response2 = self.client.post(
            f'/api/staff/hotels/{self.hotel.slug}/bookings/{self.booking.booking_id}/assign-room/',
            assign_data,
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify no new guests created
        final_guests = Guest.objects.filter(booking=self.booking)
        self.assertEqual(final_guests.count(), initial_count)
        
        # Verify existing guests were updated, not duplicated
        for guest in final_guests:
            self.assertEqual(guest.room, self.room)


class BookingSerializerPartyTest(TestCase):
    """Test serializer party data output"""
    
    def setUp(self):
        """Set up test data"""
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            address="123 Test St",
            phone="+1234567890",
            email="test@hotel.com"
        )
        
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Deluxe Room",
            code="DLX",
            max_occupancy=4,
            base_price=100.00
        )
        
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            adults=2,
            children=0,
            total_amount=200.00
        )
        
        # Add companion
        BookingGuest.objects.create(
            booking=self.booking,
            role='COMPANION',
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com',
            is_staying=True
        )
    
    def test_booking_detail_serializer_party_data(self):
        """Test RoomBookingDetailSerializer includes party data"""
        from hotel.booking_serializers import RoomBookingDetailSerializer
        
        serializer = RoomBookingDetailSerializer(self.booking)
        data = serializer.data
        
        # Verify party field exists
        self.assertIn('party', data)
        party_data = data['party']
        
        # Verify structure
        self.assertIn('primary', party_data)
        self.assertIn('companions', party_data)
        self.assertIn('total_party_size', party_data)
        
        # Verify data
        self.assertIsNotNone(party_data['primary'])
        self.assertEqual(len(party_data['companions']), 1)
        self.assertEqual(party_data['total_party_size'], 2)
        
        # Verify primary data
        primary = party_data['primary']
        self.assertEqual(primary['first_name'], 'John')
        self.assertEqual(primary['last_name'], 'Doe')
        self.assertEqual(primary['role'], 'PRIMARY')
        
        # Verify companion data
        companion = party_data['companions'][0]
        self.assertEqual(companion['first_name'], 'Jane')
        self.assertEqual(companion['last_name'], 'Doe')
        self.assertEqual(companion['role'], 'COMPANION')
    
    def test_booking_guest_serializer(self):
        """Test BookingGuestSerializer output"""
        from hotel.booking_serializers import BookingGuestSerializer
        
        primary_guest = self.booking.party_members.filter(role='PRIMARY').first()
        serializer = BookingGuestSerializer(primary_guest)
        data = serializer.data
        
        # Verify fields
        expected_fields = [
            'id', 'role', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'is_staying', 'created_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Verify data
        self.assertEqual(data['role'], 'PRIMARY')
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['full_name'], 'John Doe')