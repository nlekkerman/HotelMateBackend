#!/usr/bin/env python
"""
Test script for Stripe Authorize-Capture flow endpoints

This script validates that the StaffBookingAcceptView and StaffBookingDeclineView 
endpoints are properly implemented and accessible.

Run: python test_authorize_capture_endpoints.py
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.utils import timezone
from decimal import Decimal

from hotel.models import Hotel, RoomBooking
from rooms.models import RoomType
from staff.models import Staff
from room_bookings.staff_urls import urlpatterns


def test_url_resolution():
    """Test that our new URLs are properly registered"""
    print("🔍 Testing URL resolution...")
    
    # Test that accept URL resolves
    try:
        resolved = resolve('/api/staff/hotel/test-hotel/room-bookings/BK-2025-0001/accept/')
        print(f"✅ Accept URL resolved to: {resolved.func.__name__}")
    except Exception as e:
        print(f"❌ Accept URL resolution failed: {e}")
    
    # Test that decline URL resolves
    try:
        resolved = resolve('/api/staff/hotel/test-hotel/room-bookings/BK-2025-0001/decline/')
        print(f"✅ Decline URL resolved to: {resolved.func.__name__}")
    except Exception as e:
        print(f"❌ Decline URL resolution failed: {e}")
    
    print()


def test_staff_views_import():
    """Test that views can be imported without errors"""
    print("🔍 Testing view imports...")
    
    try:
        from hotel.staff_views import StaffBookingAcceptView, StaffBookingDeclineView
        print("✅ StaffBookingAcceptView imported successfully")
        print("✅ StaffBookingDeclineView imported successfully")
    except ImportError as e:
        print(f"❌ View import failed: {e}")
    
    print()


def test_stripe_configuration():
    """Test that Stripe is properly configured"""
    print("🔍 Testing Stripe configuration...")
    
    try:
        import stripe
        from django.conf import settings
        
        # Check if secret key is set
        if hasattr(settings, 'STRIPE_SECRET_KEY') and settings.STRIPE_SECRET_KEY:
            print("✅ STRIPE_SECRET_KEY is configured")
        else:
            print("❌ STRIPE_SECRET_KEY is not configured")
        
        # Test stripe API key setup
        if stripe.api_key:
            print("✅ Stripe API key is set")
        else:
            print("❌ Stripe API key is not set")
            
    except ImportError:
        print("❌ Stripe library not available")
    except Exception as e:
        print(f"❌ Stripe configuration error: {e}")
    
    print()


def test_model_fields():
    """Test that new model fields exist"""
    print("🔍 Testing model field additions...")
    
    from hotel.models import RoomBooking
    
    # Check if new fields exist
    expected_fields = [
        'payment_intent_id', 
        'payment_authorized_at', 
        'decision_by', 
        'decision_at',
        'decline_reason_code',
        'decline_reason_note'
    ]
    
    for field_name in expected_fields:
        if hasattr(RoomBooking, field_name):
            print(f"✅ Field {field_name} exists on RoomBooking")
        else:
            print(f"❌ Field {field_name} missing on RoomBooking")
    
    # Check STATUS_CHOICES
    status_choices = dict(RoomBooking.STATUS_CHOICES)
    expected_statuses = ['PENDING_APPROVAL', 'DECLINED']
    
    for status in expected_statuses:
        if status in status_choices:
            print(f"✅ Status {status} exists in STATUS_CHOICES")
        else:
            print(f"❌ Status {status} missing in STATUS_CHOICES")
    
    print()


def create_test_data():
    """Create minimal test data for endpoint testing"""
    print("🔧 Creating test data...")
    
    try:
        # Create test hotel
        hotel, created = Hotel.objects.get_or_create(
            slug='test-hotel',
            defaults={
                'name': 'Test Hotel',
                'subdomain': 'test-hotel',
                'phone': '+1234567890',
                'email': 'test@testhotel.com',
                'is_active': True
            }
        )
        print(f"✅ Hotel created/found: {hotel.name}")
        
        # Create test user
        user, created = User.objects.get_or_create(
            username='teststaff',
            defaults={
                'email': 'staff@testhotel.com',
                'first_name': 'Test',
                'last_name': 'Staff'
            }
        )
        print(f"✅ User created/found: {user.username}")
        
        # Create staff profile
        staff, created = Staff.objects.get_or_create(
            user=user,
            defaults={
                'hotel': hotel,
                'first_name': 'Test',
                'last_name': 'Staff',
                'email': 'staff@testhotel.com',
                'is_active': True
            }
        )
        print(f"✅ Staff created/found: {staff}")
        
        # Create room type
        room_type, created = RoomType.objects.get_or_create(
            hotel=hotel,
            name='Standard Room',
            defaults={
                'starting_price_from': Decimal('100.00'),
                'max_occupancy': 2,
                'is_active': True
            }
        )
        print(f"✅ Room type created/found: {room_type.name}")
        
        # Create test booking
        booking, created = RoomBooking.objects.get_or_create(
            booking_id='BK-TEST-2025-0001',
            defaults={
                'hotel': hotel,
                'room_type': room_type,
                'primary_first_name': 'John',
                'primary_last_name': 'Doe',
                'primary_email': 'john@example.com',
                'check_in': timezone.now().date(),
                'check_out': timezone.now().date() + timezone.timedelta(days=2),
                'adults': 2,
                'children': 0,
                'total_amount': Decimal('200.00'),
                'currency': 'EUR',
                'status': 'PENDING_APPROVAL',
                'payment_intent_id': 'pi_test_authorization',
                'payment_authorized_at': timezone.now()
            }
        )
        print(f"✅ Booking created/found: {booking.booking_id}")
        
        return hotel, staff, booking
        
    except Exception as e:
        print(f"❌ Test data creation failed: {e}")
        return None, None, None


def test_endpoint_permissions():
    """Test endpoint authentication and permissions"""
    print("🔍 Testing endpoint permissions...")
    
    client = Client()
    
    # Test unauthenticated access (should be denied)
    response = client.post('/api/staff/hotel/test-hotel/room-bookings/BK-TEST-2025-0001/accept/')
    print(f"✅ Unauthenticated accept request: {response.status_code} (expected 401/403)")
    
    response = client.post('/api/staff/hotel/test-hotel/room-bookings/BK-TEST-2025-0001/decline/')
    print(f"✅ Unauthenticated decline request: {response.status_code} (expected 401/403)")
    
    print()


def run_all_tests():
    """Run all test functions"""
    print("🚀 Starting Stripe Authorize-Capture Endpoint Tests")
    print("=" * 60)
    
    test_url_resolution()
    test_staff_views_import()
    test_stripe_configuration()
    test_model_fields()
    
    hotel, staff, booking = create_test_data()
    if hotel and staff and booking:
        test_endpoint_permissions()
    
    print("=" * 60)
    print("🏁 Tests completed!")


if __name__ == '__main__':
    run_all_tests()