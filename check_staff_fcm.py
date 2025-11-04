import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff.models import Staff

staff_with_tokens = Staff.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='')
print(f'\n✅ Staff with FCM tokens: {staff_with_tokens.count()}\n')

for s in staff_with_tokens:
    print(f'Staff {s.id} ({s.user.username}): {s.fcm_token[:30]}...')

all_staff = Staff.objects.all()
print(f'\n📊 Total staff: {all_staff.count()}')
print(f'📊 Staff without tokens: {all_staff.count() - staff_with_tokens.count()}')

# Check front-office and reception staff
front_office_staff = Staff.objects.filter(role__name__in=['front-office', 'reception'])
print(f'\n🔵 Front-office/Reception staff: {front_office_staff.count()}')
front_office_with_tokens = front_office_staff.exclude(fcm_token__isnull=True).exclude(fcm_token='')
print(f'🔵 Front-office staff with tokens: {front_office_with_tokens.count()}')
