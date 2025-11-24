# HotelMate Phase 1 CRUD & Public Page - Consolidated Implementation Plan

## Overview
This document consolidates all backend issues (B1-B8) from `issues_for_pase_on_pt_3.MD` into a single comprehensive implementation plan with specific code changes.

**Date:** November 24, 2025  
**Status:** Implementation Ready  
**Scope:** Backend API enhancements for staff CRUD and public hotel pages

---

## Current State Analysis

### Existing Models ✅
- `Hotel` - Complete with marketing fields (tagline, hero_image, location, contact)
- `HotelAccessConfig` - Portal configuration
- `BookingOptions` - CTA configuration
- `HotelPublicSettings` - Branding and content
- `Offer` - Marketing packages
- `LeisureActivity` - Facilities
- `RoomType` - Marketing room types
- `Room` - Physical inventory
- `RoomBooking` - Reservation records
- `PricingQuote` - Quote storage

### Existing Views ✅
- `HotelPublicPageView` - Public page endpoint
- `HotelAvailabilityView` - Availability check
- `HotelPricingQuoteView` - Quote calculation
- `HotelBookingCreateView` - Booking creation
- `HotelPublicSettingsStaffView` - Staff settings management
- `StaffBookingsListView` - Staff bookings list
- `StaffBookingConfirmView` - Booking confirmation

### Gap Analysis
Most infrastructure exists. Key missing pieces:
1. **Staff CRUD views** for Offer, LeisureActivity, RoomType, Room
2. **Enhanced serializers** for Room and HotelAccessConfig
3. **Persistence** in HotelPricingQuoteView and HotelBookingCreateView
4. **Public settings integration** in HotelPublicDetailSerializer

---

## Implementation Tasks

### B1: Create/Update All Required Serializers

#### Files to Modify
- `hotel/serializers.py` - Add Room, HotelAccessConfig serializers
- `rooms/serializers.py` - Create if missing, add Room serializers

#### New Serializers Needed

```python
# hotel/serializers.py additions

class HotelAccessConfigStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for access configuration"""
    class Meta:
        model = HotelAccessConfig
        fields = [
            'guest_portal_enabled',
            'staff_portal_enabled',
            'requires_room_pin',
            'room_pin_length',
            'rotate_pin_on_checkout',
            'allow_multiple_guest_sessions',
            'max_active_guest_devices_per_room',
        ]

class OfferStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for offers - includes all fields"""
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'short_description',
            'details_text',
            'details_html',
            'valid_from',
            'valid_to',
            'tag',
            'book_now_url',
            'photo',
            'photo_url',
            'sort_order',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None

class LeisureActivityStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for leisure activities"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LeisureActivity
        fields = [
            'id',
            'name',
            'category',
            'short_description',
            'details_html',
            'icon',
            'image',
            'image_url',
            'sort_order',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

class RoomTypeStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for room types"""
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomType
        fields = [
            'id',
            'code',
            'name',
            'short_description',
            'max_occupancy',
            'bed_setup',
            'photo',
            'photo_url',
            'starting_price_from',
            'currency',
            'booking_code',
            'booking_url',
            'availability_message',
            'sort_order',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None

class PricingQuoteSerializer(serializers.ModelSerializer):
    """Serializer for PricingQuote model"""
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    
    class Meta:
        model = PricingQuote
        fields = [
            'quote_id',
            'hotel',
            'room_type',
            'room_type_name',
            'check_in',
            'check_out',
            'adults',
            'children',
            'base_price_per_night',
            'number_of_nights',
            'subtotal',
            'taxes',
            'fees',
            'discount',
            'total',
            'currency',
            'promo_code',
            'applied_offer',
            'created_at',
            'valid_until',
        ]
        read_only_fields = ['quote_id', 'created_at']
```

