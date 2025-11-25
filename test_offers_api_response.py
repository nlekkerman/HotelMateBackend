"""
Test actual API endpoints for offers
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import RequestFactory
from hotel.views import HotelPublicPageView
from hotel.staff_views import StaffOfferViewSet
from hotel.models import Hotel
from staff.models import Staff

print("\n" + "=" * 70)
print("TESTING ACTUAL API RESPONSES - OFFERS")
print("=" * 70)

# Get a hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotels found!")
    exit()

print(f"\n🏨 Testing with Hotel: {hotel.name} ({hotel.slug})")

# Test 1: Public API - HotelPublicPageView
print("\n" + "=" * 70)
print("1️⃣ PUBLIC API - /api/hotel/public/page/<slug>/")
print("=" * 70)

factory = RequestFactory()
request = factory.get(f'/api/hotel/public/page/{hotel.slug}/')
view = HotelPublicPageView.as_view()

try:
    response = view(request, slug=hotel.slug)
    response.render()
    
    import json
    data = json.loads(response.content)
    
    if 'offers' in data:
        offers = data.get('offers', [])
        print(f"✅ 'offers' field EXISTS in response")
        print(f"   Count: {len(offers)}")
        
        if offers:
            print(f"\n   Sample offer:")
            first_offer = offers[0]
            for key, value in first_offer.items():
                print(f"      {key}: {value}")
        else:
            print("   ⚠️ offers array is EMPTY")
    else:
        print("❌ 'offers' field NOT FOUND in response")
        print(f"\n   Available fields: {list(data.keys())}")
        
except Exception as e:
    print(f"❌ Error: {e}")


# Test 2: Staff API - StaffOfferViewSet
print("\n" + "=" * 70)
print("2️⃣ STAFF API - /api/staff/hotel/<slug>/offers/")
print("=" * 70)

# Get a staff member
staff = Staff.objects.filter(hotel=hotel).first()

if staff:
    print(f"✅ Using staff: {staff.user.username}")
    
    from rest_framework.test import APIRequestFactory
    from django.contrib.auth.models import AnonymousUser
    
    factory = APIRequestFactory()
    request = factory.get(f'/api/staff/hotel/{hotel.slug}/offers/')
    request.user = staff.user
    
    viewset = StaffOfferViewSet.as_view({'get': 'list'})
    
    try:
        response = viewset(request, hotel_slug=hotel.slug)
        
        if hasattr(response, 'data'):
            offers = response.data
            print(f"✅ Response received")
            print(f"   Count: {len(offers) if isinstance(offers, list) else 'N/A'}")
            
            if offers and isinstance(offers, list) and len(offers) > 0:
                print(f"\n   Sample offer:")
                first_offer = offers[0]
                for key, value in first_offer.items():
                    print(f"      {key}: {value}")
            else:
                print("   ⚠️ No offers returned")
        else:
            print(f"❌ Unexpected response format")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ No staff found for this hotel")


print("\n" + "=" * 70)
print("TESTING COMPLETE")
print("=" * 70 + "\n")
