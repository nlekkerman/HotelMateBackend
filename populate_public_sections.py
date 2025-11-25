"""
Populate hotels with public page sections (hero, gallery, room_types, features).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, PublicSection, PublicElement, PublicElementItem
from rooms.models import RoomType


def clear_existing_sections(hotel):
    """Remove all existing public sections for a hotel."""
    hotel.public_sections.all().delete()
    print(f"  ✓ Cleared existing sections for {hotel.name}")


def create_hero_section(hotel, position=0):
    """Create hero section with title, subtitle, and image."""
    section = PublicSection.objects.create(
        hotel=hotel,
        position=position,
        is_active=True,
        name="Hero Banner"
    )
    
    # Use hotel's hero_image if available
    hero_image_url = str(hotel.hero_image.url) if hotel.hero_image else ""
    
    element = PublicElement.objects.create(
        section=section,
        element_type="hero",
        title=hotel.name,
        subtitle=hotel.tagline or "Welcome to our hotel",
        body=hotel.long_description or hotel.short_description,
        image_url=hero_image_url,
        settings={
            "cta_label": "Book Now",
            "cta_url": hotel.booking_url or "#booking",
            "overlay": True
        }
    )
    
    print(f"  ✓ Created hero section (image: {'Yes' if hero_image_url else 'No'})")
    return section


def create_gallery_section(hotel, position=1):
    """Create gallery section with sample images."""
    section = PublicSection.objects.create(
        hotel=hotel,
        position=position,
        is_active=True,
        name="Photo Gallery"
    )
    
    element = PublicElement.objects.create(
        section=section,
        element_type="gallery",
        title="Explore Our Hotel",
        subtitle="Take a virtual tour",
        settings={
            "layout": "grid",
            "columns": 3
        }
    )
    
    # Sample gallery items
    gallery_items = [
        {
            "title": "Luxury Rooms",
            "subtitle": "Elegantly designed",
            "image_url": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?w=800"
        },
        {
            "title": "Swimming Pool",
            "subtitle": "Relax and unwind",
            "image_url": "https://images.unsplash.com/photo-1575429198097-0414ec08e8cd?w=800"
        },
        {
            "title": "Restaurant",
            "subtitle": "Fine dining experience",
            "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800"
        },
        {
            "title": "Spa & Wellness",
            "subtitle": "Rejuvenate your senses",
            "image_url": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=800"
        },
        {
            "title": "Conference Room",
            "subtitle": "Modern facilities",
            "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800"
        },
        {
            "title": "Bar & Lounge",
            "subtitle": "Evening entertainment",
            "image_url": "https://images.unsplash.com/photo-1572116469696-31de0f17cc34?w=800"
        }
    ]
    
    for idx, item_data in enumerate(gallery_items):
        PublicElementItem.objects.create(
            element=element,
            title=item_data["title"],
            subtitle=item_data["subtitle"],
            image_url=item_data["image_url"],
            sort_order=idx,
            is_active=True
        )
    
    print(f"  ✓ Created gallery section with {len(gallery_items)} images")
    return section


def create_rooms_list_section(hotel, position=2):
    """Create room_types section (auto-populated from RoomType model)."""
    section = PublicSection.objects.create(
        hotel=hotel,
        position=position,
        is_active=True,
        name="Our Rooms"
    )
    
    element = PublicElement.objects.create(
        section=section,
        element_type="rooms_list",
        title="Accommodation Options",
        subtitle="Choose your perfect room",
        settings={
            "display_mode": "cards",
            "show_pricing": True
        }
    )
    
    # Count active room types
    room_count = RoomType.objects.filter(hotel=hotel, is_active=True).count()
    print(f"  ✓ Created rooms_list section (will auto-show {room_count} room types)")
    return section


def create_features_section(hotel, position=3):
    """Create features/amenities section."""
    section = PublicSection.objects.create(
        hotel=hotel,
        position=position,
        is_active=True,
        name="Hotel Features"
    )
    
    element = PublicElement.objects.create(
        section=section,
        element_type="features",
        title="World-Class Amenities",
        subtitle="Everything you need for a perfect stay"
    )
    
    # Sample features
    features = [
        {
            "title": "Free WiFi",
            "body": "High-speed internet throughout the hotel",
            "badge": "🌐"
        },
        {
            "title": "24/7 Reception",
            "body": "Always here to assist you",
            "badge": "🔔"
        },
        {
            "title": "Room Service",
            "body": "Dining delivered to your door",
            "badge": "🍽️"
        },
        {
            "title": "Fitness Center",
            "body": "State-of-the-art gym equipment",
            "badge": "💪"
        },
        {
            "title": "Parking",
            "body": "Complimentary on-site parking",
            "badge": "🚗"
        },
        {
            "title": "Pet Friendly",
            "body": "Your furry friends are welcome",
            "badge": "🐕"
        }
    ]
    
    for idx, feature in enumerate(features):
        PublicElementItem.objects.create(
            element=element,
            title=feature["title"],
            body=feature["body"],
            badge=feature["badge"],
            sort_order=idx,
            is_active=True
        )
    
    print(f"  ✓ Created features section with {len(features)} amenities")
    return section


def populate_hotel(hotel):
    """Populate a single hotel with all sections."""
    print(f"\n📍 Populating: {hotel.name}")
    
    # Clear existing sections first
    clear_existing_sections(hotel)
    
    # Create sections in order
    create_hero_section(hotel, position=0)
    create_gallery_section(hotel, position=1)
    create_rooms_list_section(hotel, position=2)
    create_features_section(hotel, position=3)
    
    print(f"✅ Completed {hotel.name}\n")


def main():
    print("=" * 60)
    print("🏨 POPULATING PUBLIC PAGE SECTIONS FOR HOTELS")
    print("=" * 60)
    
    # Fetch all active hotels
    hotels = Hotel.objects.filter(is_active=True)
    
    if not hotels.exists():
        print("❌ No active hotels found!")
        return
    
    print(f"\nFound {hotels.count()} active hotel(s)")
    
    for hotel in hotels:
        populate_hotel(hotel)
    
    print("=" * 60)
    print("✅ ALL HOTELS POPULATED SUCCESSFULLY!")
    print("=" * 60)
    print("\n📝 Summary:")
    print(f"   - Hero sections created: {hotels.count()}")
    print(f"   - Gallery sections created: {hotels.count()}")
    print(f"   - Rooms_list sections created: {hotels.count()}")
    print(f"   - Features sections created: {hotels.count()}")
    print(f"\n🔗 Test the endpoint:")
    for hotel in hotels:
        print(f"   GET /api/public/hotel/{hotel.slug}/page/")


if __name__ == "__main__":
    main()
