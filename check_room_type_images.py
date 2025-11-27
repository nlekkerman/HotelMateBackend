import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from rooms.models import RoomType

print("Checking RoomType images...")
print("=" * 50)

room_types = RoomType.objects.all()
print(f"Total room types: {room_types.count()}\n")

empty_photo = []
has_photo = []

for rt in room_types:
    if rt.photo:
        has_photo.append(rt)
        print(f"✅ {rt.name} ({rt.code}) - HAS PHOTO")
        print(f"   Photo URL: {rt.photo.url if hasattr(rt.photo, 'url') else rt.photo}")
    else:
        empty_photo.append(rt)
        print(f"❌ {rt.name} ({rt.code}) - NO PHOTO")

print("\n" + "=" * 50)
print(f"Summary:")
print(f"  With photos: {len(has_photo)}")
print(f"  Without photos: {len(empty_photo)}")

if empty_photo:
    print(f"\nRoom types needing images:")
    for rt in empty_photo:
        print(f"  - {rt.name} ({rt.code}) at {rt.hotel.name}")
