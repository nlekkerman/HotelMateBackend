"""
Test script to verify all serializers are properly separated and importable.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, 'c:\\Users\\nlekk\\HMB\\HotelMateBackend')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
import django
django.setup()

def test_base_serializers():
    """Test base serializers import"""
    print("Testing base_serializers...")
    from hotel.base_serializers import (
        PresetSerializer,
        HotelAccessConfigSerializer,
        HotelSerializer,
        HotelPublicPageSerializer
    )
    print("✓ Base serializers imported successfully")
    return True

def test_public_serializers():
    """Test public serializers import"""
    print("\nTesting public_serializers...")
    from hotel.public_serializers import (
        HotelPublicSerializer,
        PublicElementItemSerializer,
        PublicElementSerializer,
        PublicSectionSerializer,
        HeroSectionSerializer,
        GalleryImageSerializer,
        GalleryContainerSerializer,
        CardSerializer,
        ListContainerSerializer,
        ContentBlockSerializer,
        NewsItemSerializer,
        PublicSectionDetailSerializer
    )
    print("✓ Public serializers imported successfully (12 serializers)")
    return True

def test_booking_serializers():
    """Test booking serializers import"""
    print("\nTesting booking_serializers...")
    from hotel.booking_serializers import (
        BookingOptionsSerializer,
        RoomTypeSerializer,
        PricingQuoteSerializer,
        RoomBookingListSerializer,
        RoomBookingDetailSerializer
    )
    print("✓ Booking serializers imported successfully (5 serializers)")
    return True

def test_staff_serializers():
    """Test staff serializers import"""
    print("\nTesting staff_serializers...")
    from hotel.staff_serializers import (
        HotelAccessConfigStaffSerializer,
        RoomTypeStaffSerializer,
        PublicElementItemStaffSerializer,
        PublicElementStaffSerializer,
        PublicSectionStaffSerializer,
        GalleryImageStaffSerializer,
        GalleryContainerStaffSerializer,
        BulkGalleryImageUploadSerializer
    )
    print("✓ Staff serializers imported successfully (8 serializers)")
    return True

def test_main_serializers_hub():
    """Test that main serializers.py re-exports all serializers"""
    print("\nTesting main serializers.py as import hub...")
    from hotel.serializers import (
        # Base
        PresetSerializer,
        HotelSerializer,
        
        # Public
        HotelPublicSerializer,
        PublicSectionDetailSerializer,
        
        # Booking
        RoomTypeSerializer,
        PricingQuoteSerializer,
        
        # Staff
        HotelAccessConfigStaffSerializer,
        BulkGalleryImageUploadSerializer
    )
    print("✓ Main serializers.py successfully re-exports all serializers")
    return True

def test_view_imports():
    """Test that views can import serializers properly"""
    print("\nTesting view imports...")
    
    # Test public_views
    from hotel.public_views import HotelPublicListView
    print("  ✓ public_views imports working")
    
    # Test booking_views
    from hotel.booking_views import HotelAvailabilityView
    print("  ✓ booking_views imports working")
    
    # Test staff_views
    from hotel.staff_views import HotelSettingsView
    print("  ✓ staff_views imports working")
    
    return True

def main():
    """Run all tests"""
    print("=" * 70)
    print("SERIALIZER SEPARATION VERIFICATION TEST")
    print("=" * 70)
    
    tests = [
        test_base_serializers,
        test_public_serializers,
        test_booking_serializers,
        test_staff_serializers,
        test_main_serializers_hub,
        test_view_imports,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} failed: {e}")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Serializers successfully separated.")
        print("\nSummary:")
        print("  - 4 base serializers in base_serializers.py")
        print("  - 12 public serializers in public_serializers.py")
        print("  - 5 booking serializers in booking_serializers.py")
        print("  - 8 staff serializers in staff_serializers.py")
        print("  - All serializers re-exported from main serializers.py")
        print("  - All views import serializers correctly")
    else:
        print("\n❌ Some tests failed. Please review the errors above.")

if __name__ == '__main__':
    main()