```python
# rooms/serializers.py (new file if it doesn't exist)

from rest_framework import serializers
from .models import Room

class RoomStaffSerializer(serializers.ModelSerializer):
    """Staff CRUD for rooms (inventory management)"""
    class Meta:
        model = Room
        fields = [
            'id',
            'room_number',
            'is_occupied',
            'guest_id_pin',
            'room_service_qr_code',
            'in_room_breakfast_qr_code',
            'dinner_booking_qr_code',
            'chat_pin_qr_code',
        ]
        read_only_fields = [
            'id',
            'guest_id_pin',
            'room_service_qr_code',
            'in_room_breakfast_qr_code',
            'dinner_booking_qr_code',
            'chat_pin_qr_code',
        ]
```

**Status:** ✅ Serializers defined

---

### B2: Extend HotelPublicDetailSerializer

#### Files to Modify
- `hotel/serializers.py`

#### Changes
Update `HotelPublicDetailSerializer` to include `HotelPublicSettings` data:

```python
class HotelPublicDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for public hotel page.
    Now includes public settings for branding and additional content.
    """
    logo_url = serializers.SerializerMethodField()
    hero_image_url = serializers.SerializerMethodField()
    booking_options = BookingOptionsSerializer(read_only=True)
    public_settings = serializers.SerializerMethodField()
    room_types = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()
    leisure_activities = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = [
            # Basic info
            'slug',
            'name',
            'tagline',
            'hero_image_url',
            'logo_url',
            'short_description',
            'long_description',
            # Location
            'city',
            'country',
            'address_line_1',
            'address_line_2',
            'postal_code',
            'latitude',
            'longitude',
            # Contact
            'phone',
            'email',
            'website_url',
            'booking_url',
            # Nested objects
            'booking_options',
            'public_settings',  # NEW
            'room_types',
            'offers',
            'leisure_activities',
        ]
    
    def get_public_settings(self, obj):
        """Return public settings if they exist"""
        try:
            settings = obj.public_settings
            return HotelPublicSettingsPublicSerializer(settings).data
        except HotelPublicSettings.DoesNotExist:
            return None
    
    # ... rest of methods remain the same
```

**Impact:** HotelPublicPageView now returns complete page content including branding

---

### B3: Update HotelPublicSettingsView

#### Files to Modify
- `hotel/views.py`

#### Changes
Already implemented correctly. No changes needed.

**Status:** ✅ Already correct

---

### B4: Extend HotelPublicSettingsStaffView

#### Files to Modify
- `hotel/views.py`
- `hotel/serializers.py`

#### Changes
Add validation to `HotelPublicSettingsStaffSerializer`:

```python
class HotelPublicSettingsStaffSerializer(serializers.ModelSerializer):
    """
    Write-enabled serializer for staff to update hotel settings.
    Includes validation for colors and data formats.
    """
    class Meta:
        model = HotelPublicSettings
        fields = [
            'short_description',
            'long_description',
            'welcome_message',
            'hero_image',
            'gallery',
            'amenities',
            'contact_email',
            'contact_phone',
            'contact_address',
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'button_color',
            'theme_mode',
            'updated_at',
        ]
        read_only_fields = ['updated_at']
    
    def validate_primary_color(self, value):
        return self._validate_hex_color(value, 'primary_color')
    
    def validate_secondary_color(self, value):
        return self._validate_hex_color(value, 'secondary_color')
    
    def validate_accent_color(self, value):
        return self._validate_hex_color(value, 'accent_color')
    
    def validate_background_color(self, value):
        return self._validate_hex_color(value, 'background_color')
    
    def validate_button_color(self, value):
        return self._validate_hex_color(value, 'button_color')
    
    def _validate_hex_color(self, value, field_name):
        """Validate HEX color format"""
        import re
        if value and not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError(
                f'{field_name} must be a valid HEX color (e.g., #3B82F6)'
            )
        return value
    
    def validate_gallery(self, value):
        """Ensure gallery is a list"""
        if not isinstance(value, list):
            raise serializers.ValidationError('gallery must be a list of URLs')
        return value
    
    def validate_amenities(self, value):
        """Ensure amenities is a list"""
        if not isinstance(value, list):
            raise serializers.ValidationError('amenities must be a list of strings')
        return value
```

**Status:** ✅ Validation enhanced

---

### B5: Add Staff CRUD Views for Content

