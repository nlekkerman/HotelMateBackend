# Hotel API Endpoints - Current State (After Public Code Removal)

Last Updated: November 25, 2025

---

## 🌐 PUBLIC ENDPOINTS (No Authentication Required)

### Landing Page APIs (ACTIVE - DO NOT REMOVE)

#### 1. Get Hotel List
```
GET /api/hotel/public/
```
**Purpose:** List all active hotels for landing page  
**Used by:** Landing page to display hotel cards  
**Response:** Array of hotels with basic info, logos, portal URLs

**Query Parameters:**
- `q` - Text search (name, city, country, descriptions)
- `city` - Filter by city (exact match)
- `country` - Filter by country (exact match)
- `tags` - Comma-separated tags
- `hotel_type` - Filter by hotel type
- `sort` - 'name_asc' or 'featured' (default)

**Example:**
```bash
curl http://localhost:8000/api/hotel/public/?city=Dublin&sort=name_asc
```

#### 2. Get Filter Options
```
GET /api/hotel/public/filters/
```
**Purpose:** Get available filter options for landing page  
**Used by:** Landing page filter UI  
**Response:** Lists of cities, countries, tags, hotel types

**Example:**
```bash
curl http://localhost:8000/api/hotel/public/filters/
```

---

## 🔐 STAFF ENDPOINTS (Authentication Required)

### Hotel Settings Management

#### 1. Get/Update Hotel Settings
```
GET    /api/staff/hotels/<slug>/hotel/settings/
PUT    /api/staff/hotels/<slug>/hotel/settings/
PATCH  /api/staff/hotels/<slug>/hotel/settings/
```
**Purpose:** Staff manage hotel public settings  
**Requires:** Staff authentication + same hotel  
**Features:**
- Override hotel name, tagline, contact info
- Upload hero image, landing page image, logo
- Manage galleries
- Customize branding colors
- Edit descriptions and content

**Example:**
```bash
curl -X PATCH \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name_override": "The Grand Killarney Hotel"}' \
  http://localhost:8000/api/staff/hotels/killarney/hotel/settings/
```

### Offers Management (CRUD)

#### 2. List/Create Offers
```
GET   /api/staff/hotels/<slug>/hotel/staff/offers/
POST  /api/staff/hotels/<slug>/hotel/staff/offers/
```

#### 3. Get/Update/Delete Offer
```
GET     /api/staff/hotels/<slug>/hotel/staff/offers/<id>/
PUT     /api/staff/hotels/<slug>/hotel/staff/offers/<id>/
PATCH   /api/staff/hotels/<slug>/hotel/staff/offers/<id>/
DELETE  /api/staff/hotels/<slug>/hotel/staff/offers/<id>/
```

### Leisure Activities Management (CRUD)

#### 4. List/Create Activities
```
GET   /api/staff/hotels/<slug>/hotel/staff/leisure-activities/
POST  /api/staff/hotels/<slug>/hotel/staff/leisure-activities/
```

#### 5. Get/Update/Delete Activity
```
GET     /api/staff/hotels/<slug>/hotel/staff/leisure-activities/<id>/
PUT     /api/staff/hotels/<slug>/hotel/staff/leisure-activities/<id>/
PATCH   /api/staff/hotels/<slug>/hotel/staff/leisure-activities/<id>/
DELETE  /api/staff/hotels/<slug>/hotel/staff/leisure-activities/<id>/
```

### Room Types Management (CRUD)

#### 6. List/Create Room Types
```
GET   /api/staff/hotels/<slug>/hotel/staff/room-types/
POST  /api/staff/hotels/<slug>/hotel/staff/room-types/
```

#### 7. Get/Update/Delete Room Type
```
GET     /api/staff/hotels/<slug>/hotel/staff/room-types/<id>/
PUT     /api/staff/hotels/<slug>/hotel/staff/room-types/<id>/
PATCH   /api/staff/hotels/<slug>/hotel/staff/room-types/<id>/
DELETE  /api/staff/hotels/<slug>/hotel/staff/room-types/<id>/
```

