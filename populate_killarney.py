"""
Populate Hotel Killarney with complete public page data
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, BookingOptions, Offer, LeisureActivity
from rooms.models import RoomType
from datetime import date, timedelta

def populate_killarney():
    """Populate Hotel Killarney with all required data"""
    
    # Get Hotel Killarney
    hotel = Hotel.objects.get(id=2, slug='hotel-killarney')
    print(f"Populating data for: {hotel.name}")
    
    # 1. Update Hotel basic info
    hotel.tagline = "Your Gateway to Ireland's Natural Beauty"
    hotel.long_description = """Nestled in the heart of County Kerry, Hotel Killarney offers an unparalleled experience where luxury meets Ireland's breathtaking landscapes. Our hotel serves as the perfect base for exploring Killarney National Park, the Ring of Kerry, and the stunning lakes that have made this region famous worldwide.

With elegant accommodations, world-class dining, and warm Irish hospitality, we provide everything you need for an unforgettable stay. Whether you're here for adventure, relaxation, or romance, Hotel Killarney delivers exceptional service in one of Ireland's most beautiful settings."""
    
    hotel.address_line_1 = "College Street"
    hotel.address_line_2 = "Killarney"
    hotel.city = "Killarney"
    hotel.postal_code = "V93 X2C4"
    hotel.country = "Ireland"
    hotel.latitude = 52.0599
    hotel.longitude = -9.5044
    
    hotel.phone = "+353 64 663 1555"
    hotel.email = "info@hotelkillarney.ie"
    hotel.website_url = "https://www.hotelkillarney.ie"
    hotel.booking_url = "https://www.hotelkillarney.ie/book"
    
    # Note: hero_image requires Cloudinary - will be set via admin
    hotel.save()
    print("✓ Updated hotel basic info")
    
    # 2. Create Booking Options
    booking_options, created = BookingOptions.objects.update_or_create(
        hotel=hotel,
        defaults={
            'primary_cta_label': 'Book Now',
            'primary_cta_url': 'https://www.hotelkillarney.ie/book',
            'secondary_cta_label': 'Call to Book',
            'secondary_cta_phone': '+353 64 663 1555',
            'terms_url': 'https://www.hotelkillarney.ie/terms',
            'policies_url': 'https://www.hotelkillarney.ie/policies',
        }
    )
    print(f"✓ {'Created' if created else 'Updated'} booking options")
    
    # 3. Create Room Types
    room_types_data = [
        {
            'name': 'Deluxe Double Room',
            'short_description': 'Spacious room with king-size bed and mountain views. Perfect for couples seeking comfort and elegance.',
            'max_occupancy': 2,
            'bed_setup': '1 King Bed',
            'starting_price_from': 129.00,
            'currency': 'EUR',
            'availability_message': 'Popular choice',
            'sort_order': 1,
            'is_active': True,
        },
        {
            'name': 'Family Suite',
            'short_description': 'Generous suite with separate sleeping areas, ideal for families with children.',
            'max_occupancy': 4,
            'bed_setup': '1 King Bed + 2 Single Beds',
            'starting_price_from': 189.00,
            'currency': 'EUR',
            'availability_message': 'Great for families',
            'sort_order': 2,
            'is_active': True,
        },
        {
            'name': 'Executive Suite',
            'short_description': 'Our finest accommodation with separate living area and panoramic park views. Ultimate luxury.',
            'max_occupancy': 2,
            'bed_setup': '1 King Bed',
            'starting_price_from': 259.00,
            'currency': 'EUR',
            'availability_message': 'High demand',
            'sort_order': 3,
            'is_active': True,
        },
    ]
    
    for room_data in room_types_data:
        room_type, created = RoomType.objects.update_or_create(
            hotel=hotel,
            name=room_data['name'],
            defaults=room_data
        )
        print(f"✓ {'Created' if created else 'Updated'} room type: {room_type.name}")
    
    # 4. Create Offers
    today = date.today()
    offers_data = [
        {
            'title': 'Winter Escape Special',
            'short_description': 'Cozy up in Killarney this winter! Enjoy 20% off room rates, complimentary Irish breakfast, and late checkout.',
            'details_text': 'Valid for stays November through February. Minimum 2-night stay required. Subject to availability.',
            'valid_from': today,
            'valid_to': today + timedelta(days=90),
            'tag': 'Seasonal',
            'book_now_url': 'https://www.hotelkillarney.ie/book?offer=winter',
            'is_active': True,
        },
        {
            'title': 'Ring of Kerry Adventure Package',
            'short_description': 'Explore Ireland\'s most scenic drive! Includes 2 nights accommodation, guided tour, and dinner.',
            'details_text': 'Available March through October. Tour operates Tuesday, Thursday, Saturday. Advance booking required.',
            'valid_from': today,
            'valid_to': today + timedelta(days=120),
            'tag': 'Adventure',
            'book_now_url': 'https://www.hotelkillarney.ie/book?offer=kerry',
            'is_active': True,
        },
        {
            'title': 'Romantic Getaway',
            'short_description': 'Celebrate love in beautiful Killarney. Champagne, couples massage, and 3-course dinner for two.',
            'details_text': 'Spa booking required 48 hours in advance. Dinner reservation required.',
            'valid_from': today,
            'valid_to': today + timedelta(days=365),
            'tag': 'Romance',
            'book_now_url': 'https://www.hotelkillarney.ie/book?offer=romance',
            'is_active': True,
        },
    ]
    
    for offer_data in offers_data:
        offer, created = Offer.objects.update_or_create(
            hotel=hotel,
            title=offer_data['title'],
            defaults=offer_data
        )
        print(f"✓ {'Created' if created else 'Updated'} offer: {offer.title}")
    
    # 5. Create Leisure Activities
    activities_data = [
        {
            'name': 'Killarney National Park Tours',
            'category': 'Sports',
            'short_description': 'Guided walking and cycling tours through Ireland\'s first national park. Explore ancient woodlands and spot native red deer.',
            'is_active': True,
        },
        {
            'name': 'Traditional Irish Music Sessions',
            'category': 'Entertainment',
            'short_description': 'Live traditional music in our pub every Wednesday and Saturday evening. Local musicians, sing-alongs, and Irish dancing.',
            'is_active': True,
        },
        {
            'name': 'Spa & Wellness Center',
            'category': 'Wellness',
            'short_description': 'Luxurious spa with massage therapy, facials, sauna, steam room, and indoor heated pool.',
            'is_active': True,
        },
        {
            'name': 'Fishing on the Lakes',
            'category': 'Sports',
            'short_description': 'Fishing on Lough Leane with equipment and local guide. Pike, trout, and salmon available seasonally.',
            'is_active': True,
        },
        {
            'name': 'Horse-Drawn Jaunting Car Tours',
            'category': 'Entertainment',
            'short_description': 'Traditional horse-drawn carriage tours. A quintessential Irish experience with local stories.',
            'is_active': True,
        },
        {
            'name': 'Cooking Classes - Irish Cuisine',
            'category': 'Dining',
            'short_description': 'Learn traditional Irish dishes with our head chef. Includes soda bread, Irish stew, and apple tart.',
            'is_active': True,
        },
    ]
    
    for activity_data in activities_data:
        activity, created = LeisureActivity.objects.update_or_create(
            hotel=hotel,
            name=activity_data['name'],
            defaults=activity_data
        )
        print(f"✓ {'Created' if created else 'Updated'} activity: {activity.name}")
    
    print("\n" + "="*60)
    print(f"✅ Hotel Killarney data population complete!")
    print("="*60)
    print("\nSummary:")
    print(f"  - Room Types: {RoomType.objects.filter(hotel=hotel).count()}")
    print(f"  - Offers: {Offer.objects.filter(hotel=hotel).count()}")
    print(f"  - Activities: {LeisureActivity.objects.filter(hotel=hotel).count()}")
    print(f"  - Booking Options: {'Yes' if BookingOptions.objects.filter(hotel=hotel).exists() else 'No'}")
    print("\n⚠️  NOTE: Hero image and room/offer/activity images need to be uploaded via Django Admin")
    print("    Go to: /admin/hotel/hotel/2/change/")

if __name__ == '__main__':
    populate_killarney()
