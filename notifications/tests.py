"""
Tests for notifications app - focusing on Pusher authentication
"""
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from hotel.models import Hotel, RoomBooking, GuestBookingToken
from staff.models import Staff, StaffRole
import json


class PusherAuthViewTestCase(TestCase):
    """Test Pusher authentication endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            address="123 Test St"
        )
        
        # Create test booking
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            booking_id="BK-TEST-001",
            status="CONFIRMED",
            check_in_date=timezone.now().date(),
            check_out_date=(timezone.now() + timedelta(days=2)).date(),
            primary_guest_name="Test Guest",
            primary_guest_email="guest@test.com",
            party_size=2
        )
    
    def test_guest_auth_valid_token_success(self):
        """Test guest auth with valid token returns 200 auth response"""
        # Create valid guest token
        token_obj, raw_token = GuestBookingToken.generate_token(
            booking=self.booking,
            hotel=self.hotel,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        response = self.client.post('/api/notifications/pusher/auth/', {
            'socket_id': 'test-socket-123',
            'channel_name': f'private-guest-booking.{self.booking.booking_id}',
            'token': raw_token
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth', response.data)
        self.assertIn('channel_data', response.data)
        
        # Verify channel_data contains expected guest info
        channel_data = json.loads(response.data['channel_data'])
        self.assertEqual(channel_data['user_info']['booking_id'], self.booking.booking_id)
        self.assertEqual(channel_data['user_info']['type'], 'guest')
    
    def test_guest_auth_invalid_token_returns_403(self):
        """Test guest auth with invalid token returns 403"""
        response = self.client.post('/api/notifications/pusher/auth/', {
            'socket_id': 'test-socket-123',
            'channel_name': f'private-guest-booking.{self.booking.booking_id}',
            'token': 'invalid-token-123'
        })
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error'], 'UNAUTHORIZED')
        self.assertIn('detail', response.data)
    
    def test_guest_auth_token_from_querystring(self):
        """Test guest auth accepts token from querystring"""
        # Create valid guest token
        token_obj, raw_token = GuestBookingToken.generate_token(
            booking=self.booking,
            hotel=self.hotel,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        response = self.client.post(
            f'/api/notifications/pusher/auth/?token={raw_token}',
            {
                'socket_id': 'test-socket-123',
                'channel_name': f'private-guest-booking.{self.booking.booking_id}'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth', response.data)
    
    def test_guest_auth_wrong_booking_id_fails(self):
        """Test guest token for wrong booking ID fails"""
        # Create valid guest token
        token_obj, raw_token = GuestBookingToken.generate_token(
            booking=self.booking,
            hotel=self.hotel,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Try to access different booking channel
        response = self.client.post('/api/notifications/pusher/auth/', {
            'socket_id': 'test-socket-123',
            'channel_name': 'private-guest-booking.BK-OTHER-001',
            'token': raw_token
        })
        
        self.assertEqual(response.status_code, 403)
    
    def test_guest_auth_staff_channel_rejected(self):
        """Test guest token cannot access staff channels"""
        # Create valid guest token
        token_obj, raw_token = GuestBookingToken.generate_token(
            booking=self.booking,
            hotel=self.hotel,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Try to access staff channel
        response = self.client.post('/api/notifications/pusher/auth/', {
            'socket_id': 'test-socket-123',
            'channel_name': f'{self.hotel.slug}.room-bookings',
            'token': raw_token
        })
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error'], 'Guest tokens cannot access staff channels')
    
    def test_missing_required_fields_returns_400(self):
        """Test missing socket_id or channel_name returns 400"""
        response = self.client.post('/api/notifications/pusher/auth/', {
            'socket_id': 'test-socket-123'
            # Missing channel_name
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Missing socket_id or channel_name')
