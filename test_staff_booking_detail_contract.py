"""
Contract test to enforce staff booking detail endpoint includes required fields.
This ensures staff detail modal shows exact same fields as staff list (NO-FALLBACKS).

CRITICAL: Tests exact key presence and values for party_missing_count calculation.
"""

from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from hotel.models import Hotel, RoomBooking, BookingGuest
from rooms.models import RoomType, Room
from staff.models import Staff


class StaffBookingDetailContractTest(APITestCase):
    """Test staff booking detail endpoint contract compliance"""
    
    def setUp(self):
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            is_active=True
        )
        
        # Create room type
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            code="STD"
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='password123'
        )
        self.staff = Staff.objects.create(
            user=self.staff_user,
            hotel=self.hotel,
            first_name="Staff",
            last_name="Member"
        )
        
        # Create test booking with occupancy for 4 guests
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            booking_id="BK-2025-0001",
            confirmation_number="CONF12345",
            status='CONFIRMED',
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            adults=4,  # Expected 4 guests
            children=0,
            total_amount=200.00,
            currency='USD',
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            primary_phone="+1234567890",
            booker_type="INDIVIDUAL",
            booker_first_name="John",
            booker_last_name="Doe",
            booker_email="john@example.com",
        )
        
        # Add only 1 party member (missing 3)
        BookingGuest.objects.create(
            booking=self.booking,
            role='PRIMARY',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            is_staying=True
        )
        
        # Authenticate staff user
        self.client.force_authenticate(user=self.staff_user)
        
    def test_staff_booking_detail_exact_contract(self):
        """CRITICAL: Verify staff booking detail has exact same fields as list (NO-FALLBACKS)"""
        
        url = reverse(
            'room-bookings-staff-detail', 
            kwargs={
                'hotel_slug': self.hotel.slug,
                'booking_id': self.booking.booking_id
            }
        )
        
        response = self.client.get(url)
        
        # Must succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # 1. EXACT occupancy fields (top-level, same as list)
        self.assertIn('adults', data, "adults field missing from detail response")
        self.assertIn('children', data, "children field missing from detail response")
        self.assertEqual(data['adults'], 4, "adults must match booking expected count")
        self.assertEqual(data['children'], 0, "children must match booking expected count")
        
        # 2. EXACT party completion fields (top-level, same as list)
        self.assertIn('party_complete', data, "party_complete field missing from detail response")
        self.assertIn('party_missing_count', data, "party_missing_count field missing from detail response")
        self.assertEqual(data['party_complete'], False, "party_complete must be False when missing guests")
        self.assertEqual(data['party_missing_count'], 3, "party_missing_count must be 3 (4 expected - 1 actual)")
        
        # 3. EXACT precheckin fields (top-level, same as list)
        self.assertIn('precheckin_submitted_at', data, "precheckin_submitted_at field missing from detail response")
        self.assertIn('precheckin_payload', data, "precheckin_payload field missing from detail response")
        self.assertIsNone(data['precheckin_submitted_at'], "precheckin_submitted_at must be null when not submitted")
        
        # 4. Party structure must include precheckin_payload for members
        self.assertIn('party', data, "party field missing from detail response")
        self.assertIsInstance(data['party'], dict, "party must be object")
        self.assertIn('primary', data['party'], "party.primary missing")
        self.assertIn('companions', data['party'], "party.companions missing")
        self.assertIn('total_count', data['party'], "party.total_count missing")
        
        # Primary guest must have precheckin_payload field
        if data['party']['primary']:
            self.assertIn('precheckin_payload', data['party']['primary'], "party.primary.precheckin_payload missing")
        
        # Each companion must have precheckin_payload field  
        for companion in data['party']['companions']:
            self.assertIn('precheckin_payload', companion, "party.companions[].precheckin_payload missing")
        
        # 5. Core booking data
        self.assertEqual(data['booking_id'], 'BK-2025-0001')
        self.assertEqual(data['status'], 'CONFIRMED')
        
    def test_party_complete_shows_zero_missing(self):
        """Test party_complete=true shows party_missing_count=0"""
        
        # Add remaining 3 party members to make party complete
        for i in range(2, 5):  # Add guests 2, 3, 4
            BookingGuest.objects.create(
                booking=self.booking,
                role='COMPANION',
                first_name=f'Guest{i}',
                last_name='Doe',
                email=f'guest{i}@example.com',
                is_staying=True
            )
        
        url = reverse(
            'room-bookings-staff-detail', 
            kwargs={
                'hotel_slug': self.hotel.slug,
                'booking_id': self.booking.booking_id
            }
        )
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # EXACT assertions for complete party
        self.assertEqual(data['party_complete'], True, "party_complete must be True when all guests present")
        self.assertEqual(data['party_missing_count'], 0, "party_missing_count must be 0 when party complete")
        self.assertEqual(data['adults'], 4, "adults field must still show expected occupancy")
        self.assertEqual(data['children'], 0, "children field must still show expected occupancy")
        
    def test_no_forbidden_derived_fields(self):
        """CRITICAL: Verify no new boolean fields like precheckin_complete added"""
        
        url = reverse(
            'room-bookings-staff-detail', 
            kwargs={
                'hotel_slug': self.hotel.slug,
                'booking_id': self.booking.booking_id
            }
        )
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # These fields must NOT be present (banned derived fields)
        forbidden_fields = [
            'precheckin_complete',
            'guest_info_complete', 
            'party_status_complete',
            'expected_guests'
        ]
        
        for field in forbidden_fields:
            self.assertNotIn(
                field, 
                data, 
                f"FORBIDDEN field '{field}' found in staff booking detail response"
            )
            
        # These fields must be present in exact same location as list
        required_top_level_fields = [
            'booking_id',
            'party_complete', 
            'party_missing_count',
            'precheckin_submitted_at',
            'precheckin_payload',
            'adults',
            'children',
            'status',
        ]
        
        for field in required_top_level_fields:
            self.assertIn(
                field, 
                data, 
                f"REQUIRED top-level field '{field}' missing from staff booking detail response"
            )