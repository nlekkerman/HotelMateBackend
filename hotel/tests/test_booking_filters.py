"""
Unit tests for the modern booking list filtering system.

Tests all filtering capabilities, timezone handling, error handling, and security.
"""
from datetime import date, datetime, time
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
import pytz

from hotel.models import Hotel, RoomBooking, HotelAccessConfig
from hotel.filters.room_booking_filters import (
    StaffRoomBookingFilter, validate_ordering, get_allowed_orderings
)
from hotel.utils.hotel_time import (
    hotel_today, hotel_day_range_utc, hotel_date_range_utc,
    hotel_checkout_deadline_utc, is_overdue_checkout
)
from rooms.models import RoomType, Room
from staff.models import Staff


class HotelTimeUtilsTest(TestCase):
    """Test timezone-aware hotel time utilities."""
    
    def setUp(self):
        self.hotel_est = Hotel.objects.create(
            name="EST Hotel",
            slug="est-hotel",
            timezone="America/New_York"
        )
        self.hotel_utc = Hotel.objects.create(
            name="UTC Hotel", 
            slug="utc-hotel",
            timezone="UTC"
        )
    
    @patch('django.utils.timezone.now')
    def test_hotel_today_different_timezones(self, mock_now):
        """Test hotel_today returns correct date in different timezones."""
        # Mock UTC time as 2026-01-28 04:00 UTC (before midnight in EST, after midnight in UTC)
        mock_now.return_value = datetime(2026, 1, 28, 4, 0, 0, tzinfo=pytz.UTC)
        
        # EST hotel should be 2026-01-27 (23:00 EST)
        est_today = hotel_today(self.hotel_est)
        self.assertEqual(est_today, date(2026, 1, 27))
        
        # UTC hotel should be 2026-01-28 (04:00 UTC)
        utc_today = hotel_today(self.hotel_utc)
        self.assertEqual(utc_today, date(2026, 1, 28))
    
    def test_hotel_day_range_utc(self):
        """Test conversion of hotel date to UTC datetime range."""
        target_date = date(2026, 1, 28)
        
        start_utc, end_utc = hotel_day_range_utc(self.hotel_est, target_date)
        
        # EST hotel: 2026-01-28 00:00 EST = 2026-01-28 05:00 UTC
        # EST hotel: 2026-01-28 23:59 EST = 2026-01-29 04:59 UTC
        self.assertEqual(start_utc.replace(second=0, microsecond=0), 
                        datetime(2026, 1, 28, 5, 0, 0, tzinfo=pytz.UTC))
        self.assertEqual(end_utc.replace(second=59, microsecond=999999),
                        datetime(2026, 1, 29, 4, 59, 59, 999999, tzinfo=pytz.UTC))
    
    def test_hotel_date_range_utc(self):
        """Test conversion of hotel date range to UTC datetime range."""
        date_from = date(2026, 1, 28)
        date_to = date(2026, 1, 30)
        
        start_utc, end_utc = hotel_date_range_utc(self.hotel_est, date_from, date_to)
        
        # Should span from start of first day to end of last day
        self.assertEqual(start_utc.replace(second=0, microsecond=0),
                        datetime(2026, 1, 28, 5, 0, 0, tzinfo=pytz.UTC))
        self.assertEqual(end_utc.replace(second=59, microsecond=999999),
                        datetime(2026, 1, 31, 4, 59, 59, 999999, tzinfo=pytz.UTC))
    
    def test_hotel_checkout_deadline_utc(self):
        """Test checkout deadline calculation."""
        # Set hotel checkout time to 11:00 AM
        config = HotelAccessConfig.objects.create(
            hotel=self.hotel_est,
            standard_checkout_time=time(11, 0)
        )
        
        checkout_date = date(2026, 1, 28)
        deadline_utc = hotel_checkout_deadline_utc(self.hotel_est, checkout_date)
        
        # 11:00 AM EST = 4:00 PM UTC
        expected = datetime(2026, 1, 28, 16, 0, 0, tzinfo=pytz.UTC)
        self.assertEqual(deadline_utc, expected)
    
    @patch('django.utils.timezone.now')
    def test_is_overdue_checkout(self, mock_now):
        """Test overdue checkout detection."""
        # Mock current time as 2026-01-28 17:00 UTC (12:00 PM EST)
        mock_now.return_value = datetime(2026, 1, 28, 17, 0, 0, tzinfo=pytz.UTC)
        
        checkout_date = date(2026, 1, 28)
        
        # Should be overdue (deadline was 11:00 AM EST = 16:00 UTC)
        self.assertTrue(is_overdue_checkout(self.hotel_est, checkout_date, None))
        
        # Should not be overdue if already checked out
        checked_out_time = datetime(2026, 1, 28, 15, 0, 0, tzinfo=pytz.UTC)
        self.assertFalse(is_overdue_checkout(self.hotel_est, checkout_date, checked_out_time))


