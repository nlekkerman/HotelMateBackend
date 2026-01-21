#!/usr/bin/env python
"""
Comprehensive tests for booking approval expiry enforcement.
Tests the exact requirements from PART A and PART D of the specification.
"""
import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
sys.path.append('.')
django.setup()

from hotel.models import RoomBooking, Hotel
from staff.models import Staff, Role
from rooms.models import RoomType
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


def get_or_create_test_data():
    """Helper to get or create all required test data with proper fields."""
    # Hotel
    hotel, created = Hotel.objects.get_or_create(
        slug="test-hotel",
        defaults={
            'name': "Test Hotel",
            'city': "Test City", 
            'country': "Test Country"
        }
    )
    
    # Room Type with all required fields
    room_type, created = RoomType.objects.get_or_create(
        hotel=hotel,
        name="Standard Room",
        defaults={
            'max_occupancy': 2,
            'starting_price_from': 100.00,
            'currency': 'USD',
            'sort_order': 0,
            'is_active': True
        }
    )
    
    # User
    user, created = User.objects.get_or_create(
        username="teststaff",
        defaults={'email': "test@example.com"}
    )
    
    # Role (handle if doesn't exist)
    try:
        role, created = Role.objects.get_or_create(
            name="Reception",
            defaults={'slug': 'reception'}
        )
    except Exception:
        role = None
    
    # Staff
    staff, created = Staff.objects.get_or_create(
        user=user,
        hotel=hotel,
        defaults={
            'first_name': "Test",
            'last_name': "Staff",
            'role': role
        }
    )
    
    return hotel, room_type, user, staff


def create_booking_with_all_fields(hotel, room_type, **overrides):
    """Helper to create booking with all required fields."""
    defaults = {
        'hotel': hotel,
        'room_type': room_type,
        'booking_id': f'BK-{int(timezone.now().timestamp())}',
        'confirmation_number': f'TES-2026-{int(timezone.now().timestamp())%10000:04d}',
        'check_in': timezone.now().date(),
        'check_out': (timezone.now() + timedelta(days=1)).date(),
        'adults': 2,
        'children': 0,
        'total_amount': 100.00,
        'currency': 'USD',
        'status': 'PENDING_APPROVAL',
        'booker_type': 'SELF',
        'primary_first_name': 'Test',
        'primary_last_name': 'User',
        'primary_email': 'test@example.com',
        'assignment_version': 0,
    }
    defaults.update(overrides)
    return RoomBooking.objects.create(**defaults)


def test_expired_booking_block():
    """Test that expired bookings cannot be approved."""
    print("🧪 Testing expired booking block...")
    
    try:
        hotel, room_type, user, staff = get_or_create_test_data()
        
        # Create expired booking
        booking = create_booking_with_all_fields(
            hotel, room_type,
            status='EXPIRED',
            expired_at=timezone.now() - timedelta(minutes=10),
            auto_expire_reason_code='APPROVAL_TIMEOUT',
            payment_provider='stripe',
            paid_at=timezone.now() - timedelta(minutes=30),
        )
        
        # Create API client
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Attempt to approve expired booking
        response = client.post(
            f'/api/staff/hotel/{hotel.slug}/room-bookings/{booking.booking_id}/approve/'
        )
        
        # Verify response
        if response.status_code == status.HTTP_409_CONFLICT:
            print("✅ PASSED: Expired booking correctly blocked with HTTP 409")
            print(f"   Error message: {response.data.get('error', 'N/A')}")
        else:
            print(f"❌ FAILED: Expected HTTP 409, got {response.status_code}")
            print(f"   Response: {response.data}")
            booking.delete()
            return False
            
        # Verify booking remains expired
        booking.refresh_from_db()
        if booking.status == 'EXPIRED':
            print("✅ PASSED: Booking status remained EXPIRED")
        else:
            print(f"❌ FAILED: Booking status changed to {booking.status}")
            booking.delete()
            return False
            
        # Clean up
        booking.delete()
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED with exception: {e}")
        return False


