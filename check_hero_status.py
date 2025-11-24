from hotel.models import Hotel, HotelPublicSettings

# Check Hotel Killarney
hotel = Hotel.objects.filter(slug__icontains='killarney').first()
if hotel:
    print("=" * 50)
    print(f"Hotel: {hotel.name}")
    hero_url = hotel.hero_image.url if hotel.hero_image else None
    print(f"Hotel.hero_image: {hero_url}")
    
    # Check if public_settings exists
    try:
        settings = hotel.public_settings
        settings_hero = settings.hero_image if settings.hero_image else None
        print(f"PublicSettings.hero_image: {settings_hero}")
        print("=" * 50)
        print("\nCurrent behavior:")
        print("Public page will show:", settings_hero or hero_url or "No image")
        print("\nTo change hero image, update PublicSettings.hero_image")
    except HotelPublicSettings.DoesNotExist:
        print("No PublicSettings found")
        print("Creating PublicSettings now...")
        settings = HotelPublicSettings.objects.create(hotel=hotel)
        print("PublicSettings created!")
        print("=" * 50)
else:
    print("Hotel Killarney not found")
