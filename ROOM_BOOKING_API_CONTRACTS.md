# RoomBooking API Contracts

**Status**: Source of Truth  
**Last Updated**: December 16, 2025  
**Version**: 1.0

## Public API (No Authentication)

Base Path: `/api/public/hotel/<hotel_slug>/`

### Availability Check

**Endpoint**: `GET /api/public/hotel/<hotel_slug>/availability/`

**Required Parameters**:
```json
{
  "check_in": "2025-01-15",
  "check_out": "2025-01-17", 
  "adults": 2,
  "children": 0
}
```

**Response Schema**:
```json
{
  "success": true,
  "data": {
    "check_in": "2025-01-15",
    "check_out": "2025-01-17",
    "nights": 2,
    "available_room_types": [
      {
        "id": 123,
        "name": "Standard Double",
        "description": "Comfortable room with city view",
        "max_occupancy": 2,
        "base_price_per_night": "120.00",
        "currency": "EUR",
        "available_rooms": 3,
        "amenities": ["WiFi", "AC", "TV"]
      }
    ]
  }
}
```

**Error Cases**:
- 400: Invalid date format or past dates
- 404: Hotel not found or inactive

### Pricing Quote

**Endpoint**: `POST /api/public/hotel/<hotel_slug>/quote/`

**Required Parameters**:
```json
{
  "room_type_id": 123,
  "check_in": "2025-01-15",
  "check_out": "2025-01-17",
  "adults": 2,
  "children": 0,
  "promo_code": "SAVE20"
}
```

**Response Schema**:
```json
{
  "success": true,
  "data": {
    "quote_id": "QT-ABC123DEF4",
    "room_type": {
      "id": 123,
      "name": "Standard Double"
    },
    "dates": {
      "check_in": "2025-01-15",
      "check_out": "2025-01-17",
      "nights": 2
    },
    "occupancy": {
      "adults": 2,
      "children": 0
    },
    "pricing": {
      "base_price_per_night": "120.00",
      "subtotal": "240.00",
      "taxes": "24.00",
      "fees": "10.00", 
      "discount": "20.00",
      "total": "254.00",
      "currency": "EUR"
    },
    "promo_code": "SAVE20",
    "valid_until": "2025-12-16T18:30:00Z"
  }
}
```

**Error Cases**:
- 400: Invalid room type, dates, or occupancy
- 409: Room type not available for dates
- 422: Invalid promo code

### Create Booking

**Endpoint**: `POST /api/public/hotel/<hotel_slug>/bookings/`

**Required Parameters**:
```json
{
  "quote_id": "QT-ABC123DEF4",
  "booker_type": "SELF",
  "primary_first_name": "John",
  "primary_last_name": "Doe", 
  "primary_email": "john@example.com",
  "primary_phone": "+1234567890",
  "special_requests": "Late check-in requested"
}
```

**Response Schema**:
```json
{
  "success": true,
  "data": {
    "booking_id": "BK-2025-0001",
    "confirmation_number": "HTL-2025-0001",
    "status": "PENDING_PAYMENT",
    "guest": {
      "primary_first_name": "John",
      "primary_last_name": "Doe",
      "primary_email": "john@example.com"
    },
    "dates": {
      "check_in": "2025-01-15",
      "check_out": "2025-01-17",
      "nights": 2
    },
    "room_type": {
      "id": 123,
      "name": "Standard Double"
    },
    "pricing": {
      "total_amount": "254.00",
      "currency": "EUR"
    },
    "payment_required": true,
    "created_at": "2025-12-16T15:30:00Z"
  }
}
```

**Error Cases**:
- 400: Missing required fields or invalid quote
- 409: Quote expired or room no longer available
- 422: Validation errors

### Public Booking Detail

**Endpoint**: `GET /api/public/hotel/<hotel_slug>/bookings/<booking_id>/`

**Response Schema**:
```json
{
  "success": true,
  "data": {
    "booking_id": "BK-2025-0001",
    "confirmation_number": "HTL-2025-0001", 
    "status": "CONFIRMED",
    "guest": {
      "primary_first_name": "John",
      "primary_last_name": "Doe"
    },
    "dates": {
      "check_in": "2025-01-15",
      "check_out": "2025-01-17",
      "nights": 2
    },
    "room_type": {
      "name": "Standard Double"
    },
    "pricing": {
      "total_amount": "254.00", 
      "currency": "EUR"
    },
    "special_requests": "Late check-in requested"
  }
}
```

**Note**: Public view excludes internal fields, payment details, and staff notes.

### Payment Endpoints