class StaffRoomBookingFilterTest(TestCase):
    """Test the centralized FilterSet for comprehensive filtering."""
    
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel", 
            timezone="America/New_York"
        )
        
        self.room_type_deluxe = RoomType.objects.create(
            hotel=self.hotel,
            name="Deluxe Room",
            code="DELUXE"
        )
        
        self.room_101 = Room.objects.create(
            hotel=self.hotel,
            room_number="101",
            room_type=self.room_type_deluxe
        )
        
        # Create test bookings with different statuses and dates
        self.booking_confirmed = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type_deluxe,
            check_in=date(2026, 1, 28),
            check_out=date(2026, 1, 30),
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            adults=2,
            children=1,
            total_amount=Decimal("150.00"),
            status="CONFIRMED"
        )
        
        self.booking_in_house = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type_deluxe,
            assigned_room=self.room_101,
            check_in=date(2026, 1, 27),
            check_out=date(2026, 1, 29),
            primary_first_name="Jane",
            primary_last_name="Smith",
            primary_email="jane@example.com",
            adults=1,
            children=0,
            total_amount=Decimal("200.00"),
            status="IN_HOUSE",
            checked_in_at=timezone.now() - timezone.timedelta(days=1)
        )
        
        self.booking_cancelled = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type_deluxe,
            check_in=date(2026, 1, 25),
            check_out=date(2026, 1, 27),
            primary_first_name="Bob",
            primary_last_name="Wilson",
            primary_email="bob@example.com",
            adults=2,
            children=0,
            total_amount=Decimal("100.00"),
            status="CANCELLED"
        )
        
    def test_bucket_filter_arrivals(self):
        """Test arrivals bucket filtering."""
        data = {
            'bucket': 'arrivals',
            'date_from': '2026-01-28',
            'date_to': '2026-01-28'
        }
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().booking_id, self.booking_confirmed.booking_id)
    
    def test_bucket_filter_in_house(self):
        """Test in-house bucket filtering."""
        data = {'bucket': 'in_house'}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().booking_id, self.booking_in_house.booking_id)
    
    def test_bucket_filter_cancelled(self):
        """Test cancelled bucket filtering."""
        data = {'bucket': 'cancelled'}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().booking_id, self.booking_cancelled.booking_id)
    
    def test_text_search_filter(self):
        """Test comprehensive text search."""
        data = {'q': 'john'}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().primary_first_name, "John")
    
    def test_room_type_filter_by_code(self):
        """Test room type filtering by code."""
        data = {'room_type': 'DELUXE'}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 3)  # All test bookings are deluxe
    
    def test_room_type_filter_hotel_scoped(self):
        """Test room type filtering is hotel-scoped."""
        # Create another hotel with same room type code
        other_hotel = Hotel.objects.create(name="Other Hotel", slug="other-hotel")
        other_room_type = RoomType.objects.create(
            hotel=other_hotel,
            name="Other Deluxe",
            code="DELUXE"
        )
        
        data = {'room_type': 'DELUXE'}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        # Should only return bookings for this hotel's room type
        self.assertEqual(results.count(), 3)
        for booking in results:
            self.assertEqual(booking.hotel, self.hotel)
    
    def test_invalid_room_type_filter(self):
        """Test invalid room type returns empty queryset."""
        data = {'room_type': 'NONEXISTENT'}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 0)
    
    def test_party_size_filters(self):
        """Test party size filtering."""
        # Test minimum party size
        data = {'party_size_min': 3}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 1)  # Only booking_confirmed has 3 people (2+1)
        
        # Test maximum party size
        data = {'party_size_max': 1}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 1)  # Only booking_in_house has 1 person
    
    def test_adults_children_filters(self):
        """Test individual adults/children filtering."""
        data = {'adults': 1}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 1)  # Only booking_in_house
        
        data = {'children': 1}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 1)  # Only booking_confirmed
    
    def test_assigned_room_filter(self):
        """Test room assignment filtering."""
        data = {'assigned': True}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 1)  # Only booking_in_house has assigned room
        
        data = {'assigned': False}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 2)  # booking_confirmed and booking_cancelled
    
    def test_status_list_filter(self):
        """Test comma-separated status list filtering."""
        data = {'status': 'CONFIRMED,IN_HOUSE'}
        
        filter_obj = StaffRoomBookingFilter(
            data=data,
            queryset=RoomBooking.objects.filter(hotel=self.hotel),
            hotel=self.hotel
        )
        
        results = filter_obj.qs
        self.assertEqual(results.count(), 2)  # CONFIRMED and IN_HOUSE bookings
        
        statuses = [b.status for b in results]
        self.assertIn('CONFIRMED', statuses)
        self.assertIn('IN_HOUSE', statuses)
    
    def test_bucket_counts_consistency(self):
        """Test bucket counts match filtered logic."""
        base_queryset = RoomBooking.objects.filter(hotel=self.hotel)
        
        filter_obj = StaffRoomBookingFilter(
            data={},
            queryset=base_queryset,
            hotel=self.hotel
        )
        
        counts = filter_obj.get_bucket_counts(base_queryset)
        
        # Verify some expected counts
        self.assertEqual(counts['cancelled'], 1)
        self.assertEqual(counts['in_house'], 1)
        self.assertGreaterEqual(counts['arrivals'], 0)


