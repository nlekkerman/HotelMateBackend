import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import PublicSection
from hotel.serializers import PublicSectionStaffSerializer

# Get a section and serialize it
section = PublicSection.objects.get(id=31)
serializer = PublicSectionStaffSerializer(section)
print("Serialized data:")
print(serializer.data)
print("\nKeys in data:")
print(list(serializer.data.keys()))
print(f"\nis_active value: {serializer.data.get('is_active')}")
