# 16. API Reference

## API Routing Architecture

The HotelMate backend uses a **zone-based routing pattern** to organize endpoints by user type and access level. All APIs are REST-based using Django REST Framework.

**Base URL Structure:**
```
/api/{zone}/[hotels/{hotel_slug}/]{endpoint}
```

## Authentication Overview

**Method:** Token-based authentication via Django REST Framework
- Header: `Authorization: Token {token_value}`
- Default authentication class: `TokenAuthentication`
- Default permission: `IsAuthenticated`

Evidence: `HotelMateBackend/settings.py` lines 218-228

## API Zones

### 1. Staff Zone (`/api/staff/`)

**Routing:** `staff_urls.py` - Staff portal endpoints with hotel context
**Authentication:** Required (staff token)
**Pattern:** `/api/staff/hotels/{hotel_slug}/{app_name}/`

**Key Endpoints:**

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | `/api/staff/hotels/{hotel_slug}/me/` | `StaffMeView` | Staff | Staff profile context |
| GET/POST | `/api/staff/hotels/{hotel_slug}/presets/` | `PresetViewSet` | Staff | Styling presets CRUD |
| GET/POST | `/api/staff/hotels/{hotel_slug}/room-types/` | `StaffRoomTypeViewSet` | Staff | Room type management |
| GET/POST | `/api/staff/hotels/{hotel_slug}/public-page/` | `HotelPublicPageViewSet` | Staff | Public website builder |
| GET/POST | `/api/staff/hotels/{hotel_slug}/public-sections/` | `PublicSectionViewSet` | Staff | Page sections CRUD |

**Wrapped App Endpoints:**
Each app's URLs are wrapped under the staff zone pattern:

```python
STAFF_APPS = [
    'attendance', 'chat', 'common', 'entertainment', 'guests',
    'home', 'hotel_info', 'maintenance', 'notifications', 
    'room_services', 'staff', 'staff_chat', 'stock_tracker'
]
```

Evidence: `staff_urls.py` lines 47-60

### 2. Guest Zone (`/api/guest/`)

**Routing:** `guest_urls.py` - Guest-facing booking and service endpoints
**Authentication:** Mixed (token for authenticated guests, public for booking)
**Pattern:** `/api/guest/hotels/{hotel_slug}/{endpoint}`

**Public Guest Endpoints (No Auth):**

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | `/api/guest/hotels/{hotel_slug}/` | `guest_home` | Public | Hotel information with booking options |
| GET | `/api/guest/hotels/{hotel_slug}/site/rooms/` | `guest_rooms` | Public | Available room types with photos |
| GET | `/api/guest/hotels/{hotel_slug}/availability/` | `check_availability` | Public | Room availability checker |
| POST | `/api/guest/hotels/{hotel_slug}/pricing/quote/` | `create_quote` | Public | Generate pricing quote |
| POST | `/api/guest/hotels/{hotel_slug}/bookings/` | `create_booking` | Public | Create new booking |

**Token-Authenticated Guest Endpoints:**

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | `/api/guest/context/` | `GuestContextView` | Guest Token | Booking context from token |
| GET | `/api/guest/room-service/` | `GuestRoomServiceView` | Guest Token | Room service context |
| GET/POST | `/api/guest/hotels/{hotel_slug}/room-services/orders/` | `OrderViewSet` | Guest Token | Room service orders |

**Guest Chat Endpoints:**

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | `/api/guest/hotel/{hotel_slug}/chat/context` | `CanonicalGuestChatContextView` | Guest Token | Chat context and history |
| POST | `/api/guest/hotel/{hotel_slug}/chat/messages` | `CanonicalGuestChatSendMessageView` | Guest Token | Send chat message |
| POST | `/api/guest/hotel/{hotel_slug}/chat/pusher/auth` | `CanonicalGuestChatPusherAuthView` | Guest Token | Pusher authentication |

Evidence: `guest_urls.py` lines 515-580

### 3. Public Zone (`/api/public/`)

**Routing:** `public_urls.py` - No authentication required
**Authentication:** None
**Pattern:** `/api/public/{endpoint}`

