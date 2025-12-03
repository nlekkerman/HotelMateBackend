#!/usr/bin/env python
"""
Django test to verify section creation fix
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff.models import Staff
from hotel.models import PublicSection, HeroSection, GalleryContainer, ListContainer, NewsItem, RoomsSection, Hotel
from hotel.serializers import PublicSectionDetailSerializer

class SectionCreationTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create a test user
        User = get_user_model()
        self.user = User.objects.create_user(
            username='teststaff',
            password='testpass123',
            email='test@test.com'
        )
        
        # Create a test hotel
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel'
        )
        
        # Create staff profile with super_staff_admin permissions
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            first_name='Test',
            last_name='Staff',
            access_level='super_staff_admin'
        )
        
        # Login the client
        self.client.login(username='teststaff', password='testpass123')

    def test_list_section_creation(self):
        """Test that creating a list section works correctly"""
        print("🧪 Testing list section creation...")
        
        # Test data - matches the original frontend payload
        section_data = {
            'section_type': 'list',
            'name': 'Test List Section',
            'container_name': 'Test Container'
        }
        
        print(f"📤 Sending data: {section_data}")
        
        # Make the POST request
        response = self.client.post(
            '/api/staff/sections/',
            data=json.dumps(section_data),
            content_type='application/json'
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response data: {response.json()}")
        
        # Check response
        self.assertEqual(response.status_code, 201, f"Expected 201, got {response.status_code}")
        
        response_data = response.json()
        
        # Verify the section was created
        self.assertIn('id', response_data)
        section_id = response_data['id']
        
        # Fetch the section and check its details
        section = PublicSection.objects.get(id=section_id)
        self.assertEqual(section.name, 'Test List Section')
        
        # Check that ListContainer was created
        list_container = ListContainer.objects.filter(public_section=section).first()
        self.assertIsNotNone(list_container, "ListContainer should be created for list section")
        self.assertEqual(list_container.name, 'Test Container')
        
        # Use the serializer to check section_type
        serializer = PublicSectionDetailSerializer(section)
        serialized_data = serializer.data
        
        print(f"📊 Serialized section data: {serialized_data}")
        
        # This is the key test - section_type should be 'list', not 'unknown'
        self.assertEqual(serialized_data['section_type'], 'list', 
                        f"Expected section_type 'list', got '{serialized_data['section_type']}'")
        
        print("✅ List section creation test passed!")

    def test_hero_section_creation(self):
        """Test that creating a hero section works correctly"""
        print("🧪 Testing hero section creation...")
        
        section_data = {
            'section_type': 'hero',
            'name': 'Test Hero Section'
        }
        
        print(f"📤 Sending data: {section_data}")
        
        response = self.client.post(
            '/api/staff/sections/',
            data=json.dumps(section_data),
            content_type='application/json'
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response data: {response.json()}")
        
        self.assertEqual(response.status_code, 201)
        
        response_data = response.json()
        section_id = response_data['id']
        
        # Check that HeroSection was created
        section = PublicSection.objects.get(id=section_id)
        hero_section = HeroSection.objects.filter(public_section=section).first()
        self.assertIsNotNone(hero_section, "HeroSection should be created for hero section")
        
        # Check section_type
        serializer = PublicSectionDetailSerializer(section)
        serialized_data = serializer.data
        self.assertEqual(serialized_data['section_type'], 'hero')
        
        print("✅ Hero section creation test passed!")

if __name__ == '__main__':
    # Run the specific test
    import unittest
    
    # Create a test suite with just our tests
    suite = unittest.TestSuite()
    suite.addTest(SectionCreationTestCase('test_list_section_creation'))
    suite.addTest(SectionCreationTestCase('test_hero_section_creation'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print results
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! Section creation fix is working correctly.")
    else:
        print(f"\n💥 {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for test, traceback in result.failures + result.errors:
            print(f"❌ {test}: {traceback}")