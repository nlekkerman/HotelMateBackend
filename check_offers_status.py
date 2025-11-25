"""
Check all offers and their is_active status
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Offer, Hotel

print("\n" + "=" * 70)
print("CHECKING ALL OFFERS - is_active STATUS")
print("=" * 70)

# Get all hotels
hotels = Hotel.objects.all()

for hotel in hotels:
    print(f"\n🏨 Hotel: {hotel.name} ({hotel.slug})")
    print("-" * 70)
    
    offers = Offer.objects.filter(hotel=hotel).order_by('sort_order', '-created_at')
    
    if not offers.exists():
        print("   No offers found")
        continue
    
    for offer in offers:
        status_icon = "✅" if offer.is_active else "❌"
        print(f"   {status_icon} ID: {offer.id} | Active: {offer.is_active} | '{offer.title}'")
        print(f"      Tag: {offer.tag or 'None'} | Sort: {offer.sort_order}")
        print(f"      Photo: {'Yes' if offer.photo else 'No'}")
        print()

print("=" * 70)
print("\nSUMMARY:")
print("-" * 70)

total_offers = Offer.objects.count()
active_offers = Offer.objects.filter(is_active=True).count()
inactive_offers = Offer.objects.filter(is_active=False).count()

print(f"Total Offers: {total_offers}")
print(f"Active (is_active=True): {active_offers}")
print(f"Inactive (is_active=False): {inactive_offers}")
print("=" * 70 + "\n")