### Rooms Management (CRUD)

#### 8. List/Create Rooms
```
GET   /api/staff/hotels/<slug>/hotel/staff/rooms/
POST  /api/staff/hotels/<slug>/hotel/staff/rooms/
```

#### 9. Get/Update/Delete Room
```
GET     /api/staff/hotels/<slug>/hotel/staff/rooms/<id>/
PUT     /api/staff/hotels/<slug>/hotel/staff/rooms/<id>/
PATCH   /api/staff/hotels/<slug>/hotel/staff/rooms/<id>/
DELETE  /api/staff/hotels/<slug>/hotel/staff/rooms/<id>/
```

### Bookings Management

#### 10. List Bookings
```
GET /api/staff/hotels/<slug>/hotel/bookings/
```
**Query Parameters:**
- `status` - Filter by status (PENDING_PAYMENT, CONFIRMED, CANCELLED, etc.)
- `start_date` - Filter by check-in date (YYYY-MM-DD)
- `end_date` - Filter by check-out date (YYYY-MM-DD)

#### 11. Confirm Booking
```
POST /api/staff/hotels/<slug>/hotel/bookings/<booking_id>/confirm/
```

### Access Configuration

#### 12. Manage Access Config
```
GET     /api/staff/hotels/<slug>/hotel/staff/access-config/
PUT     /api/staff/hotels/<slug>/hotel/staff/access-config/
PATCH   /api/staff/hotels/<slug>/hotel/staff/access-config/
```

---

## 👥 GUEST ENDPOINTS (QR-Based, No Auth Required)

### Guest Site Pages

#### 1. Guest Home Page
```
GET /api/guest/hotels/<slug>/site/home/
```
**Response:** Hotel info with booking options

#### 2. Guest Rooms Page
```
GET /api/guest/hotels/<slug>/site/rooms/
```
**Response:** Room types with photos and pricing

#### 3. Guest Offers Page
```
GET /api/guest/hotels/<slug>/site/offers/
```
**Response:** Active offers with photos and descriptions

### Booking Flow

#### 4. Check Availability
```
GET /api/guest/hotels/<slug>/availability/
```
**Query Parameters:**
- `check_in` - YYYY-MM-DD
- `check_out` - YYYY-MM-DD
- `adults` - Number of adults (default: 2)
- `children` - Number of children (default: 0)

**Example:**
```bash
curl "http://localhost:8000/api/guest/hotels/killarney/availability/?check_in=2025-12-01&check_out=2025-12-03&adults=2&children=0"
```

#### 5. Get Pricing Quote
```
POST /api/guest/hotels/<slug>/pricing/quote/
```
**Body:**
```json
{
  "room_type_code": "STD",
  "check_in": "2025-12-01",
  "check_out": "2025-12-03",
  "adults": 2,
  "children": 0,
  "promo_code": "WINTER20"
}
```

#### 6. Create Booking
```
POST /api/guest/hotels/<slug>/bookings/
```
**Body:**
```json
{
  "quote_id": "abc123",
  "room_type_code": "STD",
  "check_in": "2025-12-01",
  "check_out": "2025-12-03",
  "adults": 2,
  "children": 0,
  "guest": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+353123456789"
  },
  "special_requests": "Late check-in",
  "promo_code": "WINTER20"
}
```

---

## 💳 BOOKING/PAYMENT ENDPOINTS

### Booking Availability & Pricing

#### 1. Check Hotel Availability
```
GET /api/hotel/<slug>/availability/
```
**Query Parameters:**
- `check_in` - YYYY-MM-DD
- `check_out` - YYYY-MM-DD
- `adults` - Number of adults
- `children` - Number of children

#### 2. Get Pricing Quote
```
POST /api/hotel/<slug>/pricing/quote/
```