def test_critical_but_not_expired_approval():
    """Test that CRITICAL (overdue) but not expired bookings can still be approved."""
    print("\n🧪 Testing CRITICAL approval window...")
    
    try:
        hotel, room_type, user, staff = get_or_create_test_data()
        
        # Create booking that would be CRITICAL risk level but not expired
        past_deadline = timezone.now() - timedelta(minutes=90)  # > 60 min overdue = CRITICAL
        booking = create_booking_with_all_fields(
            hotel, room_type,
            status='PENDING_APPROVAL',
            approval_deadline_at=past_deadline,
            expired_at=None,  # Not yet expired by job
            payment_provider='stripe',
            paid_at=timezone.now() - timedelta(minutes=95),
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Attempt to approve critical booking
        response = client.post(
            f'/api/staff/hotel/{hotel.slug}/room-bookings/{booking.booking_id}/approve/'
        )
        
        # Verify response
        if response.status_code == status.HTTP_200_OK:
            print("✅ PASSED: CRITICAL booking correctly approved (CRITICAL is warning, not block)")
            print(f"   Response status: {response.data.get('status', 'N/A')}")
        else:
            print(f"❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"   Response: {response.data}")
            booking.delete()
            return False
            
        # Verify booking was confirmed
        booking.refresh_from_db()
        if booking.status == 'CONFIRMED':
            print("✅ PASSED: Booking status changed to CONFIRMED")
        else:
            print(f"❌ FAILED: Expected CONFIRMED, got {booking.status}")
            booking.delete()
            return False
            
        # Clean up
        booking.delete()
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED with exception: {e}")
        return False


def test_staff_seen_functionality():
    """Test staff seen flag functionality."""
    print("\n🧪 Testing staff seen functionality...")
    
    try:
        hotel, room_type, user, staff = get_or_create_test_data()
        
        # Create new booking (not seen)
        booking = create_booking_with_all_fields(
            hotel, room_type,
            primary_first_name='Mark',
            primary_last_name='Seen',
            primary_email='mark@example.com',
        )
        
        # Verify initially not seen
        if booking.staff_seen_at is None and booking.staff_seen_by is None:
            print("✅ PASSED: Booking initially not seen")
        else:
            print("❌ FAILED: Booking should not be seen initially")
            booking.delete()
            return False
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Mark as seen
        response = client.post(
            f'/api/staff/hotel/{hotel.slug}/room-bookings/{booking.booking_id}/mark-seen/'
        )
        
        if response.status_code == status.HTTP_200_OK:
            print("✅ PASSED: Mark-seen endpoint responded successfully")
            if response.data.get('is_new_for_staff') == False:
                print("✅ PASSED: Response correctly shows is_new_for_staff = False")
            else:
                print("❌ FAILED: is_new_for_staff should be False after marking seen")
        else:
            print(f"❌ FAILED: Mark-seen failed with {response.status_code}")
            print(f"   Response: {response.data}")
            booking.delete()
            return False
        
        # Verify booking was marked as seen
        booking.refresh_from_db()
        if booking.staff_seen_at is not None and booking.staff_seen_by is not None:
            print("✅ PASSED: Booking marked as seen in database")
        else:
            print("❌ FAILED: Booking not marked as seen in database")
            booking.delete()
            return False
        
        # Test idempotency - mark seen again
        original_seen_at = booking.staff_seen_at
        response = client.post(
            f'/api/staff/hotel/{hotel.slug}/room-bookings/{booking.booking_id}/mark-seen/'
        )
        
        booking.refresh_from_db()
        if booking.staff_seen_at == original_seen_at:
            print("✅ PASSED: Mark-seen is idempotent (preserves original timestamp)")
        else:
            print("❌ FAILED: Mark-seen should be idempotent")
            booking.delete()
            return False
        
        # Clean up
        booking.delete()
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED with exception: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting booking approval expiry enforcement tests...\n")
    
    try:
        # Run tests
        test1_passed = test_expired_booking_block()
        test2_passed = test_critical_but_not_expired_approval()
        test3_passed = test_staff_seen_functionality()
        
        # Summary
        passed_count = sum([test1_passed, test2_passed, test3_passed])
        total_count = 3
        
        print(f"\n📊 Test Summary: {passed_count}/{total_count} tests passed")
        
        if passed_count == total_count:
            print("🎉 ALL TESTS PASSED - Backend enforcement correctly implemented!")
        else:
            print("💥 Some tests failed - check implementation")
            
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()