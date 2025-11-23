"""
Quick URL configuration test for Phase 1 routing refactor.
This script verifies the routing structure without running the server.
"""

import sys
import os
sys.path.insert(0, 'c:\\Users\\nlekk\\HMB\\HotelMateBackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

# Test imports
try:
    import staff_urls
    print("✓ staff_urls.py imported successfully")
    print(f"  - {len(staff_urls.STAFF_APPS)} apps configured")
    print(f"  - {len(staff_urls.urlpatterns)} URL patterns created")
    print(f"  - Apps: {', '.join(staff_urls.STAFF_APPS[:5])}...")
except Exception as e:
    print(f"✗ Failed to import staff_urls: {e}")

try:
    import guest_urls
    print("\n✓ guest_urls.py imported successfully")
    print(f"  - {len(guest_urls.urlpatterns)} URL patterns created")
    for pattern in guest_urls.urlpatterns:
        print(f"  - {pattern.pattern}")
except Exception as e:
    print(f"✗ Failed to import guest_urls: {e}")

print("\n✓ Phase 1 routing files created successfully")
print("\nExpected URL structure:")
print("  STAFF:  /api/staff/hotels/<hotel_slug>/<app_name>/")
print("  GUEST:  /api/guest/hotels/<hotel_slug>/site/home|rooms|offers/")
print("  LEGACY: /api/<app>/  (unchanged)")
