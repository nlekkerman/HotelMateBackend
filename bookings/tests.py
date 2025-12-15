from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.test import APITestCase
from rest_framework import status
from hotel.models import Hotel
from rooms.models import Room
from guests.models import Guest
from .models import (
    Restaurant, BookingSubcategory, BookingCategory, Booking
)
from .serializers import BookingCreateSerializer, BookingCategorySerializer


class MultiHotelIntegrityTestCase(TestCase):
    """Test Phase R1: Multi-hotel integrity and safe uniqueness constraints"""
    
    def setUp(self):
        # Create two hotels
        self.hotel1 = Hotel.objects.create(
            name="Hotel Alpha", 
            slug="alpha"
        )
        self.hotel2 = Hotel.objects.create(
            name="Hotel Beta", 
            slug="beta"
        )
        
        # Create rooms for each hotel
        self.room1 = Room.objects.create(
            hotel=self.hotel1,
            room_number=101
        )
        self.room2 = Room.objects.create(
            hotel=self.hotel2,
            room_number=101
        )
        
        # Create guests
        self.guest1 = Guest.objects.create(
            name="Guest Alpha",
            email="alpha@test.com"
        )
        self.guest2 = Guest.objects.create(
            name="Guest Beta",
            email="beta@test.com"
        )

    def test_same_slug_different_hotels_allowed(self):
        """Test that restaurants can have same slug in different hotels"""
        # Create restaurant with same slug in both hotels - should succeed
        restaurant1 = Restaurant.objects.create(
            name="Breakfast Café",
            slug="breakfast",
            hotel=self.hotel1
        )
        restaurant2 = Restaurant.objects.create(
            name="Breakfast Buffet", 
            slug="breakfast",
            hotel=self.hotel2
        )
        
        self.assertEqual(restaurant1.slug, restaurant2.slug)
        self.assertNotEqual(restaurant1.hotel, restaurant2.hotel)

    def test_same_slug_same_hotel_fails(self):
        """Test that restaurants cannot have same slug within same hotel"""
        Restaurant.objects.create(
            name="Breakfast Café",
            slug="breakfast",
            hotel=self.hotel1
        )
        
        # Second restaurant with same slug in same hotel should fail
        with self.assertRaises(IntegrityError):
            Restaurant.objects.create(
                name="Breakfast Buffet",
                slug="breakfast", 
                hotel=self.hotel1
            )

    def test_subcategory_same_slug_different_hotels_allowed(self):
        """Test that booking subcategories can have same slug in different hotels"""
        subcat1 = BookingSubcategory.objects.create(
            name="Dining",
            slug="dining",
            hotel=self.hotel1
        )
        subcat2 = BookingSubcategory.objects.create(
            name="Dining Service",
            slug="dining", 
            hotel=self.hotel2
        )
        
        self.assertEqual(subcat1.slug, subcat2.slug)
        self.assertNotEqual(subcat1.hotel, subcat2.hotel)

    def test_subcategory_same_slug_same_hotel_fails(self):
        """Test that booking subcategories cannot have same slug within same hotel"""
        BookingSubcategory.objects.create(
            name="Dining",
            slug="dining",
            hotel=self.hotel1
        )
        
        # Second subcategory with same slug in same hotel should fail
        with self.assertRaises(IntegrityError):
            BookingSubcategory.objects.create(
                name="Dining Service",
                slug="dining",
                hotel=self.hotel1
            )

    def test_booking_restaurant_different_hotel_fails(self):
        """Test that booking with restaurant from different hotel fails validation"""
        # Create restaurant in hotel1
        restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            slug="test-restaurant", 
            hotel=self.hotel1
        )
        
        # Create subcategory and category in hotel2
        subcategory = BookingSubcategory.objects.create(
            name="Test Subcategory",
            slug="test-subcat",
            hotel=self.hotel2
        )
        category = BookingCategory.objects.create(
            name="Test Category",
            subcategory=subcategory,
            hotel=self.hotel2
        )
        
        # Try to create booking in hotel2 with restaurant from hotel1
        booking = Booking(
            hotel=self.hotel2,
            category=category,
            restaurant=restaurant,  # Different hotel!
            date="2025-12-20"
        )
        
        with self.assertRaises(ValidationError) as cm:
            booking.full_clean()
        
        self.assertIn('restaurant', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['restaurant'][0],
            "Restaurant belongs to a different hotel."
        )

    def test_booking_category_different_hotel_fails(self):
        """Test that booking with category from different hotel fails validation"""
        # Create category in hotel1
        subcategory = BookingSubcategory.objects.create(
            name="Test Subcategory",
            slug="test-subcat",
            hotel=self.hotel1
        )
        category = BookingCategory.objects.create(
            name="Test Category", 
            subcategory=subcategory,
            hotel=self.hotel1
        )
        
        # Try to create booking in hotel2 with category from hotel1
        booking = Booking(
            hotel=self.hotel2,
            category=category,  # Different hotel!
            date="2025-12-20"
        )
        
        with self.assertRaises(ValidationError) as cm:
            booking.full_clean()
        
        self.assertIn('category', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['category'][0],
            "Category belongs to a different hotel."
        )

    def test_booking_room_different_hotel_fails(self):
        """Test that booking with room from different hotel fails validation"""
        # Create category in hotel1  
        subcategory = BookingSubcategory.objects.create(
            name="Test Subcategory",
            slug="test-subcat", 
            hotel=self.hotel1
        )
        category = BookingCategory.objects.create(
            name="Test Category",
            subcategory=subcategory,
            hotel=self.hotel1
        )
        
        # Try to create booking in hotel1 with room from hotel2
        booking = Booking(
            hotel=self.hotel1,
            category=category,
            room=self.room2,  # Different hotel!
            date="2025-12-20"
        )
        
        with self.assertRaises(ValidationError) as cm:
            booking.full_clean()
            
        self.assertIn('room', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['room'][0],
            "Room belongs to a different hotel."
        )

    def test_booking_subcategory_different_hotel_fails(self):
        """Test that booking fails when category.subcategory is from different hotel"""
        # Create subcategory in hotel1
        subcategory = BookingSubcategory.objects.create(
            name="Test Subcategory",
            slug="test-subcat",
            hotel=self.hotel1
        )
        
        # Create category in hotel2 but with subcategory from hotel1
        category = BookingCategory.objects.create(
            name="Test Category",
            subcategory=subcategory,  # From hotel1
            hotel=self.hotel2  # But category is in hotel2
        )
        
        # Try to create booking - should fail on subcategory hotel mismatch
        booking = Booking(
            hotel=self.hotel2,
            category=category, 
            date="2025-12-20"
        )
        
        with self.assertRaises(ValidationError) as cm:
            booking.full_clean()
            
        self.assertIn('subcategory', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['subcategory'][0],
            "Subcategory belongs to a different hotel."
        )

    def test_category_subcategory_hotel_mismatch_fails(self):
        """Test that BookingCategory with subcategory from different hotel fails"""
        # Create subcategory in hotel1
        subcategory = BookingSubcategory.objects.create(
            name="Test Subcategory",
            slug="test-subcat",
            hotel=self.hotel1
        )
        
        # Try to create category in hotel2 with subcategory from hotel1
        category = BookingCategory(
            name="Test Category",
            subcategory=subcategory,  # From hotel1
            hotel=self.hotel2  # But category is in hotel2
        )
        
        with self.assertRaises(ValidationError) as cm:
            category.full_clean()
            
        self.assertIn('hotel', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['hotel'][0],
            "Category hotel must match subcategory hotel."
        )


