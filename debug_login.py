#!/usr/bin/env python
"""
Debug script to check login response data for user 'sanja'
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('C:\\Users\\nlekk\\HMB\\HotelMateBackend')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.contrib.auth.models import User
from staff.models import Staff, NavigationItem
from hotel.models import Hotel

def check_login_data():
    print("=== LOGIN DEBUG SCRIPT ===")
    
    # Find the user
    try:
        user = User.objects.get(username='sanja')
        print(f"✅ Found user: {user.username}")
        print(f"   is_superuser: {user.is_superuser}")
        print(f"   is_staff: {user.is_staff}")
    except User.DoesNotExist:
        print("❌ User 'sanja' not found")
        return
    
    # Find the staff profile
    try:
        staff = Staff.objects.select_related('department', 'hotel', 'role').get(user=user)
        print(f"✅ Found staff: {staff.id}")
        print(f"   Hotel: {staff.hotel.name} ({staff.hotel.slug})")
        print(f"   Access Level: {staff.access_level}")
        print(f"   Department: {staff.department.name if staff.department else 'None'}")
        print(f"   Role: {staff.role.name if staff.role else 'None'}")
    except Staff.DoesNotExist:
        print("❌ Staff profile not found for user 'sanja'")
        return
    
    # Check navigation items for the hotel
    print(f"\n=== NAVIGATION ITEMS FOR {staff.hotel.name} ===")
    nav_items = NavigationItem.objects.filter(hotel=staff.hotel)
    print(f"Total navigation items in hotel: {nav_items.count()}")
    
    active_nav_items = nav_items.filter(is_active=True)
    print(f"Active navigation items: {active_nav_items.count()}")
    
    for nav in active_nav_items:
        print(f"  - {nav.name} ({nav.slug}) - Order: {nav.display_order}")
    
    # Check what a superuser should get
    if user.is_superuser:
        superuser_navs = [nav.slug for nav in active_nav_items]
        print(f"\nSuperuser should get these navs: {superuser_navs}")
    
    # Check staff allowed navigation items
    print(f"\n=== STAFF ALLOWED NAVIGATION ===")
    staff_navs = staff.allowed_navigation_items.all()
    print(f"Staff has {staff_navs.count()} assigned navigation items:")
    
    for nav in staff_navs:
        print(f"  - {nav.name} ({nav.slug}) - Active: {nav.is_active}")
    
    active_staff_navs = staff.allowed_navigation_items.filter(is_active=True)
    staff_nav_slugs = [nav.slug for nav in active_staff_navs]
    print(f"Active staff navs: {staff_nav_slugs}")
    
    print("\n=== SUMMARY ===")
    if user.is_superuser:
        print(f"As superuser, should get: {superuser_navs}")
    else:
        print(f"As regular staff, should get: {staff_nav_slugs}")

if __name__ == '__main__':
    check_login_data()