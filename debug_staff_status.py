#!/usr/bin/env python
"""
Debug script to check if staff duty_status is being updated correctly
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff.models import Staff
from attendance.models import ClockLog
from django.utils import timezone
from datetime import datetime, timedelta

def check_staff_status_consistency():
    """Check if staff duty_status matches their actual clock status"""
    
    print("=== STAFF STATUS CONSISTENCY CHECK ===\n")
    
    # Get all active staff
    active_staff = Staff.objects.filter(is_active=True).select_related('hotel', 'department')
    
    today = timezone.now().date()
    
    for staff in active_staff:
        print(f"Staff: {staff.first_name} {staff.last_name} (ID: {staff.id})")
        print(f"  Hotel: {staff.hotel.name}")
        print(f"  Database duty_status: {staff.duty_status}")
        
        # Check current clock status
        latest_log = ClockLog.objects.filter(
            staff=staff,
            time_in__date=today,
            time_out__isnull=True
        ).first()
        
        if latest_log:
            print(f"  Currently clocked in: YES (since {latest_log.time_in.strftime('%H:%M')})")
            expected_status = 'on_duty' if not getattr(latest_log, 'is_on_break', False) else 'on_break'
        else:
            print(f"  Currently clocked in: NO")
            expected_status = 'off_duty'
        
        print(f"  Expected duty_status: {expected_status}")
        
        # Check consistency
        if staff.duty_status == expected_status:
            print(f"  ✅ Status CONSISTENT")
        else:
            print(f"  ❌ Status INCONSISTENT - fixing...")
            # Fix the status
            staff.duty_status = expected_status
            staff.save(update_fields=['duty_status'])
            print(f"  ✅ Fixed duty_status to: {expected_status}")
        
        # Check get_current_status method
        current_status = staff.get_current_status()
        print(f"  get_current_status(): {current_status}")
        print()

def test_pusher_data():
    """Test what data would be sent via Pusher"""
    print("\n=== PUSHER DATA TEST ===\n")
    
    staff = Staff.objects.filter(is_active=True).first()
    if not staff:
        print("No active staff found")
        return
    
    print(f"Testing with staff: {staff.first_name} {staff.last_name}")
    print(f"Current duty_status: {staff.duty_status}")
    
    # Simulate what pusher_utils would send
    from staff.pusher_utils import trigger_clock_status_update
    
    # Test different actions
    for action in ['clock_in', 'clock_out', 'start_break', 'end_break']:
        print(f"\n--- Testing action: {action} ---")
        
        # Simulate the duty_status that would be set
        duty_status = staff.duty_status
        if action == 'clock_in':
            duty_status = 'on_duty'
        elif action == 'clock_out':
            duty_status = 'off_duty'
        elif action == 'start_break':
            duty_status = 'on_break'
        elif action == 'end_break':
            duty_status = 'on_duty'
        
        print(f"Would set duty_status to: {duty_status}")
        
        current_status = staff.get_current_status()
        current_status['status'] = duty_status
        current_status['is_on_break'] = (duty_status == 'on_break')
        
        status_labels = {
            'off_duty': 'Off Duty',
            'on_duty': 'On Duty', 
            'on_break': 'On Break'
        }
        current_status['label'] = status_labels.get(duty_status, 'Unknown')
        
        print(f"Pusher data would include:")
        print(f"  duty_status: {duty_status}")
        print(f"  current_status: {current_status}")

if __name__ == "__main__":
    check_staff_status_consistency()
    test_pusher_data()