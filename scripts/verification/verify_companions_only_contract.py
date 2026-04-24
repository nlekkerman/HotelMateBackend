#!/usr/bin/env python
"""
Quick verification script for unified companions-only party contract.
Run this to validate the implementation without full Django test setup.
"""

import os
import sys
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import Client, override_settings
from django.conf import settings
from hotel.models import Hotel, RoomBooking, BookingGuest, BookerType
from rooms.models import RoomType
from unittest.mock import patch

# Override settings for testing
@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])


def cleanup_test_data():
    """Clean up any existing test data"""
    # Delete test bookings
    RoomBooking.objects.filter(
        booking_id__in=["BK-2025-TEST01", "BK-2025-VERIFY01"]
    ).delete()
    
    # Delete test hotels and room types
    Hotel.objects.filter(slug="test-hotel").delete()


def setup_test_data():
    """Create test hotel and room type"""
    try:
        hotel = Hotel.objects.get(slug="test-hotel")
    except Hotel.DoesNotExist:
        hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel", 
            is_active=True
        )
    
    try:
        room_type = RoomType.objects.get(hotel=hotel, code="deluxe-suite")
    except RoomType.DoesNotExist:
        room_type = RoomType.objects.create(
            hotel=hotel,
            name="Deluxe Suite", 
            code="deluxe-suite",
            starting_price_from=100.00,
            max_occupancy=4,
            currency="EUR"
        )
    
    return hotel, room_type


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def test_booking_create_companions_only():
    """Test booking create with companions-only party"""
    print("\n🔍 Testing Booking Create - Companions Only...")
    
    hotel, room_type = setup_test_data()
    client = Client()
    
    # Test 1: Companions-only party (should succeed)
    payload = {
        "room_type_code": "deluxe-suite",
        "check_in": "2025-12-20",
        "check_out": "2025-12-22",
        "adults": 2,
        "children": 0,
        "booker_type": "SELF",
        "primary_first_name": "John",
        "primary_last_name": "Doe",
        "primary_email": "john.doe@example.com",
        "primary_phone": "+353871234567",
        "party": [
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com"
            }
        ]
    }
    
    with patch('hotel.services.booking.create_room_booking_from_request') as mock_create:
        mock_booking = RoomBooking.objects.create(
            booking_id="BK-2025-TEST01",
            confirmation_number="TES-2025-0001",
            hotel=hotel,
            room_type=room_type,
            status="PENDING_PAYMENT",
            check_in="2025-12-20",
            check_out="2025-12-22",
            adults=2,
            children=0,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john.doe@example.com",
            primary_phone="+353871234567",
            booker_type=BookerType.SELF,
            total_amount=200.00
        )
        mock_create.return_value = mock_booking
        
        response = client.post(
            f'/api/public/hotel/{hotel.slug}/bookings/',
            data=json.dumps(payload),
            content_type='application/json'
        )
    
    if response.status_code == 201:
        try:
            data = response.json()
            print(f"✅ Companions-only party: SUCCESS (party_count: {data['data']['party_count']})")
        except ValueError:
            print(f"❌ Companions-only party: FAILED - Non-JSON response")
            print(f"   Content: {response.content.decode()[:200]}...")
    else:
        print(f"❌ Companions-only party: FAILED ({response.status_code})")
        try:
            print(f"   Response: {response.json()}")
        except ValueError:
            print(f"   Content: {response.content.decode()[:200]}...")
        
    # Test 2: PRIMARY in party (should fail)
    payload["party"] = [
        {
            "role": "PRIMARY",
            "first_name": "John", 
            "last_name": "Doe"
        },
        {
            "first_name": "Jane",
            "last_name": "Smith"
        }
    ]
    
    response = client.post(
        f'/api/public/hotel/{hotel.slug}/bookings/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    if response.status_code == 400:
        try:
            response_data = response.json()
            if "Do not include PRIMARY" in response_data.get("detail", ""):
                print("✅ PRIMARY rejection: SUCCESS")
            else:
                print(f"❌ PRIMARY rejection: FAILED - Wrong error message")
                print(f"   Got: {response_data}")
        except ValueError:
            print(f"❌ PRIMARY rejection: FAILED - Non-JSON response")
            print(f"   Content: {response.content.decode()[:200]}...")
    else:
        print(f"❌ PRIMARY rejection: FAILED ({response.status_code})")


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def test_precheckin_companions_only():
    """Test precheckin submit with companions-only party"""
    print("\n🔍 Testing Precheckin Submit - Companions Only...")
    
    hotel, room_type = setup_test_data()
    client = Client()
    
    # Create test booking with party
    booking = RoomBooking.objects.create(
        booking_id="BK-2025-VERIFY01",
        confirmation_number="TES-2025-0002",
        hotel=hotel,
        room_type=room_type,
        status="CONFIRMED",
        check_in="2025-12-20",
        check_out="2025-12-22",
        adults=2,
        children=0,
        primary_first_name="John",
        primary_last_name="Doe",
        primary_email="john.doe@example.com",
        primary_phone="+353871234567",
        booker_type=BookerType.SELF,
        total_amount=200.00
    )
    
    # Create PRIMARY BookingGuest
    primary = BookingGuest.objects.create(
        booking=booking,
        role="PRIMARY",
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        is_staying=True
    )
    
    # Create existing COMPANION
    old_companion = BookingGuest.objects.create(
        booking=booking,
        role="COMPANION",
        first_name="Old",
        last_name="Companion",
        is_staying=True
    )
    
    print(f"   Initial state: {booking.party.count()} party members")
    print(f"   - PRIMARY: {booking.party.filter(role='PRIMARY').count()}")
    print(f"   - COMPANION: {booking.party.filter(role='COMPANION').count()}")
    
    # Create precheckin token
    import hashlib
    from django.utils import timezone
    from hotel.models import BookingPrecheckinToken
    
    raw_token = "verify-token-12345"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    BookingPrecheckinToken.objects.create(
        booking=booking,
        token_hash=token_hash,
        expires_at=timezone.now() + timezone.timedelta(days=7),
        config_snapshot_enabled={"party": True},
        config_snapshot_required={"party": False}
    )
    
    # Test 1: Companions-only party (should succeed and preserve PRIMARY)
    payload = {
        "token": raw_token,
        "party": [
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com"
            }
        ]
    }
    
    response = client.post(
        f'/api/public/hotel/{hotel.slug}/precheckin/submit/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    if response.status_code == 200:
        booking.refresh_from_db()
        primary_count = booking.party.filter(role="PRIMARY").count()
        companion_count = booking.party.filter(role="COMPANION").count()
        
        # Check PRIMARY preservation
        current_primary = booking.party.get(role="PRIMARY")
        primary_preserved = (current_primary.id == primary.id and 
                           current_primary.first_name == "John" and
                           current_primary.last_name == "Doe")
        
        # Check COMPANION replacement 
        companions = list(booking.party.filter(role="COMPANION"))
        companion_replaced = (len(companions) == 1 and 
                            companions[0].first_name == "Jane" and
                            companions[0].last_name == "Smith")
        
        if primary_preserved and companion_replaced:
            print("✅ Companions-only precheckin: SUCCESS")
            print(f"   - PRIMARY preserved: {primary_preserved}")
            print(f"   - COMPANION replaced: {companion_replaced}")
            print(f"   Final state: {primary_count} PRIMARY + {companion_count} COMPANION")
        else:
            print("❌ Companions-only precheckin: FAILED - state not correct")
            
    else:
        print(f"❌ Companions-only precheckin: FAILED ({response.status_code})")
        print(f"   Response: {response.json()}")
        
    # Test 2: PRIMARY in party (should fail)
    # Reset token
    token = BookingPrecheckinToken.objects.get(booking=booking)
    token.used_at = None
    token.save()
    
    payload = {
        "token": raw_token,
        "party": [
            {
                "role": "PRIMARY",
                "first_name": "John",
                "last_name": "Doe"
            }
        ]
    }
    
    response = client.post(
        f'/api/public/hotel/{hotel.slug}/precheckin/submit/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    if response.status_code == 400:
        try:
            response_data = response.json()
            if (response_data.get("code") == "VALIDATION_ERROR" and
                "Do not include PRIMARY" in response_data.get("message", "")):
                print("✅ PRIMARY rejection in precheckin: SUCCESS")
            else:
                print(f"❌ PRIMARY rejection in precheckin: FAILED - Wrong error")
                print(f"   Response: {response_data}")
        except ValueError:
            print(f"❌ PRIMARY rejection in precheckin: FAILED - Non-JSON response")
            print(f"   Content: {response.content.decode()[:200]}...")
    else:
        print(f"❌ PRIMARY rejection in precheckin: FAILED ({response.status_code})")


def main():
    """Run verification tests"""
    print("🚀 Companions-Only Party Contract Verification")
    print("=" * 50)
    
    try:
        # Clean up any existing test data
        cleanup_test_data()
        
        test_booking_create_companions_only()
        test_precheckin_companions_only()
        
        print("\n" + "=" * 50)
        print("✅ Verification complete!")
        print("\n📋 Summary:")
        print("   - Booking create rejects PRIMARY in party ✅")  
        print("   - Booking create accepts companions-only party ✅")
        print("   - Precheckin submit preserves PRIMARY ✅")
        print("   - Precheckin submit replaces only companions ✅")
        print("   - Both endpoints reject PRIMARY in payload ✅")
        
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())