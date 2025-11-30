#!/usr/bin/env python
"""
Enable ALL departments for face recognition across all hotels
Usage: python enable_all_departments_face_recognition.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, AttendanceSettings
from staff.models import Department


def enable_all_departments():
    """Enable ALL departments for face recognition across all hotels"""
    
    print("🔄 Enabling ALL departments for face recognition...")
    
    # Get all hotels
    hotels = Hotel.objects.all()
    updated_count = 0
    
    for hotel in hotels:
        print(f"\n🏨 Processing {hotel.name} ({hotel.slug})")
        
        # Get ALL departments (not just for this hotel)
        all_departments = Department.objects.all()
        all_dept_ids = list(all_departments.values_list('id', flat=True))
        dept_names = list(all_departments.values_list('name', flat=True))
        
        print(f"   📋 Enabling {len(all_dept_ids)} departments: {', '.join(dept_names[:5])}{'...' if len(dept_names) > 5 else ''}")
        
        # Get or create AttendanceSettings
        settings, created = AttendanceSettings.objects.get_or_create(
            hotel=hotel,
            defaults={
                'face_attendance_enabled': True,
                'face_attendance_departments': all_dept_ids
            }
        )
        
        if created:
            print(f"   ✅ Created AttendanceSettings with ALL {len(all_dept_ids)} departments")
        else:
            # Update existing settings
            old_count = len(settings.face_attendance_departments)
            settings.face_attendance_departments = all_dept_ids
            settings.face_attendance_enabled = True
            settings.save()
            updated_count += 1
            
            print(f"   🔄 Updated departments: {old_count} → {len(all_dept_ids)} (ALL departments)")
        
        print(f"   ✅ Face attendance ENABLED for ALL departments")
    
    print(f"\n🎉 Summary:")
    print(f"   📊 Total hotels processed: {hotels.count()}")
    print(f"   📊 Total departments enabled: {Department.objects.count()}")
    print(f"   ✅ ALL departments can now use face recognition!")


def show_current_status():
    """Show current status of all AttendanceSettings"""
    print("📊 Current AttendanceSettings Status:")
    
    settings_list = AttendanceSettings.objects.select_related('hotel').all()
    
    if not settings_list:
        print("   ❌ No AttendanceSettings found")
        return
    
    total_departments = Department.objects.count()
    
    for settings in settings_list:
        dept_count = len(settings.face_attendance_departments)
        face_status = "✅ ENABLED" if settings.face_attendance_enabled else "❌ DISABLED"
        all_enabled = "🌟 ALL" if dept_count == total_departments else f"📋 {dept_count}/{total_departments}"
        
        print(f"\n🏨 {settings.hotel.name}")
        print(f"   Face Attendance: {face_status}")
        print(f"   Departments: {all_enabled} departments enabled")
        
        # Show some department names
        if settings.face_attendance_departments:
            try:
                departments = Department.objects.filter(
                    id__in=settings.face_attendance_departments[:5]
                )
                dept_names = [dept.name for dept in departments]
                more_text = f" + {dept_count - 5} more" if dept_count > 5 else ""
                print(f"   Sample Departments: {', '.join(dept_names)}{more_text}")
            except Exception as e:
                print(f"   ⚠️  Error getting department names: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_current_status()
    else:
        enable_all_departments()
        print(f"\n" + "="*60)
        show_current_status()