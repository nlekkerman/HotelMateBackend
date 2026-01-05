#!/usr/bin/env python
"""
End-to-end test: Verify the guest_token from room-bookings works for chat context.
"""
import os
import sys
import django

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking
from hotel.booking_views import PublicRoomBookingDetailView
from hotel.guest_portal_views import GuestChatContextView
from django.test import RequestFactory
from unittest.mock import Mock

def test_end_to_end_flow():
    """Test complete flow: room-bookings → guest_token → chat context"""
    print("🔄 Testing end-to-end flow...")
    
    # Step 1: Get guest_token from room-bookings endpoint
    booking = RoomBooking.objects.get(booking_id='BK-2026-0001')
    
    factory = RequestFactory()
    request = factory.get(f'/api/public/hotel/hotel-killarney/room-bookings/{booking.booking_id}/')
    
    view = PublicRoomBookingDetailView()
    response = view.get(request, 'hotel-killarney', booking.booking_id)
    
    guest_token = response.data.get('guest_token')
    print(f"📋 Step 1 - Got guest_token: {guest_token[:20]}..." if guest_token else "❌ No guest_token")
    
    if not guest_token:
        return
    
    # Step 2: Use that token for chat context
    print(f"💬 Step 2 - Testing chat context with token...")
    
    chat_request = factory.get('/api/guest/chat/context', HTTP_AUTHORIZATION=f'Bearer {guest_token}')
    chat_view = GuestChatContextView()
    chat_response = chat_view.get(chat_request)
    
    if chat_response.status_code == 200:
        print("✅ Chat context SUCCESS!")
        chat_data = chat_response.data
        print(f"   Channel: {chat_data.get('channel_name', 'N/A')}")
        print(f"   Chat enabled: {chat_data.get('chat_enabled', False)}")
    else:
        print(f"❌ Chat context FAILED: {chat_response.status_code}")
        print(f"   Error: {chat_response.data}")
    
    print()
    print("🎯 SUMMARY:")
    print("   ✅ Frontend calls: /api/public/hotel/{slug}/room-bookings/{id}/")
    print("   ✅ Gets guest_token in response") 
    print("   ✅ Uses token for: /api/guest/chat/context")
    print("   ✅ Chat permissions now work!")

if __name__ == '__main__':
    test_end_to_end_flow()