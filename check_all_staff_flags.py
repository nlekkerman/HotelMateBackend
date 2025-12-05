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
from hotel.models import Hotel

def check_all_killarney_staff():
    print("=== CHECKING ALL HOTEL KILLARNEY STAFF is_staff FLAGS ===")
    
    try:
        # Get Hotel Killarney
        hotel = Hotel.objects.get(slug='hotel-killarney')
        print(f"Hotel: {hotel.name} (ID: {hotel.id})")
        
        # Get all staff for this hotel
        staff_members = Staff.objects.filter(hotel=hotel).select_related('user', 'role', 'department')
        print(f"Total staff members: {staff_members.count()}")
        
        print("\n=== STAFF MEMBERS ANALYSIS ===")
        inconsistent_count = 0
        
        for i, staff in enumerate(staff_members, 1):
            user = staff.user
            
            print(f"\n{i}. Staff ID: {staff.id}")
            print(f"   Username: {user.username}")
            print(f"   Name: {staff.first_name} {staff.last_name}")
            print(f"   Role: {staff.role.name if staff.role else 'No Role'}")
            print(f"   Department: {staff.department.name if staff.department else 'No Department'}")
            print(f"   Access Level: {staff.access_level}")
            print(f"   User is_staff: {user.is_staff}")
            print(f"   User is_superuser: {user.is_superuser}")
            print(f"   User is_active: {user.is_active}")
            
            # Check for inconsistencies
            should_be_staff = staff.access_level in ['staff', 'staff_admin', 'super_staff_admin']
            should_be_superuser = staff.access_level == 'super_staff_admin'
            
            issues = []
            if should_be_staff and not user.is_staff:
                issues.append(f"Should have is_staff=True (has access_level='{staff.access_level}')")
                
            if not should_be_staff and user.is_staff:
                issues.append(f"Should have is_staff=False (has access_level='{staff.access_level}')")
                
            if should_be_superuser and not user.is_superuser:
                issues.append(f"Should have is_superuser=True (has access_level='{staff.access_level}')")
                
            if not should_be_superuser and user.is_superuser:
                issues.append(f"Should have is_superuser=False (has access_level='{staff.access_level}')")
            
            if issues:
                print(f"   ❌ INCONSISTENCIES:")
                for issue in issues:
                    print(f"      - {issue}")
                inconsistent_count += 1
            else:
                print(f"   ✅ Consistent")
        
        print(f"\n=== SUMMARY ===")
        print(f"Total staff: {staff_members.count()}")
        print(f"Inconsistent staff: {inconsistent_count}")
        print(f"Consistent staff: {staff_members.count() - inconsistent_count}")
        
        if inconsistent_count > 0:
            print(f"\n=== FIXING INCONSISTENCIES ===")
            fix_count = 0
            
            for staff in staff_members:
                user = staff.user
                should_be_staff = staff.access_level in ['staff', 'staff_admin', 'super_staff_admin']
                should_be_superuser = staff.access_level == 'super_staff_admin'
                
                updated = False
                if should_be_staff != user.is_staff:
                    print(f"Fixing {user.username}: is_staff {user.is_staff} -> {should_be_staff}")
                    user.is_staff = should_be_staff
                    updated = True
                    
                if should_be_superuser != user.is_superuser:
                    print(f"Fixing {user.username}: is_superuser {user.is_superuser} -> {should_be_superuser}")
                    user.is_superuser = should_be_superuser
                    updated = True
                
                if updated:
                    user.save()
                    fix_count += 1
            
            print(f"✅ Fixed {fix_count} staff members")
        else:
            print("✅ All staff members are consistent!")
            
    except Hotel.DoesNotExist:
        print("❌ Hotel Killarney not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_all_killarney_staff()