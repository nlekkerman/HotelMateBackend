from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from hotel.models import Hotel
from rooms.models import Room, RoomType
from staff.models import Staff
from guests.models import Guest

User = get_user_model()


class CheckoutRoomsTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create a hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            is_active=True
        )
        
        # Create a room type
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            base_price=100.00
        )
        
        # Create rooms
        self.room1 = Room.objects.create(
            hotel=self.hotel,
            room_number=101,
            room_type=self.room_type,
            is_occupied=True,
            room_status='OCCUPIED'
        )
        
        self.room2 = Room.objects.create(
            hotel=self.hotel,
            room_number=102,
            room_type=self.room_type,
            is_occupied=True,
            room_status='OCCUPIED'
        )
        
        self.room3 = Room.objects.create(
            hotel=self.hotel,
            room_number=103,
            room_type=self.room_type,
            is_occupied=False,
            room_status='READY_FOR_GUEST'
        )
        
        # Create guests in rooms
        self.guest1 = Guest.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            room=self.room1
        )
        
        self.guest2 = Guest.objects.create(
            first_name="Jane",
            last_name="Smith", 
            email="jane@example.com",
            room=self.room2
        )
        
        # Create staff user for authentication
        self.staff_user = User.objects.create_user(
            username="teststaff",
            email="staff@test.com",
            password="testpass123"
        )
        
        self.staff = Staff.objects.create(
            user=self.staff_user,
            hotel=self.hotel,
            department="FRONT_DESK"
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff_user)

    def test_checkout_rooms_success(self):
        """Test successful checkout of multiple rooms"""
        url = f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/'
        data = {
            'room_ids': [self.room1.id, self.room2.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check rooms are no longer occupied
        self.room1.refresh_from_db()
        self.room2.refresh_from_db()
        
        self.assertFalse(self.room1.is_occupied)
        self.assertFalse(self.room2.is_occupied)
        self.assertEqual(self.room1.room_status, 'CHECKOUT_DIRTY')
        self.assertEqual(self.room2.room_status, 'CHECKOUT_DIRTY')
        
        # Check guests are deleted
        self.assertFalse(Guest.objects.filter(room=self.room1).exists())
        self.assertFalse(Guest.objects.filter(room=self.room2).exists())
        
    def test_checkout_rooms_empty_list(self):
        """Test checkout with empty room_ids list"""
        url = f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/'
        data = {
            'room_ids': []
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], '`room_ids` must be a non-empty list.')
        
    def test_checkout_rooms_missing_room_ids(self):
        """Test checkout without room_ids field"""
        url = f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/'
        data = {}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], '`room_ids` must be a non-empty list.')
        
    def test_checkout_rooms_invalid_room_ids(self):
        """Test checkout with non-existent room IDs"""
        url = f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/'
        data = {
            'room_ids': [9999, 8888]  # Non-existent IDs
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'No matching rooms found for this hotel.')
        
    def test_checkout_rooms_wrong_hotel(self):
        """Test checkout with room IDs from different hotel"""
        # Create another hotel and room
        other_hotel = Hotel.objects.create(
            name="Other Hotel",
            slug="other-hotel"
        )
        other_room = Room.objects.create(
            hotel=other_hotel,
            room_number=201,
            room_type=self.room_type
        )
        
        url = f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/'
        data = {
            'room_ids': [other_room.id]  # Room from different hotel
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'No matching rooms found for this hotel.')
        
    def test_checkout_rooms_string_ids(self):
        """Test checkout with string room numbers instead of integer IDs"""
        url = f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/'
        data = {
            'room_ids': ['101', '102']  # Room numbers as strings
        }
        
        response = self.client.post(url, data, format='json')
        
        # This should fail because it's looking for integer IDs, not room numbers
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_checkout_rooms_unauthenticated(self):
        """Test checkout without authentication"""
        self.client.logout()
        
        url = f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/'
        data = {
            'room_ids': [self.room1.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_checkout_single_room(self):
        """Test checkout of single room using bulk endpoint"""
        url = f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/'
        data = {
            'room_ids': [self.room1.id]  # Single room in array
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.room1.refresh_from_db()
        self.assertFalse(self.room1.is_occupied)
        self.assertEqual(self.room1.room_status, 'CHECKOUT_DIRTY')
        
    def test_room_id_vs_room_number_difference(self):
        """Demonstrate the difference between room ID and room number"""
        print(f"\nRoom 101: database ID = {self.room1.id}, room_number = {self.room1.room_number}")
        print(f"Room 102: database ID = {self.room2.id}, room_number = {self.room2.room_number}")
        print(f"Room 103: database ID = {self.room3.id}, room_number = {self.room3.room_number}")
        
        # Test with correct database IDs
        url = f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/'
        data = {
            'room_ids': [self.room1.id, self.room2.id]  # Database IDs
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)