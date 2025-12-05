import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.contrib.auth.models import User
from staff.models import Staff, NavigationItem
from staff.serializers import StaffLoginOutputSerializer

def test_login_serializer():
    print("=== TESTING STAFF LOGIN OUTPUT SERIALIZER ===")
    
    # Get the sanja user
    try:
        user = User.objects.get(username='sanja')
        staff = Staff.objects.select_related('department', 'hotel', 'role').prefetch_related('allowed_navigation_items').get(user=user)
    except Exception as e:
        print(f"Error getting user/staff: {e}")
        return
    
    print('=== DATABASE VALUES ===')
    print(f'User ID: {user.id}')
    print(f'Username: {user.username}')
    print(f'is_superuser: {user.is_superuser}')
    print(f'is_staff: {user.is_staff}')
    print(f'Staff ID: {staff.id}')
    print(f'Staff access_level: {staff.access_level}')
    print(f'Staff hotel: {staff.hotel.name if staff.hotel else None}')
    print(f'Staff role: {staff.role.name if staff.role else None}')
    print(f'Staff department: {staff.department.name if staff.department else None}')
    
    # Create the data dict exactly like the CustomAuthToken view does
    hotel_id = staff.hotel.id if staff and staff.hotel else None
    hotel_name = staff.hotel.name if staff and staff.hotel else None
    hotel_slug = staff.hotel.slug if staff and staff.hotel else None
    access_level = staff.access_level if staff else None
    
    profile_image_url = None
    if staff and staff.profile_image:
        profile_image_url = str(staff.profile_image)
    
    # Get navigation items exactly like the view does
    if user.is_superuser:
        print(f"🔍 User is superuser, getting ALL navigation items for hotel: {staff.hotel}")
        nav_items = NavigationItem.objects.filter(
            hotel=staff.hotel,
            is_active=True
        )
        print(f"🔍 Found {nav_items.count()} active navigation items")
        allowed_navs = [nav.slug for nav in nav_items]
        print(f"🔍 Navigation slugs: {allowed_navs}")
    else:
        print(f"🔍 User is regular staff, getting assigned navigation items")
        nav_items = staff.allowed_navigation_items.filter(is_active=True)
        print(f"🔍 Found {nav_items.count()} allowed navigation items")
        allowed_navs = [nav.slug for nav in nav_items]
        print(f"🔍 Navigation slugs: {allowed_navs}")
    
    # Create the exact data dictionary from CustomAuthToken view
    data = {
        'staff_id': staff.id,
        'token': 'dummy-token-for-testing',
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
        'isAdmin': user.is_superuser,  # Add isAdmin field for frontend compatibility
        'access_level': access_level,
        'allowed_navs': allowed_navs,
        'navigation_items': allowed_navs,  # Provide same data in navigation_items field
        'profile_image_url': profile_image_url,
        'role': staff.role.name if staff.role else None,
        'department': staff.department.name if staff.department else None,
    }
    
    print('\n=== DATA DICT BEFORE SERIALIZER ===')
    for key, value in data.items():
        if isinstance(value, dict):
            print(f'{key}: {value}')
        elif isinstance(value, list):
            print(f'{key}: {value} (length: {len(value)})')
        else:
            print(f'{key}: {repr(value)} (type: {type(value).__name__})')
    
    # Test the serializer
    print('\n=== TESTING SERIALIZER ===')
    try:
        serializer = StaffLoginOutputSerializer(data=data)
        is_valid = serializer.is_valid()
        print(f'Serializer is_valid(): {is_valid}')
        
        if not is_valid:
            print('❌ SERIALIZER VALIDATION ERRORS:')
            for field, errors in serializer.errors.items():
                print(f'  {field}: {errors}')
        else:
            print('✅ SERIALIZER VALIDATION PASSED')
            
            print('\n=== SERIALIZER.VALIDATED_DATA ===')
            validated_data = serializer.validated_data
            for key, value in validated_data.items():
                print(f'{key}: {repr(value)} (type: {type(value).__name__})')
            
            print('\n=== SERIALIZER.DATA (FINAL OUTPUT TO FRONTEND) ===')
            final_data = serializer.data
            for key, value in final_data.items():
                print(f'{key}: {repr(value)} (type: {type(value).__name__})')
            
            # Check for critical fields that are showing as undefined in frontend
            critical_fields = ['is_superuser', 'access_level', 'allowed_navs', 'staff_id', 'is_staff']
            print('\n=== CRITICAL FIELDS CHECK ===')
            for field in critical_fields:
                if field in final_data:
                    value = final_data[field]
                    if value is None:
                        print(f'⚠️  {field}: None (will be null in JSON)')
                    else:
                        print(f'✅ {field}: {repr(value)}')
                else:
                    print(f'❌ {field}: MISSING from output')
    
    except Exception as e:
        print(f'❌ ERROR testing serializer: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_login_serializer()