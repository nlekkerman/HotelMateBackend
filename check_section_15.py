import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import PublicSection, PublicElement

# Check section 15
try:
    section = PublicSection.objects.get(id=15)
    print(f"Section 15: {section.name} (Hotel: {section.hotel.name})")
    
    # Check if it has an element
    try:
        element = section.element
        print(f"  ✅ Has element: {element.element_type} - '{element.title}'")
    except PublicElement.DoesNotExist:
        print(f"  ❌ No element exists")
        
except PublicSection.DoesNotExist:
    print("Section 15 does not exist")