#### Files to Create/Modify
- `hotel/staff_views.py` (new file)
- `hotel/urls.py` (update with new routes)

#### New Views

```python
# hotel/staff_views.py (NEW FILE)

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from staff_chat.permissions import IsStaffMember, IsSameHotel
from .models import Offer, LeisureActivity, HotelAccessConfig
from rooms.models import RoomType, Room
from .serializers import (
    OfferStaffSerializer,
    LeisureActivityStaffSerializer,
    RoomTypeStaffSerializer,
    HotelAccessConfigStaffSerializer,
)


class StaffOfferViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for hotel offers.
    Scoped to staff's hotel only.
    """
    serializer_class = OfferStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return offers for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return Offer.objects.filter(
                hotel=staff.hotel
            ).order_by('sort_order', '-created_at')
        except AttributeError:
            return Offer.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)


class StaffLeisureActivityViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for leisure activities.
    Scoped to staff's hotel only.
    """
    serializer_class = LeisureActivityStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return activities for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return LeisureActivity.objects.filter(
                hotel=staff.hotel
            ).order_by('category', 'sort_order', 'name')
        except AttributeError:
            return LeisureActivity.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)


class StaffRoomTypeViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for room types (marketing).
    Scoped to staff's hotel only.
    """
    serializer_class = RoomTypeStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return room types for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return RoomType.objects.filter(
                hotel=staff.hotel
            ).order_by('sort_order', 'name')
        except AttributeError:
            return RoomType.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)


class StaffRoomViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for rooms (physical inventory).
    Scoped to staff's hotel only.
    """
    from rooms.serializers import RoomStaffSerializer
    serializer_class = RoomStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return rooms for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return Room.objects.filter(
                hotel=staff.hotel
            ).order_by('room_number')
        except AttributeError:
            return Room.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)
    
    @action(detail=True, methods=['post'])
    def generate_pin(self, request, pk=None):
        """Generate new guest PIN for room"""
        room = self.get_object()
        room.generate_guest_pin()
        return Response({
            'message': 'PIN generated successfully',
            'guest_id_pin': room.guest_id_pin
        })
    
    @action(detail=True, methods=['post'])
    def generate_qr(self, request, pk=None):
        """Generate QR codes for room"""
        room = self.get_object()
        qr_type = request.data.get('type', 'room_service')
        
        if qr_type == 'room_service':
            room.generate_qr_code('room_service')
        elif qr_type == 'breakfast':
            room.generate_qr_code('in_room_breakfast')
        elif qr_type == 'chat_pin':
            room.generate_chat_pin_qr_code()
        elif qr_type == 'restaurant':
            # Need restaurant slug
            restaurant_slug = request.data.get('restaurant_slug')
            if not restaurant_slug:
                return Response(
                    {'error': 'restaurant_slug required for restaurant QR'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            from bookings.models import Restaurant
            restaurant = get_object_or_404(
                Restaurant,
                hotel=room.hotel,
                slug=restaurant_slug
            )
            room.generate_booking_qr_for_restaurant(restaurant)
        else:
            return Response(
                {'error': f'Invalid QR type: {qr_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(room)
        return Response(serializer.data)


class StaffAccessConfigView(viewsets.ModelViewSet):
    """
    Staff endpoint to manage hotel access configuration.
    OneToOne relationship - only one config per hotel.
    """
    serializer_class = HotelAccessConfigStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    http_method_names = ['get', 'put', 'patch']  # No create/delete
    
    def get_queryset(self):
        """Only return config for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return HotelAccessConfig.objects.filter(hotel=staff.hotel)
        except AttributeError:
            return HotelAccessConfig.objects.none()
    
    def get_object(self):
        """Get or create config for staff's hotel"""
        staff = self.request.user.staff_profile
        config, created = HotelAccessConfig.objects.get_or_create(
            hotel=staff.hotel
        )
        return config
```

**Status:** ✅ Staff CRUD views defined

---

### B6: Wire HotelPricingQuoteView to PricingQuote Model

#### Files to Modify
- `hotel/views.py`

