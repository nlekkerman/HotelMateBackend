"""
Upload images to RoomType models for public hotel page.
Simple script to add photos to room cards.

Usage:
    python upload_room_images.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from rooms.models import RoomType
from hotel.models import Hotel
from django.core.files import File

# ===== CONFIGURATION =====
# Change these to match your needs

HOTEL_SLUG = "hotel-killarney"  # Change to your hotel slug

# Option 1: Upload from local files
ROOM_IMAGES_LOCAL = {
    # "Room Name": "path/to/image.jpg",
    # "Deluxe Double Room": "images/deluxe.jpg",
    # "Standard Room": "images/standard.jpg",
    # "Family Suite": "images/family.jpg",
}

# Option 2: Use direct URLs (Cloudinary/Unsplash/etc)
ROOM_IMAGES_URLS = {
    # "Room Name": "https://full-url-to-image.jpg",
    # "Deluxe Double Room": "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800",
    # "Standard Room": "https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=800",
    # "Family Suite": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800",
}

# =========================


def upload_from_urls():
    """Upload images from URLs (direct assignment for CloudinaryField)"""
    try:
        hotel = Hotel.objects.get(slug=HOTEL_SLUG)
        print(f'\n✓ Found hotel: {hotel.name}\n')
    except Hotel.DoesNotExist:
        print(f'\n✗ Hotel not found: {HOTEL_SLUG}')
        print('\nAvailable hotels:')
        for h in Hotel.objects.all():
            print(f'  - {h.slug} ({h.name})')
        return

    if not ROOM_IMAGES_URLS:
        print('No URL mappings configured in ROOM_IMAGES_URLS')
        return

    print('Uploading room images from URLs...\n')
    
    for room_name, image_url in ROOM_IMAGES_URLS.items():
        try:
            room = RoomType.objects.get(hotel=hotel, name=room_name)
            room.photo = image_url  # CloudinaryField accepts URLs directly
            room.save()
            print(f'✓ {room_name}: {image_url}')
        except RoomType.DoesNotExist:
            print(f'✗ Room not found: {room_name}')

    print('\n✓ Upload complete!')


def upload_from_files():
    """Upload images from local files"""
    try:
        hotel = Hotel.objects.get(slug=HOTEL_SLUG)
        print(f'\n✓ Found hotel: {hotel.name}\n')
    except Hotel.DoesNotExist:
        print(f'\n✗ Hotel not found: {HOTEL_SLUG}')
        print('\nAvailable hotels:')
        for h in Hotel.objects.all():
            print(f'  - {h.slug} ({h.name})')
        return

    if not ROOM_IMAGES_LOCAL:
        print('No file mappings configured in ROOM_IMAGES_LOCAL')
        return

    print('Uploading room images from local files...\n')
    
    for room_name, image_path in ROOM_IMAGES_LOCAL.items():
        if not os.path.exists(image_path):
            print(f'✗ File not found: {image_path}')
            continue

        try:
            room = RoomType.objects.get(hotel=hotel, name=room_name)
            with open(image_path, 'rb') as f:
                file_name = os.path.basename(image_path)
                room.photo = File(f, name=file_name)
                room.save()
            print(f'✓ {room_name}: {room.photo.url}')
        except RoomType.DoesNotExist:
            print(f'✗ Room not found: {room_name}')

    print('\n✓ Upload complete!')


def list_rooms():
    """List all rooms for the configured hotel"""
    try:
        hotel = Hotel.objects.get(slug=HOTEL_SLUG)
        print(f'\n=== Room Types for {hotel.name} ===\n')
        
        rooms = RoomType.objects.filter(hotel=hotel).order_by('sort_order', 'name')
        
        if not rooms:
            print('No room types found for this hotel.')
            return
        
        for room in rooms:
            photo_status = '✓ Has photo' if room.photo else '✗ No photo'
            print(f'{room.id}. {room.name} ({room.code}) - {photo_status}')
            if room.photo:
                print(f'   Photo: {room.photo.url}')
            print()
            
    except Hotel.DoesNotExist:
        print(f'\n✗ Hotel not found: {HOTEL_SLUG}')
        print('\nAvailable hotels:')
        for h in Hotel.objects.all():
            print(f'  - {h.slug} ({h.name})')


def main():
    print('\n' + '='*60)
    print('  Room Type Image Upload Script')
    print('='*60)
    
    # List current rooms
    list_rooms()
    
    # Upload images
    if ROOM_IMAGES_URLS:
        upload_from_urls()
    elif ROOM_IMAGES_LOCAL:
        upload_from_files()
    else:
        print('\n' + '='*60)
        print('  HOW TO USE THIS SCRIPT')
        print('='*60)
        print('\n1. Edit this file (upload_room_images.py)')
        print('2. Set HOTEL_SLUG to your hotel slug')
        print('3. Choose one option:\n')
        print('   Option A - Use image URLs:')
        print('   ROOM_IMAGES_URLS = {')
        print('       "Deluxe Double Room": "https://your-image-url.jpg",')
        print('       "Standard Room": "https://another-image-url.jpg",')
        print('   }\n')
        print('   Option B - Use local files:')
        print('   ROOM_IMAGES_LOCAL = {')
        print('       "Deluxe Double Room": "path/to/deluxe.jpg",')
        print('       "Standard Room": "path/to/standard.jpg",')
        print('   }\n')
        print('4. Run: python upload_room_images.py')
        print('\n' + '='*60)


if __name__ == '__main__':
    main()