#### 3. Create Booking
```
POST /api/hotel/<slug>/bookings/
```

### Payment Processing

#### 4. Create Payment Session
```
POST /api/hotel/<slug>/bookings/<booking_id>/payment/
POST /api/hotel/<slug>/bookings/<booking_id>/payment/session/
```

#### 5. Verify Payment
```
POST /api/hotel/<slug>/bookings/<booking_id>/payment/verify/
```

#### 6. Stripe Webhook
```
POST /api/hotel/bookings/stripe-webhook/
```

---

## 🔴 REMOVED ENDPOINTS (No Longer Available)

### Old Public Hotel Pages (REMOVED)

#### ❌ 1. Hotel Public Detail
```
GET /api/hotel/public/<slug>/
```
**Status:** 404 - Endpoint removed  
**Reason:** Old public marketing page replaced by dynamic sections

#### ❌ 2. Hotel Public Page (Complete)
```
GET /api/hotel/public/page/<slug>/
```
**Status:** 404 - Endpoint removed  
**Reason:** Old comprehensive hotel page replaced by dynamic sections

#### ❌ 3. Public Hotel Settings
```
GET /api/public/hotels/<slug>/settings/
```
**Status:** 404 - Endpoint removed  
**Reason:** Public settings now managed via staff endpoint only

---

## 📊 Endpoint Summary

### Active Endpoints:
- **2** Landing page public endpoints (hotel list, filters)
- **12** Staff management endpoints (settings, offers, rooms, bookings)
- **6** Guest/QR endpoints (home, rooms, offers, availability, quote, booking)
- **6** Payment endpoints (session, verify, webhook)

### Total: ~26 active endpoints

### Removed Endpoints:
- **3** Old public hotel page endpoints

---

## 🔄 Real-Time Updates (Pusher)

### Staff Settings Updates
When staff updates hotel settings, a Pusher event is broadcast:
```
Channel: hotel-<slug>
Event: settings-updated
Data: Full settings object with all fields
```

**Frontend should listen on:**
```javascript
const channel = pusher.subscribe(`hotel-${hotelSlug}`);
channel.bind('settings-updated', (data) => {
  // Update UI with new settings
});
```

---

## 🚀 Future Endpoints (To Be Added)

### Dynamic Section-Based Pages
```
GET  /api/public/pages/<slug>/              # Get page with sections
GET  /api/staff/pages/<slug>/sections/      # List sections
POST /api/staff/pages/<slug>/sections/      # Create section
PUT  /api/staff/pages/<slug>/sections/<id>/ # Update section
DELETE /api/staff/pages/<slug>/sections/<id>/ # Delete section
POST /api/staff/pages/<slug>/sections/reorder/ # Reorder sections
```

### Gallery Management (Enhanced)
```
POST /api/staff/hotels/<slug>/settings/gallery/upload/   # Upload images
POST /api/staff/hotels/<slug>/settings/gallery/reorder/  # Reorder gallery
DELETE /api/staff/hotels/<slug>/settings/gallery/remove/ # Delete image
```

---

## 📝 Notes

1. **Landing page APIs are critical** - Do not remove or modify without careful consideration
2. **Staff endpoints require authentication** - Use Bearer token in Authorization header
3. **Guest endpoints are public** - No authentication required (QR code based)
4. **Payment endpoints use Stripe** - Webhook endpoint must be registered in Stripe dashboard
5. **Real-time updates use Pusher** - Ensure Pusher credentials are configured

---

## 🔗 Related Documentation

- `PUBLIC_CODE_REMOVAL_SUMMARY.md` - Details of what was removed
- `docs/PHASE1_IMPLEMENTATION_COMPLETE.md` - Phase 1 implementation details
- `docs/FRONTEND_API_INTEGRATION.md` - Frontend integration guide
- `guest_urls.py` - Guest endpoint implementations
- `hotel/urls.py` - Main hotel endpoint routing
