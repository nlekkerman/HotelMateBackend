"""
Test suite for unified companions-only party contract.
Verifies both booking create and precheckin submit endpoints follow the same contract:
- PRIMARY never sent in party payloads
- PRIMARY inferred from RoomBooking.primary_*
- party payloads contain companions only
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
import json
import hashlib

from hotel.models import (
    Hotel, RoomBooking, BookingGuest, 
    BookingPrecheckinToken, BookerType
)
from rooms.models import RoomType


class CompanionsOnlyPartyContractTest(TestCase):
    """Test unified companions-only party contract across endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            is_active=True
        )
        
        # Create test room type
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Deluxe Suite",
            code="deluxe-suite",
            starting_price_from=100.00,
            max_occupancy=4,
            currency="EUR"
        )
        
        # Base booking payload for testing
        self.base_booking_payload = {
            "room_type_code": "deluxe-suite",
            "check_in": "2025-12-20",
            "check_out": "2025-12-22",
            "adults": 2,
            "children": 0,
            "booker_type": "SELF",
            "primary_first_name": "John",
            "primary_last_name": "Doe",
            "primary_email": "john.doe@example.com",
            "primary_phone": "+353871234567"
        }
        
    # ===== BOOKING CREATE TESTS =====
    
    def test_booking_create_companions_only_success(self):
        """✅ Booking create with companions-only party should succeed"""
        payload = self.base_booking_payload.copy()
        payload["party"] = [
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com",
                "phone": "+353871234568"
            }
        ]
        
        with patch('hotel.services.booking.create_room_booking_from_request') as mock_create:
            # Mock booking creation
            mock_booking = RoomBooking(
                booking_id="BK-2025-TEST01",
                hotel=self.hotel,
                room_type=self.room_type,
                status="PENDING_PAYMENT",
                primary_first_name="John",
                primary_last_name="Doe"
            )
            mock_create.return_value = mock_booking
            
            response = self.client.post(
                f'/api/public/hotel/{self.hotel.slug}/bookings/',
                data=json.dumps(payload),
                content_type='application/json'
            )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["party_count"], 2)  # 1 PRIMARY + 1 COMPANION
        
    def test_booking_create_reject_primary_in_party(self):
        """❌ Booking create should reject PRIMARY in party payload"""
        payload = self.base_booking_payload.copy()
        payload["party"] = [
            {
                "role": "PRIMARY",  # ❌ Should be rejected
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com"
            },
            {
                "first_name": "Jane",
                "last_name": "Smith"
            }
        ]
        
        response = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/bookings/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Do not include PRIMARY in party", response.json()["detail"])
        
    def test_booking_create_empty_party_success(self):
        """✅ Booking create with no party (PRIMARY only) should succeed"""
        with patch('hotel.services.booking.create_room_booking_from_request') as mock_create:
            # Mock booking creation
            mock_booking = RoomBooking(
                booking_id="BK-2025-TEST02",
                hotel=self.hotel,
                room_type=self.room_type,
                status="PENDING_PAYMENT",
                primary_first_name="John",
                primary_last_name="Doe"
            )
            mock_create.return_value = mock_booking
            
            response = self.client.post(
                f'/api/public/hotel/{self.hotel.slug}/bookings/',
                data=json.dumps(self.base_booking_payload),
                content_type='application/json'
            )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["data"]["party_count"], 1)  # 1 PRIMARY only
        
    def test_booking_create_companion_validation(self):
        """❌ Booking create should validate companion required fields"""
        payload = self.base_booking_payload.copy()
        payload["party"] = [
            {
                "first_name": "Jane",
                # Missing last_name
                "email": "jane@example.com"
            }
        ]
        
        response = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/bookings/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("first_name and last_name", response.json()["detail"])
    
    # ===== PRECHECKIN SUBMIT TESTS =====
    
    def _create_test_booking_with_token(self):
        """Helper to create booking with precheckin token"""
        booking = RoomBooking.objects.create(
            booking_id="BK-2025-TEST03",
            hotel=self.hotel,
            room_type=self.room_type,
            status="CONFIRMED",
            check_in="2025-12-20",
            check_out="2025-12-22",
            adults=3,
            children=0,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john.doe@example.com",
            primary_phone="+353871234567",
            booker_type=BookerType.SELF
        )
        
        # Create PRIMARY BookingGuest (would normally be auto-created)
        BookingGuest.objects.create(
            booking=booking,
            role="PRIMARY",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+353871234567",
            is_staying=True
        )
        
        # Create existing COMPANION (to be replaced)
        BookingGuest.objects.create(
            booking=booking,
            role="COMPANION",
            first_name="Old",
            last_name="Companion",
            email="old@example.com",
            is_staying=True
        )
        
        # Create precheckin token
        raw_token = "test-token-12345"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        token = BookingPrecheckinToken.objects.create(
            booking=booking,
            token_hash=token_hash,
            expires_at=timezone.now() + timezone.timedelta(days=7),
            config_snapshot_enabled={"party": True},
            config_snapshot_required={"party": False}
        )
        
        return booking, raw_token
        
    def test_precheckin_companions_only_success(self):
        """✅ Precheckin with companions-only party should preserve PRIMARY"""
        booking, raw_token = self._create_test_booking_with_token()
        
        # Verify initial state: 1 PRIMARY + 1 old COMPANION
        self.assertEqual(booking.party.count(), 2)
        self.assertEqual(booking.party.filter(role="PRIMARY").count(), 1)
        self.assertEqual(booking.party.filter(role="COMPANION").count(), 1)
        
        payload = {
            "token": raw_token,
            "party": [
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@example.com"
                },
                {
                    "first_name": "Bob",
                    "last_name": "Johnson",
                    "phone": "+353871234569"
                }
            ]
        }
        
        response = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        
        # Verify final state: 1 PRIMARY (preserved) + 2 new COMPANIONS
        booking.refresh_from_db()
        self.assertEqual(booking.party.count(), 3)
        self.assertEqual(booking.party.filter(role="PRIMARY").count(), 1)
        self.assertEqual(booking.party.filter(role="COMPANION").count(), 2)
        
        # Verify PRIMARY is unchanged
        primary = booking.party.get(role="PRIMARY")
        self.assertEqual(primary.first_name, "John")
        self.assertEqual(primary.last_name, "Doe")
        
        # Verify old COMPANION was replaced
        companions = booking.party.filter(role="COMPANION")
        companion_names = [(c.first_name, c.last_name) for c in companions]
        self.assertIn(("Jane", "Smith"), companion_names)
        self.assertIn(("Bob", "Johnson"), companion_names)
        self.assertNotIn(("Old", "Companion"), companion_names)
        
    def test_precheckin_reject_primary_in_party(self):
        """❌ Precheckin should reject PRIMARY in party payload"""
        booking, raw_token = self._create_test_booking_with_token()
        
        payload = {
            "token": raw_token,
            "party": [
                {
                    "role": "PRIMARY",  # ❌ Should be rejected
                    "first_name": "John",
                    "last_name": "Doe"
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith"
                }
            ]
        }
        
        response = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["code"], "VALIDATION_ERROR")
        self.assertIn("Do not include PRIMARY in party", data["message"])
        
    def test_precheckin_empty_party_success(self):
        """✅ Precheckin with empty party (PRIMARY only) should succeed"""
        booking, raw_token = self._create_test_booking_with_token()
        
        # Update booking to expect only 1 guest total
        booking.adults = 1
        booking.children = 0
        booking.save()
        
        payload = {
            "token": raw_token,
            "party": []  # No companions, PRIMARY only
        }
        
        response = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify final state: 1 PRIMARY only (old COMPANION removed)
        booking.refresh_from_db()
        self.assertEqual(booking.party.count(), 1)
        self.assertEqual(booking.party.filter(role="PRIMARY").count(), 1)
        self.assertEqual(booking.party.filter(role="COMPANION").count(), 0)
        
    def test_precheckin_party_size_validation(self):
        """❌ Precheckin should validate party size matches adults+children"""
        booking, raw_token = self._create_test_booking_with_token()
        # booking has adults=3, children=0, so expects 3 total
        
        payload = {
            "token": raw_token,
            "party": [
                {
                    "first_name": "Jane", 
                    "last_name": "Smith"
                }
                # Only 1 companion + 1 PRIMARY = 2 total, but expects 3
            ]
        }
        
        response = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["code"], "PARTY_SIZE_MISMATCH")
        self.assertIn("Expected 3, got 2", data["message"])
        
    def test_precheckin_idempotency(self):
        """✅ Submitting precheckin twice should not duplicate companions"""
        booking, raw_token = self._create_test_booking_with_token()
        
        payload = {
            "token": raw_token,
            "party": [
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@example.com"
                }
            ]
        }
        
        # Submit first time
        response1 = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, 200)
        
        # Verify state after first submit
        booking.refresh_from_db()
        self.assertEqual(booking.party.count(), 2)  # 1 PRIMARY + 1 COMPANION
        
        # Update token to allow reuse (normally would be used_at)
        token = BookingPrecheckinToken.objects.get(booking=booking)
        token.used_at = None
        token.save()
        
        # Submit second time with different companion
        payload["party"] = [
            {
                "first_name": "Bob", 
                "last_name": "Johnson"
            }
        ]
        
        response2 = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 200)
        
        # Verify final state: still 2 total, but companion replaced
        booking.refresh_from_db()
        self.assertEqual(booking.party.count(), 2)  # 1 PRIMARY + 1 COMPANION
        
        companion = booking.party.get(role="COMPANION")
        self.assertEqual(companion.first_name, "Bob")
        self.assertEqual(companion.last_name, "Johnson")
        
    def test_precheckin_constraint_invariant(self):
        """✅ Verify PRIMARY constraint is maintained throughout process"""
        booking, raw_token = self._create_test_booking_with_token()
        
        # Verify constraint before
        self.assertEqual(booking.party.filter(role="PRIMARY").count(), 1)
        
        payload = {
            "token": raw_token,
            "party": [
                {"first_name": "Jane", "last_name": "Smith"},
                {"first_name": "Bob", "last_name": "Johnson"}
            ]
        }
        
        response = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify constraint after - exactly 1 PRIMARY always
        booking.refresh_from_db()
        self.assertEqual(booking.party.filter(role="PRIMARY").count(), 1)


