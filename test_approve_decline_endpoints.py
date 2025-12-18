#!/usr/bin/env python
"""
Test script for the approve/decline booking endpoints.
This tests the business logic without making actual HTTP requests.
"""

import os
import sys
import django
from decimal import Decimal
import uuid
import time

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import Mock, patch, MagicMock

from hotel.models import Hotel, RoomBooking
from hotel.staff_views import StaffBookingAcceptView, StaffBookingDeclineView
from staff.models import Staff, Role, Department
from rooms.models import RoomType

User = get_user_model()

def cleanup_test_data():
    """Clean up any existing test data"""
    try:
        # Clean up test bookings
        RoomBooking.objects.filter(booking_id__startswith='BK-TEST-').delete()
        
        # Clean up test staff and users
        Staff.objects.filter(user__username__startswith='teststaff').delete()
        User.objects.filter(username__startswith='teststaff').delete()
        
        # Clean up test room types and hotels
        RoomType.objects.filter(hotel__slug__startswith='test-hotel').delete()
        Hotel.objects.filter(slug__startswith='test-hotel').delete()
        
        # Clean up test roles and departments (be careful with shared data)
        Role.objects.filter(name="Front Desk").delete()
        Department.objects.filter(name="Front Office").delete()
        
    except Exception as e:
        print(f"Note: Cleanup encountered: {e}")

def create_test_data():
    """Create test hotel, staff, and booking for testing"""
    
    # Generate unique identifiers
    test_id = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
    hotel_slug = f"test-hotel-{test_id}"
    
    # Create hotel
    hotel = Hotel.objects.create(
        name=f"Test Hotel {test_id}",
        slug=hotel_slug,
        city="Dublin", 
        country="Ireland",
        email=f"test{test_id}@testhotel.com",
        phone="+353123456789",
        is_active=True
    )
    
    # Create room type
    room_type = RoomType.objects.create(
        hotel=hotel,
        name="Standard Room",
        code="STD",
        short_description="A comfortable standard room",
        starting_price_from=Decimal('100.00'),
        max_occupancy=2,
        currency="EUR",
        is_active=True
    )
    
    # Create department and role
    department, _ = Department.objects.get_or_create(
        name="Front Office",
        defaults={'slug': 'front-office', 'description': 'Front desk operations'}
    )
    
    role, _ = Role.objects.get_or_create(
        name="Front Desk",
        defaults={'slug': 'front-desk', 'department': department, 'description': 'Front desk staff'}
    )
    
    # Create user and staff
    user = User.objects.create_user(
        username=f'teststaff{test_id}',
        email=f'staff{test_id}@testhotel.com',
        password='testpass123'
    )
    
    staff = Staff.objects.create(
        user=user,
        hotel=hotel,
        first_name="Test",
        last_name="Staff",
        department=department,
        role=role,
        is_active=True
    )
    
    # Create a booking ready for approval
    booking = RoomBooking.objects.create(
        hotel=hotel,
        room_type=room_type,
        booking_id=f"BK-TEST-{test_id}",
        confirmation_number=f"CONF-{test_id}", 
        check_in=timezone.now().date(),
        check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
        adults=2,
        children=0,
        total_amount=Decimal('200.00'),
        currency='EUR',
        status='PENDING_APPROVAL',  # Ready for staff approval
        payment_provider='stripe',
        payment_intent_id='pi_test_123456789',
        payment_reference='pi_test_123456789', 
        payment_authorized_at=timezone.now(),
        primary_first_name="John",
        primary_last_name="Doe",
        primary_email="john.doe@example.com",
        booker_email="john.doe@example.com"
    )
    
    return hotel, staff, booking, user

def test_approve_booking():
    """Test the approve booking endpoint"""
    print("🧪 Testing approve booking endpoint...")
    
    hotel, staff, booking, user = create_test_data()
    
    # Create request factory and mock request
    factory = RequestFactory()
    request = factory.post(f'/api/staff/hotel/{hotel.slug}/room-bookings/{booking.booking_id}/approve/')
    request.user = user
    
    # Mock Stripe payment capture
    with patch('stripe.PaymentIntent.capture') as mock_capture:
        mock_capture.return_value = Mock(
            status='succeeded',
            id='pi_test_123456789'
        )
        
        # Mock email service
        with patch('notifications.email_service.send_booking_confirmation_email') as mock_email:
            mock_email.return_value = True
            
            # Test the view
            view = StaffBookingAcceptView()
            view.request = request
            
            response = view.post(request, hotel.slug, booking.booking_id)
            
            print(f"✅ Response status: {response.status_code}")
            print(f"✅ Response data: {response.data}")
            
            # Verify booking was updated
            booking.refresh_from_db()
            print(f"✅ Booking status: {booking.status}")
            print(f"✅ Booking paid_at: {booking.paid_at}")
            
            # Verify Stripe was called
            assert mock_capture.called, "Stripe capture should have been called"
            print("✅ Stripe PaymentIntent.capture was called")
            
            # Verify email was attempted
            assert mock_email.called, "Email service should have been called"
            print("✅ Email service was called")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response.data['status'] == 'approved', f"Expected approved status"
            assert booking.status == 'CONFIRMED', f"Expected CONFIRMED status, got {booking.status}"
            
    print("✅ Approve booking test passed!\n")