#### Changes
Update `HotelPricingQuoteView.post()` to persist quotes:

```python
def post(self, request, slug):
    from decimal import Decimal
    import uuid
    from django.utils import timezone
    from .models import PricingQuote
    
    # ... existing validation code ...
    
    # Calculate pricing (existing code)
    nights = (check_out - check_in).days
    base_price = Decimal(str(room_type.starting_price_from))
    subtotal = base_price * nights
    tax_rate = Decimal('0.09')
    taxes = subtotal * tax_rate
    
    # Apply promo code (existing code)
    discount = Decimal('0')
    applied_promo = None
    applied_offer_obj = None
    
    if promo_code:
        promo_code_upper = promo_code.upper()
        if promo_code_upper == 'WINTER20':
            discount = subtotal * Decimal('0.20')
            applied_promo = {
                "code": "WINTER20",
                "description": "20% off winter bookings",
                "discount_percentage": "20.00"
            }
        elif promo_code_upper == 'SAVE10':
            discount = subtotal * Decimal('0.10')
            applied_promo = {
                "code": "SAVE10",
                "description": "10% off your stay",
                "discount_percentage": "10.00"
            }
    
    fees = Decimal('0')
    total = subtotal + taxes + fees - discount
    
    # Quote valid for 30 minutes
    valid_until = timezone.now() + timezone.timedelta(minutes=30)
    
    # NEW: Create PricingQuote record
    quote = PricingQuote.objects.create(
        hotel=hotel,
        room_type=room_type,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        children=children,
        base_price_per_night=base_price,
        number_of_nights=nights,
        subtotal=subtotal,
        taxes=taxes,
        fees=fees,
        discount=discount,
        total=total,
        currency=room_type.currency,
        promo_code=promo_code if promo_code else '',
        applied_offer=applied_offer_obj,
        valid_until=valid_until
    )
    
    # Use quote_id from saved model
    response_data = {
        "quote_id": quote.quote_id,
        "valid_until": valid_until.isoformat(),
        "currency": room_type.currency,
        "room_type": {
            "code": room_type.code or room_type.name,
            "name": room_type.name,
            "photo": room_type.photo.url if room_type.photo else None
        },
        "dates": {
            "check_in": check_in_str,
            "check_out": check_out_str,
            "nights": nights
        },
        "guests": {
            "adults": adults,
            "children": children,
            "total": adults + children
        },
        "breakdown": {
            "base_price_per_night": f"{base_price:.2f}",
            "number_of_nights": nights,
            "subtotal": f"{subtotal:.2f}",
            "taxes": f"{taxes:.2f}",
            "fees": f"{fees:.2f}",
            "discount": f"-{discount:.2f}" if discount > 0 else "0.00",
            "total": f"{total:.2f}"
        },
        "applied_promo": applied_promo
    }
    
    return Response(response_data, status=status.HTTP_200_OK)
```

**Status:** ✅ Quote persistence added

---

### B7: Refactor HotelBookingCreateView

#### Files to Modify
- `hotel/views.py`

#### Changes
Update to create `RoomBooking` records:

