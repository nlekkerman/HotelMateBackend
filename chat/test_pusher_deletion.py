"""
Test script to verify Pusher deletion broadcasts reach guest UI.

This script simulates a staff deletion and broadcasts Pusher events
to the guest room channel to verify the entire real-time flow.

Usage:
    python chat/test_pusher_deletion.py <hotel_slug> <room_number> <message_id>

Example:
    python chat/test_pusher_deletion.py hotel-killarney 101 680
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from chat.utils import pusher_client
from hotel.models import Hotel
from rooms.models import Room
from django.shortcuts import get_object_or_404


def test_deletion_broadcast(hotel_slug, room_number, message_id, hard_delete=True):
    """
    Test deletion broadcast to guest channel.
    
    Args:
        hotel_slug: Hotel identifier (e.g., 'hotel-killarney')
        room_number: Room number (e.g., '101')
        message_id: Message ID to simulate deletion (e.g., 680)
        hard_delete: Whether to simulate hard delete (True) or soft delete (False)
    """
    print("\n" + "=" * 80)
    print("🧪 PUSHER DELETION BROADCAST TEST")
    print("=" * 80)
    
    # Verify hotel exists
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
        print(f"✅ Hotel found: {hotel.name}")
    except Hotel.DoesNotExist:
        print(f"❌ Hotel not found: {hotel_slug}")
        return False
    
    # Verify room exists
    try:
        room = Room.objects.get(room_number=room_number, hotel=hotel)
        print(f"✅ Room found: {room.room_number}")
    except Room.DoesNotExist:
        print(f"❌ Room not found: {room_number}")
        return False
    
    # Prepare channel and payload
    room_channel = f'{hotel_slug}-room-{room_number}-chat'
    pusher_data = {
        "message_id": int(message_id),
        "hard_delete": hard_delete
    }
    
    print(f"\n📋 Test Configuration:")
    print(f"   Hotel: {hotel_slug}")
    print(f"   Room: {room_number}")
    print(f"   Channel: {room_channel}")
    print(f"   Message ID: {message_id}")
    print(f"   Hard Delete: {hard_delete}")
    print(f"   Payload: {pusher_data}")
    print("\n" + "-" * 80)
    
    results = {
        "success": True,
        "broadcasts": []
    }
    
    # Test 1: Broadcast 'message-deleted' event
    print(f"\n📡 TEST 1: Broadcasting 'message-deleted' to {room_channel}")
    try:
        response = pusher_client.trigger(
            room_channel,
            'message-deleted',
            pusher_data
        )
        print(f"✅ SUCCESS: 'message-deleted' event sent")
        print(f"   Pusher Response: {response}")
        results["broadcasts"].append({
            "event": "message-deleted",
            "status": "success",
            "response": str(response)
        })
    except Exception as e:
        print(f"❌ FAILED: 'message-deleted' event")
        print(f"   Error: {e}")
        results["success"] = False
        results["broadcasts"].append({
            "event": "message-deleted",
            "status": "error",
            "error": str(e)
        })
    
    # Test 2: Broadcast 'message-removed' event (alias)
    print(f"\n📡 TEST 2: Broadcasting 'message-removed' to {room_channel}")
    try:
        response = pusher_client.trigger(
            room_channel,
            'message-removed',
            pusher_data
        )
        print(f"✅ SUCCESS: 'message-removed' event sent")
        print(f"   Pusher Response: {response}")
        results["broadcasts"].append({
            "event": "message-removed",
            "status": "success",
            "response": str(response)
        })
    except Exception as e:
        print(f"❌ FAILED: 'message-removed' event")
        print(f"   Error: {e}")
        results["success"] = False
        results["broadcasts"].append({
            "event": "message-removed",
            "status": "error",
            "error": str(e)
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Overall Status: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
    print(f"Events Sent: {len([b for b in results['broadcasts'] if b['status'] == 'success'])}/{len(results['broadcasts'])}")
    
    print(f"\n🔍 What to check in guest browser console:")
    print(f"   1. Open guest chat window for room {room_number}")
    print(f"   2. Look for: 🔔 [GUEST PUSHER] or 🗑️ [PUSHER EVENT]")
    print(f"   3. Message {message_id} should be removed from UI")
    print(f"   4. Check Network → WS tab for incoming frames")
    
    print("\n" + "=" * 80 + "\n")
    
    return results["success"]


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python chat/test_pusher_deletion.py <hotel_slug> <room_number> <message_id>")
        print("Example: python chat/test_pusher_deletion.py hotel-killarney 101 680")
        sys.exit(1)
    
    hotel_slug = sys.argv[1]
    room_number = sys.argv[2]
    message_id = sys.argv[3]
    hard_delete = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else True
    
    success = test_deletion_broadcast(hotel_slug, room_number, message_id, hard_delete)
    sys.exit(0 if success else 1)
