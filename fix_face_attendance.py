#!/usr/bin/env python
"""
Quick fix to enable face attendance for all hotels
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, AttendanceSettings

def enable_face_attendance_for_all():
    """Enable face attendance for all hotels"""
    hotels = Hotel.objects.all()
    
    print(f"Found {hotels.count()} hotels:")
    
    for hotel in hotels:
        print(f"\n🏨 {hotel.name} ({hotel.slug})")
        
        # Get or create attendance settings
        settings, created = AttendanceSettings.objects.get_or_create(
            hotel=hotel,
            defaults={
                'break_warning_hours': 6.0,
                'overtime_warning_hours': 10.0,
                'hard_limit_hours': 12.0,
                'enforce_limits': True,
                'face_attendance_enabled': True,  # ✅ ENABLE FACE ATTENDANCE
                'face_attendance_min_confidence': 0.80,
                'require_face_consent': True,
                'allow_face_self_registration': True,
                'face_data_retention_days': 365,
                'face_attendance_departments': []
            }
        )
        
        if created:
            print(f"   ✅ Created AttendanceSettings with face attendance ENABLED")
        else:
            # Update existing settings to enable face attendance
            settings.face_attendance_enabled = True
            settings.save()
            print(f"   ✅ Updated AttendanceSettings - face attendance ENABLED")
    
    print(f"\n🎉 Face attendance is now enabled for all {hotels.count()} hotels!")

if __name__ == "__main__":
    enable_face_attendance_for_all()