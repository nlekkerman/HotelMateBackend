import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, Offer, LeisureActivity
from rooms.models import RoomType

h = Hotel.objects.get(id=2)

print(f'Hotel: {h.name}')
print(f'Hero Image: {h.hero_image.url if h.hero_image else "None"}')

print(f'\nRoom Types:')
for r in RoomType.objects.filter(hotel=h):
    print(f'  - {r.name}: {r.photo.url if r.photo else "No photo"}')

print(f'\nOffers:')
for o in Offer.objects.filter(hotel=h):
    print(f'  - {o.title}: {o.photo.url if o.photo else "No photo"}')

print(f'\nActivities:')
for a in LeisureActivity.objects.filter(hotel=h):
    print(f'  - {a.name}: {a.image.url if a.image else "No image"}')
