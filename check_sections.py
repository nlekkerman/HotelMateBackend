import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import PublicSection

# Check recent sections
sections = PublicSection.objects.filter(id__in=[31, 32, 33]).values('id', 'name', 'is_active', 'position')
for section in sections:
    print(f"Section {section['id']}: {section['name']} - is_active: {section['is_active']} - position: {section['position']}")
