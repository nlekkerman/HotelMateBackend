"""
Clear all branding and content from Hotel Killarney.
This prepares the hotel for fresh setup from the frontend.

Clears:
- Hero image
- Logo
- Tagline
- Short/long descriptions
- Tags
- Booking URL
- All public sections (already done)

Usage:
    python clear_killarney_hotel.py
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
        print("=" * 50)
        
        # Clear sections first
        section_count = PublicSection.objects.filter(hotel=hotel).count()
        if section_count > 0:
            PublicSection.objects.filter(hotel=hotel).delete()
            print(f"✓ Deleted {section_count} public sections")
        else:
            print("✓ No public sections to clear")
        
        # Clear hotel branding/content fields
        hotel.hero_image = None
        hotel.logo = None
        hotel.tagline = ""
        hotel.short_description = ""
        hotel.long_description = ""
        hotel.tags = []
        hotel.booking_url = ""
        hotel.website_url = ""
        
        hotel.save()
        
        print("\n✓ Cleared hotel fields:")
        print("  - Hero image")
        print("  - Logo")
        print("  - Tagline")
        print("  - Short description")
        print("  - Long description")
        print("  - Tags")
        print("  - Booking URL")
        print("  - Website URL")
        
        print("\n" + "=" * 50)
        print(f"✓ {hotel.name} is now blank!")
        print("  Ready for fresh setup from frontend builder")
        
        print("\nRemaining info:")
        print(f"  Name: {hotel.name}")
        print(f"  Slug: {hotel.slug}")
        print(f"  City: {hotel.city}")
        print(f"  Country: {hotel.country}")
        print(f"  Address: {hotel.address_line_1}")
        
    except Hotel.DoesNotExist:
        print("✗ Hotel with id=2 (Killarney) not found")
        print("Available hotels:")
        for h in Hotel.objects.all():
            print(f"  - {h.name} (id={h.id}, slug={h.slug})")

if __name__ == "__main__":
    main()
