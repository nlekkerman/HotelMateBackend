from hotel.models import Hotel, HotelPublicSettings
from hotel.serializers import HotelPublicSettingsStaffSerializer

# Get Hotel Killarney
hotel = Hotel.objects.filter(slug__icontains='killarney').first()
if hotel:
    # Get or create settings
    settings, created = HotelPublicSettings.objects.get_or_create(hotel=hotel)
    
    # Serialize with staff serializer
    serializer = HotelPublicSettingsStaffSerializer(settings)
    data = serializer.data
    
    print("=" * 60)
    print("SETTINGS API RESPONSE (what staff sees when editing):")
    print("=" * 60)
    print(f"hero_image (editable): {data.get('hero_image')}")
    print(f"hero_image_display (current shown): {data.get('hero_image_display')}")
    print()
    print(f"logo (editable): {data.get('logo')}")
    print(f"logo_display (current shown): {data.get('logo_display')}")
    print("=" * 60)
    print("\nThis means:")
    print("- hero_image_display shows what's CURRENTLY displayed")
    print("- Staff can edit hero_image to customize it")
    print("- Once edited, hero_image_display will show the new value")
else:
    print("Hotel not found")
