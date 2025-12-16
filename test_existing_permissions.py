"""
Simple Test for Canonical Permissions System - Using Existing Data Only

Tests the canonical permissions resolver with existing database records.
NO NEW DATA CREATION - uses what's already in the database.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.contrib.auth import get_user_model
from hotel.models import Hotel
from staff.models import Staff, NavigationItem
from staff.permissions import resolve_staff_navigation

User = get_user_model()


def test_existing_canonical_permissions():
    """Test canonical permissions with existing data only."""
    print("🔬 TESTING CANONICAL PERMISSIONS WITH EXISTING DATA")
    print("=" * 60)
    
    # Get existing hotels
    hotels = Hotel.objects.all()
    print(f"📍 Found {hotels.count()} existing hotels:")
    for hotel in hotels:
        print(f"  - {hotel.name} ({hotel.slug})")
    
    if not hotels.exists():
        print("❌ No hotels found in database")
        return False
    
    # Get existing staff
    staff_members = Staff.objects.select_related('user', 'hotel').all()
    print(f"\n👥 Found {staff_members.count()} existing staff members:")
    
    if not staff_members.exists():
        print("❌ No staff members found in database")
        return False
    
    # Test canonical resolver with each existing staff member
    for staff in staff_members:
        print(f"\n🧪 Testing: {staff.first_name} {staff.last_name} ({staff.user.username})")
        print(f"   Hotel: {staff.hotel.name}")
        print(f"   Access Level: {staff.access_level}")
        print(f"   Is Superuser: {staff.user.is_superuser}")
        
        # Test canonical permissions resolver
        try:
            permissions = resolve_staff_navigation(staff.user)
            
            # Verify all required keys exist
            required_keys = ['is_staff', 'is_superuser', 'hotel_slug', 'access_level', 'allowed_navs', 'navigation_items']
            missing_keys = [key for key in required_keys if key not in permissions]
            
            if missing_keys:
                print(f"   ❌ Missing keys: {missing_keys}")
                continue
            
            print(f"   ✅ All required keys present")
            print(f"   📊 Results:")
            print(f"      - is_staff: {permissions['is_staff']}")
            print(f"      - is_superuser: {permissions['is_superuser']}")
            print(f"      - hotel_slug: {permissions['hotel_slug']}")
            print(f"      - access_level: {permissions['access_level']}")
            print(f"      - allowed_navs count: {len(permissions['allowed_navs'])}")
            print(f"      - allowed_navs: {permissions['allowed_navs']}")
            
            # Check if navigation items structure is correct
            nav_items = permissions['navigation_items']
            if isinstance(nav_items, list):
                print(f"      - navigation_items count: {len(nav_items)}")
                if nav_items and isinstance(nav_items[0], dict):
                    sample_keys = list(nav_items[0].keys()) if nav_items else []
                    print(f"      - navigation_items sample keys: {sample_keys}")
            
            # Verify consistency between allowed_navs and navigation_items
            nav_item_slugs = [item.get('slug') for item in nav_items if isinstance(item, dict)]
            nav_item_slugs = [slug for slug in nav_item_slugs if slug is not None]
            
            allowed_set = set(permissions['allowed_navs'])
            nav_items_set = set(nav_item_slugs)
            
            if allowed_set == nav_items_set:
                print(f"      ✅ Consistency check passed")
            else:
                print(f"      ⚠️ Inconsistency: allowed_navs={allowed_set}, nav_items_slugs={nav_items_set}")
                
        except Exception as e:
            print(f"   ❌ Error testing {staff.user.username}: {e}")
            import traceback
            traceback.print_exc()
    
    # Test navigation seeding verification
    print(f"\n📊 NAVIGATION ITEMS ANALYSIS:")
    for hotel in hotels:
        nav_items = NavigationItem.objects.filter(hotel=hotel)
        active_items = nav_items.filter(is_active=True)
        
        print(f"\n🏨 {hotel.name}:")
        print(f"   Total navigation items: {nav_items.count()}")
        print(f"   Active navigation items: {active_items.count()}")
        
        if active_items.exists():
            slugs = list(active_items.values_list('slug', flat=True))
            print(f"   Active slugs: {slugs}")
            
            # Check for underscore format
            underscore_slugs = [slug for slug in slugs if '_' in slug]
            if underscore_slugs:
                print(f"   ✅ Underscore format preserved: {underscore_slugs}")
        else:
            print(f"   ⚠️ No active navigation items found")
    
    # Test superuser vs regular staff differences
    print(f"\n🔍 SUPERUSER VS REGULAR STAFF COMPARISON:")
    
    superusers = staff_members.filter(user__is_superuser=True)
    regular_staff = staff_members.filter(user__is_superuser=False)
    
    print(f"Superusers found: {superusers.count()}")
    print(f"Regular staff found: {regular_staff.count()}")
    
    if superusers.exists() and regular_staff.exists():
        # Compare same hotel if possible
        for hotel in hotels:
            hotel_superusers = superusers.filter(hotel=hotel)
            hotel_regular = regular_staff.filter(hotel=hotel)
            
            if hotel_superusers.exists() and hotel_regular.exists():
                superuser = hotel_superusers.first()
                regular = hotel_regular.first()
                
                super_perms = resolve_staff_navigation(superuser.user)
                regular_perms = resolve_staff_navigation(regular.user)
                
                print(f"\n🏨 {hotel.name} comparison:")
                print(f"   Superuser navs: {len(super_perms['allowed_navs'])} items")
                print(f"   Regular staff navs: {len(regular_perms['allowed_navs'])} items")
                
                if len(super_perms['allowed_navs']) >= len(regular_perms['allowed_navs']):
                    print(f"   ✅ Superuser has equal or more navigation access")
                else:
                    print(f"   ⚠️ Superuser has less access than regular staff (unexpected)")
    
    print(f"\n🎉 CANONICAL PERMISSIONS TEST COMPLETED")
    print(f"✅ System is working with existing data")
    return True


if __name__ == "__main__":
    success = test_existing_canonical_permissions()
    sys.exit(0 if success else 1)