def test_decline_booking():
    """Test the decline booking endpoint"""
    print("🧪 Testing decline booking endpoint...")
    
    hotel, staff, booking, user = create_test_data()
    
    # Create request factory and mock request
    factory = RequestFactory()
    request_data = {
        'reason_code': 'AVAILABILITY',
        'reason_note': 'Room no longer available for this date'
    }
    request = factory.post(
        f'/api/staff/hotel/{hotel.slug}/room-bookings/{booking.booking_id}/decline/', 
        data=request_data,
        content_type='application/json'
    )
    request.user = user
    request.data = request_data  # Add data attribute for DRF
    
    # Mock Stripe payment cancellation
    with patch('stripe.PaymentIntent.cancel') as mock_cancel:
        mock_cancel.return_value = Mock(
            status='canceled',
            id='pi_test_123456789'
        )
        
        # Mock email service
        with patch('notifications.email_service.send_booking_cancellation_email') as mock_email:
            mock_email.return_value = True
            
            # Test the view
            view = StaffBookingDeclineView()
            view.request = request
            
            response = view.post(request, hotel.slug, booking.booking_id)
            
            print(f"✅ Response status: {response.status_code}")
            print(f"✅ Response data: {response.data}")
            
            # Verify booking was updated
            booking.refresh_from_db()
            print(f"✅ Booking status: {booking.status}")
            print(f"✅ Booking decline reason: {booking.decline_reason_code}")
            
            # Verify Stripe was called
            assert mock_cancel.called, "Stripe cancel should have been called"
            print("✅ Stripe PaymentIntent.cancel was called")
            
            # Verify email was attempted
            assert mock_email.called, "Email service should have been called"
            print("✅ Email service was called")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response.data['status'] == 'declined', f"Expected declined status"
            assert booking.status == 'DECLINED', f"Expected DECLINED status, got {booking.status}"
            assert booking.decline_reason_code == 'AVAILABILITY', f"Expected reason code to be saved"
            
    print("✅ Decline booking test passed!\n")

def test_idempotency():
    """Test idempotency of the endpoints"""
    print("🧪 Testing idempotency...")
    
    # Generate a unique test ID for this specific test
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    hotel_slug = f"test-hotel-idempotent-{unique_id}"
    
    # Create fresh test data for idempotency test
    hotel = Hotel.objects.create(
        name=f"Test Hotel Idempotent {unique_id}",
        slug=hotel_slug,
        city="Dublin", 
        country="Ireland",
        email=f"test{unique_id}@testhotel.com",
        phone="+353123456789",
        is_active=True
    )
    
    room_type = RoomType.objects.create(
        hotel=hotel,
        name="Standard Room",
        code="STD",
        short_description="A comfortable standard room",
        starting_price_from=Decimal('100.00'),
        max_occupancy=2,
        currency="EUR",
        is_active=True
    )
    
    department, _ = Department.objects.get_or_create(
        name="Front Office",
        defaults={'slug': 'front-office', 'description': 'Front desk operations'}
    )
    
    role, _ = Role.objects.get_or_create(
        name="Front Desk",
        defaults={'slug': 'front-desk', 'department': department, 'description': 'Front desk staff'}
    )
    
    user = User.objects.create_user(
        username=f'teststaff{unique_id}',
        email=f'staff{unique_id}@testhotel.com',
        password='testpass123'
    )
    
    staff = Staff.objects.create(
        user=user,
        hotel=hotel,
        first_name="Test",
        last_name="Staff",
        department=department,
        role=role,
        is_active=True
    )
    
    booking = RoomBooking.objects.create(
        hotel=hotel,
        room_type=room_type,
        booking_id=f"BK-TEST-IDEMPOTENT-{unique_id}",
        confirmation_number=f"CONF-IDEMPOTENT-{unique_id}",
        check_in=timezone.now().date(),
        check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
        adults=2,
        children=0,
        total_amount=Decimal('200.00'),
        currency='EUR',
        status='CONFIRMED',  # Start as already confirmed
        payment_provider='stripe',
        payment_intent_id='pi_test_123456789',
        payment_reference='pi_test_123456789', 
        payment_authorized_at=timezone.now(),
        paid_at=timezone.now(),  # Already paid
        decision_at=timezone.now(),
        decision_by=staff,
        primary_first_name="John",
        primary_last_name="Doe",
        primary_email="john.doe@example.com",
        booker_email="john.doe@example.com"
    )
    
    factory = RequestFactory()
    request = factory.post(f'/api/staff/hotel/{hotel.slug}/room-bookings/{booking.booking_id}/approve/')
    request.user = user
    
    # Test approve on already confirmed booking (should be idempotent)
    with patch('stripe.PaymentIntent.capture') as mock_capture:
        view = StaffBookingAcceptView()
        response = view.post(request, hotel.slug, booking.booking_id)
        
        print(f"✅ Idempotent response: {response.status_code}")
        assert response.status_code == 200
        assert response.data['message'].endswith('(idempotent)')
        assert not mock_capture.called, "Stripe should not be called for idempotent requests"
        print("✅ Idempotency test passed!")
    
    # Clean up idempotency test data
    booking.delete()
    staff.delete()
    user.delete()
    room_type.delete()
    hotel.delete()
    
    print("✅ All idempotency tests passed!\n")

if __name__ == '__main__':
    print("🚀 Starting approve/decline endpoint tests...\n")
    
    try:
        # Clean up any existing test data
        print("🧹 Cleaning up existing test data...")
        cleanup_test_data()
        print("✅ Cleanup completed\n")
        
        test_approve_booking()
        test_decline_booking()  
        test_idempotency()
        print("🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        # Clean up after tests
        print("\n🧹 Cleaning up test data...")
        try:
            cleanup_test_data()
            print("✅ Final cleanup completed")
        except Exception as e:
            print(f"Note: Final cleanup encountered: {e}")