class OrderingValidationTest(TestCase):
    """Test ordering parameter validation."""
    
    def test_valid_ordering(self):
        """Test valid ordering parameters."""
        allowed = get_allowed_orderings()
        
        for ordering in allowed:
            try:
                result = validate_ordering(ordering, allowed)
                self.assertEqual(result, ordering)
            except ValueError:
                self.fail(f"Valid ordering '{ordering}' raised ValueError")
    
    def test_invalid_ordering(self):
        """Test invalid ordering parameters raise ValueError."""
        allowed = get_allowed_orderings()
        
        invalid_orderings = [
            'invalid_field',
            'booking_id__malicious',
            '-nonexistent',
            'DROP TABLE;',
            ''
        ]
        
        for ordering in invalid_orderings:
            with self.assertRaises(ValueError):
                validate_ordering(ordering, allowed)
    
    def test_allowed_orderings_list(self):
        """Test allowed orderings list contains expected options."""
        allowed = get_allowed_orderings()
        
        expected_fields = [
            'check_in', '-check_in',
            'check_out', '-check_out',
            'created_at', '-created_at',
            'updated_at', '-updated_at',
            'booking_id', '-booking_id',
            'status', '-status',
            'total_amount', '-total_amount'
        ]
        
        for field in expected_fields:
            self.assertIn(field, allowed)


class StaffBookingListAPITest(APITestCase):
    """Integration tests for the staff booking list API endpoint."""
    
    def setUp(self):
        # Create test user and staff profile
        self.user = User.objects.create_user(
            username='staff@hotel.com',
            email='staff@hotel.com',
            password='testpass123'
        )
        
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            timezone="UTC"
        )
        
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            role="MANAGER"
        )
        
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            code="STD"
        )
        
        # Create test booking
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=date(2026, 1, 28),
            check_out=date(2026, 1, 30),
            primary_first_name="Test",
            primary_last_name="Guest",
            primary_email="test@example.com",
            adults=2,
            children=0,
            total_amount=Decimal("100.00"),
            status="CONFIRMED"
        )
    
    def test_endpoint_requires_authentication(self):
        """Test endpoint requires authentication."""
        url = f'/api/staff/hotel/{self.hotel.slug}/room-bookings/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_endpoint_requires_hotel_scope(self):
        """Test endpoint enforces hotel scoping."""
        # Create another hotel and try to access its bookings
        other_hotel = Hotel.objects.create(name="Other Hotel", slug="other-hotel")
        
        self.client.force_authenticate(user=self.user)
        url = f'/api/staff/hotel/{other_hotel.slug}/room-bookings/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_successful_filtering(self):
        """Test successful filtering with valid parameters."""
        self.client.force_authenticate(user=self.user)
        url = f'/api/staff/hotel/{self.hotel.slug}/room-bookings/'
        
        # Test basic request
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('bucket_counts', response.data)
        
        # Test with filters
        response = self.client.get(url, {
            'q': 'Test',
            'status': 'CONFIRMED',
            'adults': '2'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_invalid_filter_parameters(self):
        """Test error handling for invalid filter parameters."""
        self.client.force_authenticate(user=self.user)
        url = f'/api/staff/hotel/{self.hotel.slug}/room-bookings/'
        
        # Test invalid date format
        response = self.client.get(url, {'date_from': 'invalid-date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'INVALID_FILTER_PARAMETERS')
    
    def test_invalid_ordering_parameter(self):
        """Test error handling for invalid ordering."""
        self.client.force_authenticate(user=self.user)
        url = f'/api/staff/hotel/{self.hotel.slug}/room-bookings/'
        
        response = self.client.get(url, {'ordering': 'invalid_field'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'INVALID_ORDERING')
    
    def test_response_format_consistency(self):
        """Test response format is consistent."""
        self.client.force_authenticate(user=self.user)
        url = f'/api/staff/hotel/{self.hotel.slug}/room-bookings/'
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check required response fields
        required_fields = ['count', 'results', 'bucket_counts']
        for field in required_fields:
            self.assertIn(field, response.data)
        
        # Check bucket_counts structure
        bucket_counts = response.data['bucket_counts']
        expected_buckets = [
            'arrivals', 'in_house', 'departures', 'pending',
            'checked_out', 'cancelled', 'expired', 'no_show', 'overdue_checkout'
        ]
        for bucket in expected_buckets:
            self.assertIn(bucket, bucket_counts)
            self.assertIsInstance(bucket_counts[bucket], int)