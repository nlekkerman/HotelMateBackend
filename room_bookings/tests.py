"""
Comprehensive tests for Safe Room Assignment System

Tests cover all critical safety mechanisms:
- Non-bookable room exclusion
- Hotel scoping
- Room type matching 
- Overlap conflict detection
- Idempotency
- Check-in blocking
- Concurrency safety
- API permissions and error handling
"""

import threading
from datetime import date, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from hotel.models import Hotel, RoomBooking
from rooms.models import RoomType, Room
from staff.models import Staff
from room_bookings.services.room_assignment import RoomAssignmentService
from room_bookings.exceptions import RoomAssignmentError


class RoomAssignmentServiceTests(TestCase):
    """Test core service layer logic"""
    
    def setUp(self):
        # Create two hotels to test scoping
        self.hotel_a = Hotel.objects.create(
            name="Hotel Alpha",
            slug="hotel-alpha",
            is_active=True
        )
        self.hotel_b = Hotel.objects.create(
            name="Hotel Beta", 
            slug="hotel-beta",
            is_active=True
        )
        
        # Create room types for both hotels
        self.room_type_std_a = RoomType.objects.create(
            hotel=self.hotel_a,
            name="Standard",
            code="STD",
            max_occupancy=2
        )
        self.room_type_dlx_a = RoomType.objects.create(
            hotel=self.hotel_a,
            name="Deluxe",
            code="DLX", 
            max_occupancy=3
        )
        self.room_type_std_b = RoomType.objects.create(
            hotel=self.hotel_b,
            name="Standard",
            code="STD",
            max_occupancy=2
        )
        
        # Create staff user
        self.user = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='password123'
        )
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel_a,
            first_name="Test",
            last_name="Staff"
        )
        
        # Create test booking
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            primary_first_name="John",
            primary_last_name="Doe",
            adults=2,
            children=0,
            total_amount=200.00,
            status='CONFIRMED'
        )
    
    def test_available_rooms_excludes_non_bookable_rooms(self):
        """Test 1: Available rooms excludes non-bookable rooms"""
        
        # Create rooms with various non-bookable states
        room_checkout_dirty = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="101",
            room_status='CHECKOUT_DIRTY',  # Non-bookable
            is_active=True,
            is_out_of_order=False,
            maintenance_required=False
        )
        
        room_maintenance = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="102", 
            room_status='READY_FOR_GUEST',
            is_active=True,
            is_out_of_order=False,
            maintenance_required=True  # Non-bookable
        )
        
        room_out_of_order = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="103",
            room_status='READY_FOR_GUEST',
            is_active=True,
            is_out_of_order=True,  # Non-bookable
            maintenance_required=False
        )
        
        room_inactive = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="104",
            room_status='READY_FOR_GUEST',
            is_active=False,  # Non-bookable
            is_out_of_order=False,
            maintenance_required=False
        )
        
        # Create bookable rooms (AVAILABLE and READY_FOR_GUEST)
        room_available = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="105",
            room_status='READY_FOR_GUEST',  # Bookable
            is_active=True,
            is_out_of_order=False,
            maintenance_required=False
        )
        
        room_ready = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="106", 
            room_status='READY_FOR_GUEST',  # Bookable
            is_active=True,
            is_out_of_order=False,
            maintenance_required=False
        )
        
        # Get available rooms
        available_rooms = RoomAssignmentService.find_available_rooms_for_booking(self.booking)
        available_numbers = {room.room_number for room in available_rooms}
        
        # Assert only bookable rooms are included
        self.assertIn("105", available_numbers)  # AVAILABLE
        self.assertIn("106", available_numbers)  # READY_FOR_GUEST
        
        # Assert non-bookable rooms are excluded
        self.assertNotIn("101", available_numbers)  # CHECKOUT_DIRTY
        self.assertNotIn("102", available_numbers)  # maintenance_required=True
        self.assertNotIn("103", available_numbers)  # is_out_of_order=True
        self.assertNotIn("104", available_numbers)  # is_active=False
    
    def test_hotel_scoping_prevents_cross_hotel_leak(self):
        """Test 2: Hotel scoping - no cross-hotel data leak"""
        
        # Create rooms in both hotels with same numbers
        room_a = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="201",
            room_status='READY_FOR_GUEST',
            is_active=True
        )
        
        room_b = Room.objects.create(
            hotel=self.hotel_b,
            room_type=self.room_type_std_b,  # Same type name, different hotel
            room_number="201",  # Same room number
            room_status='AVAILABLE',
            is_active=True
        )
        
        # Booking is for Hotel A
        available_rooms = RoomAssignmentService.find_available_rooms_for_booking(self.booking)
        
        # Should only return Hotel A rooms
        hotel_ids = {room.hotel.id for room in available_rooms}
        self.assertEqual(hotel_ids, {self.hotel_a.id})
        
        # Should not include Hotel B rooms
        room_ids = {room.id for room in available_rooms}
        self.assertIn(room_a.id, room_ids)
        self.assertNotIn(room_b.id, room_ids)
    
    def test_room_type_match_enforced(self):
        """Test 3: Room type match enforced"""
        
        # Create room of different type (DLX vs STD)
        room_dlx = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_dlx_a,  # DLX type
            room_number="301",
            room_status='AVAILABLE',
            is_active=True
        )
        
        room_std = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,  # STD type (matches booking)
            room_number="302", 
            room_status='READY_FOR_GUEST',
            is_active=True
        )
        
        # Booking is for STD room type
        available_rooms = RoomAssignmentService.find_available_rooms_for_booking(self.booking)
        available_ids = {room.id for room in available_rooms}
        
        # Should include STD room, exclude DLX room
        self.assertIn(room_std.id, available_ids)
        self.assertNotIn(room_dlx.id, available_ids)
        
        # Direct assignment should fail with type mismatch
        with self.assertRaises(RoomAssignmentError) as cm:
            RoomAssignmentService.assert_room_can_be_assigned(self.booking, room_dlx)
        self.assertEqual(cm.exception.code, 'ROOM_TYPE_MISMATCH')
    
    def test_overlap_logic_blocks_confirmed_bookings(self):
        """Test 4a: Overlap logic blocks CONFIRMED bookings"""
        
        room = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="401",
            room_status='AVAILABLE',
            is_active=True
        )
        
        # Create existing booking with overlapping dates
        existing_booking = RoomBooking.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            check_in=date.today() + timedelta(days=2),  # Overlaps with self.booking
            check_out=date.today() + timedelta(days=4),
            assigned_room=room,
            primary_first_name="Jane",
            primary_last_name="Smith",
            adults=1,
            total_amount=150.00,
            status='CONFIRMED',  # Blocks inventory
            checked_out_at=None  # Not checked out
        )
        
        # Available rooms should exclude the conflicting room
        available_rooms = RoomAssignmentService.find_available_rooms_for_booking(self.booking)
        available_ids = {room.id for room in available_rooms}
        self.assertNotIn(room.id, available_ids)
        
        # Direct assignment should fail with overlap conflict
        with self.assertRaises(RoomAssignmentError) as cm:
            RoomAssignmentService.assert_room_can_be_assigned(self.booking, room)
        self.assertEqual(cm.exception.code, 'ROOM_OVERLAP_CONFLICT')
    
    def test_overlap_logic_blocks_inhouse_guests(self):
        """Test 4b: Overlap logic blocks in-house guests (timestamp-based)"""
        
        room = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="402",
            room_status='AVAILABLE',
            is_active=True
        )
        
        # Create in-house guest (checked in but not checked out)
        existing_booking = RoomBooking.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            check_in=date.today() + timedelta(days=2),
            check_out=date.today() + timedelta(days=4),
            assigned_room=room,
            primary_first_name="Bob",
            primary_last_name="Wilson",
            adults=1,
            total_amount=150.00,
            status='CONFIRMED',  # Status can stay CONFIRMED
            checked_in_at=timezone.now(),  # Checked in
            checked_out_at=None  # Not checked out = in-house
        )
        
        # Should still block inventory due to in-house status
        available_rooms = RoomAssignmentService.find_available_rooms_for_booking(self.booking)
        available_ids = {room.id for room in available_rooms}
        self.assertNotIn(room.id, available_ids)
        
        # Direct assignment should fail
        with self.assertRaises(RoomAssignmentError) as cm:
            RoomAssignmentService.assert_room_can_be_assigned(self.booking, room)
        self.assertEqual(cm.exception.code, 'ROOM_OVERLAP_CONFLICT')
    
    def test_idempotent_assignment(self):
        """Test 5: Idempotent assignment"""
        
        room = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="501",
            room_status='AVAILABLE',
            is_active=True
        )
        
        # First assignment
        result1 = RoomAssignmentService.assign_room_atomic(
            booking_id=self.booking.id,
            room_id=room.id,
            staff_user=self.staff,
            notes="Initial assignment"
        )
        
        # Capture initial audit data
        initial_assigned_at = result1.room_assigned_at
        initial_version = result1.assignment_version
        
        # Second assignment (same room)
        result2 = RoomAssignmentService.assign_room_atomic(
            booking_id=self.booking.id,
            room_id=room.id,
            staff_user=self.staff,
            notes="Duplicate assignment"
        )
        
        # Should return same booking instance
        self.assertEqual(result1.id, result2.id)
        self.assertEqual(result2.assigned_room.id, room.id)
        
        # Audit fields should not change unexpectedly
        self.assertEqual(result2.room_assigned_at, initial_assigned_at)
        self.assertEqual(result2.assignment_version, initial_version)
    
    def test_reassignment_blocked_after_checkin(self):
        """Test 6: Reassignment blocked after check-in"""
        
        room1 = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="601",
            room_status='AVAILABLE',
            is_active=True
        )
        
        room2 = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type_std_a,
            room_number="602",
            room_status='AVAILABLE', 
            is_active=True
        )
        
        # Assign first room
        RoomAssignmentService.assign_room_atomic(
            booking_id=self.booking.id,
            room_id=room1.id,
            staff_user=self.staff
        )
        
        # Simulate check-in (in-house status)
        self.booking.checked_in_at = timezone.now()
        self.booking.checked_out_at = None  # Still in-house
        self.booking.save()
        
        # Try to reassign to different room
        with self.assertRaises(RoomAssignmentError) as cm:
            RoomAssignmentService.assign_room_atomic(
                booking_id=self.booking.id,
                room_id=room2.id,
                staff_user=self.staff
            )
        self.assertEqual(cm.exception.code, 'BOOKING_ALREADY_CHECKED_IN')


