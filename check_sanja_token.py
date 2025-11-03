"""Check if Sanja has FCM token saved"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff.models import Staff

sanja = Staff.objects.get(id=36)

print("\n" + "="*60)
print(f"PORTER: {sanja.first_name} {sanja.last_name} (ID: {sanja.id})")
print("="*60)
print(f"Role: {sanja.role}")
print(f"On Duty: {sanja.is_on_duty}")
print(f"Active: {sanja.is_active}")

if sanja.fcm_token:
    token_preview = sanja.fcm_token[:50] + "..." if len(sanja.fcm_token) > 50 else sanja.fcm_token
    print(f"\n✅ FCM Token: {token_preview}")
    print(f"   Token Length: {len(sanja.fcm_token)} characters")
else:
    print(f"\n❌ FCM Token: Not saved yet")
    print("\nTo save FCM token:")
    print("1. Implement Firebase in React web app")
    print("2. Login as Sanja (porter)")
    print("3. Grant browser notification permissions")
    print("4. App will automatically save token via POST /api/staff/save-fcm-token/")

print("="*60 + "\n")