**Hotel Discovery:**

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | `/api/public/hotels/` | `HotelPublicListView` | Public | Hotel listing for landing page |
| GET | `/api/public/hotels/filters/` | `HotelFilterOptionsView` | Public | Available filters (tags, types, locations) |
| GET | `/api/public/hotel/{hotel_slug}/page/` | `HotelPublicPageView` | Public | Individual hotel public page |
| GET | `/api/public/presets/` | `PublicPresetsView` | Public | Frontend styling presets |

**Booking Management:**

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | `/api/public/hotel/{hotel_slug}/availability/` | `HotelAvailabilityView` | Public | Check room availability |
| POST | `/api/public/hotel/{hotel_slug}/pricing/quote/` | `HotelPricingQuoteView` | Public | Generate pricing quote |
| POST | `/api/public/hotel/{hotel_slug}/bookings/` | `HotelBookingCreateView` | Public | Create new booking |
| GET | `/api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/` | `PublicRoomBookingDetailView` | Public | Booking lookup |

**Payment Processing:**

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| POST | `/api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/payment/` | `CreatePaymentSessionView` | Public | Stripe payment session |
| POST | `/api/public/payment/verify/` | `VerifyPaymentView` | Public | Payment verification |
| POST | `/api/public/stripe/webhook/` | `StripeWebhookView` | Webhook | Stripe webhook handler |

**Booking Management:**

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | `/api/public/booking/{token}/validate/` | `ValidateBookingManagementTokenView` | Token | Validate booking token |
| POST | `/api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/cancel/` | `CancelBookingView` | Token | Cancel booking |
| GET | `/api/public/hotel/{hotel_slug}/cancellation-policy/` | `HotelCancellationPolicyView` | Public | Cancellation policy |

Evidence: `public_urls.py` lines 30-100

### 4. Hotel Admin Zone (`/api/hotel/`)

**Routing:** `hotel/urls.py` - Superuser hotel management
**Authentication:** Superuser required
**Pattern:** `/api/hotel/{endpoint}`

UNCLEAR IN CODE: Exact endpoints need analysis of `hotel/urls.py` file

### 5. Direct Access Zones

**Chat (`/api/chat/`):**
- Direct access to chat functionality
- Legacy compatibility maintained
- Evidence: `HotelMateBackend/urls.py` line 63

**Room Services (`/api/room_services/`):**
- Direct access to room service endpoints
- Evidence: `HotelMateBackend/urls.py` line 65

**Bookings (`/api/bookings/`):**
- Restaurant booking management system
- Evidence: `HotelMateBackend/urls.py` line 67

**Notifications (`/api/notifications/`):**
- Global Pusher authentication endpoint
- Evidence: `HotelMateBackend/urls.py` line 69

## Special Endpoints

**Face Configuration:**
```
GET /api/hotels/{hotel_slug}/face-config/
```
- Handler: `HotelFaceConfigView`
- Auth: Public access
- Purpose: Face recognition configuration
- Evidence: `HotelMateBackend/urls.py` line 53

**Root API Discovery:**
```
GET /
```
- Handler: `home` function
- Returns: HTML list of available API endpoints
- Evidence: `HotelMateBackend/urls.py` lines 26-41

## Request/Response Headers

**CORS Configuration:**
- Allowed Origins: Multiple frontend domains + localhost
- Allowed Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
- Custom Headers: `idempotency-key`, `x-hotel-id`, `x-hotel-slug`, `x-hotel-identifier`
- Credentials: Enabled

Evidence: `HotelMateBackend/settings.py` lines 278-309

## Error Handling

**Custom 404 Handler:**
```python
handler404 = 'common.views.custom_404'
```
Evidence: `HotelMateBackend/urls.py` line 44

## Multi-tenancy

Hotels are isolated using:
1. **Hotel Slug** in URL paths
2. **Custom Headers** for hotel identification  
3. **Database-level filtering** by hotel foreign keys

The routing system ensures all hotel-scoped endpoints include the hotel context, either through URL parameters or authentication tokens.