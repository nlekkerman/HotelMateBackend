#!/usr/bin/env python
"""
Enable face attendance for a hotel
Usage: python enable_face_attendance.py <hotel_slug>
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, AttendanceSettings


def enable_face_attendance(hotel_slug):
    """Enable face attendance for the specified hotel"""
    try:
        # Get the hotel
        hotel = Hotel.objects.get(slug=hotel_slug)
        print(f"Found hotel: {hotel.name} ({hotel.slug})")
        
        # Get or create attendance settings
        settings, created = AttendanceSettings.objects.get_or_create(
            hotel=hotel,
            defaults={
                'break_warning_hours': 6.0,
                'overtime_warning_hours': 10.0,
                'hard_limit_hours': 12.0,
                'enforce_limits': True,
                'face_attendance_enabled': True,  # Enable face attendance
                'face_attendance_min_confidence': 0.80,
                'require_face_consent': True,
                'allow_face_self_registration': True,
                'face_data_retention_days': 365,
                'face_attendance_departments': []  # Empty = all departments allowed
            }
        )
        
        if created:
            print(f"✅ Created new AttendanceSettings for {hotel.name}")
        else:
            # Update existing settings
            settings.face_attendance_enabled = True
            settings.face_attendance_min_confidence = 0.80
            settings.require_face_consent = True
            settings.allow_face_self_registration = True
            settings.face_data_retention_days = 365
            settings.face_attendance_departments = []
            settings.save()
            print(f"✅ Updated AttendanceSettings for {hotel.name}")
        
        print(f"✅ Face attendance is now ENABLED for {hotel.name}")
        print(f"   - Min confidence: {settings.face_attendance_min_confidence}")
        print(f"   - Consent required: {settings.require_face_consent}")
        print(f"   - Self registration: {settings.allow_face_self_registration}")
        print(f"   - Departments allowed: {'All' if not settings.face_attendance_departments else settings.face_attendance_departments}")
        
        return True
        
    except Hotel.DoesNotExist:
        print(f"❌ Hotel with slug '{hotel_slug}' not found")
        print("Available hotels:")
        for hotel in Hotel.objects.all():
            print(f"   - {hotel.name} ({hotel.slug})")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def list_all_hotels():
    """List all available hotels"""
    print("Available hotels:")
    hotels = Hotel.objects.all()
    if not hotels:
        print("   No hotels found")
    else:
        for hotel in hotels:
            try:
                settings = hotel.attendance_settings
                face_enabled = settings.face_attendance_enabled
                status = "✅ ENABLED" if face_enabled else "❌ DISABLED"
            except AttributeError:
                status = "❌ NO SETTINGS"
            
            print(f"   - {hotel.name} ({hotel.slug}) - Face: {status}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python enable_face_attendance.py <hotel_slug>")
        print("       python enable_face_attendance.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_all_hotels()
    else:
        hotel_slug = sys.argv[1]
        success = enable_face_attendance(hotel_slug)
        sys.exit(0 if success else 1)