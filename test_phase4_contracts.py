#!/usr/bin/env python
"""
Phase 4 API Contract Stability Tests

Validates that canonical serializers produce stable output shapes
and that hotel scoping is consistently enforced across all endpoints.
"""

import json
from datetime import date, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.test import APIClient
from hotel.models import (
    Hotel, Room, RoomType, RoomBooking, 
    BookingGuest, Guest, Section, MenuItem
)
from notifications.notification_manager import NotificationManager

User = get_user_model()

class Phase4ContractStabilityTests(TestCase):
    """Test suite ensuring API contract stability for Phase 4"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for hotel with bookings"""
        # Create test hotels
        cls.hotel1 = Hotel.objects.create(
            name="Test Hotel 1",
            slug="test-hotel-1", 
            address="123 Test St",
            phone="555-0001"
        )
        cls.hotel2 = Hotel.objects.create(
            name="Test Hotel 2", 
            slug="test-hotel-2",
            address="456 Test Ave", 
            phone="555-0002"
        )
        
        # Create room types and rooms for hotel1
        cls.single_type = RoomType.objects.create(
            name="Single",
            max_occupancy=2,
            hotel=cls.hotel1
        )
        cls.suite_type = RoomType.objects.create(
            name="Suite", 
            max_occupancy=4,
            hotel=cls.hotel1
        )
        
        cls.room_101 = Room.objects.create(
            room_number="101",
            room_type=cls.single_type,
            hotel=cls.hotel1,
            floor=1
        )
        cls.room_201 = Room.objects.create(
            room_number="201", 
            room_type=cls.suite_type,
            hotel=cls.hotel1,
            floor=2
        )
        
        # Create staff user
        cls.staff_user = User.objects.create_user(
            username="staff1",
            email="staff@hotel.com", 
            password="testpass",
            is_staff=True
        )
        cls.staff_user.hotels.add(cls.hotel1)
        
        # Create guests
        cls.primary_guest = Guest.objects.create(
            first_name="John",
            last_name="Doe", 
            email="john@example.com",
            phone="555-1001",
            id_pin="1234",
            guest_type="PRIMARY",
            hotel=cls.hotel1
        )
        cls.companion_guest = Guest.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com", 
            phone="555-1002",
            id_pin="5678",
            guest_type="COMPANION",
            hotel=cls.hotel1
        )
        
        # Create booking with party
        cls.booking = RoomBooking.objects.create(
            booking_id="BK001",
            confirmation_number="CONF001",
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3), 
            status="confirmed",
            assigned_room=cls.room_101,
            hotel=cls.hotel1
        )
        
        # Add guests to booking
        cls.primary_booking_guest = BookingGuest.objects.create(
            booking=cls.booking,
            guest=cls.primary_guest,
            first_name=cls.primary_guest.first_name,
            last_name=cls.primary_guest.last_name,
            role="PRIMARY"
        )
        cls.companion_booking_guest = BookingGuest.objects.create(
            booking=cls.booking,
            guest=cls.companion_guest, 
            first_name=cls.companion_guest.first_name,
            last_name=cls.companion_guest.last_name,
            role="COMPANION"
        )
        
        # Create second booking for testing party management
        cls.booking2 = RoomBooking.objects.create(
            booking_id="BK002",
            confirmation_number="CONF002", 
            check_in=date.today() + timedelta(days=2),
            check_out=date.today() + timedelta(days=4),
            status="pending",
            hotel=cls.hotel1
        )
    
    def setUp(self):
        """Set up API client for each test"""
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff_user)
    
    def test_staff_booking_list_contract_stability(self):
        """Test that staff booking list returns stable contract shape"""
        response = self.client.get(f'/api/staff/hotels/{self.hotel1.slug}/bookings/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Validate response structure
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)
        
        if data['results']:
            booking_item = data['results'][0]
            
            # Required fields from StaffRoomBookingListSerializer
            required_fields = [
                'booking_id', 'confirmation_number', 'check_in', 'check_out',
                'status', 'nights', 'assigned_room_number', 'room_type_name',
                'primary_guest_name', 'total_guests', 'has_unread_notifications'
            ]
            
            for field in required_fields:
                self.assertIn(field, booking_item, f"Missing required field: {field}")
            
            # Validate field types
            self.assertIsInstance(booking_item['booking_id'], str)
            self.assertIsInstance(booking_item['nights'], int)
            self.assertIsInstance(booking_item['total_guests'], int)
            self.assertIsInstance(booking_item['has_unread_notifications'], bool)
    
    def test_staff_booking_detail_contract_stability(self):
        """Test that staff booking detail returns stable contract shape"""
        response = self.client.get(f'/api/staff/hotels/{self.hotel1.slug}/bookings/{self.booking.booking_id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Required fields from StaffRoomBookingDetailSerializer
        required_fields = [
            'booking_id', 'confirmation_number', 'check_in', 'check_out',
            'status', 'nights', 'assigned_room_number', 'room_type_name', 
            'room_type_id', 'party', 'can_checkin', 'can_checkout', 
            'can_modify_party', 'is_within_checkin_window',
            'unread_notifications_count', 'has_unread_notifications'
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        # Validate party structure (from BookingPartyGroupedSerializer)
        party = data['party']
        self.assertIn('primary', party)
        self.assertIn('companions', party) 
        self.assertIn('total_count', party)
        self.assertIsInstance(party['companions'], list)
        self.assertIsInstance(party['total_count'], int)
        
        if party['primary']:
            primary = party['primary']
            primary_fields = ['id', 'first_name', 'last_name', 'role']
            for field in primary_fields:
                self.assertIn(field, primary)
    
    def test_booking_party_contract_stability(self):
        """Test that booking party endpoint returns stable contract shape"""
        response = self.client.get(f'/api/staff/hotels/{self.hotel1.slug}/bookings/{self.booking.booking_id}/party/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should match BookingPartyGroupedSerializer output
        required_fields = ['primary', 'companions', 'total_count']
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        self.assertIsInstance(data['companions'], list)
        self.assertIsInstance(data['total_count'], int)
        
        # Validate member structure
        if data['primary']:
            member = data['primary']
            member_fields = ['id', 'first_name', 'last_name', 'role']
            for field in member_fields:
                self.assertIn(field, member)
    
    def test_inhouse_guests_contract_stability(self):
        """Test that in-house guests endpoint returns stable contract shape"""
        # Check in the booking first
        self.booking.status = 'checked_in'
        self.booking.save()
        
        response = self.client.get(f'/api/staff/hotels/{self.hotel1.slug}/guests/inhouse/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should match InHouseGuestsGroupedSerializer output  
        required_fields = ['primary_guests', 'companions', 'walkins', 'total_count']
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        for group in [data['primary_guests'], data['companions'], data['walkins']]:
            self.assertIsInstance(group, list)
        
        self.assertIsInstance(data['total_count'], int)
    
    def test_hotel_scoping_enforcement(self):
        """Test that all endpoints properly enforce hotel scoping"""
        # Test accessing hotel1 data with hotel2 slug should fail
        endpoints = [
            f'/api/staff/hotels/{self.hotel2.slug}/bookings/',
            f'/api/staff/hotels/{self.hotel2.slug}/bookings/{self.booking.booking_id}/',
            f'/api/staff/hotels/{self.hotel2.slug}/guests/inhouse/',
        ]
        
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                # Should return empty results or 404, not data from hotel1
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data:
                        self.assertEqual(len(data['results']), 0)
                    elif isinstance(data, list):
                        self.assertEqual(len(data), 0)
                else:
                    self.assertIn(response.status_code, [404, 403])
    
    def test_capacity_validation_contract(self):
        """Test that capacity validation returns consistent error structure"""
        # Try to assign a party of 3 to a room with max occupancy 2
        add_guest_data = {
            'first_name': 'Extra',
            'last_name': 'Guest', 
            'role': 'COMPANION'
        }
        
        # Add third guest to booking
        extra_guest = Guest.objects.create(
            first_name="Extra",
            last_name="Guest",
            email="extra@example.com",
            guest_type="COMPANION", 
            hotel=self.hotel1
        )
        BookingGuest.objects.create(
            booking=self.booking,
            guest=extra_guest,
            first_name="Extra", 
            last_name="Guest",
            role="COMPANION"
        )
        
        # Try to assign to room with capacity 2 - should fail
        response = self.client.post(
            f'/api/staff/hotels/{self.hotel1.slug}/bookings/{self.booking.booking_id}/assign-room/',
            {'room_id': self.room_101.id}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        # Validate error structure
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'capacity_exceeded')
        self.assertIn('message', data['error'])
        self.assertIn('details', data['error'])
        
        # Validate details structure
        details = data['error']['details']
        required_detail_fields = ['party_size', 'room_capacity', 'room_number']
        for field in required_detail_fields:
            self.assertIn(field, details)
    
    def test_error_message_consistency(self):
        """Test that error messages follow consistent format across endpoints"""
        # Test 404 for non-existent booking
        response = self.client.get(f'/api/staff/hotels/{self.hotel1.slug}/bookings/INVALID/')
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        
        # Should have consistent error structure
        self.assertIn('error', data)
        error = data['error']
        self.assertIn('code', error)
        self.assertIn('message', error)
        
        # Test 400 for invalid room assignment  
        response = self.client.post(
            f'/api/staff/hotels/{self.hotel1.slug}/bookings/{self.booking.booking_id}/assign-room/',
            {'room_id': 99999}  # Non-existent room
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertIn('error', data)
        error = data['error']
        self.assertIn('code', error)
        self.assertIn('message', error)


class Phase4NotificationContractTests(TransactionTestCase):
    """Test notification payload contracts"""
    
    def setUp(self):
        """Set up test data"""
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            address="123 Test St"
        )
        
        self.room_type = RoomType.objects.create(
            name="Single",
            max_occupancy=2,
            hotel=self.hotel
        )
        
        self.room = Room.objects.create(
            room_number="101",
            room_type=self.room_type,
            hotel=self.hotel
        )
        
        self.primary_guest = Guest.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            guest_type="PRIMARY",
            hotel=self.hotel
        )
        
        self.booking = RoomBooking.objects.create(
            booking_id="BK001",
            confirmation_number="CONF001",
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            status="confirmed",
            assigned_room=self.room,
            hotel=self.hotel
        )
        
        BookingGuest.objects.create(
            booking=self.booking,
            guest=self.primary_guest,
            first_name=self.primary_guest.first_name,
            last_name=self.primary_guest.last_name,
            role="PRIMARY"
        )
        
        self.notification_manager = NotificationManager()
    
    def test_booking_party_updated_payload_contract(self):
        """Test that booking party updated notification has stable payload"""
        with transaction.atomic():
            # Mock pusher to capture payload
            original_trigger = self.notification_manager._safe_pusher_trigger
            captured_payload = None
            
            def mock_trigger(channel, event, data):
                nonlocal captured_payload
                captured_payload = data
                return True
                
            self.notification_manager._safe_pusher_trigger = mock_trigger
            
            # Trigger notification
            self.notification_manager.realtime_booking_party_updated(self.booking)
            
            # Restore original method
            self.notification_manager._safe_pusher_trigger = original_trigger
            
            # Validate payload structure
            self.assertIsNotNone(captured_payload)
            
            payload = captured_payload.get('payload', {})
            
            # Should have booking details
            self.assertIn('booking_id', payload)
            self.assertIn('status', payload) 
            self.assertIn('assigned_room_number', payload)
            
            # Should have party structure 
            self.assertIn('primary', payload)
            self.assertIn('companions', payload)
            self.assertIn('total_count', payload)
    
    def test_booking_checked_in_payload_contract(self):
        """Test that booking checked-in notification has complete booking data"""
        with transaction.atomic():
            # Mock pusher to capture payload
            captured_payload = None
            
            def mock_trigger(channel, event, data):
                nonlocal captured_payload
                captured_payload = data
                return True
                
            self.notification_manager._safe_pusher_trigger = mock_trigger
            
            # Trigger notification
            self.notification_manager.realtime_booking_checked_in(self.booking)
            
            # Validate payload has complete booking structure from canonical serializer
            self.assertIsNotNone(captured_payload)
            
            payload = captured_payload.get('payload', {})
            
            # Should have event marker
            self.assertEqual(payload.get('event'), 'booking_checked_in')
            
            # Should have complete booking data
            required_fields = [
                'booking_id', 'confirmation_number', 'check_in', 'check_out',
                'status', 'nights', 'assigned_room_number', 'party'
            ]
            
            for field in required_fields:
                self.assertIn(field, payload, f"Missing required field: {field}")
    
    def test_room_occupancy_updated_payload_contract(self):
        """Test that room occupancy notification includes booking context"""
        with transaction.atomic():
            captured_payload = None
            
            def mock_trigger(channel, event, data):
                nonlocal captured_payload
                captured_payload = data
                return True
                
            self.notification_manager._safe_pusher_trigger = mock_trigger
            
            # Trigger notification
            self.notification_manager.realtime_room_occupancy_updated(self.room)
            
            # Validate payload structure
            self.assertIsNotNone(captured_payload)
            
            payload = captured_payload.get('payload', {})
            
            # Should have room details
            required_fields = [
                'room_number', 'is_occupied', 'room_type', 'max_occupancy',
                'current_occupancy', 'guests_in_room', 'current_booking'
            ]
            
            for field in required_fields:
                self.assertIn(field, payload, f"Missing required field: {field}")
            
            # If there's a current booking, should have complete booking data
            if payload['current_booking']:
                booking_data = payload['current_booking']
                self.assertIn('booking_id', booking_data)
                self.assertIn('party', booking_data)


if __name__ == '__main__':
    import django
    import os
    import sys
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotelmate.settings')
    django.setup()
    
    # Run tests
    import unittest
    unittest.main()