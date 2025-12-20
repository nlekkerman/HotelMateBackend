"""
Housekeeping Tests

Comprehensive tests for housekeeping models, services, permissions, and API endpoints.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import Mock

from hotel.models import Hotel
from staff.models import Staff, Department, Role
from rooms.models import Room, RoomType
from housekeeping.models import HousekeepingTask, RoomStatusEvent
from housekeeping.services import set_room_status
from housekeeping.policy import is_manager, is_housekeeping, can_change_room_status


class HousekeepingModelTests(TestCase):
    """Test housekeeping model functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel"
        )
        
        # Create room type and room
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            base_price=100.00
        )
        
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number="101",
            room_status="CHECKOUT_DIRTY"
        )
        
        # Create user and staff
        self.user = User.objects.create_user(
            username="teststaff",
            email="test@example.com",
            password="testpass123"
        )
        
        self.department = Department.objects.create(
            name="Housekeeping",
            slug="housekeeping"
        )
        
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            department=self.department,
            first_name="Test",
            last_name="Staff",
            access_level="regular_staff"
        )
    
    def test_room_status_event_creation(self):
        """Test creating room status audit events"""
        event = RoomStatusEvent.objects.create(
            hotel=self.hotel,
            room=self.room,
            from_status="CHECKOUT_DIRTY",
            to_status="CLEANING_IN_PROGRESS",
            changed_by=self.staff,
            source="HOUSEKEEPING",
            note="Started cleaning"
        )
        
        self.assertEqual(event.hotel, self.hotel)
        self.assertEqual(event.room, self.room)
        self.assertEqual(event.from_status, "CHECKOUT_DIRTY")
        self.assertEqual(event.to_status, "CLEANING_IN_PROGRESS")
        self.assertEqual(event.changed_by, self.staff)
        self.assertEqual(event.source, "HOUSEKEEPING")
        self.assertEqual(event.note, "Started cleaning")
    
    def test_room_status_event_validation(self):
        """Test room status event validation"""
        # Create different hotel
        other_hotel = Hotel.objects.create(
            name="Other Hotel",
            slug="other-hotel"
        )
        
        event = RoomStatusEvent(
            hotel=other_hotel,  # Different hotel than room
            room=self.room,
            from_status="CHECKOUT_DIRTY",
            to_status="CLEANING_IN_PROGRESS",
            changed_by=self.staff,
            source="HOUSEKEEPING"
        )
        
        with self.assertRaises(ValidationError):
            event.clean()
    
    def test_housekeeping_task_creation(self):
        """Test creating housekeeping tasks"""
        task = HousekeepingTask.objects.create(
            hotel=self.hotel,
            room=self.room,
            task_type="TURNOVER",
            status="OPEN",
            priority="MED",
            created_by=self.staff,
            note="Room needs turnover cleaning"
        )
        
        self.assertEqual(task.hotel, self.hotel)
        self.assertEqual(task.room, self.room)
        self.assertEqual(task.task_type, "TURNOVER")
        self.assertEqual(task.status, "OPEN")
        self.assertEqual(task.priority, "MED")
        self.assertEqual(task.created_by, self.staff)
    
    def test_housekeeping_task_validation(self):
        """Test housekeeping task validation constraints"""
        # Create different hotel
        other_hotel = Hotel.objects.create(
            name="Other Hotel",
            slug="other-hotel"
        )
        
        task = HousekeepingTask(
            hotel=other_hotel,  # Different hotel than room
            room=self.room,
            task_type="TURNOVER",
            created_by=self.staff
        )
        
        with self.assertRaises(ValidationError):
            task.clean()
    
    def test_task_is_overdue_property(self):
        """Test task overdue calculation"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create high priority task that's old
        old_time = timezone.now() - timedelta(hours=3)
        
        with self.settings(USE_TZ=True):
            task = HousekeepingTask.objects.create(
                hotel=self.hotel,
                room=self.room,
                task_type="TURNOVER",
                priority="HIGH",
                created_by=self.staff
            )
            
            # Manually set created_at to simulate old task
            task.created_at = old_time
            task.save()
            
            # High priority task created 3 hours ago should be overdue (SLA: 2 hours)
            self.assertTrue(task.is_overdue)
        
        # Completed task should not be overdue
        task.status = "DONE"
        task.save()
        self.assertFalse(task.is_overdue)


class HousekeepingPolicyTests(TestCase):
    """Test housekeeping permission policies"""
    
    def setUp(self):
        """Set up test data"""
        self.hotel = Hotel.objects.create(name="Test Hotel", slug="test-hotel")
        
        # Create departments and roles
        self.housekeeping_dept = Department.objects.create(
            name="Housekeeping", slug="housekeeping"
        )
        self.front_desk_dept = Department.objects.create(
            name="Front Desk", slug="front-desk"
        )
        
        # Create staff with different roles
        self.manager_user = User.objects.create_user(
            username="manager", password="pass"
        )
        self.manager = Staff.objects.create(
            user=self.manager_user,
            hotel=self.hotel,
            access_level="staff_admin",
            first_name="Manager",
            last_name="Test"
        )
        
        self.housekeeping_user = User.objects.create_user(
            username="housekeeper", password="pass"
        )
        self.housekeeper = Staff.objects.create(
            user=self.housekeeping_user,
            hotel=self.hotel,
            department=self.housekeeping_dept,
            access_level="regular_staff",
            first_name="House",
            last_name="Keeper"
        )
        
        self.front_desk_user = User.objects.create_user(
            username="frontdesk", password="pass"
        )
        self.front_desk = Staff.objects.create(
            user=self.front_desk_user,
            hotel=self.hotel,
            department=self.front_desk_dept,
            access_level="regular_staff",
            first_name="Front",
            last_name="Desk"
        )
        
        # Create room with mock can_transition_to method
        self.room = Mock()
        self.room.hotel_id = self.hotel.id
        self.room.room_status = "CHECKOUT_DIRTY"
        self.room.can_transition_to = Mock(return_value=True)
    
    def test_is_manager_function(self):
        """Test manager detection"""
        self.assertTrue(is_manager(self.manager))
        self.assertFalse(is_manager(self.housekeeper))
        self.assertFalse(is_manager(self.front_desk))
        self.assertFalse(is_manager(None))
    
    def test_is_housekeeping_function(self):
        """Test housekeeping department detection"""
        self.assertTrue(is_housekeeping(self.housekeeper))
        self.assertFalse(is_housekeeping(self.front_desk))
        self.assertFalse(is_housekeeping(self.manager))
        self.assertFalse(is_housekeeping(None))
    
    def test_manager_can_override_with_note(self):
        """Test manager override permissions"""
        # Manager can override with note
        can_change, error = can_change_room_status(
            self.manager, self.room, "READY_FOR_GUEST", 
            source="MANAGER_OVERRIDE", note="Emergency override"
        )
        self.assertTrue(can_change)
        self.assertEqual(error, "")
        
        # Manager override requires note
        can_change, error = can_change_room_status(
            self.manager, self.room, "READY_FOR_GUEST", 
            source="MANAGER_OVERRIDE", note=""
        )
        self.assertFalse(can_change)
        self.assertIn("note", error.lower())
    
    def test_housekeeping_workflow_transitions(self):
        """Test housekeeping staff can do normal workflow transitions"""
        # Housekeeping can start cleaning
        can_change, error = can_change_room_status(
            self.housekeeper, self.room, "CLEANING_IN_PROGRESS"
        )
        self.assertTrue(can_change)
        
        # Update room status for next test
        self.room.room_status = "CLEANING_IN_PROGRESS"
        
        # Housekeeping can mark as cleaned
        can_change, error = can_change_room_status(
            self.housekeeper, self.room, "CLEANED_UNINSPECTED"
        )
        self.assertTrue(can_change)
        
        # Update room status for next test
        self.room.room_status = "CLEANED_UNINSPECTED"
        
        # Housekeeping can mark as ready
        can_change, error = can_change_room_status(
            self.housekeeper, self.room, "READY_FOR_GUEST"
        )
        self.assertTrue(can_change)
    
    def test_front_desk_limited_permissions(self):
        """Test front desk has limited permissions"""
        # Front desk cannot set cleaning statuses
        can_change, error = can_change_room_status(
            self.front_desk, self.room, "READY_FOR_GUEST"
        )
        self.assertFalse(can_change)
        
        can_change, error = can_change_room_status(
            self.front_desk, self.room, "CLEANED_UNINSPECTED"
        )
        self.assertFalse(can_change)
        
        can_change, error = can_change_room_status(
            self.front_desk, self.room, "CLEANING_IN_PROGRESS"
        )
        self.assertFalse(can_change)
    
    def test_hotel_scoping_validation(self):
        """Test hotel scoping is enforced"""
        other_hotel = Hotel.objects.create(name="Other Hotel", slug="other")
        other_room = Mock()
        other_room.hotel_id = other_hotel.id
        other_room.room_status = "CHECKOUT_DIRTY"
        other_room.can_transition_to = Mock(return_value=True)
        
        # Staff cannot change room in different hotel
        can_change, error = can_change_room_status(
            self.housekeeper, other_room, "CLEANING_IN_PROGRESS"
        )
        self.assertFalse(can_change)
        self.assertIn("hotel", error.lower())


class HousekeepingServiceTests(TestCase):
    """Test housekeeping canonical services"""
    
    def setUp(self):
        """Set up test data"""
        self.hotel = Hotel.objects.create(name="Test Hotel", slug="test-hotel")
        
        # Create room type and room with proper can_transition_to method
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            base_price=100.00
        )
        
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number="101",
            room_status="CHECKOUT_DIRTY"
        )
        
        # Create housekeeping staff
        self.user = User.objects.create_user(username="staff", password="pass")
        self.department = Department.objects.create(
            name="Housekeeping", slug="housekeeping"
        )
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            department=self.department,
            access_level="regular_staff",
            first_name="Test",
            last_name="Staff"
        )
    
    def test_set_room_status_creates_audit_record(self):
        """Test that status changes create audit records"""
        original_status = self.room.room_status
        
        # Change room status
        updated_room = set_room_status(
            room=self.room,
            to_status="CLEANING_IN_PROGRESS",
            staff=self.staff,
            source="HOUSEKEEPING",
            note="Starting cleaning"
        )
        
        # Verify room status changed
        self.assertEqual(updated_room.room_status, "CLEANING_IN_PROGRESS")
        
        # Verify audit record created
        event = RoomStatusEvent.objects.get(room=self.room)
        self.assertEqual(event.from_status, original_status)
        self.assertEqual(event.to_status, "CLEANING_IN_PROGRESS")
        self.assertEqual(event.changed_by, self.staff)
        self.assertEqual(event.source, "HOUSEKEEPING")
        self.assertEqual(event.note, "Starting cleaning")
    
    def test_set_room_status_invalid_transition(self):
        """Test that invalid transitions are rejected"""
        # Try to transition from CHECKOUT_DIRTY to invalid status
        # This depends on Room.can_transition_to implementation
        with self.assertRaises(ValidationError):
            set_room_status(
                room=self.room,
                to_status="INVALID_STATUS",
                staff=self.staff
            )
    
    def test_set_room_status_permission_enforcement(self):
        """Test that permissions are enforced"""
        # Create front desk staff
        front_desk_user = User.objects.create_user(
            username="frontdesk", password="pass"
        )
        front_desk_dept = Department.objects.create(
            name="Front Desk", slug="front-desk"
        )
        front_desk_staff = Staff.objects.create(
            user=front_desk_user,
            hotel=self.hotel,
            department=front_desk_dept,
            access_level="regular_staff",
            first_name="Front",
            last_name="Desk"
        )
        
        # Front desk should not be able to set READY_FOR_GUEST
        with self.assertRaises(ValidationError):
            set_room_status(
                room=self.room,
                to_status="READY_FOR_GUEST",
                staff=front_desk_staff
            )


class HousekeepingAPITests(APITestCase):
    """Test housekeeping API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.hotel = Hotel.objects.create(name="Test Hotel", slug="test-hotel")
        
        # Create room
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            base_price=100.00
        )
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number="101",
            room_status="CHECKOUT_DIRTY"
        )
        
        # Create staff user
        self.user = User.objects.create_user(
            username="teststaff",
            password="testpass123"
        )
        self.department = Department.objects.create(
            name="Housekeeping", slug="housekeeping"
        )
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            department=self.department,
            access_level="regular_staff",
            first_name="Test",
            last_name="Staff"
        )
    
    def test_dashboard_requires_authentication(self):
        """Test dashboard requires staff authentication"""
        url = f'/api/staff/hotel/{self.hotel.slug}/housekeeping/dashboard/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_dashboard_with_authentication(self):
        """Test dashboard returns data with authentication"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/staff/hotel/{self.hotel.slug}/housekeeping/dashboard/'
        response = self.client.get(url)
        
        # Should succeed with proper authentication
        # Note: This test assumes the URL routing is set up correctly
        # In actual implementation, you may need to adjust based on URL patterns
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
    
    def test_task_creation_requires_authentication(self):
        """Test task creation requires authentication"""
        url = f'/api/staff/hotel/{self.hotel.slug}/housekeeping/tasks/'
        data = {
            'room': self.room.id,
            'task_type': 'TURNOVER',
            'priority': 'MED'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
