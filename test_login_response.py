#!/usr/bin/env python
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff.models import Staff, NavigationItem
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from staff.serializers import StaffLoginOutputSerializer

def test_login_response():
    print("=== TESTING SUPERUSER LOGIN RESPONSE ===\n")
    
    # Get the superuser
    try:
        user = User.objects.get(username='nikola', is_superuser=True)
        print(f"Testing login for superuser: {user.username}")
        
        # Get or create token (simulating login)
        token, created = Token.objects.get_or_create(user=user)
        print(f"Token: {token.key}")
        
        # Get staff profile
        staff = Staff.objects.select_related(
            'department', 'hotel', 'role'
        ).prefetch_related('allowed_navigation_items').get(user=user)
        
        # Build the same data structure as CustomAuthToken
        hotel_id = staff.hotel.id if staff and staff.hotel else None
        hotel_name = staff.hotel.name if staff and staff.hotel else None
        hotel_slug = staff.hotel.slug if staff and staff.hotel else None
        access_level = staff.access_level if staff else None
        
        profile_image_url = None
        if staff and staff.profile_image:
            profile_image_url = str(staff.profile_image)
        
        # Get allowed navigation slugs from database
        allowed_navs = [
            nav.slug for nav in staff.allowed_navigation_items.filter(
                is_active=True
            )
        ]
        
        data = {
            'staff_id': staff.id,
            'token': token.key,
            'username': user.username,
            'hotel_id': hotel_id,
            'hotel_name': hotel_name,
            'hotel_slug': hotel_slug,
            'hotel': {
                'id': hotel_id,
                'name': hotel_name,
                'slug': hotel_slug,
            },
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'access_level': access_level,
            'allowed_navs': allowed_navs,
            'profile_image_url': profile_image_url,
            'role': staff.role.name if staff.role else None,
            'department': staff.department.name if staff.department else None,
        }
        
        print(f"\n=== RAW LOGIN RESPONSE DATA ===")
        print(json.dumps(data, indent=2))
        
        # Test serializer validation
        print(f"\n=== TESTING SERIALIZER ===")
        output_serializer = StaffLoginOutputSerializer(data=data)
        if output_serializer.is_valid():
            print("✅ Serializer validation PASSED")
            print("Final serialized data:")
            print(json.dumps(output_serializer.data, indent=2))
        else:
            print("❌ Serializer validation FAILED")
            print("Errors:")
            print(json.dumps(output_serializer.errors, indent=2))
            
        # Check specific superuser privileges that should be available
        print(f"\n=== SUPERUSER PRIVILEGES CHECK ===")
        print(f"✅ Can access Django Admin: {user.is_superuser and user.is_staff}")
        print(f"✅ Can create navigation items: {user.is_superuser}")
        print(f"✅ Can manage all staff: {staff.access_level == 'super_staff_admin'}")
        print(f"✅ Has all navigation permissions: {len(allowed_navs) == NavigationItem.objects.filter(hotel=staff.hotel, is_active=True).count()}")
        
        # Check what frontend should save
        print(f"\n=== WHAT FRONTEND SHOULD SAVE ===")
        print(f"🔑 Authentication Token: {data['token']}")
        print(f"👤 User Info: staff_id={data['staff_id']}, username={data['username']}")
        print(f"🏨 Hotel Context: {data['hotel']}")
        print(f"🔒 Permissions: is_superuser={data['is_superuser']}, access_level={data['access_level']}")
        print(f"🧭 Navigation Access: {len(data['allowed_navs'])} items = {data['allowed_navs']}")
        
    except User.DoesNotExist:
        print("❌ Superuser 'nikola' not found")
    except Staff.DoesNotExist:
        print("❌ Staff profile for superuser not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login_response()