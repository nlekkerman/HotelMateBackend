#!/usr/bin/env python
"""
Test script to verify Pusher event structure for clock status updates.
Run this script to test that the Pusher events match the expected format.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from hotel.models import Hotel
from staff.models import Staff
from staff.pusher_utils import trigger_clock_status_update
import json
from unittest.mock import patch


def test_pusher_event_structure():
    """Test that Pusher events match the expected structure."""
    
    # Get or create test data
    hotel = Hotel.objects.first()
    staff = Staff.objects.first()
    
    if not hotel or not staff:
        print("❌ No hotel or staff found. Please ensure you have test data.")
        return
    
    print(f"✅ Testing with Hotel: {hotel.name} (slug: {hotel.slug})")
    print(f"✅ Testing with Staff: {staff.first_name} {staff.last_name} (ID: {staff.id})")
    print()
    
    # Test each action type
    actions = ['clock_in', 'clock_out', 'start_break', 'end_break']
    
    for action in actions:
        print(f"🔍 Testing action: {action}")
        
        # Mock the pusher_client.trigger to capture the event data
        with patch('staff.pusher_utils.pusher_client.trigger') as mock_trigger:
            trigger_clock_status_update(hotel.slug, staff, action)
            
            # Get the call arguments
            call_args = mock_trigger.call_args
            if call_args:
                channel, event, data = call_args[0]
                
                print(f"  📡 Channel: {channel}")
                print(f"  📅 Event: {event}")
                print(f"  📊 Data keys: {list(data.keys())}")
                
                # Verify channel format
                expected_channel = f"hotel-{hotel.slug}"
                if channel == expected_channel:
                    print(f"  ✅ Channel format correct")
                else:
                    print(f"  ❌ Channel format incorrect. Expected: {expected_channel}, Got: {channel}")
                
                # Verify event name
                if event == 'clock-status-updated':
                    print(f"  ✅ Event name correct")
                else:
                    print(f"  ❌ Event name incorrect. Expected: clock-status-updated, Got: {event}")
                
                # Verify required fields
                required_fields = [
                    'user_id', 'staff_id', 'duty_status', 'is_on_duty', 'is_on_break',
                    'status_label', 'clock_time', 'first_name', 'last_name', 'action',
                    'department', 'department_slug', 'current_status'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    print(f"  ❌ Missing required fields: {missing_fields}")
                else:
                    print(f"  ✅ All required fields present")
                
                # Verify current_status structure
                current_status = data.get('current_status', {})
                if isinstance(current_status, dict):
                    status_fields = ['status', 'label', 'is_on_break']
                    missing_status_fields = [field for field in status_fields if field not in current_status]
                    if missing_status_fields:
                        print(f"  ❌ Missing current_status fields: {missing_status_fields}")
                    else:
                        print(f"  ✅ current_status structure correct")
                        
                    # Verify consistency
                    if data['duty_status'] == current_status.get('status'):
                        print(f"  ✅ duty_status and current_status.status are consistent")
                    else:
                        print(f"  ❌ duty_status ({data['duty_status']}) != current_status.status ({current_status.get('status')})")
                else:
                    print(f"  ❌ current_status is not a dictionary")
                
                print(f"  📄 Full data structure:")
                print(f"    {json.dumps(data, indent=4, default=str)}")
                
            else:
                print(f"  ❌ No Pusher event triggered")
        
        print("-" * 50)
    
    print("🎯 Test completed!")


if __name__ == "__main__":
    test_pusher_event_structure()