# ===== INTEGRATION TEST FOR END-TO-END WORKFLOW =====

class EndToEndCompanionsOnlyTest(TestCase):
    """Test complete booking create -> precheckin submit workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            is_active=True
        )
        
        # Create test room type  
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Deluxe Suite",
            code="deluxe-suite",
            starting_price_from=100.00,
            max_occupancy=4,
            currency="EUR"
        )
    
    @patch('hotel.services.booking.create_room_booking_from_request')
    def test_end_to_end_companions_only_workflow(self, mock_create):
        """✅ Test complete workflow: booking create -> precheckin submit"""
        
        # Step 1: Create booking with companions-only party
        booking_payload = {
            "room_type_code": "deluxe-suite",
            "check_in": "2025-12-20", 
            "check_out": "2025-12-22",
            "adults": 3,
            "children": 0,
            "booker_type": "SELF",
            "primary_first_name": "John",
            "primary_last_name": "Doe", 
            "primary_email": "john.doe@example.com",
            "primary_phone": "+353871234567",
            "party": [
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@example.com"
                },
                {
                    "first_name": "Bob", 
                    "last_name": "Johnson"
                }
            ]
        }
        
        # Mock booking creation and party setup
        mock_booking = RoomBooking.objects.create(
            booking_id="BK-2025-E2E01",
            hotel=self.hotel,
            room_type=self.room_type,
            status="CONFIRMED",
            check_in="2025-12-20",
            check_out="2025-12-22", 
            adults=3,
            children=0,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john.doe@example.com",
            primary_phone="+353871234567",
            booker_type=BookerType.SELF
        )
        mock_create.return_value = mock_booking
        
        # Create booking
        booking_response = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/bookings/',
            data=json.dumps(booking_payload),
            content_type='application/json'
        )
        
        self.assertEqual(booking_response.status_code, 201)
        
        # Simulate BookingGuest creation (normally done by RoomBooking.save())
        BookingGuest.objects.create(
            booking=mock_booking,
            role="PRIMARY",
            first_name="John",
            last_name="Doe", 
            email="john.doe@example.com",
            phone="+353871234567",
            is_staying=True
        )
        
        # Verify initial party count
        self.assertEqual(mock_booking.party.count(), 3)  # 1 PRIMARY + 2 COMPANIONs
        
        # Step 2: Create precheckin token
        raw_token = "e2e-test-token" 
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        BookingPrecheckinToken.objects.create(
            booking=mock_booking,
            token_hash=token_hash,
            expires_at=timezone.now() + timezone.timedelta(days=7),
            config_snapshot_enabled={"party": True},
            config_snapshot_required={"party": False}
        )
        
        # Step 3: Submit precheckin with updated companions-only party
        precheckin_payload = {
            "token": raw_token,
            "party": [
                {
                    "first_name": "Jane",
                    "last_name": "Smith-Updated",  # Updated name
                    "email": "jane.updated@example.com"
                },
                {
                    "first_name": "Alice",  # Replaced Bob with Alice
                    "last_name": "Wilson",
                    "phone": "+353871234570"
                }
            ]
        }
        
        precheckin_response = self.client.post(
            f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/',
            data=json.dumps(precheckin_payload), 
            content_type='application/json'
        )
        
        self.assertEqual(precheckin_response.status_code, 200)
        
        # Step 4: Verify final state
        mock_booking.refresh_from_db()
        
        # Should still have 3 total: 1 PRIMARY + 2 COMPANIONs
        self.assertEqual(mock_booking.party.count(), 3)
        self.assertEqual(mock_booking.party.filter(role="PRIMARY").count(), 1)
        self.assertEqual(mock_booking.party.filter(role="COMPANION").count(), 2)
        
        # PRIMARY should be unchanged
        primary = mock_booking.party.get(role="PRIMARY")
        self.assertEqual(primary.first_name, "John") 
        self.assertEqual(primary.last_name, "Doe")
        
        # COMPANIONs should be updated from precheckin
        companions = list(mock_booking.party.filter(role="COMPANION").order_by('first_name'))
        self.assertEqual(len(companions), 2)
        
        # Check Alice
        alice = companions[0]  # Alice comes first alphabetically
        self.assertEqual(alice.first_name, "Alice")
        self.assertEqual(alice.last_name, "Wilson")
        
        # Check Jane (updated)
        jane = companions[1] 
        self.assertEqual(jane.first_name, "Jane")
        self.assertEqual(jane.last_name, "Smith-Updated")
        self.assertEqual(jane.email, "jane.updated@example.com")


if __name__ == '__main__':
    # Run tests
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
    django.setup()
    
    import unittest
    unittest.main()