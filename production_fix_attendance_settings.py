#!/usr/bin/env python
"""
Production fix: Create AttendanceSettings for all hotels
This script should be run on production to fix the face clock-in issue
Usage: python production_fix_attendance_settings.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, AttendanceSettings
from staff.models import Department


def create_attendance_settings_for_all_hotels():
    """Create AttendanceSettings for all hotels if they don't exist"""
    
    print("🔧 Production Fix: Creating AttendanceSettings for all hotels...")
    
    hotels = Hotel.objects.all()
    created_count = 0
    updated_count = 0
    
    # Get ALL department IDs for global access
    all_dept_ids = list(Department.objects.values_list('id', flat=True))
    
    for hotel in hotels:
        print(f"\n🏨 Processing {hotel.name}")
        
        try:
            # Check if AttendanceSettings already exists
            settings = hotel.attendance_settings
            
            # Update existing settings to enable face attendance
            if not settings.face_attendance_enabled:
                settings.face_attendance_enabled = True
                settings.face_attendance_departments = all_dept_ids
                settings.save()
                updated_count += 1
                print(f"   ✅ Updated existing settings - Face attendance ENABLED")
            else:
                print(f"   ✅ Already configured and enabled")
                
        except AttributeError:
            # AttendanceSettings doesn't exist, create it
            settings = AttendanceSettings.objects.create(
                hotel=hotel,
                face_attendance_enabled=True,
                face_attendance_departments=all_dept_ids,
                break_warning_hours=6.0,
                overtime_warning_hours=8.0,
                hard_limit_hours=12.0,
                enforce_limits=False,
                face_attendance_min_confidence=0.6,
                require_face_consent=True,
                allow_face_self_registration=False,
                face_data_retention_days=365
            )
            created_count += 1
            print(f"   ✅ Created new AttendanceSettings - Face attendance ENABLED")
    
    print(f"\n🎉 Production Fix Complete!")
    print(f"   📊 Created: {created_count} new AttendanceSettings")
    print(f"   📊 Updated: {updated_count} existing AttendanceSettings") 
    print(f"   📊 Total hotels: {hotels.count()}")
    print(f"   📊 Total departments enabled: {len(all_dept_ids)}")
    print(f"   ✅ Face clock-in should now work for ALL hotels!")


if __name__ == "__main__":
    create_attendance_settings_for_all_hotels()