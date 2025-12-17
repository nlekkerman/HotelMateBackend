#!/usr/bin/env python
"""
Comprehensive test for Guest Pre-Check-in Implementation
Uses existing data to avoid model creation issues
"""

import os
import sys
import django
import secrets
import hashlib
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from hotel.models import Hotel, RoomBooking, BookingGuest, BookingPrecheckinToken
from staff.models import Staff
from rooms.models import RoomType, Room
import json

class PreCheckinIntegrationTest:
    """Comprehensive test for pre-check-in functionality using existing data"""
    
    def __init__(self):
        self.client = Client()
        self.setup_test_data()
    
    def setup_test_data(self):
        """Use existing data or create minimal test data"""
        print("🔧 Setting up test data...")
        
        # Use existing hotel or create one
        try:
            self.hotel = Hotel.objects.first()
            if not self.hotel:
                print("❌ No hotels found in database")
                sys.exit(1)
                
            print(f"✅ Using hotel: {self.hotel.name} ({self.hotel.slug})")
            
            # Get room type
            self.room_type = self.hotel.room_types.first() 
            if not self.room_type:
                print("❌ No room types found")
                sys.exit(1)
                
            # Get room
            self.room = Room.objects.filter(hotel=self.hotel).first()
            if not self.room:
                print("❌ No rooms found")
                sys.exit(1)
                
            # Get or create staff user
            self.user, created = User.objects.get_or_create(
                username='teststaff_precheckin',
                defaults={
                    'email': 'teststaff@example.com',
                    'first_name': 'Test',
                    'last_name': 'Staff'
                }
            )
            if created:
                self.user.set_password('testpass123')
                self.user.save()
                
            # Get or create staff profile 
            # Use existing staff or skip staff creation for test
            self.staff = Staff.objects.filter(user=self.user).first()
            if not self.staff:
                # Use any existing staff member
                self.staff = Staff.objects.filter(hotel=self.hotel).first()
                if self.staff:
                    self.user = self.staff.user
                else:
                    print("❌ No staff found - creating basic user only")
                    self.staff = None
            
            # Clean up any existing test bookings
            RoomBooking.objects.filter(
                primary_email='john.doe.test@example.com'
            ).delete()
            
            # Create test booking
            self.booking = RoomBooking.objects.create(
                hotel=self.hotel,
                room_type=self.room_type,
                check_in=timezone.now().date() + timedelta(days=1),
                check_out=timezone.now().date() + timedelta(days=3),
                adults=2,
                children=0,
                total_amount=200.00,
                currency='EUR',
                status='CONFIRMED',
                booker_type='SELF',
                primary_first_name='John',
                primary_last_name='Doe',
                primary_email='john.doe.test@example.com',
                primary_phone='+353123456789'
            )
            
            print(f"✅ Created booking: {self.booking.booking_id}")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            sys.exit(1)
        
    def authenticate_staff(self):
        """Authenticate as staff member"""
        if self.staff:
            self.client.login(username=self.user.username, password='testpass123')
        else:
            print("⚠️ No staff available - skipping authentication")
        
    def test_phase_b_party_completion(self):
        """Test Phase B: Party completion computation"""
        print("\n📋 Testing Phase B: Party completion computation")
        
        # Clear any existing party members first
        BookingGuest.objects.filter(booking=self.booking).delete()
        
        # Initially should be incomplete (no party members)
        self.booking.refresh_from_db()
        print(f"Debug: Adults={self.booking.adults}, Children={self.booking.children}")
        print(f"Debug: Party count={self.booking.party.count()}, Staying count={self.booking.party.filter(is_staying=True).count()}")
        
        assert not self.booking.party_complete, "Booking should be incomplete initially"
        assert self.booking.party_missing_count == 2, f"Should be missing 2 guests, got {self.booking.party_missing_count}"
        print("✅ Party completion correctly shows incomplete")
        
        # Add one party member
        BookingGuest.objects.create(
            booking=self.booking,
            role='PRIMARY',
            first_name='John',
            last_name='Doe',
            email='john.doe@test.com',
            is_staying=True
        )
        
        # Refresh from DB
        self.booking.refresh_from_db()
        assert not self.booking.party_complete, "Booking should still be incomplete"
        assert self.booking.party_missing_count == 1, f"Should be missing 1 guest, got {self.booking.party_missing_count}"
        print("✅ Party completion correctly shows 1 missing")
        
        # Add second party member
        BookingGuest.objects.create(
            booking=self.booking,
            role='COMPANION',
            first_name='Jane',
            last_name='Doe',
            email='jane.doe@test.com',
            is_staying=True
        )
        
        # Refresh from DB
        self.booking.refresh_from_db()
        assert self.booking.party_complete, "Booking should now be complete"
        assert self.booking.party_missing_count == 0, f"Should be missing 0 guests, got {self.booking.party_missing_count}"
        print("✅ Party completion correctly shows complete")
        
        # Clear party for further tests
        BookingGuest.objects.filter(booking=self.booking).delete()
        
    def test_phase_d_staff_send_link(self):
        """Test Phase D: Staff send pre-check-in link"""
        print("\n📧 Testing Phase D: Staff send pre-check-in link")
        
        self.authenticate_staff()
        
        url = f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{self.booking.booking_id}/send-precheckin-link/'
        print(f"Testing URL: {url}")
        
        response = self.client.post(url)
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response content: {response.content}")
            
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'success' in data, "Response should contain success field"
        assert 'sent_to' in data, "Response should contain sent_to field" 
        assert 'expires_at' in data, "Response should contain expires_at field"
        assert data['sent_to'] == self.booking.primary_email, "Should send to primary email"
        
        print("✅ Staff send link endpoint working correctly")
        
        # Get the created token for next test
        self.token = BookingPrecheckinToken.objects.filter(booking=self.booking).first()
        assert self.token is not None, "Token should have been created"
        print(f"✅ Token created with hash: {self.token.token_hash[:16]}...")
        
    def test_phase_e_public_endpoints(self):
        """Test Phase E: Public guest endpoints"""
        print("\n🌐 Testing Phase E: Public guest endpoints")
        
        # We need a raw token - let's create one manually for testing
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Create token manually for testing
        self.token = BookingPrecheckinToken.objects.create(
            booking=self.booking,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(hours=72),
            sent_to_email=self.booking.primary_email
        )
        
        # Test validate endpoint
        validate_url = f'/api/public/hotel/{self.hotel.slug}/precheckin/?token={raw_token}'
        print(f"Testing validate URL: {validate_url}")
        
        response = self.client.get(validate_url)
        assert response.status_code == 200, f"Validate endpoint failed: {response.status_code}"
        
        validate_data = response.json()
        assert 'booking_summary' in validate_data, "Should contain booking summary"
        assert 'party_complete' in validate_data, "Should contain party_complete"
        assert validate_data['party_complete'] == False, "Should show party incomplete"
        
        print("✅ Validate endpoint working correctly")
        
        # Test submit endpoint
        submit_url = f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/'
        submit_data = {
            'token': raw_token,
            'party': [
                {
                    'role': 'PRIMARY',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john.doe@test.com',
                    'phone': '+353123456789',
                    'is_staying': True
                },
                {
                    'role': 'COMPANION', 
                    'first_name': 'Jane',
                    'last_name': 'Doe',
                    'email': 'jane.doe@test.com',
                    'phone': '+353987654321',
                    'is_staying': True
                }
            ],
            'accept_terms': True
        }
        
        print(f"Testing submit URL: {submit_url}")
        response = self.client.post(
            submit_url,
            data=json.dumps(submit_data),
            content_type='application/json'
        )
        
        print(f"Submit response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Submit response content: {response.content}")
            
        assert response.status_code == 200, f"Submit endpoint failed: {response.status_code}"
        
        submit_response = response.json()
        assert 'success' in submit_response, "Should contain success field"
        assert submit_response['party_complete'] == True, "Party should now be complete"
        
        print("✅ Submit endpoint working correctly")
        
        # Verify token is now used
        self.token.refresh_from_db()
        assert self.token.used_at is not None, "Token should be marked as used"
        print("✅ Token correctly marked as used")
        
    def test_phase_f_enforcement(self):
        """Test Phase F: Party completion enforcement"""
        print("\n🚫 Testing Phase F: Party completion enforcement")
        
        # Clear party to make booking incomplete
        BookingGuest.objects.filter(booking=self.booking).delete()
        
        self.authenticate_staff()
        
        # Try to assign room with incomplete party
        assign_url = f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{self.booking.booking_id}/safe-assign-room/'
        assign_data = {'room_id': self.room.id}
        
        print(f"Testing assignment URL: {assign_url}")
        response = self.client.post(
            assign_url,
            data=json.dumps(assign_data),
            content_type='application/json'
        )
        
        print(f"Assignment response status: {response.status_code}")
        assert response.status_code == 400, f"Should block assignment, got {response.status_code}"
        
        error_data = response.json()
        assert 'code' in error_data, "Should contain error code"
        assert error_data['code'] == 'PARTY_INCOMPLETE', f"Should return PARTY_INCOMPLETE, got {error_data.get('code')}"
        
        print("✅ Room assignment correctly blocked for incomplete party")
        
        # Now complete the party and try again
        BookingGuest.objects.create(
            booking=self.booking,
            role='PRIMARY',
            first_name='John',
            last_name='Doe',
            email='john.doe@test.com',
            is_staying=True
        )
        BookingGuest.objects.create(
            booking=self.booking,
            role='COMPANION',
            first_name='Jane', 
            last_name='Doe',
            email='jane.doe@test.com',
            is_staying=True
        )
        
        # Try assignment again
        response = self.client.post(
            assign_url,
            data=json.dumps(assign_data),
            content_type='application/json'
        )
        
        print(f"Assignment with complete party status: {response.status_code}")
        assert response.status_code == 200, f"Should allow assignment with complete party, got {response.status_code}"
        
        print("✅ Room assignment correctly allowed for complete party")
        
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting comprehensive pre-check-in tests...")
        print(f"🏨 Hotel: {self.hotel.name} ({self.hotel.slug})")
        print(f"📋 Booking: {self.booking.booking_id}")
        
        try:
            self.test_phase_b_party_completion()
            self.test_phase_d_staff_send_link()
            self.test_phase_e_public_endpoints()
            self.test_phase_f_enforcement()
            
            print("\n🎉 ALL TESTS PASSED! Guest pre-check-in system is working correctly!")
            return True
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    tester = PreCheckinIntegrationTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Ready for production!")
        sys.exit(0)
    else:
        print("\n❌ Issues found - check implementation")
        sys.exit(1)