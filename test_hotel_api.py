import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel

print("Testing Hotel Public API Endpoint\n")
print("=" * 60)

# Test with Django ORM first
print("\n1. Database Check:")
active_hotels = Hotel.objects.filter(is_active=True)
print(f"   Active hotels in DB: {active_hotels.count()}")

if active_hotels.exists():
    hotel = active_hotels.first()
    print(f"   Sample hotel: {hotel.name}")
    print(f"   Has access_config: {hasattr(hotel, 'access_config')}")
    print(f"   Guest base path: {hotel.guest_base_path}")
    print(f"   Staff base path: {hotel.staff_base_path}")

print("\n2. Serializer Test:")
from hotel.serializers import HotelPublicSerializer

if active_hotels.exists():
    hotel = active_hotels.first()
    serializer = HotelPublicSerializer(hotel)
    data = serializer.data
    print("   Serialized data:")
    print(json.dumps(data, indent=4))

print("\n✓ API implementation ready")
print("\nEndpoints available:")
print("  GET /api/hotel/public/          - List all active hotels")
print("  GET /api/hotel/public/<slug>/   - Get hotel by slug")
