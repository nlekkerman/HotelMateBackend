#!/usr/bin/env python
"""
Populate all AttendanceSettings with department IDs
Usage: python populate_attendance_departments.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, AttendanceSettings
from staff.models import Department


def populate_attendance_departments():
    """Populate all AttendanceSettings with their hotel's department IDs"""
    
    print("🔄 Populating AttendanceSettings with department IDs...")
    
    # Get all hotels
    hotels = Hotel.objects.all()
    updated_count = 0
    created_count = 0
    
    for hotel in hotels:
        print(f"\n🏨 Processing {hotel.name} ({hotel.slug})")
        
        # Get all departments for this hotel (through staff members)
        departments = Department.objects.filter(staff_members__hotel=hotel).distinct()
        dept_ids = list(departments.values_list('id', flat=True))
        dept_names = list(departments.values_list('name', flat=True))
        
        print(f"   📋 Found {len(dept_ids)} departments: {', '.join(dept_names)}")
        
        # Get or create AttendanceSettings
        settings, created = AttendanceSettings.objects.get_or_create(
            hotel=hotel,
            defaults={
                'break_warning_hours': 6.0,
                'overtime_warning_hours': 10.0,
                'hard_limit_hours': 12.0,
                'enforce_limits': True,
                'face_attendance_enabled': True,  # ✅ Enable by default
                'face_attendance_min_confidence': 0.80,
                'require_face_consent': True,
                'allow_face_self_registration': True,
                'face_data_retention_days': 365,
                'face_attendance_departments': dept_ids  # Auto-populate departments
            }
        )
        
        if created:
            created_count += 1
            print(f"   ✅ Created AttendanceSettings with {len(dept_ids)} departments")
            print(f"   ✅ Face attendance ENABLED")
        else:
            # Update existing settings
            old_depts = settings.face_attendance_departments.copy()
            settings.face_attendance_departments = dept_ids
            settings.face_attendance_enabled = True  # Ensure it's enabled
            settings.save()
            updated_count += 1
            
            print(f"   🔄 Updated departments: {old_depts} → {dept_ids}")
            print(f"   ✅ Face attendance ENABLED")
    
    print(f"\n🎉 Summary:")
    print(f"   📊 Created: {created_count} AttendanceSettings")
    print(f"   📊 Updated: {updated_count} AttendanceSettings")
    print(f"   📊 Total hotels: {hotels.count()}")
    print(f"   ✅ Face attendance enabled for all hotels!")


def show_current_status():
    """Show current status of all AttendanceSettings"""
    print("📊 Current AttendanceSettings Status:")
    
    settings_list = AttendanceSettings.objects.select_related('hotel').all()
    
    if not settings_list:
        print("   ❌ No AttendanceSettings found")
        return
    
    for settings in settings_list:
        dept_count = len(settings.face_attendance_departments)
        face_status = "✅ ENABLED" if settings.face_attendance_enabled else "❌ DISABLED"
        
        print(f"\n🏨 {settings.hotel.name}")
        print(f"   Face Attendance: {face_status}")
        print(f"   Departments: {dept_count} IDs = {settings.face_attendance_departments}")
        
        # Show actual department names
        if settings.face_attendance_departments:
            try:
                departments = Department.objects.filter(
                    id__in=settings.face_attendance_departments
                )
                dept_names = [dept.name for dept in departments]
                print(f"   Department Names: {', '.join(dept_names)}")
            except Exception as e:
                print(f"   ⚠️  Error getting department names: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_current_status()
    else:
        populate_attendance_departments()
        print(f"\n" + "="*50)
        show_current_status()