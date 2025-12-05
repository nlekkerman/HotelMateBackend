import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.contrib.auth.models import User
from staff.models import Staff

def fix_user_is_staff():
    print("=== FIXING USER is_staff INCONSISTENCY ===")
    
    # Get the sanja user
    user = User.objects.get(username='sanja')
    staff = Staff.objects.get(user=user)
    
    print('=== CURRENT USER FIELDS ===')
    print(f'User ID: {user.id}')
    print(f'Username: {user.username}')
    print(f'is_staff: {user.is_staff}')
    print(f'is_superuser: {user.is_superuser}')
    print(f'is_active: {user.is_active}')
    
    print('=== CURRENT STAFF FIELDS ===')
    print(f'Staff ID: {staff.id}')
    print(f'access_level: {staff.access_level}')
    print(f'Hotel: {staff.hotel.name}')
    print(f'Role: {staff.role.name if staff.role else None}')
    print(f'Department: {staff.department.name if staff.department else None}')
    
    print('\n=== PROBLEM IDENTIFIED ===')
    print(f'❌ User has access_level "{staff.access_level}" but is_staff={user.is_staff}')
    print('This is inconsistent - staff members should have is_staff=True')
    
    print('\n=== FIXING is_staff FIELD ===')
    # If user has a staff profile with access_level, they should have is_staff=True
    if staff.access_level in ['staff_admin', 'super_staff_admin', 'staff']:
        print(f'✅ User with access_level "{staff.access_level}" should have is_staff=True')
        user.is_staff = True
        user.save()
        print('✅ Updated user.is_staff to True')
        
        # Check if they should also be superuser based on access_level
        if staff.access_level == 'super_staff_admin' and not user.is_superuser:
            print('✅ User with super_staff_admin access should be superuser')
            user.is_superuser = True
            user.save()
            print('✅ Updated user.is_superuser to True')
    else:
        print(f'⚠️  User access_level "{staff.access_level}" - no change needed')
    
    # Refresh and verify
    user.refresh_from_db()
    staff.refresh_from_db()
    
    print(f'\n=== AFTER FIX ===')
    print(f'is_staff: {user.is_staff}')
    print(f'is_superuser: {user.is_superuser}')
    print(f'access_level: {staff.access_level}')
    
    # Check for consistency
    print(f'\n=== CONSISTENCY CHECK ===')
    if user.is_staff and staff.access_level in ['staff_admin', 'super_staff_admin', 'staff']:
        print('✅ is_staff and access_level are now consistent')
    else:
        print('❌ Still inconsistent!')
        
    if user.is_superuser == (staff.access_level == 'super_staff_admin'):
        print('✅ is_superuser and access_level are consistent')
    else:
        print(f'❌ is_superuser ({user.is_superuser}) vs access_level ({staff.access_level}) still inconsistent!')

if __name__ == '__main__':
    fix_user_is_staff()