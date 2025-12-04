#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff.models import Staff, NavigationItem
from django.contrib.auth.models import User

def check_superuser_login():
    print("=== SUPERUSER LOGIN DATA CHECK ===\n")
    
    # Check super users
    super_users = User.objects.filter(is_superuser=True)
    print(f"Found {super_users.count()} super users:")
    
    for user in super_users:
        print(f"\n--- User: {user.username} ---")
        print(f"  - is_superuser: {user.is_superuser}")
        print(f"  - is_staff: {user.is_staff}")
        print(f"  - is_active: {user.is_active}")
        
        try:
            staff = Staff.objects.select_related('hotel', 'department', 'role').get(user=user)
            print(f"  - Staff ID: {staff.id}")
            print(f"  - Hotel: {staff.hotel.name} ({staff.hotel.slug})")
            print(f"  - Access Level: {staff.access_level}")
            print(f"  - Department: {staff.department.name if staff.department else 'None'}")
            print(f"  - Role: {staff.role.name if staff.role else 'None'}")
            
            # Check navigation items assigned
            nav_items = staff.allowed_navigation_items.all()
            print(f"  - Navigation items assigned ({nav_items.count()}): {[nav.slug for nav in nav_items]}")
            
            # Check what navigation items exist for this hotel
            hotel_nav_items = NavigationItem.objects.filter(hotel=staff.hotel, is_active=True)
            print(f"  - Available navigation items for hotel ({hotel_nav_items.count()}): {[nav.slug for nav in hotel_nav_items]}")
            
            # Check if missing navigation items
            assigned_slugs = set(nav.slug for nav in nav_items)
            available_slugs = set(nav.slug for nav in hotel_nav_items)
            missing_slugs = available_slugs - assigned_slugs
            
            if missing_slugs:
                print(f"  - MISSING navigation items: {list(missing_slugs)}")
            else:
                print(f"  - All navigation items assigned ✓")
                
        except Staff.DoesNotExist:
            print("  - ERROR: No staff profile found for this superuser!")
            print("  - This superuser cannot login because they have no Staff record")
    
    print(f"\n=== ALL NAVIGATION ITEMS IN SYSTEM ===")
    all_nav_items = NavigationItem.objects.select_related('hotel').all()
    hotels = {}
    
    for nav in all_nav_items:
        hotel_slug = nav.hotel.slug
        if hotel_slug not in hotels:
            hotels[hotel_slug] = []
        hotels[hotel_slug].append(f"{nav.slug} ({nav.name})")
    
    for hotel_slug, nav_list in hotels.items():
        print(f"\nHotel: {hotel_slug}")
        for nav in nav_list:
            print(f"  - {nav}")

def fix_superuser_navigation():
    print(f"\n=== FIXING SUPERUSER NAVIGATION PERMISSIONS ===")
    
    super_users = User.objects.filter(is_superuser=True)
    
    for user in super_users:
        try:
            staff = Staff.objects.get(user=user)
            hotel_nav_items = NavigationItem.objects.filter(hotel=staff.hotel, is_active=True)
            
            print(f"\nFixing navigation for {user.username}...")
            print(f"Assigning {hotel_nav_items.count()} navigation items to superuser")
            
            # Assign ALL navigation items for their hotel to superuser
            staff.allowed_navigation_items.set(hotel_nav_items)
            staff.save()
            
            print(f"✓ Fixed navigation permissions for {user.username}")
            
        except Staff.DoesNotExist:
            print(f"✗ Cannot fix {user.username} - no Staff profile exists")

if __name__ == "__main__":
    check_superuser_login()
    
    # Ask if user wants to fix the issues
    fix_it = input("\nDo you want to fix superuser navigation permissions? (y/n): ").strip().lower()
    if fix_it == 'y':
        fix_superuser_navigation()
        print("\n=== CHECKING AGAIN AFTER FIX ===")
        check_superuser_login()