"""
Comprehensive tests for Hotel Public API.

Tests models, serializers, views, security, and edge cases for the
public hotel page API functionality.
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal

from hotel.models import Hotel, HotelAccessConfig, BookingOptions, Offer
from hotel.models import LeisureActivity
from rooms.models import RoomType


class BookingOptionsModelTests(TestCase):
    """Test BookingOptions model creation and relationships."""
    
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
    
    def test_booking_options_creation(self):
        """Test creating BookingOptions for a hotel."""
        booking_options = BookingOptions.objects.create(
            hotel=self.hotel,
            primary_cta_label='Book Now',
            primary_cta_url='https://booking.test.com',
            secondary_cta_label='Call Us',
            secondary_cta_phone='+353 1 234 5678'
        )
        
        self.assertEqual(booking_options.hotel, self.hotel)
        self.assertEqual(booking_options.primary_cta_label, 'Book Now')
        self.assertTrue(hasattr(self.hotel, 'booking_options'))
    
    def test_booking_options_optional_fields(self):
        """Test BookingOptions with optional fields."""
        booking_options = BookingOptions.objects.create(
            hotel=self.hotel,
            primary_cta_label='Book',
            terms_url='https://test.com/terms',
            policies_url='https://test.com/policies'
        )
        
        self.assertIsNotNone(booking_options.terms_url)
        self.assertIsNotNone(booking_options.policies_url)


class RoomTypeModelTests(TestCase):
    """Test RoomType model creation, ordering, and filtering."""
    
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
    
    def test_room_type_creation(self):
        """Test creating RoomType with all fields."""
        room_type = RoomType.objects.create(
            hotel=self.hotel,
            code='DLX',
            name='Deluxe Suite',
            short_description='Luxury suite',
            max_occupancy=4,
            bed_setup='King Bed + Sofa',
            starting_price_from=Decimal('159.00'),
            currency='EUR',
            is_active=True,
            sort_order=10
        )
        
        self.assertEqual(room_type.hotel, self.hotel)
        self.assertEqual(room_type.code, 'DLX')
        self.assertEqual(room_type.max_occupancy, 4)
    
    def test_room_type_ordering(self):
        """Test RoomType ordering by sort_order."""
        room1 = RoomType.objects.create(
            hotel=self.hotel,
            code='STD',
            name='Standard',
            sort_order=20
        )
        room2 = RoomType.objects.create(
            hotel=self.hotel,
            code='DLX',
            name='Deluxe',
            sort_order=10
        )
        room3 = RoomType.objects.create(
            hotel=self.hotel,
            code='STE',
            name='Suite',
            sort_order=30
        )
        
        rooms = list(RoomType.objects.filter(hotel=self.hotel))
        self.assertEqual(rooms[0].code, 'DLX')
        self.assertEqual(rooms[1].code, 'STD')
        self.assertEqual(rooms[2].code, 'STE')
    
    def test_room_type_filtering_by_active(self):
        """Test filtering RoomTypes by is_active."""
        RoomType.objects.create(
            hotel=self.hotel,
            code='STD',
            name='Standard',
            is_active=True
        )
        RoomType.objects.create(
            hotel=self.hotel,
            code='OLD',
            name='Old Room',
            is_active=False
        )
        
        active_rooms = RoomType.objects.filter(
            hotel=self.hotel,
            is_active=True
        )
        self.assertEqual(active_rooms.count(), 1)


class OfferModelTests(TestCase):
    """Test Offer model creation, is_valid() method, and filtering."""
    
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
        self.today = date.today()
    
    def test_offer_creation(self):
        """Test creating Offer with all fields."""
        offer = Offer.objects.create(
            hotel=self.hotel,
            title='Weekend Special',
            short_description='Great deal',
            details_html='<p>Details here</p>',
            valid_from=self.today,
            valid_to=self.today + timedelta(days=30),
            tag='Weekend',
            is_active=True
        )
        
        self.assertEqual(offer.hotel, self.hotel)
        self.assertEqual(offer.title, 'Weekend Special')
    
    def test_offer_is_valid_method(self):
        """Test Offer is_valid() method."""
        # Valid offer
        valid_offer = Offer.objects.create(
            hotel=self.hotel,
            title='Current Offer',
            valid_from=self.today - timedelta(days=5),
            valid_to=self.today + timedelta(days=5),
            is_active=True
        )
        self.assertTrue(valid_offer.is_valid())
        
        # Expired offer
        expired_offer = Offer.objects.create(
            hotel=self.hotel,
            title='Expired Offer',
            valid_from=self.today - timedelta(days=30),
            valid_to=self.today - timedelta(days=1),
            is_active=True
        )
        self.assertFalse(expired_offer.is_valid())
        
        # Future offer
        future_offer = Offer.objects.create(
            hotel=self.hotel,
            title='Future Offer',
            valid_from=self.today + timedelta(days=5),
            valid_to=self.today + timedelta(days=30),
            is_active=True
        )
        self.assertFalse(future_offer.is_valid())
    
    def test_offer_filtering_by_active(self):
        """Test filtering Offers by is_active."""
        Offer.objects.create(
            hotel=self.hotel,
            title='Active Offer',
            valid_from=self.today,
            valid_to=self.today + timedelta(days=30),
            is_active=True
        )
        Offer.objects.create(
            hotel=self.hotel,
            title='Inactive Offer',
            valid_from=self.today,
            valid_to=self.today + timedelta(days=30),
            is_active=False
        )
        
        active_offers = Offer.objects.filter(
            hotel=self.hotel,
            is_active=True
        )
        self.assertEqual(active_offers.count(), 1)


class LeisureActivityModelTests(TestCase):
    """Test LeisureActivity model creation and category choices."""
    
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
    
    def test_leisure_activity_creation(self):
        """Test creating LeisureActivity."""
        activity = LeisureActivity.objects.create(
            hotel=self.hotel,
            name='Indoor Pool',
            category='WELLNESS',
            short_description='Heated pool',
            icon='swimming-pool',
            is_active=True
        )
        
        self.assertEqual(activity.hotel, self.hotel)
        self.assertEqual(activity.category, 'WELLNESS')
    
    def test_leisure_activity_categories(self):
        """Test different category choices."""
        categories = [
            'WELLNESS',
            'FAMILY',
            'DINING',
            'SPORTS',
            'ENTERTAINMENT',
            'BUSINESS'
        ]
        
        for cat in categories:
            LeisureActivity.objects.create(
                hotel=self.hotel,
                name=f'Activity {cat}',
                category=cat,
                is_active=True
            )
        
        self.assertEqual(
            LeisureActivity.objects.filter(hotel=self.hotel).count(),
            6
        )


class HotelPublicPageViewTests(TestCase):
    """Test Hotel Public Page API view."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test hotel with all data
        self.hotel = Hotel.objects.create(
            name='Grand Test Hotel',
            slug='grand-test-hotel',
            city='Dublin',
            country='Ireland',
            tagline='Luxury awaits',
            short_description='Beautiful hotel',
            long_description='Extended description here',
            address_line_1='123 Main St',
            postal_code='D01 ABC1',
            latitude=Decimal('53.349804'),
            longitude=Decimal('-6.260310'),
            phone='+353 1 234 5678',
            email='info@test.com',
            is_active=True
        )
        
        # Create booking options
        self.booking_options = BookingOptions.objects.create(
            hotel=self.hotel,
            primary_cta_label='Book Now',
            primary_cta_url='https://booking.test.com'
        )
        
        # Create room types
        self.room1 = RoomType.objects.create(
            hotel=self.hotel,
            code='STD',
            name='Standard Room',
            max_occupancy=2,
            starting_price_from=Decimal('89.00'),
            is_active=True,
            sort_order=1
        )
        self.room2 = RoomType.objects.create(
            hotel=self.hotel,
            code='DLX',
            name='Deluxe Suite',
            max_occupancy=4,
            starting_price_from=Decimal('159.00'),
            is_active=True,
            sort_order=2
        )
        
        # Create offers
        today = date.today()
        self.offer1 = Offer.objects.create(
            hotel=self.hotel,
            title='Weekend Special',
            valid_from=today,
            valid_to=today + timedelta(days=30),
            is_active=True,
            sort_order=1
        )
        
        # Create leisure activities
        self.activity1 = LeisureActivity.objects.create(
            hotel=self.hotel,
            name='Indoor Pool',
            category='WELLNESS',
            is_active=True,
            sort_order=1
        )
        self.activity2 = LeisureActivity.objects.create(
            hotel=self.hotel,
            name='Restaurant',
            category='DINING',
            is_active=True,
            sort_order=2
        )
    
    def test_valid_slug_returns_200(self):
        """Test valid hotel slug returns 200 with full data."""
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Grand Test Hotel')
        self.assertEqual(response.data['slug'], 'grand-test-hotel')
    
    def test_invalid_slug_returns_404(self):
        """Test invalid hotel slug returns 404."""
        response = self.client.get(
            '/api/hotel/public/page/nonexistent-hotel/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_inactive_hotel_returns_404(self):
        """Test inactive hotel returns 404."""
        self.hotel.is_active = False
        self.hotel.save()
        
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_no_authentication_required(self):
        """Test no authentication is required for public endpoint."""
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_response_structure_matches_spec(self):
        """Test response structure contains all expected fields."""
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        data = response.data
        
        # Basic hotel fields
        self.assertIn('slug', data)
        self.assertIn('name', data)
        self.assertIn('city', data)
        self.assertIn('country', data)
        
        # Marketing fields
        self.assertIn('tagline', data)
        self.assertIn('short_description', data)
        
        # Contact fields
        self.assertIn('phone', data)
        self.assertIn('email', data)
        
        # Nested collections
        self.assertIn('booking_options', data)
        self.assertIn('room_types', data)
        self.assertIn('offers', data)
        self.assertIn('leisure_activities', data)
    
    def test_multiple_room_types_returned(self):
        """Test multiple room types are returned."""
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        room_types = response.data['room_types']
        self.assertEqual(len(room_types), 2)
        self.assertEqual(room_types[0]['code'], 'STD')
        self.assertEqual(room_types[1]['code'], 'DLX')
    
    def test_multiple_offers_returned(self):
        """Test multiple offers are returned."""
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        offers = response.data['offers']
        self.assertGreaterEqual(len(offers), 1)
        self.assertEqual(offers[0]['title'], 'Weekend Special')
    
    def test_multiple_leisure_activities_returned(self):
        """Test multiple leisure activities are returned."""
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        activities = response.data['leisure_activities']
        self.assertEqual(len(activities), 2)
        self.assertEqual(activities[0]['name'], 'Indoor Pool')
        self.assertEqual(activities[1]['name'], 'Restaurant')


class SecurityTests(TestCase):
    """Test security: no sensitive fields exposed."""
    
    def setUp(self):
        self.client = APIClient()
        
        self.hotel = Hotel.objects.create(
            name='Security Test Hotel',
            slug='security-test-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
    
    def test_no_sensitive_ids_leaked(self):
        """Test that internal IDs are not in response."""
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        data = response.data
        # Should not have database ID
        self.assertNotIn('id', data)
    
    def test_no_internal_config_exposed(self):
        """Test that internal config is not exposed."""
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        data = response.data
        # Should not have access config fields
        self.assertNotIn('access_config', data)
        self.assertNotIn('guest_portal_enabled', data)
        self.assertNotIn('staff_portal_enabled', data)


class EdgeCaseTests(TestCase):
    """Test edge cases for the public API."""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_hotel_with_no_booking_options(self):
        """Test hotel without booking_options."""
        hotel = Hotel.objects.create(
            name='No Options Hotel',
            slug='no-options-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
        
        response = self.client.get(
            f'/api/hotel/public/page/{hotel.slug}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data.get('booking_options'))
    
    def test_hotel_with_no_room_types(self):
        """Test hotel with no room types."""
        hotel = Hotel.objects.create(
            name='No Rooms Hotel',
            slug='no-rooms-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
        
        response = self.client.get(
            f'/api/hotel/public/page/{hotel.slug}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['room_types']), 0)
    
    def test_hotel_with_no_offers(self):
        """Test hotel with no offers."""
        hotel = Hotel.objects.create(
            name='No Offers Hotel',
            slug='no-offers-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
        
        response = self.client.get(
            f'/api/hotel/public/page/{hotel.slug}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['offers']), 0)
    
    def test_hotel_with_no_leisure_activities(self):
        """Test hotel with no leisure activities."""
        hotel = Hotel.objects.create(
            name='No Activities Hotel',
            slug='no-activities-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
        
        response = self.client.get(
            f'/api/hotel/public/page/{hotel.slug}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['leisure_activities']), 0)
    
    def test_hotel_with_all_optional_fields_blank(self):
        """Test hotel with all optional fields blank."""
        hotel = Hotel.objects.create(
            name='Minimal Hotel',
            slug='minimal-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
        
        response = self.client.get(
            f'/api/hotel/public/page/{hotel.slug}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Minimal Hotel')


class ActiveItemsFilteringTests(TestCase):
    """Test that only active items are included in nested lists."""
    
    def setUp(self):
        self.client = APIClient()
        
        self.hotel = Hotel.objects.create(
            name='Filter Test Hotel',
            slug='filter-test-hotel',
            city='Dublin',
            country='Ireland',
            is_active=True
        )
    
    def test_only_active_room_types_included(self):
        """Test only active room types are in response."""
        RoomType.objects.create(
            hotel=self.hotel,
            code='ACTIVE',
            name='Active Room',
            is_active=True
        )
        RoomType.objects.create(
            hotel=self.hotel,
            code='INACTIVE',
            name='Inactive Room',
            is_active=False
        )
        
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        room_types = response.data['room_types']
        self.assertEqual(len(room_types), 1)
        self.assertEqual(room_types[0]['code'], 'ACTIVE')
    
    def test_only_active_offers_included(self):
        """Test only active offers are in response."""
        today = date.today()
        Offer.objects.create(
            hotel=self.hotel,
            title='Active Offer',
            valid_from=today,
            valid_to=today + timedelta(days=30),
            is_active=True
        )
        Offer.objects.create(
            hotel=self.hotel,
            title='Inactive Offer',
            valid_from=today,
            valid_to=today + timedelta(days=30),
            is_active=False
        )
        
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        offers = response.data['offers']
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]['title'], 'Active Offer')
    
    def test_only_active_leisure_activities_included(self):
        """Test only active leisure activities are in response."""
        LeisureActivity.objects.create(
            hotel=self.hotel,
            name='Active Pool',
            category='WELLNESS',
            is_active=True
        )
        LeisureActivity.objects.create(
            hotel=self.hotel,
            name='Inactive Gym',
            category='SPORTS',
            is_active=False
        )
        
        response = self.client.get(
            f'/api/hotel/public/page/{self.hotel.slug}/'
        )
        
        activities = response.data['leisure_activities']
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0]['name'], 'Active Pool')
