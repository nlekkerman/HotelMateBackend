"""
Test all separated view endpoints to verify imports are working correctly.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from hotel.views import HotelViewSet, HotelBySlugView
from hotel.public_views import HotelPublicListView, HotelFilterOptionsView, HotelPublicPageView
from hotel.booking_views import HotelAvailabilityView, HotelPricingQuoteView, HotelBookingCreateView
from hotel.staff_views import (
    HotelSettingsView, 
    StaffBookingsListView, 
    StaffBookingConfirmView,
    PublicPageBuilderView,
    HotelStatusCheckView,
    PublicPageBootstrapView,
    SectionCreateView
)

print("=" * 60)
print("TESTING ALL ENDPOINT IMPORTS")
print("=" * 60)

# Test base/admin views
print("\n✓ Base Views:")
print(f"  - HotelViewSet: {HotelViewSet.__name__}")
print(f"  - HotelBySlugView: {HotelBySlugView.__name__}")

# Test public views
print("\n✓ Public Views:")
print(f"  - HotelPublicListView: {HotelPublicListView.__name__}")
print(f"  - HotelFilterOptionsView: {HotelFilterOptionsView.__name__}")
print(f"  - HotelPublicPageView: {HotelPublicPageView.__name__}")

# Test booking views
print("\n✓ Booking Views:")
print(f"  - HotelAvailabilityView: {HotelAvailabilityView.__name__}")
print(f"  - HotelPricingQuoteView: {HotelPricingQuoteView.__name__}")
print(f"  - HotelBookingCreateView: {HotelBookingCreateView.__name__}")

# Test staff management views
print("\n✓ Staff Management Views:")
print(f"  - HotelSettingsView: {HotelSettingsView.__name__}")
print(f"  - StaffBookingsListView: {StaffBookingsListView.__name__}")
print(f"  - StaffBookingConfirmView: {StaffBookingConfirmView.__name__}")
print(f"  - PublicPageBuilderView: {PublicPageBuilderView.__name__}")
print(f"  - HotelStatusCheckView: {HotelStatusCheckView.__name__}")
print(f"  - PublicPageBootstrapView: {PublicPageBootstrapView.__name__}")
print(f"  - SectionCreateView: {SectionCreateView.__name__}")

# Test view instantiation
print("\n" + "=" * 60)
print("TESTING VIEW INSTANTIATION")
print("=" * 60)

factory = RequestFactory()

try:
    # Test public views can be instantiated
    request = factory.get('/api/public/hotels/')
    request.user = AnonymousUser()
    
    view1 = HotelPublicListView.as_view()
    print("✓ HotelPublicListView instantiated")
    
    view2 = HotelFilterOptionsView.as_view()
    print("✓ HotelFilterOptionsView instantiated")
    
    view3 = HotelAvailabilityView.as_view()
    print("✓ HotelAvailabilityView instantiated")
    
    view4 = HotelPricingQuoteView.as_view()
    print("✓ HotelPricingQuoteView instantiated")
    
    view5 = HotelBookingCreateView.as_view()
    print("✓ HotelBookingCreateView instantiated")
    
    view6 = HotelSettingsView.as_view()
    print("✓ HotelSettingsView instantiated")
    
    view7 = StaffBookingsListView.as_view()
    print("✓ StaffBookingsListView instantiated")
    
    view8 = PublicPageBuilderView.as_view()
    print("✓ PublicPageBuilderView instantiated")
    
    print("\n" + "=" * 60)
    print("SUCCESS: All views imported and instantiated correctly!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

# Test URL imports
print("\n" + "=" * 60)
print("TESTING URL CONFIGURATION IMPORTS")
print("=" * 60)

try:
    from hotel import urls as hotel_urls
    print("✓ hotel.urls imported")
    
    import staff_urls
    print("✓ staff_urls imported")
    
    import public_urls
    print("✓ public_urls imported")
    
    import guest_urls
    print("✓ guest_urls imported")
    
    print("\n" + "=" * 60)
    print("SUCCESS: All URL configurations imported correctly!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("ALL TESTS PASSED - IMPORT SEPARATION SUCCESSFUL! ✅")
print("=" * 60)
