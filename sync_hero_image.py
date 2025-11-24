from hotel.models import Hotel, HotelPublicSettings

# Sync Hotel Killarney hero image to PublicSettings
hotel = Hotel.objects.filter(slug__icontains='killarney').first()
if hotel:
    settings, created = HotelPublicSettings.objects.get_or_create(hotel=hotel)
    
    if hotel.hero_image:
        # Copy the hero_image URL to public_settings
        settings.hero_image = hotel.hero_image.url
        settings.save()
        print(f"✓ Synced hero image to PublicSettings")
        print(f"  URL: {settings.hero_image}")
    else:
        print("Hotel has no hero_image to sync")
else:
    print("Hotel not found")
