# Booking API Contract Documentation

This document defines the canonical data shapes for booking objects across different API contexts in the HotelMate system.

## Overview

The HotelMate booking system uses different serializers to ensure consistent data shapes across various contexts:

- **Public API**: External booking system endpoints for guests
- **Staff API**: Internal hotel staff management endpoints  
- **Real-time Notifications**: WebSocket events for live updates

## API Contexts

### 1. Public API Booking Objects

**Used by**: External booking system, payment processing, guest-facing endpoints  
**Authentication**: No authentication required  
**Serializers**: `hotel.booking_serializers.*`

#### Public Booking Detail Response
```json
{
  "booking_id": "BK-2025-123456",
  "confirmation_number": "HOT-2025-1234",
  "status": "PENDING_PAYMENT",
  "created_at": "2025-12-16T15:30:00Z",
  "hotel": {
    "name": "Hotel Killarney",
    "slug": "hotel-killarney",
    "phone": "+353 64 663 1555",
    "email": "info@hotelkillarney.ie"
  },
  "room": {
    "type": "Deluxe King Room",
    "code": "DLX-KING",
    "photo": "https://example.com/room.jpg"
  },
  "dates": {
    "check_in": "2025-12-20",
    "check_out": "2025-12-22",
    "nights": 2
  },
  "guests": {
    "adults": 2,
    "children": 0,
    "total": 2
  },
  "guest": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+353 87 123 4567"
  },
  "special_requests": "Late check-in requested",
  "pricing": {
    "subtotal": "300.00",
    "taxes": "27.00", 
    "discount": "0.00",
    "total": "327.00",
    "currency": "EUR"
  },
  "promo_code": null,
  "payment_required": true,
  "payment_url": "/api/public/hotel/hotel-slug/room-bookings/BK-2025-123456/payment/session/"
}
```

**Characteristics**:
- Simple guest object (name, email, phone)
- Basic pricing breakdown
- Marketing-focused room information
- External payment URLs

### 2. Staff API Booking Objects

**Used by**: Hotel staff management interfaces, internal operations  
**Authentication**: Staff authentication required  
**Serializers**: `hotel.canonical_serializers.Staff*`

#### Staff Booking List Item
```json
{
  "booking_id": "BK-2025-123456",
  "confirmation_number": "HOT-2025-1234", 
  "status": "CONFIRMED",
  "check_in": "2025-12-20",
  "check_out": "2025-12-22",
  "nights": 2,
  "assigned_room_number": "101",
  "booker_type": "GUEST",
  "booker_summary": "John Doe (john@example.com)",
  "primary_guest_name": "John Doe",
  "party_total_count": 2,
  "created_at": "2025-12-16T15:30:00Z",
  "updated_at": "2025-12-16T16:00:00Z"
}
```

#### Staff Booking Detail
```json
{
  "booking_id": "BK-2025-123456",
  "confirmation_number": "HOT-2025-1234",
  "status": "CONFIRMED",
  "check_in": "2025-12-20",
  "check_out": "2025-12-22", 
  "nights": 2,
  "booker": {
    "type": "GUEST",
    "summary": "John Doe (john@example.com)",
    "details": {
      "first_name": "John",
      "last_name": "Doe", 
      "email": "john@example.com",
      "phone": "+353 87 123 4567"
    }
  },
  "primary_guest": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com", 
    "phone": "+353 87 123 4567"
  },
  "party": {
    "primary": {
      "id": 1,
      "role": "PRIMARY",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "email": "john@example.com",
      "phone": "+353 87 123 4567",
      "is_staying": true
    },
    "companions": [
      {
        "id": 2,
        "role": "COMPANION", 
        "first_name": "Jane",
        "last_name": "Doe",
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+353 87 123 4568",
        "is_staying": true
      }
    ],
    "walkins": [],
    "total_count": 2
  },
  "room": {
    "assigned_number": "101",
    "type_name": "Deluxe King Room",
    "type_code": "DLX-KING"
  },
  "flags": {
    "has_party": true,
    "is_checked_in": false,
    "has_special_requests": true,
    "payment_pending": false
  },
  "created_at": "2025-12-16T15:30:00Z",
  "updated_at": "2025-12-16T16:00:00Z"
}
```

**Characteristics**:
- Detailed party management with roles
- Operational flags for staff workflows
- Room assignment information
- Structured booker vs primary guest separation

### 3. Real-time Notification Payloads

**Used by**: WebSocket events, push notifications, live updates  
**Authentication**: Staff authentication required  
**Serializers**: Same as Staff API (`hotel.canonical_serializers.StaffRoomBookingDetailSerializer`)

#### Notification Event Example
```json
{
  "event": "booking_checked_in",
  "checked_in_at": "2025-12-20T15:00:00Z",
  "booking_id": "BK-2025-123456",
  "confirmation_number": "HOT-2025-1234",
  "status": "CHECKED_IN",
  // ... rest of Staff Booking Detail structure
}
```

**Characteristics**:
- Event metadata (event type, timestamp)
- Complete staff booking detail payload
- Consistent with staff API shapes

## Contract Guarantees

### Public API Contracts
- ✅ **Stable URLs**: `/api/public/hotel/{slug}/room-bookings/{booking_id}/`
- ✅ **Simple Structure**: Minimal guest info, basic pricing
- ✅ **External Integration**: Payment URLs, confirmation numbers
- ✅ **No Authentication**: Open access for booking lookups

### Staff API Contracts  
- ✅ **Canonical Serializers**: `StaffRoomBookingListSerializer`, `StaffRoomBookingDetailSerializer`
- ✅ **Rich Party Data**: Detailed guest management with roles
- ✅ **Operational Context**: Room assignments, status flags, timestamps
- ✅ **Consistent Structure**: Same shape across all staff endpoints

### Real-time Contracts
- ✅ **Staff Alignment**: Uses same canonical serializers as staff API
- ✅ **Event Metadata**: Event type, timestamps for all notifications
- ✅ **Complete Payloads**: Full booking detail in each event

## Implementation Notes

### Serializer Locations
- **Public**: `hotel/booking_serializers.py`
- **Staff**: `hotel/canonical_serializers.py` 
- **Notifications**: Uses `hotel/canonical_serializers.py`

### Validation Rules
- All booking IDs follow format: `BK-YYYY-XXXXXX`
- Staff endpoints require hotel slug validation
- Public endpoints allow anonymous access for booking lookups
- Payment sessions validate booking ownership via hotel+booking_id

### Migration Path
If breaking changes are required:
1. Create new serializer versions (e.g., `StaffRoomBookingDetailSerializerV2`)
2. Update contracts documentation
3. Coordinate frontend updates
4. Remove old serializers after migration period

## Endpoints Reference

### Public Booking Endpoints
- `GET /api/public/hotel/{slug}/room-bookings/{booking_id}/` - Booking detail lookup
- `POST /api/public/hotel/{slug}/room-bookings/{booking_id}/payment/session/` - Payment session

### Staff Booking Endpoints  
- `GET /api/staff/hotel/{slug}/room-bookings/` - List bookings
- `GET /api/staff/hotel/{slug}/room-bookings/{booking_id}/` - Booking detail
- `POST /api/staff/hotel/{slug}/room-bookings/{booking_id}/confirm/` - Confirm booking
- `POST /api/staff/hotel/{slug}/room-bookings/{booking_id}/cancel/` - Cancel booking

### Notification Events
- `booking_checked_in` - Guest checked into room
- `booking_checked_out` - Guest checked out of room  
- `booking_confirmed` - Staff confirmed booking
- `booking_cancelled` - Booking was cancelled