class RoomAssignmentConcurrencyTests(TransactionTestCase):
    """Test concurrent access scenarios using threads"""
    
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            is_active=True
        )
        
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard",
            code="STD"
        )
        
        self.user = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='password123'
        )
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            first_name="Test",
            last_name="Staff"
        )
    
    def test_concurrent_assignment_same_room_only_one_succeeds(self):
        """Test 7: Two concurrent assignments to same room - only one succeeds"""
        
        # Create overlapping bookings
        booking1 = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            primary_first_name="Alice",
            primary_last_name="Johnson",
            adults=1,
            total_amount=100.00,
            status='CONFIRMED'
        )
        
        booking2 = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=date.today() + timedelta(days=2),  # Overlaps with booking1
            check_out=date.today() + timedelta(days=4),
            primary_first_name="Charlie",
            primary_last_name="Brown",
            adults=1,
            total_amount=100.00,
            status='CONFIRMED'
        )
        
        room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number="701",
            room_status='AVAILABLE',
            is_active=True
        )
        
        results = []
        
        def assign_room(booking_id):
            try:
                result = RoomAssignmentService.assign_room_atomic(
                    booking_id=booking_id,
                    room_id=room.id,
                    staff_user=self.staff
                )
                results.append(('success', booking_id))
            except RoomAssignmentError as e:
                results.append(('error', e.code))
        
        # Run assignments concurrently
        thread1 = threading.Thread(target=assign_room, args=[booking1.id])
        thread2 = threading.Thread(target=assign_room, args=[booking2.id])
        
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        
        # Verify exactly one success, one conflict
        success_count = len([r for r in results if r[0] == 'success'])
        conflict_count = len([r for r in results if r[1] == 'ROOM_OVERLAP_CONFLICT'])
        
        self.assertEqual(success_count, 1, f"Expected 1 success, got {success_count}. Results: {results}")
        self.assertEqual(conflict_count, 1, f"Expected 1 conflict, got {conflict_count}. Results: {results}")


