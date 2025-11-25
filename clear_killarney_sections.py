"""
Clear all public sections from Hotel Killarney.
This prepares the hotel for fresh building from the frontend builder.

Usage:
    python clear_killarney_sections.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, PublicSection

def main():
    try:
        # Get Hotel Killarney (id=2)
        hotel = Hotel.objects.get(id=2)
        print(f"Found hotel: {hotel.name} (slug: {hotel.slug})")
        
        # Count existing sections
        section_count = PublicSection.objects.filter(hotel=hotel).count()
        print(f"Found {section_count} existing sections")
        
        if section_count == 0:
            print("✓ Hotel is already empty - ready for building!")
            return
        
        # Delete all sections (cascades to elements and items)
        PublicSection.objects.filter(hotel=hotel).delete()
        print(f"✓ Deleted {section_count} sections from {hotel.name}")
        print("✓ Hotel is now empty - ready for frontend builder!")
        
    except Hotel.DoesNotExist:
        print("✗ Hotel with id=2 (Killarney) not found")
        print("Available hotels:")
        for h in Hotel.objects.all():
            print(f"  - {h.name} (id={h.id}, slug={h.slug})")

if __name__ == "__main__":
    main()