```python
def post(self, request, slug):
    from decimal import Decimal
    from django.utils import timezone
    
    # ... existing validation code ...
    
    # Calculate pricing (existing code)
    nights = (check_out - check_in).days
    base_price = Decimal(str(room_type.starting_price_from))
    subtotal = base_price * nights
    tax_rate = Decimal('0.09')
    taxes = subtotal * tax_rate
    
    discount = Decimal('0')
    if promo_code:
        promo_code_upper = promo_code.upper()
        if promo_code_upper == 'WINTER20':
            discount = subtotal * Decimal('0.20')
        elif promo_code_upper == 'SAVE10':
            discount = subtotal * Decimal('0.10')
    
    total = subtotal + taxes - discount
    
    # NEW: Create RoomBooking record
    booking = RoomBooking.objects.create(
        hotel=hotel,
        room_type=room_type,
        check_in=check_in,
        check_out=check_out,
        guest_first_name=guest_data['first_name'],
        guest_last_name=guest_data['last_name'],
        guest_email=guest_data['email'],
        guest_phone=guest_data['phone'],
        adults=adults,
        children=children,
        total_amount=total,
        currency=room_type.currency,
        status='PENDING_PAYMENT',
        special_requests=special_requests,
        promo_code=promo_code if promo_code else ''
    )
    # booking_id and confirmation_number auto-generated by model
    
    # Return response using booking data
    booking_data = {
        "booking_id": booking.booking_id,
        "confirmation_number": booking.confirmation_number,
        "status": booking.status,
        "created_at": booking.created_at.isoformat(),
        "hotel": {
            "name": hotel.name,
            "slug": hotel.slug,
            "phone": hotel.phone,
            "email": hotel.email
        },
        "room": {
            "type": room_type.name,
            "code": room_type.code or room_type.name,
            "photo": room_type.photo.url if room_type.photo else None
        },
        "dates": {
            "check_in": check_in_str,
            "check_out": check_out_str,
            "nights": nights
        },
        "guests": {
            "adults": adults,
            "children": children,
            "total": adults + children
        },
        "guest": {
            "name": booking.guest_name,
            "email": booking.guest_email,
            "phone": booking.guest_phone
        },
        "special_requests": special_requests,
        "pricing": {
            "subtotal": f"{subtotal:.2f}",
            "taxes": f"{taxes:.2f}",
            "discount": f"{discount:.2f}",
            "total": f"{total:.2f}",
            "currency": room_type.currency
        },
        "promo_code": promo_code if promo_code else None,
        "quote_id": quote_id if quote_id else None,
        "payment_required": True,
        "payment_url": f"/api/bookings/{booking.booking_id}/payment/session/"
    }
    
    return Response(booking_data, status=status.HTTP_201_CREATED)
```

**Status:** ✅ Booking persistence added

---

### B8: Improve Staff Booking Views

#### Files to Modify
- `hotel/views.py`

#### Changes
Already well-implemented. Minor enhancements:

```python
class StaffBookingsListView(APIView):
    # ... existing code ...
    
    def get(self, request, hotel_slug):
        # ... existing validation ...
        
        # Get bookings with better error handling
        bookings = RoomBooking.objects.filter(
            hotel=staff.hotel
        ).select_related('hotel', 'room_type').order_by('-created_at')

        # Apply status filter with uppercase normalization
        status_filter = request.query_params.get('status')
        if status_filter:
            status_upper = status_filter.upper()
            # Validate status is a valid choice
            valid_statuses = [choice[0] for choice in RoomBooking.STATUS_CHOICES]
            if status_upper not in valid_statuses:
                return Response(
                    {
                        'error': f'Invalid status. Choose from: {", ".join(valid_statuses)}'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            bookings = bookings.filter(status=status_upper)

        # ... rest of existing code ...
```

**Status:** ✅ Enhanced validation

---

## URL Routing Updates

### hotel/urls.py
Add routes for new staff views:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, staff_views

# Staff router for CRUD views
staff_router = DefaultRouter()
staff_router.register(r'offers', staff_views.StaffOfferViewSet, basename='staff-offers')
staff_router.register(r'leisure-activities', staff_views.StaffLeisureActivityViewSet, basename='staff-leisure')
staff_router.register(r'room-types', staff_views.StaffRoomTypeViewSet, basename='staff-room-types')
staff_router.register(r'rooms', staff_views.StaffRoomViewSet, basename='staff-rooms')
staff_router.register(r'access-config', staff_views.StaffAccessConfigView, basename='staff-access-config')