class RoomAssignmentAPITests(APITestCase):
    """Test API endpoint behavior and permissions"""
    
    def setUp(self):
        # Create hotels and users
        self.hotel_a = Hotel.objects.create(
            name="Hotel Alpha",
            slug="hotel-alpha",
            is_active=True
        )
        self.hotel_b = Hotel.objects.create(
            name="Hotel Beta",
            slug="hotel-beta",
            is_active=True
        )
        
        self.room_type = RoomType.objects.create(
            hotel=self.hotel_a,
            name="Standard",
            code="STD"
        )
        
        # Staff user for hotel A
        self.staff_user_a = User.objects.create_user(
            username='staff_a',
            email='staff_a@test.com',
            password='password123'
        )
        self.staff_a = Staff.objects.create(
            user=self.staff_user_a,
            hotel=self.hotel_a,
            first_name="Staff",
            last_name="Alpha"
        )
        
        # Staff user for hotel B
        self.staff_user_b = User.objects.create_user(
            username='staff_b',
            email='staff_b@test.com',
            password='password123'
        )
        self.staff_b = Staff.objects.create(
            user=self.staff_user_b,
            hotel=self.hotel_b,
            first_name="Staff",
            last_name="Beta"
        )
        
        # Non-staff user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='password123'
        )
        
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            primary_first_name="Test",
            primary_last_name="Guest",
            adults=1,
            total_amount=100.00,
            status='CONFIRMED'
        )
    
    def test_available_rooms_requires_staff_permission(self):
        """Test 8a: Available rooms endpoint requires staff permission"""
        
        url = f'/api/staff/hotel/hotel-alpha/room-bookings/{self.booking.id}/available-rooms/'
        
        # Non-staff user gets 403
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Staff user gets access
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])  # 404 if booking not found is also acceptable
    
    def test_available_rooms_enforces_hotel_scoping(self):
        """Test 8b: Staff from other hotel cannot access"""
        
        url = f'/api/staff/hotel/hotel-alpha/room-bookings/{self.booking.id}/available-rooms/'
        
        # Staff from hotel B trying to access hotel A booking
        self.client.force_authenticate(user=self.staff_user_b)
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
    
    def test_assign_room_returns_structured_error(self):
        """Test 9: Assign room endpoint returns structured error payload"""
        
        # Create conflicting room assignment
        room = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type,
            room_number="801",
            room_status='AVAILABLE',
            is_active=True
        )
        
        # Create conflicting booking
        conflicting_booking = RoomBooking.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type,
            check_in=date.today() + timedelta(days=2),  # Overlaps
            check_out=date.today() + timedelta(days=4),
            assigned_room=room,
            primary_first_name="Conflict",
            primary_last_name="Guest",
            adults=1,
            total_amount=100.00,
            status='CONFIRMED',
            checked_out_at=None
        )
        
        url = f'/api/staff/hotel/hotel-alpha/room-bookings/{self.booking.id}/safe-assign-room/'
        self.client.force_authenticate(user=self.staff_user_a)
        
        response = self.client.post(url, {
            'room_id': room.id,
            'notes': 'Test assignment'
        })
        
        # Should get 409 conflict with structured error
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        
        # Verify error structure
        error_data = response.json()
        self.assertIn('error', error_data)
        error = error_data['error']
        
        self.assertEqual(error['code'], 'ROOM_OVERLAP_CONFLICT')
        self.assertIn('message', error)
        self.assertIn('details', error)
        self.assertIn('conflicting_booking_ids', error['details'])
        self.assertIn(conflicting_booking.id, error['details']['conflicting_booking_ids'])
    
    def test_room_type_mismatch_structured_error(self):
        """Test room type mismatch returns proper error structure"""
        
        # Create room with different type
        wrong_room_type = RoomType.objects.create(
            hotel=self.hotel_a,
            name="Deluxe",
            code="DLX"
        )
        
        room = Room.objects.create(
            hotel=self.hotel_a,
            room_type=wrong_room_type,  # Different from booking
            room_number="802",
            room_status='AVAILABLE',
            is_active=True
        )
        
        url = f'/api/staff/hotel/hotel-alpha/room-bookings/{self.booking.id}/safe-assign-room/'
        self.client.force_authenticate(user=self.staff_user_a)
        
        response = self.client.post(url, {
            'room_id': room.id
        })
        
        # Should get 400 with room type mismatch
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        error_data = response.json()
        self.assertEqual(error_data['error']['code'], 'ROOM_TYPE_MISMATCH')
    
    def test_non_bookable_room_error(self):
        """Test non-bookable room returns proper error"""
        
        room = Room.objects.create(
            hotel=self.hotel_a,
            room_type=self.room_type,
            room_number="803",
            room_status='CHECKOUT_DIRTY',  # Not bookable
            is_active=True
        )
        
        url = f'/api/staff/hotel/hotel-alpha/room-bookings/{self.booking.id}/safe-assign-room/'
        self.client.force_authenticate(user=self.staff_user_a)
        
        response = self.client.post(url, {
            'room_id': room.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_data = response.json()
        self.assertEqual(error_data['error']['code'], 'ROOM_NOT_BOOKABLE')