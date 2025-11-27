"""
Quick test to check the actual API response for section_type field.
Run: python test_api_response.py
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, PublicSection
from hotel.public_serializers import PublicSectionDetailSerializer

# Get hotel and sections
hotel = Hotel.objects.get(id=2)
sections = hotel.public_sections.filter(is_active=True).order_by('position')

print("=" * 80)
print("CHECKING API RESPONSE STRUCTURE")
print("=" * 80)

for section in sections:
    serializer = PublicSectionDetailSerializer(section)
    data = serializer.data
    
    print(f"\nSection: {data.get('name')}")
    print(f"  section_type field: '{data.get('section_type')}'")
    print(f"  Has section_type: {('section_type' in data)}")
    
    # Show all top-level keys
    print(f"  All keys: {list(data.keys())}")
    
    # Pretty print first section for inspection
    if section.position == 0:
        print(f"\n  Full data structure:")
        print(json.dumps(data, indent=2, default=str)[:500])

print("\n" + "=" * 80)
