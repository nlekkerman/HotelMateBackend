"""
Serializers for hotel-related models.
This module imports and re-exports all serializers from organized submodules.
"""

# Import all serializers from organized modules
from .base_serializers import (
    PresetSerializer,
    HotelAccessConfigSerializer,
    HotelSerializer,
    HotelPublicPageSerializer
)

from .public_serializers import (
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
    RoomTypePublicSerializer,
    RoomsSectionSerializer,
    PublicSectionDetailSerializer
)

from .booking_serializers import (
    BookingOptionsSerializer,
    RoomTypeSerializer,
    PricingQuoteSerializer,
    RoomBookingListSerializer,
    RoomBookingDetailSerializer
)

from .staff_serializers import (
    HotelAccessConfigStaffSerializer,
    RoomTypeStaffSerializer,
    PublicElementItemStaffSerializer,
    PublicElementStaffSerializer,
    PublicSectionStaffSerializer,
    GalleryImageStaffSerializer,
    GalleryContainerStaffSerializer,
    BulkGalleryImageUploadSerializer,
    RoomsSectionStaffSerializer
)

from .cancellation_policy_serializers import (
    CancellationPolicySerializer,
    CancellationPolicyListSerializer,
    CancellationPolicyTierSerializer
)

from .rate_plan_serializers import (
    RatePlanSerializer,
    RatePlanListSerializer
)

# Re-export all serializers for backwards compatibility
__all__ = [
    # Base/Admin serializers
    'PresetSerializer',
    'HotelAccessConfigSerializer',
    'HotelSerializer',
    'HotelPublicPageSerializer',
    
    # Public serializers
    'HotelPublicSerializer',
    'PublicElementItemSerializer',
    'PublicElementSerializer',
    'PublicSectionSerializer',
    'HeroSectionSerializer',
    'GalleryImageSerializer',
    'GalleryContainerSerializer',
    'CardSerializer',
    'ListContainerSerializer',
    'ContentBlockSerializer',
    'NewsItemSerializer',
    'RoomTypePublicSerializer',
    'RoomsSectionSerializer',
    'PublicSectionDetailSerializer',
    
    # Booking serializers
    'BookingOptionsSerializer',
    'RoomTypeSerializer',
    'PricingQuoteSerializer',
    'RoomBookingListSerializer',
    'RoomBookingDetailSerializer',
    
    # Staff serializers
    'HotelAccessConfigStaffSerializer',
    'RoomTypeStaffSerializer',
    'PublicElementItemStaffSerializer',
    'PublicElementStaffSerializer',
    'PublicSectionStaffSerializer',
    'GalleryImageStaffSerializer',
    'GalleryContainerStaffSerializer',
    'BulkGalleryImageUploadSerializer',
    'RoomsSectionStaffSerializer',
    
    # Cancellation policy serializers
    'CancellationPolicySerializer',
    'CancellationPolicyListSerializer', 
    'CancellationPolicyTierSerializer',
    
    # Rate plan serializers
    'RatePlanSerializer',
    'RatePlanListSerializer',
]