urlpatterns = [
    # ... existing public routes ...
    
    # Staff routes
    path('staff/<slug:hotel_slug>/', include(staff_router.urls)),
    path('staff/<slug:hotel_slug>/settings/', views.HotelPublicSettingsStaffView.as_view(), name='staff-settings'),
    path('staff/<slug:hotel_slug>/bookings/', views.StaffBookingsListView.as_view(), name='staff-bookings-list'),
    path('staff/<slug:hotel_slug>/bookings/<str:booking_id>/confirm/', views.StaffBookingConfirmView.as_view(), name='staff-booking-confirm'),
]
```

---

## Testing Checklist

### B1 - Serializers
- [ ] All models have public and staff serializers
- [ ] Serializers handle Cloudinary fields correctly
- [ ] Read-only fields are properly marked

### B2 - HotelPublicDetailSerializer
- [ ] Returns complete hotel page payload
- [ ] Includes public_settings
- [ ] Active-only filtering works

### B3 - HotelPublicSettingsView
- [ ] Public endpoint returns safe subset
- [ ] No authentication required
- [ ] Returns 404 for missing hotels

### B4 - HotelPublicSettingsStaffView
- [ ] Color validation works
- [ ] Gallery/amenities validation works
- [ ] Staff can update all fields
- [ ] Non-staff cannot access

### B5 - Staff CRUD Views
- [ ] Offers CRUD works
- [ ] LeisureActivities CRUD works
- [ ] RoomTypes CRUD works
- [ ] Rooms CRUD works
- [ ] QR generation actions work
- [ ] Cross-hotel access blocked

### B6 - PricingQuoteView
- [ ] Quotes are persisted
- [ ] Quote IDs are unique
- [ ] Valid_until is set correctly
- [ ] Old quotes can be validated

### B7 - HotelBookingCreateView
- [ ] Bookings are persisted
- [ ] Booking IDs auto-generate
- [ ] Confirmation numbers auto-generate
- [ ] Status defaults to PENDING_PAYMENT

### B8 - Staff Booking Views
- [ ] List filters work correctly
- [ ] Status validation works
- [ ] Date filters work
- [ ] Confirm action updates status
- [ ] Error messages are clear

---

## Migration Requirements

No database migrations needed - all models already exist with correct fields.

---

## Frontend Integration Points

### For F1 - Public Hotel Page
**Endpoint:** `GET /api/public/hotels/<slug>/page/`
**Returns:** Complete hotel page data including:
- Hotel meta (name, tagline, hero, location)
- Booking options (CTAs, links)
- Room types (active only)
- Offers (active, date-valid)
- Leisure activities (active, grouped by category)
- Public settings (branding, gallery, amenities, contact)

### For F2-F8 - Staff Settings Sections
**Base Path:** `/api/staff/<hotel_slug>/`

**Endpoints:**
- `GET/PUT/PATCH /settings/` - Public page content & branding
- `GET/PUT/PATCH /access-config/` - Portal configuration
- `GET /offers/` - List offers
- `POST /offers/` - Create offer
- `PUT/PATCH /offers/{id}/` - Update offer
- `DELETE /offers/{id}/` - Delete offer
- (Similar patterns for leisure-activities, room-types, rooms)

### For F9 - Staff Bookings
**Endpoints:**
- `GET /bookings/?status=PENDING_PAYMENT&start_date=2025-01-01` - List bookings
- `POST /bookings/{booking_id}/confirm/` - Confirm booking

---

## Implementation Order

1. **Create new serializers** (B1)
2. **Update HotelPublicDetailSerializer** (B2)
3. **Add validation to settings serializer** (B4)
4. **Create staff_views.py with CRUD views** (B5)
5. **Update quote view** (B6)
6. **Update booking create view** (B7)
7. **Enhance booking list view** (B8)
8. **Update URL routing**
9. **Test all endpoints**
10. **Document for frontend team**

---

## Success Criteria

✅ All content models have staff CRUD APIs  
✅ Public page endpoint returns complete content  
✅ Quotes and bookings are persisted  
✅ Staff can manage all public content  
✅ Permissions properly restrict cross-hotel access  
✅ Validation prevents invalid data  
✅ Frontend can build complete UI from API responses  

---

## Next Steps After Implementation

1. Create frontend issues based on F1-F9
2. Document API with Swagger/OpenAPI
3. Add unit tests for all new views
4. Add integration tests for full booking flow
5. Set up monitoring for booking creation
6. Plan Phase 2 enhancements (payments, advanced booking)

---

**Document Status:** Ready for Implementation  
**Estimated Implementation Time:** 4-6 hours  
**Risk Level:** Low (most infrastructure exists)
