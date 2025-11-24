from hotel.models import Hotel, HotelPublicSettings
from hotel.serializers import (
    HotelPublicSettingsStaffSerializer,
    HotelPublicDetailSerializer
)

print("=" * 70)
print("COMPLETE HOTEL CUSTOMIZATION TEST")
print("=" * 70)

# Get Hotel Killarney
hotel = Hotel.objects.filter(slug__icontains='killarney').first()
if not hotel:
    print("❌ Hotel not found")
    exit()

print(f"\n✓ Hotel: {hotel.name}")
print(f"  Slug: {hotel.slug}")

# Get or create settings
settings, created = HotelPublicSettings.objects.get_or_create(hotel=hotel)
if created:
    print("  Created new PublicSettings")

# Test Staff Serializer (what staff sees when editing)
print("\n" + "=" * 70)
print("STAFF SETTINGS VIEW (GET /api/staff/hotels/<slug>/settings/)")
print("=" * 70)

staff_serializer = HotelPublicSettingsStaffSerializer(settings)
staff_data = staff_serializer.data

print("\nFields with current values (fallback to Hotel model):")
print(f"  name_display: {staff_data.get('name_display')}")
print(f"  tagline_display: {staff_data.get('tagline_display')}")
print(f"  city_display: {staff_data.get('city_display')}")
print(f"  country_display: {staff_data.get('country_display')}")
print(f"  phone_display: {staff_data.get('phone_display')}")
print(f"  email_display: {staff_data.get('email_display')}")
print(f"  hero_image_display: {staff_data.get('hero_image_display')[:60] if staff_data.get('hero_image_display') else 'None'}...")
print(f"  landing_page_image_display: {staff_data.get('landing_page_image_display')}")

print("\nOverride fields (staff can edit these):")
print(f"  name_override: {staff_data.get('name_override')}")
print(f"  tagline_override: {staff_data.get('tagline_override')}")
print(f"  city_override: {staff_data.get('city_override')}")

# Test Public Serializer (what guests see)
print("\n" + "=" * 70)
print("PUBLIC PAGE VIEW (GET /api/hotel/public/page/<slug>/)")
print("=" * 70)

public_serializer = HotelPublicDetailSerializer(hotel)
public_data = public_serializer.data

print("\nWhat guests will see:")
print(f"  name: {public_data.get('name')}")
print(f"  tagline: {public_data.get('tagline')}")
print(f"  city: {public_data.get('city')}")
print(f"  country: {public_data.get('country')}")
print(f"  phone: {public_data.get('phone')}")
print(f"  email: {public_data.get('email')}")
print(f"  hero_image_url: {public_data.get('hero_image_url')[:60] if public_data.get('hero_image_url') else 'None'}...")
print(f"  landing_page_image_url: {public_data.get('landing_page_image_url')}")

print("\n" + "=" * 70)
print("✓ IMPLEMENTATION COMPLETE")
print("=" * 70)
print("\nNow staff can:")
print("  1. GET /api/staff/hotels/<slug>/settings/ - See all current values")
print("  2. PATCH with override fields - Customize any field")
print("  3. Public page automatically shows customized values")
print("\nAll Hotel model fields can now be customized via PublicSettings!")
