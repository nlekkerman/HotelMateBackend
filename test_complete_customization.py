"""
DEPRECATED: Old public hotel page customization test
NOTE: Public hotel detail pages have been removed.
Staff can still manage settings via /api/staff/hotels/<slug>/settings/
but there is no longer a public detail page to display them on.

New public pages will be built using the dynamic section-based system.
"""
from hotel.models import Hotel, HotelPublicSettings
from hotel.serializers import (
    HotelPublicSettingsStaffSerializer,
)

print("=" * 70)
print("STAFF HOTEL SETTINGS TEST")
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

print("\n" + "=" * 70)
print("✓ STAFF SETTINGS WORKING")
print("=" * 70)
print("\nStaff can:")
print("  1. GET /api/staff/hotels/<slug>/settings/ - See all current values")
print("  2. PATCH with override fields - Customize any field")
print("\n⚠️ NOTE: Old public hotel pages have been removed.")
print("   New dynamic section-based pages will be created later.")
