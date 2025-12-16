"""
Test suite for the NEW RoomBooking public create endpoint.
Tests the enforcement of new canonical fields and rejection of legacy payloads.
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from hotel.models import Hotel, RoomBooking, BookingGuest, BookerType
from rooms.models import RoomType


class NewBookingCreateViewTests(TestCase):
    """Test the new HotelBookingCreateView with strict field validation"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            is_active=True,
            phone="+353 1 234 5678",
            email="test@hotel.com"
        )
        
        # Create test room type
        self.room_type = RoomType.objects.create(
            name="Deluxe King",
            code="DLX",
            hotel=self.hotel,
            base_price=Decimal('150.00'),
            currency="EUR",
            max_occupancy=2,
            is_active=True
        )
        
        self.url = reverse('hotel:booking-create', kwargs={'hotel_slug': self.hotel.slug})
        
        # Valid new payload structure
        self.valid_payload = {
            "room_type_code": "DLX",
            "check_in": "2025-12-25",
            "check_out": "2025-12-27",
            "primary_first_name": "John",
            "primary_last_name": "Doe", 
            "primary_email": "john@example.com",
            "primary_phone": "+353 87 123 4567",
            "booker_type": BookerType.SELF,
            "adults": 2,
            "children": 0
        }
    
    def test_create_booking_self_success(self):
        """Test successful booking creation with SELF booker_type"""
        response = self.client.post(self.url, self.valid_payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        # Verify response structure
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        booking_data = data['data']
        self.assertIn('booking_id', booking_data)
        self.assertEqual(booking_data['status'], 'PENDING_PAYMENT')
        self.assertEqual(booking_data['primary_guest_name'], 'John Doe')
        self.assertEqual(booking_data['booker_type'], BookerType.SELF)
        self.assertEqual(booking_data['party_count'], 1)
        
        # Verify booking was created in database
        booking = RoomBooking.objects.get(booking_id=booking_data['booking_id'])
        self.assertEqual(booking.primary_first_name, 'John')
        self.assertEqual(booking.primary_last_name, 'Doe')
        self.assertEqual(booking.primary_email, 'john@example.com')
        self.assertEqual(booking.primary_phone, '+353 87 123 4567')
        self.assertEqual(booking.booker_type, BookerType.SELF)
        
        # Verify primary BookingGuest was auto-created
        primary_guest = BookingGuest.objects.get(booking=booking, role='PRIMARY')
        self.assertEqual(primary_guest.first_name, 'John')
        self.assertEqual(primary_guest.last_name, 'Doe')
    
    def test_create_booking_third_party_success(self):
        """Test successful booking creation with THIRD_PARTY booker_type"""
        payload = self.valid_payload.copy()
        payload.update({
            "booker_type": BookerType.THIRD_PARTY,
            "booker_first_name": "Jane",
            "booker_last_name": "Smith",
            "booker_email": "jane@company.com",
            "booker_phone": "+353 87 987 6543"
        })
        
        response = self.client.post(self.url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        booking_data = data['data']
        self.assertEqual(booking_data['booker_type'], BookerType.THIRD_PARTY)
        
        # Verify booking was created with booker info
        booking = RoomBooking.objects.get(booking_id=booking_data['booking_id'])
        self.assertEqual(booking.booker_first_name, 'Jane')
        self.assertEqual(booking.booker_last_name, 'Smith')
        self.assertEqual(booking.booker_email, 'jane@company.com')
        self.assertEqual(booking.booker_phone, '+353 87 987 6543')
        self.assertEqual(booking.booker_company, '')  # Not required for THIRD_PARTY
    
    def test_create_booking_company_success(self):
        """Test successful booking creation with COMPANY booker_type"""
        payload = self.valid_payload.copy()
        payload.update({
            "booker_type": BookerType.COMPANY,
            "booker_first_name": "Corporate",
            "booker_last_name": "Agent",
            "booker_email": "bookings@company.com",
            "booker_phone": "+353 1 555 1234",
            "booker_company": "Acme Corp Ltd"
        })
        
        response = self.client.post(self.url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        booking_data = data['data']
        self.assertEqual(booking_data['booker_type'], BookerType.COMPANY)
        
        # Verify booking was created with company info
        booking = RoomBooking.objects.get(booking_id=booking_data['booking_id'])
        self.assertEqual(booking.booker_company, 'Acme Corp Ltd')
    
    def test_reject_legacy_guest_payload(self):
        """Test that legacy guest{} payload is rejected with 400"""
        legacy_payload = {
            "room_type_code": "DLX",
            "check_in": "2025-12-25",
            "check_out": "2025-12-27",
            "guest": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "+353 87 123 4567"
            }
        }
        
        response = self.client.post(self.url, legacy_payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("Legacy guest payload is not supported", data['detail'])
    
    def test_missing_required_fields(self):
        """Test validation of required fields"""
        # Missing primary_first_name
        payload = self.valid_payload.copy()
        del payload['primary_first_name']
        
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Required fields", response.json()['detail'])
    
    def test_invalid_booker_type(self):
        """Test validation of booker_type field"""
        payload = self.valid_payload.copy()
        payload['booker_type'] = 'INVALID_TYPE'
        
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("booker_type must be one of", response.json()['detail'])
    
    def test_third_party_missing_booker_fields(self):
        """Test that THIRD_PARTY bookings require booker fields"""
        payload = self.valid_payload.copy()
        payload['booker_type'] = BookerType.THIRD_PARTY
        # Missing booker fields
        
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("booker_first_name", response.json()['detail'])
    
    def test_company_missing_company_field(self):
        """Test that COMPANY bookings require booker_company"""
        payload = self.valid_payload.copy()
        payload.update({
            "booker_type": BookerType.COMPANY,
            "booker_first_name": "Corporate",
            "booker_last_name": "Agent",
            "booker_email": "bookings@company.com",
            "booker_phone": "+353 1 555 1234"
            # Missing booker_company
        })
        
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("booker_company is required", response.json()['detail'])
    
    def test_create_booking_with_party(self):
        """Test booking creation with party list"""
        payload = self.valid_payload.copy()
        payload['party'] = [
            {
                "role": "PRIMARY",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "+353 87 123 4567"
            },
            {
                "role": "COMPANION", 
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com"
            }
        ]
        
        response = self.client.post(self.url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        # Should show party_count = 2
        self.assertEqual(data['data']['party_count'], 2)
        
        # Verify both party members were created
        booking = RoomBooking.objects.get(booking_id=data['data']['booking_id'])
        self.assertEqual(booking.party.count(), 2)
        self.assertEqual(booking.party.filter(role='PRIMARY').count(), 1)
        self.assertEqual(booking.party.filter(role='COMPANION').count(), 1)
    
    def test_party_primary_mismatch(self):
        """Test that PRIMARY party member must match primary_* fields"""
        payload = self.valid_payload.copy()
        payload['party'] = [
            {
                "role": "PRIMARY",
                "first_name": "Wrong",  # Doesn't match primary_first_name
                "last_name": "Name",
                "email": "wrong@example.com"
            }
        ]
        
        response = self.client.post(self.url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("PRIMARY party member must match", response.json()['detail'])
    
    def test_party_no_primary(self):
        """Test that party must include exactly one PRIMARY"""
        payload = self.valid_payload.copy()
        payload['party'] = [
            {
                "role": "COMPANION",
                "first_name": "Jane",
                "last_name": "Doe"
            }
        ]
        
        response = self.client.post(self.url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("exactly one PRIMARY guest", response.json()['detail'])
    
    def test_invalid_room_type(self):
        """Test validation for non-existent room type"""
        payload = self.valid_payload.copy()
        payload['room_type_code'] = 'NONEXISTENT'
        
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Room type 'NONEXISTENT' not found", response.json()['detail'])
    
    def test_invalid_dates(self):
        """Test validation for invalid check-in/check-out dates"""
        payload = self.valid_payload.copy()
        payload['check_out'] = '2025-12-24'  # Before check_in
        
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)