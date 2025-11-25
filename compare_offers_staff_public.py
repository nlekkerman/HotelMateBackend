"""
Compare offers between Staff API and Public API
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Offer, Hotel
from hotel.serializers import OfferStaffSerializer, OfferSerializer

print("\n" + "=" * 70)
print("COMPARING STAFF API vs PUBLIC API - OFFERS")
print("=" * 70)

# Get all hotels
hotels = Hotel.objects.all()

for hotel in hotels:
    print(f"\n🏨 Hotel: {hotel.name} ({hotel.slug})")
    print("-" * 70)
    
    # Staff API - ALL offers (no filter)
    staff_offers = Offer.objects.filter(hotel=hotel).order_by('sort_order', '-created_at')
    
    # Public API - ONLY active offers (is_active=True)
    public_offers = Offer.objects.filter(hotel=hotel, is_active=True).order_by('sort_order', '-created_at')
    
    print(f"\n📊 STAFF API (shows ALL offers):")
    if not staff_offers.exists():
        print("   No offers")
    else:
        for offer in staff_offers:
            status = "✅ ACTIVE" if offer.is_active else "❌ INACTIVE"
            print(f"   {status} | ID: {offer.id} | '{offer.title}'")
    
    print(f"\n🌐 PUBLIC API (shows ONLY active offers):")
    if not public_offers.exists():
        print("   No offers (or all inactive)")
    else:
        for offer in public_offers:
            print(f"   ✅ ID: {offer.id} | '{offer.title}'")
    
    print(f"\n📈 COUNTS:")
    print(f"   Staff API sees: {staff_offers.count()} offers")
    print(f"   Public API sees: {public_offers.count()} offers")
    print(f"   Hidden from public: {staff_offers.count() - public_offers.count()} offers")

print("\n" + "=" * 70)
print("SUMMARY:")
print("=" * 70)

total_all = Offer.objects.count()
total_active = Offer.objects.filter(is_active=True).count()
total_inactive = Offer.objects.filter(is_active=False).count()

print(f"\n✅ Staff API shows: {total_all} offers (ALL)")
print(f"🌐 Public API shows: {total_active} offers (ACTIVE only)")
print(f"🔒 Hidden from public: {total_inactive} offers (INACTIVE)")
print("=" * 70 + "\n")

# Show field differences
print("\n" + "=" * 70)
print("FIELD DIFFERENCES BETWEEN SERIALIZERS:")
print("=" * 70)

print("\n📝 STAFF SERIALIZER (OfferStaffSerializer):")
print("   Fields: id, title, short_description, details_text, details_html,")
print("           valid_from, valid_to, tag, book_now_url, photo, photo_url,")
print("           sort_order, is_active ✅, created_at")
print("   → Can EDIT is_active field")
print("   → Sees ALL offers")

print("\n🌐 PUBLIC SERIALIZER (OfferSerializer):")
print("   Fields: id, title, short_description, details_html, valid_from,")
print("           valid_to, tag, book_now_url, photo_url")
print("   → NO is_active field (hidden)")
print("   → Only sees is_active=True offers")

print("\n🔑 KEY DIFFERENCE:")
print("   Staff: Full control, sees everything, can toggle is_active")
print("   Public: Limited fields, only sees active offers")
print("=" * 70 + "\n")
