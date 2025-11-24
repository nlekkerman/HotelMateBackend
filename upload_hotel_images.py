"""
Upload real Hotel Killarney images via Django shell
Save these images in a folder called 'hotel_images' and run this script
"""
from hotel.models import Hotel, Offer, LeisureActivity
from rooms.models import RoomType
from django.core.files import File
import os

# Image mapping - update paths to match where you saved the images
IMAGES = {
    'hero': 'hotel_images/exterior.jpg',  # The exterior/building image
    'rooms': {
        'Deluxe Double Room': 'hotel_images/room1.jpg',  # Red/gold room
        'Family Suite': 'hotel_images/room2.jpg',  # Yellow/teal room
        'Executive Suite': 'hotel_images/room1.jpg',  # Can reuse
    },
    'leisure': 'hotel_images/pool.jpg',  # Swimming pool
}

# Get Hotel Killarney
hotel = Hotel.objects.get(id=2, slug='hotel-killarney')
print(f"Uploading images for: {hotel.name}")

# 1. Upload hero image
hero_path = IMAGES['hero']
if os.path.exists(hero_path):
    with open(hero_path, 'rb') as f:
        hotel.hero_image = File(f, name=os.path.basename(hero_path))
        hotel.save()
    print(f"✓ Hero image uploaded: {hotel.hero_image.url}")
else:
    print(f"✗ Hero image not found: {hero_path}")

# 2. Upload room images
for room_name, image_path in IMAGES['rooms'].items():
    if os.path.exists(image_path):
        try:
            room = RoomType.objects.get(hotel=hotel, name=room_name)
            with open(image_path, 'rb') as f:
                room.photo = File(f, name=f"{room_name.lower().replace(' ', '_')}.jpg")
                room.save()
            print(f"✓ Room image uploaded: {room_name} -> {room.photo.url}")
        except RoomType.DoesNotExist:
            print(f"✗ Room not found: {room_name}")
    else:
        print(f"✗ Image not found: {image_path}")

# 3. Upload leisure/pool image for activities
leisure_path = IMAGES['leisure']
if os.path.exists(leisure_path):
    activities = LeisureActivity.objects.filter(hotel=hotel)
    for activity in activities:
        with open(leisure_path, 'rb') as f:
            activity.image = File(f, name=f"activity_{activity.id}.jpg")
            activity.save()
        print(f"✓ Activity image uploaded: {activity.name} -> {activity.image.url}")
else:
    print(f"✗ Leisure image not found: {leisure_path}")

# 4. Upload offer images (use room images)
offers = Offer.objects.filter(hotel=hotel)
offer_image = IMAGES['rooms']['Deluxe Double Room']
if os.path.exists(offer_image):
    for offer in offers:
        with open(offer_image, 'rb') as f:
            offer.photo = File(f, name=f"offer_{offer.id}.jpg")
            offer.save()
        print(f"✓ Offer image uploaded: {offer.title} -> {offer.photo.url}")

print("\n✅ All images uploaded successfully!")