**Payment Initiation**: `POST /api/public/hotel/<hotel_slug>/bookings/<booking_id>/payment/`

**Webhook Handler**: `POST /api/public/webhooks/payment/<provider>/`

**Payment verification handled by payment processor integration. Booking status updated automatically on successful payment.**

## Staff API (Authentication Required)

Base Path: `/api/staff/hotel/<hotel_slug>/room-bookings/`

**Authentication**: JWT token required. Staff must have access to hotel.

### List Bookings

**Endpoint**: `GET /api/staff/hotel/<hotel_slug>/room-bookings/`

**Query Parameters**:
- `status`: Filter by status (PENDING_PAYMENT, CONFIRMED, etc.)
- `check_in_date`: Filter by check-in date
- `search`: Search by guest name, booking ID, or confirmation number
- `page`: Page number for pagination

**Response Schema**:
```json
{
  "success": true,
  "data": {
    "count": 25,
    "next": "?page=2", 
    "previous": null,
    "results": [
      {
        "booking_id": "BK-2025-0001",
        "confirmation_number": "HTL-2025-0001",
        "status": "CONFIRMED",
        "primary_guest_name": "John Doe",
        "check_in": "2025-01-15",
        "check_out": "2025-01-17",
        "room_type": "Standard Double",
        "assigned_room": null,
        "total_amount": "254.00",
        "created_at": "2025-12-16T15:30:00Z"
      }
    ]
  }
}
```

### Booking Detail

**Endpoint**: `GET /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/`

**Response Schema**: 
```json
{
  "success": true,
  "data": {
    "booking_id": "BK-2025-0001",
    "confirmation_number": "HTL-2025-0001",
    "status": "CONFIRMED",
    "booker_type": "SELF",
    "primary_first_name": "John",
    "primary_last_name": "Doe",
    "primary_email": "john@example.com", 
    "primary_phone": "+1234567890",
    "check_in": "2025-01-15",
    "check_out": "2025-01-17",
    "nights": 2,
    "adults": 2,
    "children": 0,
    "room_type": {
      "id": 123,
      "name": "Standard Double"
    },
    "assigned_room": null,
    "total_amount": "254.00",
    "currency": "EUR",
    "payment_reference": "pi_abc123",
    "payment_provider": "stripe",
    "paid_at": "2025-12-16T16:00:00Z",
    "special_requests": "Late check-in requested",
    "internal_notes": "",
    "party": {
      "primary": {
        "id": 456,
        "first_name": "John", 
        "last_name": "Doe",
        "email": "john@example.com",
        "role": "PRIMARY"
      },
      "companions": []
    },
    "created_at": "2025-12-16T15:30:00Z",
    "updated_at": "2025-12-16T16:00:00Z"
  }
}
```

### Confirm Booking

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/confirm/`

**Response**: Updated booking detail with `status: "CONFIRMED"`

**Permissions**: Staff with booking management role

### Cancel Booking  

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/cancel/`

**Parameters**:
```json
{
  "reason": "Guest requested cancellation"
}
```

**Response**: Updated booking detail with `status: "CANCELLED"`

### Assign Room

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/assign-room/`

**Parameters**:
```json
{
  "room_id": 789
}
```

**Response**: Updated booking detail with assigned room

**Validation**: Room must be available and match booking room_type

### Check-in

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/check-in/`

**Requirements**: 
- Booking status must be CONFIRMED
- Room must be assigned
- Check-in date must be today or past

**Response**: Updated booking detail with `checked_in_at` timestamp

### Check-out

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/check-out/`

**Response**: Updated booking detail with `checked_out_at` timestamp and `status: "COMPLETED"`

### Party Management

**Add Companion**: `POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/party/`

**Update Party Member**: `PATCH /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/party/<guest_id>/`

**Remove Companion**: `DELETE /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/party/<guest_id>/`

**Note**: PRIMARY party member cannot be deleted, only updated.

## Public vs Staff Response Differences

### Public API Excludes:
- Internal notes
- Payment details (reference, provider)
- Staff-only fields (booker info when booker_type != SELF)
- Party management details
- Audit timestamps (updated_at)
- Room assignment details

### Staff API Includes:
- All booking fields
- Complete payment information  
- Internal notes and audit trail
- Full party management
- Room assignment workflow
- Advanced filtering and search

## Error Response Format

All APIs use consistent error format:
```json
{
  "success": false,
  "error": {
    "code": "BOOKING_NOT_FOUND",
    "message": "Booking not found or you don't have permission to access it",
    "details": {}
  }
}
```

## Rate Limiting

- Public API: 100 requests/minute per IP
- Staff API: 1000 requests/minute per authenticated user