class MultiHotelSerializerTestCase(APITestCase):
    """Test that DRF serializers enforce cross-hotel validation"""
    
    def setUp(self):
        # Create two hotels
        self.hotel1 = Hotel.objects.create(
            name="Hotel Alpha",
            slug="alpha"
        )
        self.hotel2 = Hotel.objects.create(
            name="Hotel Beta", 
            slug="beta"
        )
        
        # Create subcategories and categories
        self.subcategory1 = BookingSubcategory.objects.create(
            name="Test Subcategory 1",
            slug="test-subcat-1",
            hotel=self.hotel1
        )
        self.subcategory2 = BookingSubcategory.objects.create(
            name="Test Subcategory 2", 
            slug="test-subcat-2",
            hotel=self.hotel2
        )
        
        self.category1 = BookingCategory.objects.create(
            name="Test Category 1",
            subcategory=self.subcategory1,
            hotel=self.hotel1
        )
        
        # Create restaurant in hotel1
        self.restaurant1 = Restaurant.objects.create(
            name="Test Restaurant",
            slug="test-restaurant",
            hotel=self.hotel1
        )

    def test_serializer_triggers_cross_hotel_validation(self):
        """Test that BookingCreateSerializer triggers model validation"""
        serializer = BookingCreateSerializer(data={
            'hotel': self.hotel2.id,
            'category': self.category1.id,  # From hotel1
            'restaurant': self.restaurant1.id,  # From hotel1  
            'date': '2025-12-20'
        })
        
        self.assertFalse(serializer.is_valid())
        # Should fail during create() when full_clean() is called

    def test_category_serializer_triggers_validation(self):
        """Test that BookingCategorySerializer triggers model validation"""
        serializer = BookingCategorySerializer(data={
            'name': 'Test Category',
            'subcategory': self.subcategory1.id,  # From hotel1
            'hotel': self.hotel2.id  # Different hotel
        })
        
        self.assertFalse(serializer.is_valid())
        # Should fail during create() when full_clean() is called
