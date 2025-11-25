"""
Check staff authentication setup
Diagnose "No Staff matches" error
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from staff.models import Staff

print('\n' + '='*60)
print('  Staff Authentication Diagnostic')
print('='*60)

# Check all users
users = User.objects.all()
print(f'\n📍 Total Users: {users.count()}')

for user in users:
    print(f'\n--- User: {user.username} ---')
    print(f'  ID: {user.id}')
    print(f'  Email: {user.email}')
    print(f'  Is Active: {user.is_active}')
    
    # Check token
    try:
        token = Token.objects.get(user=user)
        print(f'  ✓ Token: {token.key[:20]}...')
    except Token.DoesNotExist:
        print(f'  ✗ No token')
    
    # Check staff profile
    try:
        staff = user.staff_profile
        print(f'  ✓ Staff Profile: {staff}')
        print(f'     Hotel: {staff.hotel.name} ({staff.hotel.slug})')
        print(f'     Role: {staff.role}')
    except:
        print(f'  ✗ NO STAFF PROFILE - This is the problem!')
        print(f'     User exists but has no staff_profile relation')

# Check staff without users
print('\n' + '='*60)
print('  Staff Records Without Users')
print('='*60)

all_staff = Staff.objects.all()
print(f'\n📍 Total Staff: {all_staff.count()}')

for staff in all_staff:
    if not staff.user:
        print(f'\n✗ Staff without user: {staff}')
        print(f'  Hotel: {staff.hotel.name}')
        print(f'  Name: {staff.first_name} {staff.last_name}')

print('\n' + '='*60)
print('  Solution')
print('='*60)
print('\nIf you see "NO STAFF PROFILE" above:')
print('  1. Create staff profile for the user')
print('  2. Or login with a user that has staff profile')
print('  3. Or link existing staff to user')
print('\nTo create staff profile in Django shell:')
print('  from staff.models import Staff')
print('  from hotel.models import Hotel')
print('  from django.contrib.auth.models import User')
print('  ')
print('  user = User.objects.get(username="your-username")')
print('  hotel = Hotel.objects.get(slug="hotel-killarney")')
print('  ')
print('  staff = Staff.objects.create(')
print('      user=user,')
print('      hotel=hotel,')
print('      first_name="John",')
print('      last_name="Doe",')
print('      email=user.email')
print('  )')
print('\n' + '='*60 + '\n')
