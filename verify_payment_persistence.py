#!/usr/bin/env python
"""
Verification script for Stripe payment persistence implementation.
Tests that payment_provider and payment_reference are immediately persisted 
during session creation and that webhooks properly confirm bookings.
"""

import os
import sys
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import Client, override_settings
from hotel.models import Hotel, RoomBooking, BookerType
from rooms.models import RoomType
from unittest.mock import patch, MagicMock
from decimal import Decimal


def cleanup_test_data():
    """Clean up any existing test data"""
    # Delete test bookings
    RoomBooking.objects.filter(
        booking_id__in=["BK-2025-PAY01", "BK-2025-PAY02"]
    ).delete()
    
    # Delete test hotels and room types
    Hotel.objects.filter(slug="payment-test-hotel").delete()


def setup_test_data():
    """Create test hotel and room type"""
    try:
        hotel = Hotel.objects.get(slug="payment-test-hotel")
    except Hotel.DoesNotExist:
        hotel = Hotel.objects.create(
            name="Payment Test Hotel",
            slug="payment-test-hotel", 
            is_active=True
        )
    
    try:
        room_type = RoomType.objects.get(hotel=hotel, code="payment-suite")
    except RoomType.DoesNotExist:
        room_type = RoomType.objects.create(
            hotel=hotel,
            name="Payment Suite", 
            code="payment-suite",
            starting_price_from=150.00,
            max_occupancy=2,
            currency="EUR"
        )
    
    return hotel, room_type


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def test_payment_session_persistence():
    """Test that payment info is immediately persisted during session creation"""
    print("\n🔍 Testing Payment Session Persistence...")
    
    hotel, room_type = setup_test_data()
    
    # Create test booking
    booking = RoomBooking.objects.create(
        booking_id="BK-2025-PAY01",
        confirmation_number="PAY-2025-0001",
        hotel=hotel,
        room_type=room_type,
        status="PENDING_PAYMENT",
        check_in="2025-12-25",
        check_out="2025-12-27",
        adults=2,
        children=0,
        primary_first_name="Alice",
        primary_last_name="Payment",
        primary_email="alice.payment@example.com",
        primary_phone="+353871111111",
        booker_type=BookerType.SELF,
        total_amount=300.00
    )
    
    # Verify initial state: no payment info
    print(f"   Initial state - Provider: {booking.payment_provider}, Reference: {booking.payment_reference}")
    assert not booking.payment_provider
    assert not booking.payment_reference
    
    client = Client()
    
    # Mock Stripe session creation
    mock_session = MagicMock()
    mock_session.id = "cs_test_payment_session_123"
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_payment_session_123"
    mock_session.amount_total = 30000  # €300.00 in cents
    mock_session.currency = "eur"
    
    payload = {
        "success_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }
    
    with patch('stripe.checkout.Session.create', return_value=mock_session):
        with patch('hotel.payment_views.store_idempotency_session'):
            with patch('hotel.payment_views.store_payment_session'):
                with patch('hotel.payment_views.generate_idempotency_key', return_value='test_key'):
                    response = client.post(
                        f'/api/public/hotel/{hotel.slug}/room-bookings/{booking.booking_id}/payment/session/',
                        data=json.dumps(payload),
                        content_type='application/json'
                    )
    
    if response.status_code == 200:
        # Refresh booking from database
        booking.refresh_from_db()
        
        # Verify payment info was persisted immediately
        if (booking.payment_provider == "stripe" and 
            booking.payment_reference == "cs_test_payment_session_123"):
            print("✅ Payment session persistence: SUCCESS")
            print(f"   Provider: {booking.payment_provider}")
            print(f"   Reference: {booking.payment_reference}")
            return True
        else:
            print("❌ Payment session persistence: FAILED")
            print(f"   Expected: provider='stripe', reference='cs_test_payment_session_123'")
            print(f"   Got: provider='{booking.payment_provider}', reference='{booking.payment_reference}'")
            return False
    else:
        print(f"❌ Payment session creation failed: {response.status_code}")
        try:
            print(f"   Response: {response.json()}")
        except:
            print(f"   Content: {response.content.decode()[:200]}...")
        return False


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def test_webhook_booking_confirmation():
    """Test that webhook properly confirms booking atomically"""
    print("\n🔍 Testing Webhook Booking Confirmation...")
    
    hotel, room_type = setup_test_data()
    
    # Create test booking with payment info already set (simulating session creation)
    booking = RoomBooking.objects.create(
        booking_id="BK-2025-PAY02",
        confirmation_number="PAY-2025-0002",
        hotel=hotel,
        room_type=room_type,
        status="PENDING_PAYMENT",
        check_in="2025-12-26",
        check_out="2025-12-28",
        adults=2,
        children=0,
        primary_first_name="Bob",
        primary_last_name="Webhook",
        primary_email="bob.webhook@example.com",
        primary_phone="+353872222222",
        booker_type=BookerType.SELF,
        total_amount=400.00,
        payment_provider="stripe",
        payment_reference="cs_test_webhook_session_456"
    )
    
    # Verify initial state: payment info set, but not paid
    print(f"   Initial state - Status: {booking.status}, Paid: {booking.paid_at}")
    assert booking.status == "PENDING_PAYMENT"
    assert not booking.paid_at
    
    client = Client()
    
    # Mock Stripe webhook event
    webhook_payload = {
        "id": "evt_test_webhook_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_webhook_session_456",
                "payment_intent": "pi_test_payment_intent_789",
                "customer_email": "bob.webhook@example.com",
                "amount_total": 40000,  # €400.00 in cents
                "currency": "eur",
                "payment_status": "paid",
                "metadata": {
                    "booking_id": "BK-2025-PAY02",
                    "hotel_slug": "payment-test-hotel",
                    "guest_name": "Bob Webhook",
                    "check_in": "2025-12-26",
                    "check_out": "2025-12-28"
                }
            }
        }
    }
    
    with patch('stripe.Webhook.construct_event', return_value=webhook_payload):
        with patch('hotel.payment_views.is_webhook_processed', return_value=False):
            with patch('hotel.payment_views.mark_webhook_processed'):
                with patch('django.core.mail.send_mail'):  # Mock email sending
                    response = client.post(
                        '/api/public/hotel/room-bookings/stripe-webhook/',
                        data=json.dumps(webhook_payload),
                        content_type='application/json',
                        HTTP_STRIPE_SIGNATURE='test_signature'
                    )
    
    if response.status_code == 200:
        # Refresh booking from database
        booking.refresh_from_db()
        
        # Verify booking was confirmed atomically
        if (booking.status == "CONFIRMED" and 
            booking.paid_at and
            booking.payment_provider == "stripe" and
            booking.payment_reference == "pi_test_payment_intent_789"):
            print("✅ Webhook booking confirmation: SUCCESS")
            print(f"   Status: {booking.status}")
            print(f"   Paid at: {booking.paid_at}")
            print(f"   Provider: {booking.payment_provider}")
            print(f"   Reference: {booking.payment_reference}")
            return True
        else:
            print("❌ Webhook booking confirmation: FAILED")
            print(f"   Expected: status='CONFIRMED', paid_at set, provider='stripe', reference='pi_test_payment_intent_789'")
            print(f"   Got: status='{booking.status}', paid_at='{booking.paid_at}', provider='{booking.payment_provider}', reference='{booking.payment_reference}'")
            return False
    else:
        print(f"❌ Webhook processing failed: {response.status_code}")
        try:
            print(f"   Response: {response.json()}")
        except:
            print(f"   Content: {response.content.decode()[:200]}...")
        return False


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def test_webhook_idempotency():
    """Test that webhook is idempotent - repeated events don't break anything"""
    print("\n🔍 Testing Webhook Idempotency...")
    
    hotel, room_type = setup_test_data()
    
    # Get the already confirmed booking from previous test
    try:
        booking = RoomBooking.objects.get(booking_id="BK-2025-PAY02")
    except RoomBooking.DoesNotExist:
        print("❌ Idempotency test: No booking found from previous test")
        return False
    
    # Verify it's already confirmed
    if booking.status != "CONFIRMED" or not booking.paid_at:
        print("❌ Idempotency test: Booking not in expected paid state")
        return False
    
    initial_paid_at = booking.paid_at
    initial_reference = booking.payment_reference
    
    client = Client()
    
    # Send the same webhook event again
    webhook_payload = {
        "id": "evt_test_idempotency_456",  # Different event ID
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_webhook_session_456",
                "payment_intent": "pi_test_payment_intent_different",  # Different payment intent
                "customer_email": "bob.webhook@example.com",
                "amount_total": 40000,
                "currency": "eur",
                "payment_status": "paid",
                "metadata": {
                    "booking_id": "BK-2025-PAY02",
                    "hotel_slug": "payment-test-hotel",
                    "guest_name": "Bob Webhook",
                    "check_in": "2025-12-26",
                    "check_out": "2025-12-28"
                }
            }
        }
    }
    
    with patch('stripe.Webhook.construct_event', return_value=webhook_payload):
        with patch('hotel.payment_views.is_webhook_processed', return_value=False):
            with patch('hotel.payment_views.mark_webhook_processed'):
                with patch('django.core.mail.send_mail'):
                    response = client.post(
                        '/api/public/hotel/room-bookings/stripe-webhook/',
                        data=json.dumps(webhook_payload),
                        content_type='application/json',
                        HTTP_STRIPE_SIGNATURE='test_signature'
                    )
    
    if response.status_code == 200:
        # Refresh booking from database
        booking.refresh_from_db()
        
        # Verify booking state didn't change (idempotency)
        if (booking.paid_at == initial_paid_at and 
            booking.payment_reference == initial_reference and
            booking.status == "CONFIRMED"):
            print("✅ Webhook idempotency: SUCCESS")
            print(f"   Status unchanged: {booking.status}")
            print(f"   Paid at unchanged: {booking.paid_at}")
            print(f"   Reference unchanged: {booking.payment_reference}")
            return True
        else:
            print("❌ Webhook idempotency: FAILED - booking state changed")
            print(f"   Initial: paid_at={initial_paid_at}, ref={initial_reference}")
            print(f"   Final: paid_at={booking.paid_at}, ref={booking.payment_reference}")
            return False
    else:
        print(f"❌ Webhook idempotency test failed: {response.status_code}")
        return False


def main():
    """Run payment persistence verification tests"""
    print("🚀 Stripe Payment Persistence Verification")
    print("=" * 50)
    
    try:
        # Clean up any existing test data
        cleanup_test_data()
        
        results = []
        results.append(test_payment_session_persistence())
        results.append(test_webhook_booking_confirmation())
        results.append(test_webhook_idempotency())
        
        print("\n" + "=" * 50)
        
        success_count = sum(results)
        total_count = len(results)
        
        if success_count == total_count:
            print("✅ All payment persistence tests PASSED!")
            print("\n📋 Verified:")
            print("   ✅ Payment provider + reference persisted immediately")
            print("   ✅ Webhook atomically processes payment (→ CONFIRMED)")  
            print("   ✅ Webhook is idempotent (repeated events safe)")
            print("\n🎉 Stripe payment persistence implementation is working correctly!")
        else:
            print(f"❌ {total_count - success_count}/{total_count} tests FAILED")
            
        return 0 if success_count == total_count else 1
        
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())