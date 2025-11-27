import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from rooms.models import RoomType
from hotel.models import Hotel

print("Checking Hotel Killarney room types...")
print("=" * 50)

try:
    killarney = Hotel.objects.get(slug='hotel-killarney')
    room_types = RoomType.objects.filter(hotel=killarney)
    
    print(f"Hotel: {killarney.name}")
    print(f"Total room types: {room_types.count()}\n")
    
    for rt in room_types:
        status = "✅ HAS PHOTO" if rt.photo else "❌ NO PHOTO"
        print(f"{status} - {rt.name} ({rt.code})")
        if rt.photo:
            print(f"   Photo: {rt.photo.url if hasattr(rt.photo, 'url') else rt.photo}")
        print(f"   Price: {rt.currency}{rt.starting_price_from}/night")
        print()
        
except Hotel.DoesNotExist:
    print("❌ Hotel Killarney not found")
