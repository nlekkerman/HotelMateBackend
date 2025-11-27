import os
import django
import cloudinary.uploader
import requests
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from rooms.models import RoomType

# Sample hotel room images from Unsplash (free to use)
ROOM_IMAGES = {
    'STD': 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=800',  # Standard room
    'DLX': 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800',  # Deluxe suite
    'FAM': 'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=800',  # Family room
}

print("Populating room type images...")
print("=" * 50)

room_types_without_photos = RoomType.objects.filter(photo__isnull=True) | RoomType.objects.filter(photo='')

print(f"Found {room_types_without_photos.count()} room types without photos\n")

for rt in room_types_without_photos:
    # Determine which image to use based on code
    image_url = ROOM_IMAGES.get(rt.code, ROOM_IMAGES['STD'])
    
    try:
        print(f"Uploading image for: {rt.name} ({rt.code}) at {rt.hotel.name}")
        
        # Download image
        response = requests.get(image_url)
        img_data = BytesIO(response.content)
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            img_data,
            folder='room_types',
            public_id=f"{rt.hotel.slug}_{rt.code}_{rt.id}"
        )
        
        # Save to model
        rt.photo = result['secure_url']
        rt.save()
        
        print(f"   ✅ Uploaded: {result['secure_url']}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("✅ Image population complete!")

# Verify
remaining = RoomType.objects.filter(photo__isnull=True).count() + RoomType.objects.filter(photo='').count()
print(f"Room types still without photos: {remaining}")
