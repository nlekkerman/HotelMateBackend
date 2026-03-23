# HotelMates Backend Audit Report

**Date:** March 23, 2026  
**Scope:** Django backend only — models, views, services, permissions, realtime, scheduling  
**Codebase:** `HotelMateBackend/` — Django 4.x + DRF + Pusher + Firebase + Stripe + Cloudinary

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Domain Map](#2-domain-map)
3. [Model Relationships](#3-model-relationships)
4. [Multi-Tenant Design Analysis](#4-multi-tenant-design-analysis)
5. [Booking & Room Allocation Flow](#5-booking--room-allocation-flow)
6. [Guest Lifecycle & Token System](#6-guest-lifecycle--token-system)
7. [Pre-Check-In System](#7-pre-check-in-system)
8. [RBAC Analysis](#8-rbac-analysis)
9. [Communication & Realtime](#9-communication--realtime)
10. [Attendance & Roster](#10-attendance--roster)
11. [Automation & Scheduler Overview](#11-automation--scheduler-overview)
12. [API Design Overview](#12-api-design-overview)
13. [Risk Areas](#13-risk-areas)
14. [Top 5 Backend Weaknesses](#14-top-5-backend-weaknesses)
15. [Top 5 Backend Strengths](#15-top-5-backend-strengths)

---

## 1. Executive Summary

HotelMates is a **multi-tenant hotel operations platform** built on Django + Django REST Framework. It spans ~20 Django apps, 33+ models in the core `hotel` app alone, and covers bookings, guest lifecycle, staff management, real-time chat, attendance/roster, room service, and a CMS-style public page builder.

**Architecture style:** Monolithic Django with app-per-domain separation. Real-time via Pusher (not Django Channels/WebSockets). Push notifications via Firebase FCM. Payments via Stripe Checkout. Media via Cloudinary. Deployed on Heroku (single web dyno, no worker process).

**Multi-tenant model:** Hotel-scoped via `slug` in URL paths. Every domain model FKs to `Hotel`. No schema-based isolation — tenant separation is enforced per-view, **inconsistently**.

### Key Findings

| Category | Rating | Summary |
|----------|--------|---------|
| Token security | **Strong** | 256-bit entropy, SHA-256 hash storage, atomic rotation, scope-based access |
| Booking flow | **Strong** | Complete lifecycle with Stripe integration, cancellation tiers, overstay handling |
| Room state machine | **Strong** | 7-state workflow with enforced transitions, atomic assignment with row locks |
| Multi-tenant isolation | **Critical gaps** | 4+ apps have unscoped `objects.all()` querysets; cross-hotel data leakage confirmed |
| RBAC | **Critical gaps** | Superuser escalation vulnerability; 15+ endpoints fully unprotected |
| Realtime security | **High risk** | Most Pusher channels lack `private-` prefix; test endpoints exposed |
| Scheduling | **High risk** | 6 of 7 critical scheduled commands have no deployment configuration |
| Notifications | **No persistence** | Fire-and-forget only; no notification inbox, history, or retry |

---

## 2. Domain Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HOTELMATES BACKEND                          │
├─────────────┬───────────────┬──────────────┬────────────────────────┤
│  CORE       │  OPERATIONS   │  COMMS       │  SUPPORT               │
│             │               │              │                        │
│  hotel      │  rooms        │  chat        │  entertainment         │
│  (33+ models)│  housekeeping │  staff_chat  │  stock_tracker         │
│  guests     │  room_services│  notifications│  maintenance          │
│  staff      │  attendance   │              │  hotel_info            │
│  bookings   │  room_bookings│              │  voice_recognition     │
│             │               │              │  common                │
│  apps/      │               │              │  home                  │
│   booking   │               │              │                        │
└─────────────┴───────────────┴──────────────┴────────────────────────┘
```

### App Purposes

| App | Purpose | Main Models |
|-----|---------|-------------|
| `hotel` | Core tenant model, RoomBooking, tokens, cancellation, public page builder, surveys, overstay | Hotel, RoomBooking, BookingGuest, GuestBookingToken, CancellationPolicy, HotelPublicPage, HotelAccessConfig, HotelPrecheckinConfig, AttendanceSettings, OverstayIncident |
| `rooms` | Room inventory, types, rates, daily pricing, turnover state machine | Room, RoomType, RatePlan, RoomTypeRatePlan, DailyRate |
| `staff` | Staff profiles, departments, roles, navigation, registration codes | Staff, Department, Role, NavigationItem, RegistrationCode |
| `guests` | In-house guest tracking (created at check-in from BookingGuest) | Guest |
| `housekeeping` | Room turnover workflow (cleaning, inspection) | HousekeepingTask, TurnoverPolicy |
| `room_bookings` | PMS-level booking management, room assignment, checkout, overstay | Services only (uses hotel models) |
| `bookings` | Restaurant/service bookings | ServiceBooking |
| `chat` | Guest ↔ staff chat (per-room conversations) | Conversation, RoomMessage, MessageAttachment |
| `staff_chat` | Staff ↔ staff chat (1:1 and group) | StaffConversation, StaffChatMessage |
| `attendance` | Clock-in/out, face recognition, roster, shift planning | ClockLog, StaffFace, RosterPeriod, StaffRoster, ShiftTemplate |
| `notifications` | Pusher events, FCM push, email dispatch | No persistence models — fire-and-forget |
| `room_services` | Room service menu items and guest orders | RoomServiceItem, RoomServiceOrder |
| `stock_tracker` | Inventory management, stocktaking, cocktails | Ingredient, StockItem, Stocktake, Sale |
| `maintenance` | Maintenance requests and comments | MaintenanceRequest, MaintenanceComment |
| `hotel_info` | Hotel info categories, QR codes | HotelInfoCategory, HotelInfo |
| `entertainment` | Quiz, memory games, tournaments | QuizSession, MemoryGameSession, Tournament |
| `voice_recognition` | OpenAI Whisper voice transcription | — |
| `common` | Shared mixins, utilities, custom 404 | HotelScopedViewSetMixin |
| `apps/booking` | Additional booking services | Services only |

---

## 3. Model Relationships

### Core Tenant Graph

```
Hotel (slug, name, timezone)
 ├── 1:1 HotelAccessConfig (checkout times, approval SLA, PIN settings)
 ├── 1:1 HotelPrecheckinConfig (fields_enabled, fields_required JSONFields)
 ├── 1:1 HotelSurveyConfig (survey field config, email policy)
 ├── 1:1 AttendanceSettings (break/overtime thresholds, face recognition config)
 ├── 1:1 BookingOptions (booking CTA config)
 ├── FK  CancellationPolicy → CancellationPolicyTier (tiered cancellation fees)
 ├── FK  RoomType (code, max_occupancy, bed_setup, starting_price)
 │    ├── FK  RoomTypeRatePlan → RatePlan (discount, refundable, cancellation_policy)
 │    └── FK  DailyRate (date-specific pricing per room_type + rate_plan)
 ├── FK  Room (room_number, room_type, room_status [7-state machine])
 ├── FK  Staff (user 1:1, department, role, access_level, duty_status)
 │    ├── FK  Department → Role
 │    └── M2M NavigationItem (frontend nav permissions)
 ├── FK  RoomBooking (booking_id, status, check_in/out, payment, room assignment)
 │    ├── FK  BookingGuest (role: PRIMARY/COMPANION/BOOKER, precheckin_payload)
 │    ├── FK  GuestBookingToken (hashed token, scopes, expiry)
 │    ├── FK  BookingPrecheckinToken (hashed, 72h expiry, config snapshot)
 │    ├── FK  BookingManagementToken (status-based validity)
 │    ├── FK  BookingSurveyToken (single-use, post-checkout)
 │    ├── FK  OverstayIncident (OPEN/ACKED/DISMISSED/RESOLVED)
 │    └── FK  BookingExtension (extended checkout, Stripe PaymentIntent)
 ├── FK  Guest (created at check-in from BookingGuest, links to Room)
 ├── FK  Conversation → RoomMessage → MessageAttachment
 ├── FK  StaffConversation → StaffChatMessage
 ├── FK  ClockLog (clock in/out, face verified, roster shift link)
 ├── FK  RosterPeriod → StaffRoster (shift date/time/location)
 ├── FK  StaffFace (128-dim encoding, consent, audit trail)
 └── FK  HotelPublicPage → PublicSection → PublicElement → PublicElementItem
```

### Booking ↔ Room ↔ Guest Triangle

```
RoomBooking ──FK──> RoomType (what was booked)
RoomBooking ──FK──> Room (assigned_room, set post-confirmation)
RoomBooking ──1:N─> BookingGuest (party members)
Guest ──FK──> Room (current room)
Guest ──FK──> RoomBooking (source booking)
Guest ──FK──> BookingGuest (source party member)
Room ──FK──> RoomType
```

---

## 4. Multi-Tenant Design Analysis

### How Hotels Are Represented

The `Hotel` model ([hotel/models.py](../hotel/models.py)) is the central tenant entity with a unique `slug` and optional unique `subdomain`. Every domain model has a `ForeignKey` to `Hotel`.

### How Hotel Slug Is Used

Three URL zones resolve hotel from the URL path:

| Zone | URL Pattern | Resolution |
|------|-------------|-----------|
| Staff | `/api/staff/hotel/<hotel_slug>/...` | URL slug + staff profile cross-check |
| Guest | `/api/guest/hotels/<hotel_slug>/...` | URL slug via `get_object_or_404(Hotel, slug=...)` |
| Public | `/api/public/hotel/<hotel_slug>/...` | URL slug, no auth required |

A parallel `hotel/middleware.py` resolves hotel from subdomain → `request.hotel`, but this is **not used** by the main URL-based routing.

### How Requests Are Scoped

Four distinct patterns exist across the codebase:

| Pattern | Security | Used By |
|---------|----------|---------|
| **A. `HotelScopedViewSetMixin`** ([common/mixins.py](../common/mixins.py)) — resolves hotel from URL, cross-checks against `staff_profile.hotel`, forces `queryset.filter(hotel=staff_hotel)` on reads and `hotel=staff_hotel` on writes | **Excellent** | attendance, housekeeping |
| **B. Staff profile scoping** — `request.user.staff_profile.hotel` used to filter querysets | **Good** | rooms, hotel/staff_views |
| **C. URL slug direct** — `get_object_or_404(Hotel, slug=...)` with manual cross-check | **Adequate** | housekeeping, chat, bookings |
| **D. Header-based** — `x-hotel-slug` HTTP header (client-controlled) | **Risky** | guests app |

### Tenant Isolation Assessment: RISKY

#### CRITICAL — No Hotel Filtering At All

| App/View | Issue | Impact |
|----------|-------|--------|
| `maintenance/views.py` — `MaintenanceRequestViewSet` | `queryset = MaintenanceRequest.objects.all()` — no hotel filter on reads | Any authenticated user sees all hotels' maintenance requests |
| `maintenance/views.py` — `MaintenanceCommentViewSet` | `AllowAny` + `objects.all()` | Anyone can read maintenance comments from any hotel |
| `staff/views.py` — `DepartmentViewSet`, `RoleViewSet` | `objects.all()` | Cross-hotel department/role data visible |
| `staff/views.py` — `NavigationItemViewSet` | Filters by hotel only if `?hotel_slug=` param sent | Any authenticated user can CRUD nav items for any hotel |
| `entertainment/views.py` — All ViewSets | `AllowAny` + `objects.all()` with optional `?hotel=` | Anonymous users access/modify game data across hotels |
| `stock_tracker/report_views.py` | `AllowAny` on stock value and sales reports | Anyone can view financial data for any hotel |

#### HIGH — Header-Based Trust

`guests/views.py` — Relies on `x-hotel-slug` HTTP header. An authenticated user from Hotel A can pass `x-hotel-slug: hotel-b` to access Hotel B's guest data.

### Recommendations

1. **Standardize on `HotelScopedViewSetMixin`** for all staff-facing ViewSets
2. **Replace header-based scoping** in `guests/views.py` with URL slug + staff profile cross-check
3. **Audit and fix all `objects.all()`** querysets in hotel-scoped models
4. **Make hotel filtering mandatory** — any `get_queryset()` that optionally filters should be treated as a bug

---

## 5. Booking & Room Allocation Flow

### Booking Creation Pipeline

```
1. GET  /api/public/hotel/{slug}/availability/     → get_room_type_availability()
2. POST /api/public/hotel/{slug}/pricing/quote/     → build_pricing_quote_data()
3. POST /api/public/hotel/{slug}/booking/create/    → create_room_booking_from_request()
4. POST /api/public/hotel/{slug}/payment/session/   → Stripe Checkout Session
5. WEBHOOK Stripe checkout.session.completed         → PENDING_APPROVAL + email
6. STAFF  approve/decline                            → CONFIRMED or DECLINED + refund
```

### State Machine

```
PENDING_PAYMENT ──(pay)──> PENDING_APPROVAL ──(approve)──> CONFIRMED ──(check-in)──> IN_HOUSE ──(checkout)──> COMPLETED
                                             ──(decline)──> DECLINED
                ──(expire)──> EXPIRED / CANCELLED_DRAFT
CONFIRMED ──(cancel)──> CANCELLED
PENDING_PAYMENT ──(cancel)──> CANCELLED
```

### Room Assignment

Room assignment is a **post-confirmation staff action**, not automated. `RoomAssignmentService` ([room_bookings/services/room_assignment.py](../room_bookings/services/room_assignment.py)):

- `find_available_rooms_for_booking()` — filters by: same hotel, matching `room_type`, `is_bookable()==True`, no date overlap
- `assign_room_atomic()` — uses `select_for_update()` on booking + room + conflicting bookings for concurrency safety
- Only CONFIRMED bookings can have rooms assigned
- Reassignment allowed pre-check-in only

### Room State Machine

7-state turnover workflow in `Room` model ([rooms/models.py](../rooms/models.py)):

```
OCCUPIED → CHECKOUT_DIRTY → CLEANING_IN_PROGRESS → CLEANED_UNINSPECTED → READY_FOR_GUEST → OCCUPIED
                          → MAINTENANCE_REQUIRED → OUT_OF_ORDER → READY_FOR_GUEST
```

`is_bookable()` = `room_status == 'READY_FOR_GUEST'` AND `is_active` AND NOT `maintenance_required` AND NOT `is_out_of_order`

### Pricing

Priority chain: `DailyRate` → `RoomTypeRatePlan.base_price` → `RoomType.starting_price_from`  
VAT hardcoded at 9% (Ireland). Promotions via DB `Promotion` model or legacy hardcoded codes (WINTER20, SAVE10).

### Cancellation

`CancellationCalculator` ([hotel/services/cancellation.py](../hotel/services/cancellation.py)):
- **FLEXIBLE / MODERATE / NON_REFUNDABLE** templates with `free_until_hours` threshold
- **CUSTOM** policies with tiered `hours_before_checkin` thresholds
- Penalty types: NONE, FIXED, PERCENTAGE, FIRST_NIGHT, FULL_STAY
- Guest cancellation triggers Stripe void (pending) or refund (paid)

### Overstay Handling

`detect_overstays()` ([room_bookings/services/overstay.py](../room_bookings/services/overstay.py)):
- Scans IN_HOUSE bookings past checkout deadline (hotel timezone-aware)
- Creates `OverstayIncident` (OPEN → ACKED → RESOLVED)
- Extension: extends `check_out`, creates `BookingExtension` with Stripe PaymentIntent, checks room conflicts

### Booking Risks

| Risk | Severity | Detail |
|------|----------|--------|
| No availability re-check at creation | **HIGH** | `create_room_booking_from_request()` never calls `is_room_type_available()`. Two concurrent bookings for the last room could both succeed. |
| Booking ID race condition | **HIGH** | `_generate_unique_booking_id()` in `RoomBooking.save()` uses count+increment without locking. |
| Dual booking ID generators | **MEDIUM** | Model's `save()` and service's `generate_booking_id()` produce different formats (`BK-{YEAR}-NNNN` vs `BK-{HOTEL}-{YEAR}-NNNN`). |
| Extension updates dates before payment | **HIGH** | `extend_overstay()` sets `booking.check_out` immediately; if payment fails, extended dates persist. |
| Webhook fallback cross-hotel | **MEDIUM** | If metadata lookup fails, `payment_reference` search may match wrong booking across hotels. |
| Hardcoded VAT rate | **LOW** | 9% for Ireland — no multi-country support. |

---

## 6. Guest Lifecycle & Token System

### Token Architecture

| Token Type | Model | Purpose | Expiry | Auth |
|------------|-------|---------|--------|------|
| `GuestBookingToken` | [hotel/models.py](../hotel/models.py) | Ongoing guest portal access | check_out + 30 days | Scope-based |
| `BookingPrecheckinToken` | [hotel/models.py](../hotel/models.py) | One-time pre-check-in form | 72 hours | Single-use |
| `BookingManagementToken` | [hotel/models.py](../hotel/models.py) | Booking status + cancellation | Status-based (no time limit) | Action-tracked |
| `BookingSurveyToken` | [hotel/models.py](../hotel/models.py) | Post-checkout survey | Time-based (hotel config) | Single-use |

### Generation & Storage

All tokens use identical cryptographic generation:
```
raw_token = secrets.token_urlsafe(32)    → 256 bits entropy (CSPRNG)
token_hash = SHA-256(raw_token)          → stored in DB (raw never stored)
```

DB lookup by `token_hash` (indexed). `UniqueConstraint` on `GuestBookingToken` ensures one active token per booking. Generating a new token atomically revokes the previous.

### GuestBookingToken Scopes

| Scope | Access | Required Booking Status |
|-------|--------|------------------------|
| `STATUS_READ` | View booking context (dates, room, status) | Any active |
| `CHAT` | Guest ↔ staff messaging | CONFIRMED or CHECKED_IN |
| `ROOM_SERVICE` | Place room service orders | CHECKED_IN + assigned room |

### Full Guest Lifecycle

```
BROWSING → BOOKING CREATED → PAYMENT → CONFIRMED → PRE-CHECK-IN → CHECK-IN → IN-HOUSE → CHECKOUT → POST-STAY
           ↓                 ↓         ↓            ↓               ↓          ↓          ↓          ↓
           GuestBookingToken  New       —            Precheckin      New        Chat+      Tokens     Survey
           (FULL_ACCESS)      status                 Token           GBT        RoomSvc    revoked    token
           + ManagementToken  token                  (72h)           (CHAT)     active                sent
```

### Security Assessment

**Strengths:**
- 256-bit token entropy — brute-force infeasible
- Hash-only storage — DB compromise doesn't leak tokens
- Atomic token rotation — new token revokes old
- Anti-enumeration — all invalid states return identical 404 responses
- Config snapshots — precheckin/survey tokens freeze field configuration

**Risks:**

| Risk | Severity | Detail |
|------|----------|--------|
| No rate limiting on token validation | **MEDIUM** | Endpoints lack throttling (brute-force impractical but endpoints exposed to DoS) |
| Management token never time-expires | **LOW-MEDIUM** | Valid until booking status changes — could persist for months |
| `VIEW_STATUS` vs `STATUS_READ` scope mismatch | **LOW** | Payment webhook creates token with `VIEW_STATUS` scope but `resolve_token_context()` checks for `STATUS_READ` — guest gets no `allowed_actions` after payment |
| Token in URL query parameter | **LOW** | Management emails send `?token=` in URL — appears in server logs, browser history, referrer headers |

---

## 7. Pre-Check-In System

### Form Definition

**Dynamic per-hotel configuration** via `HotelPrecheckinConfig` ([hotel/models.py](../hotel/models.py)):
- `fields_enabled` (JSONField) — `{field_key: bool}` for which fields appear
- `fields_required` (JSONField) — `{field_key: bool}` for mandatory fields

**Field Registry** ([hotel/precheckin/field_registry.py](../hotel/precheckin/field_registry.py)):

| Field | Type | Scope |
|-------|------|-------|
| `eta` | text | booking |
| `special_requests` | textarea | booking |
| `consent_checkbox` | checkbox | booking |
| `nationality` | select (countries) | guest |
| `country_of_residence` | select (countries) | guest |
| `date_of_birth` | date | guest |
| `id_document_type` | select | guest |
| `id_document_number` | text | guest |
| `address_line_1` | text | guest |
| `city` | text | guest |
| `postcode` | text | guest |

### Data Storage

Two-level scheme based on field scope:
- **Booking-scoped** (eta, special_requests, consent): `RoomBooking.precheckin_payload` JSONField
- **Guest-scoped** (nationality, DOB, ID docs, address): each `BookingGuest.precheckin_payload` JSONField

### Validation Logic

`SubmitPrecheckinDataView` ([hotel/public_views.py](../hotel/public_views.py)):
1. Token validation (hash lookup, `is_valid` check)
2. Config resolution (token's config snapshot or current hotel config)
3. Required-field enforcement
4. Unknown-field rejection (not in registry)
5. Disabled-field rejection (not enabled in config)
6. Party structure validation (size match, PRIMARY preserved, companions need names)
7. Atomic transaction (delete old companions, update PRIMARY, create new companions)

### Config Snapshot Mechanism

When staff sends a pre-check-in link, current `fields_enabled` and `fields_required` are copied into the token's `config_snapshot_enabled` and `config_snapshot_required`. This ensures the guest's form doesn't change mid-flight if hotel admin updates config.

### Pre-Check-In Risks

| Risk | Severity | Detail |
|------|----------|--------|
| PII in logs | **HIGH** | `print()` statements with `json.dumps(request.data)` output names, emails, ID docs to stdout |
| Guest-scoped required fields not validated | **HIGH** | Required-field check only runs against top-level `request.data`, not per-guest `precheckin_payload` fields |
| Snapshot fallback bug | **MEDIUM** | `if token.config_snapshot_enabled` is falsy for empty `{}` dicts, falling through to current config instead of respecting the snapshot |
| No management command for token cleanup | **MEDIUM** | Referenced in docs but doesn't exist; expired tokens accumulate |
| `clean()` not auto-called on `save()` | **LOW** | Config validation only runs when staff view calls `full_clean()` |

---

## 8. RBAC Analysis

### Roles & Access Levels

**Staff `access_level`** (3 tiers in [staff/models.py](../staff/models.py)):

| Level | Intent |
|-------|--------|
| `regular_staff` | Default, limited access |
| `staff_admin` | Can generate registration codes, view open housekeeping |
| `super_staff_admin` | Can manage nav permissions, update access levels, manage hotel page builder |

**Additional privilege axes:**
- `is_superuser` (Django) — grants full `StaffViewSet` access, bypasses nav permissions
- `Department` / `Role` — used for display/filtering, not enforcement (except staff_chat: `role.slug in ['manager', 'admin']`)
- `NavigationItem` M2M — frontend nav, enforced server-side via `HasNavPermission`

### Custom Permission Classes

| Class | File | Purpose |
|-------|------|---------|
| `IsSuperUser` | [staff/permissions_superuser.py](../staff/permissions_superuser.py) | `user.is_superuser` check |
| `IsSuperUser` (duplicate) | [hotel/base_views.py](../hotel/base_views.py) | Different implementation |
| `IsSuperStaffAdminForHotel` | [hotel/permissions.py](../hotel/permissions.py) | `access_level == 'super_staff_admin'` + hotel scope |
| `HasNavPermission` | [staff/permissions.py](../staff/permissions.py) | Checks `allowed_navigation_items` |
| `IsStaffMember` | [staff_chat/permissions.py](../staff_chat/permissions.py) | `hasattr(user, 'staff_profile')` |
| `IsSameHotel` | [staff_chat/permissions.py](../staff_chat/permissions.py) | Staff hotel matches URL slug |
| `IsConversationParticipant` | [staff_chat/permissions.py](../staff_chat/permissions.py) | Object-level participant check |
| `CanManageConversation` | [staff_chat/permissions.py](../staff_chat/permissions.py) | Creator or manager role |

### CRITICAL Vulnerabilities

**1. Superuser Escalation at Staff Registration** ([staff/views.py](../staff/views.py))
```python
user.is_superuser = False
if "is_superuser" in request.data:
    user.is_superuser = request.data["is_superuser"]  # Any staff can escalate!
```
Any authenticated staff member creating another staff profile can set `is_superuser=True` via the POST body, granting full Django admin + `IsSuperUser` bypass.

**2. stock_tracker ViewSets — No Permissions** ([stock_tracker/views.py](../stock_tracker/views.py))  
All 15 ViewSets rely only on DRF default `IsAuthenticated`. Any authenticated user from any hotel can read/write stock data across all hotels.

**3. stock_tracker Reports — Fully Open** ([stock_tracker/report_views.py](../stock_tracker/report_views.py))  
`AllowAny` on `StockValueReportView` and `SalesReportView`. Anyone can view financial data for any hotel.

**4. No Access Level Check on Staff Creation** ([staff/views.py](../staff/views.py))  
`CreateStaffFromUserAPIView` has no `access_level` restriction. A `regular_staff` can create `super_staff_admin` users.

### Fully Unprotected Endpoints (AllowAny)

| App | Count | Risk Level |
|-----|-------|------------|
| `entertainment` | ~15+ | All quiz/game data — public by design, but mutation is open |
| `chat` | ~14 | Guest chat — some use manual token auth internally |
| `hotel/public_views` | ~12 | Public hotel pages — by design |
| `bookings` | 5+ | Restaurant bookings; one has `permission_classes = []` |
| `room_services` | 4+ | Room service menus AND order creation — fully open |
| `hotel/booking_views` | 4 | Public booking flow — by design |
| `stock_tracker/report_views` | 2 | Financial reports — **should not be open** |

### Hotel Scoping by App

| App | Scoped? | Method |
|-----|---------|--------|
| attendance | Partial | 1 view uses Mixin, rest use default |
| housekeeping | Yes | `HotelScopedViewSetMixin` |
| staff_chat | Yes | `IsSameHotel` permission |
| hotel/staff_views | Yes | `IsSuperStaffAdminForHotel` |
| rooms | Partial | Some views use `IsSameHotel`, some only `IsAuthenticated` |
| **stock_tracker** | **No** | URL-based hotel lookup, no permission check |
| **bookings** | **No** | AllowAny or IsAuthenticatedOrReadOnly |
| **overstay** | **No** | Only IsAuthenticated, no hotel check |

---

## 9. Communication & Realtime

### Architecture

- **Guest ↔ Staff chat:** `Conversation` (per-room) → `RoomMessage` → Pusher events on booking-scoped channels
- **Staff ↔ Staff chat:** `StaffConversation` (1:1 or group) → `StaffChatMessage` → Pusher events on conversation channels
- **Realtime delivery:** Pusher (server-side trigger, client-side subscribe)
- **Push notifications:** Firebase FCM via Admin SDK
- **Email:** Django `send_mail()` synchronously

### Pusher Channel Naming

| Domain | Channel Pattern | Private? |
|--------|----------------|----------|
| Guest booking lifecycle | `private-guest-booking.{booking_id}` | **Yes** |
| Guest chat (booking-scoped) | `private-hotel-{slug}-guest-chat-booking-{booking_id}` | **Yes** |
| Staff chat | `{slug}-conversation-{cid}-chat` | **No** |
| Staff notifications | `{slug}-staff-{sid}-notifications` | **No** |
| Room bookings (staff) | `{slug}.room-bookings` | **No** |
| Rooms (staff) | `{slug}.rooms` | **No** |
| Attendance | `{slug}.attendance` | **No** |
| Room service | `{slug}.room-service` | **No** |
| Hotel-wide | `{slug}` | **No** |

### Pusher Auth

Dual-mode `PusherAuthView` ([notifications/views.py](../notifications/views.py)):
- **Staff mode:** JWT/session auth → allowed channels include hotel-scoped + staff personal
- **Guest mode:** GuestBookingToken → restricted to `private-guest-booking.{booking_id}` only

### FCM Push Notifications

Firebase Admin SDK from `FIREBASE_SERVICE_ACCOUNT_JSON` env. Staff tokens on `Staff.fcm_token`, guest tokens on `Room.guest_fcm_token`. Sent for: guest messages, staff replies, room service orders, booking confirmations/cancellations.

### Communication Risks

| Risk | Severity | Detail |
|------|----------|--------|
| Staff chat channels unprefixed | **HIGH** | `{slug}-conversation-{cid}-chat` has no `private-` prefix — anyone with Pusher key can subscribe |
| Hotel-wide channels unprefixed | **HIGH** | `{slug}.room-bookings`, `{slug}.rooms` etc. broadcast booking/room data on public channels |
| 15+ chat endpoints use AllowAny | **CRITICAL** | No auth on message read/write/delete for guest chat; anyone with a conversation ID can interact |
| Test endpoint exposed in production | **CRITICAL** | `test_deletion_broadcast` is `AllowAny`, lets anyone trigger arbitrary Pusher events |
| Bug: `current_booking` used before defined | **CRITICAL** | `realtime_guest_chat_message_deleted()` has a `NameError` — crashes on every guest message delete |
| Channel naming inconsistency | **HIGH** | Staff notifications use both `{slug}.staff-{sid}-notifications` (dot) and `{slug}-staff-{sid}-notifications` (dash) — events split across channels |
| FCM token stored per-room, not per-booking | **MEDIUM** | Room reassignment overwrites guest FCM token; no multi-token support |
| Duplicate event broadcasting for uploads | **MEDIUM** | File uploads trigger both `NotificationManager` and manual `pusher_client.trigger()` |

---

## 10. Attendance & Roster

### Models

| Model | Purpose |
|-------|---------|
| `ClockLog` | Clock-in/out with face verification, break tracking, approval workflow |
| `StaffFace` | 128-dim face encoding + Cloudinary image, consent, active/revoked lifecycle |
| `RosterPeriod` | Named date-range container for shifts, supports finalization |
| `StaffRoster` | Individual planned shift (staff + date + start/end + department + location) |
| `StaffAvailability` | Staff availability declarations per date |
| `ShiftTemplate` | Reusable shift definitions (morning/evening/night) |
| `RosterRequirement` | Staff-per-role requirements per date |
| `ShiftLocation` | Named locations with color coding |
| `DailyPlan` / `DailyPlanEntry` | Daily operational view auto-generated from roster |
| `RosterAuditLog` | All roster mutations tracked |
| `FaceAuditLog` | Face registration/revocation lifecycle |

### Clock-In/Out Flow

Two parallel paths (legacy + enhanced):

1. Client sends 128-float face descriptor
2. Server matches against all active `StaffFace` for hotel (Euclidean distance ≤ 0.6)
3. If open `ClockLog` exists → clock out; else → check for matching `StaffRoster`
4. **Rostered:** Create `ClockLog` linked to shift
5. **Unrostered:** Return prompt → confirmation → `ClockLog(is_unrostered=True, is_approved=False)` → manager approval/rejection

### Shift Matching

`find_matching_shift_for_datetime()` checks today and yesterday (for overnight shifts). Uses `shift_to_datetime_range()` which handles cross-midnight by adding +1 day when `end < start`.

### Roster Operations

- **Bulk save** with duplicate + overlap detection
- **Copy operations:** day-to-day, period-to-period, staff-specific
- **Business rules** ([business_rules.py](../attendance/business_rules.py)): max 12h/day, 48h/week, 30min break for 6h+ shifts
- **Period finalization:** locks shifts + clock logs
- **Audit logging:** all mutations tracked in `RosterAuditLog`

### 3-Tier Progressive Alerting

1. **Break warning** at 6h → Pusher to staff + managers
2. **Overtime warning** at 10h → Pusher notification
3. **Hard limit** at 12h → Pusher with action buttons (stay/clock-out)
4. **Auto clock-out** via management command for sessions exceeding hard limit

### What Does NOT Exist

- No missed clock-out detection (only hard-limit auto-clock-out)
- No late arrival detection
- No early departure detection
- No no-show detection
- No break compliance enforcement
- No actual-vs-planned comparison in analytics
- No weekly overtime aggregation alerts (48h limit defined but never checked at runtime)

### Attendance Risks

| Risk | Severity | Detail |
|------|----------|--------|
| No actual-vs-planned analytics | **HIGH** | System tracks both but never compares them |
| Face matching is O(n) linear scan | **MEDIUM** | Degrades with scale; no spatial indexing |
| Two parallel clock-in codepaths | **MEDIUM** | Legacy and enhanced paths may drift apart |
| Duplicate analytics files | **MEDIUM** | `analytics.py` and `analytics_roster.py` both define `RosterAnalytics` with different field names |
| Break time not deducted from hours_worked | **MEDIUM** | `save()` does `time_out - time_in` without subtracting breaks |
| Period finalization doesn't prevent new clock-ins | **LOW** | New clock-ins can be created within finalized date ranges |

---

## 11. Automation & Scheduler Overview

### Infrastructure

- **Platform:** Heroku Scheduler (cron-like)
- **Worker process:** None — single web dyno only (`Procfile: web: gunicorn ...`)
- **Celery:** Not configured
- **Django Channels:** Not used (WSGI only; Pusher handles realtime)

### Management Commands

| Command | Purpose | Configured? |
|---------|---------|-------------|
| `auto_clock_out_excessive` | Force clock-out for excessive sessions | **Yes** — Heroku Scheduler every 30 min |
| `check_attendance_alerts` | Send break/overtime/hard-limit alerts | **No** |
| `auto_expire_overdue_bookings` | Expire bookings past approval deadline + refund | **No** |
| `flag_overstay_bookings` | Detect IN_HOUSE bookings past checkout | **No** |
| `send_scheduled_surveys` | Send post-checkout survey emails | **No** |
| `cleanup_survey_tokens` | Delete expired/used tokens | **No** |
| `update_tournament_statuses` | Transition tournament lifecycle states | **No** |

**Critical gap:** Only 1 of 7 operational commands is actually scheduled. The other 6 exist in code but never run automatically.

### Notification Delivery

All notifications are **synchronous and fire-and-forget**:
- Pusher events: `pusher_client.trigger()` inline in request handlers
- FCM push: Firebase Admin SDK inline
- Email: `send_mail()` inline
- **No retry, no queue, no fallback** — if the external service is slow or fails, the notification is lost and the user's request is delayed

### Seed & One-Time Commands

`seed_hotels`, `seed_killarney_public_page`, `populate_killarney_pms`, `simulate_killarney_bookings`, `seed_default_cancellation_policies`, `seed_navigation_items`, `heal_booking_integrity`, `backfill_hotel_related_objects`, various stock_tracker seeders

---

## 12. API Design Overview

### Tri-Zone Architecture

| Zone | Prefix | Auth | Purpose |
|------|--------|------|---------|
| Public | `/api/public/` | None | Hotel discovery, booking, payment |
| Staff | `/api/staff/hotel/<hotel_slug>/` | Token | Back-office management |
| Guest | `/api/guest/hotels/<hotel_slug>/` | Token/Guest token | Guest portal |
| Legacy | `/api/chat/`, `/api/room_services/`, `/api/bookings/`, `/api/hotel/`, `/api/notifications/` | Mixed | Direct routes (dual access paths) |

### URL Consistency Issues

1. **Singular vs plural hotel:** Staff uses `/hotel/`, Guest uses `/hotels/`, face-config uses `/hotels/`
2. **Legacy routes still mounted** alongside zoned routes — dual access paths for same data
3. **Naming inconsistency:** `room-bookings` vs `bookings` vs `service-bookings` for different booking types

### Error Handling

- **No custom exception handler** — DRF defaults
- **Custom 404** in [common/views.py](../common/views.py) returns JSON for `/api/` paths
- **Inconsistent error formats:**
  - `{"error": "message"}` — notifications, some chat
  - `{"detail": "message"}` — DRF default
  - `{"error": "CODE", "detail": "description"}` — Pusher auth
  - `{"status": "success"}` / `{"message": "..."}` — mixed success formats

### Pagination

- **Global default:** `PageNumberPagination` with `PAGE_SIZE=10`
- **Widely overridden:** stock_tracker (~12 ViewSets), entertainment, hotel_info, attendance disable pagination
- **Result:** Most views return unbounded datasets — potential performance issue at scale

### Authentication

- **Default:** `TokenAuthentication` + `IsAuthenticated`
- **Guest token:** Custom `GuestBookingToken.validate_token()` (not DRF auth backend)
- **Public endpoints:** `AllowAny` (by design for booking flow, hotel pages)

---

## 13. Risk Areas

### Critical Priority

| # | Area | Risk | Location |
|---|------|------|----------|
| 1 | RBAC | **Superuser escalation** — any staff can set `is_superuser=True` on new users | `staff/views.py` |
| 2 | Multi-tenant | **Cross-hotel data leakage** — maintenance, entertainment, stock_tracker, navigation items return unscoped `objects.all()` | Multiple apps |
| 3 | Realtime | **Test endpoint in production** — `test_deletion_broadcast` is AllowAny, triggers arbitrary Pusher events | `chat/views.py` |
| 4 | Realtime | **15+ chat endpoints fully unprotected** — no auth on message CRUD | `chat/views.py` |
| 5 | RBAC | **Financial reports fully open** — `AllowAny` on stock value/sales reports | `stock_tracker/report_views.py` |
| 6 | Scheduling | **6 of 7 operational commands not scheduled** — bookings won't expire, overstays undetected, alerts won't fire | Heroku config |

### High Priority

| # | Area | Risk | Location |
|---|------|------|----------|
| 7 | Booking | **No availability re-check at creation** — race condition for last room | `hotel/services/booking.py` |
| 8 | Booking | **Extension updates dates before payment** — failed payment leaves extended dates | `room_bookings/services/overstay.py` |
| 9 | Realtime | **Staff channels not private** — booking data, room status broadcast on public Pusher channels | Notification manager |
| 10 | RBAC | **No access level check on staff creation** — regular_staff can create super_staff_admin | `staff/views.py` |
| 11 | Pre-check-in | **PII in logs** — print() dumps names, emails, ID docs to stdout | `hotel/public_views.py` |
| 12 | Pre-check-in | **Guest-scoped required fields not validated** | `hotel/public_views.py` |
| 13 | Realtime | **NameError bug** — `current_booking` used before defined in message deletion | `notifications/notification_manager.py` |
| 14 | Notifications | **All notifications synchronous** — no queue, no retry, adds latency | Across all views |
| 15 | RBAC | **Overstay views only check IsAuthenticated** — no hotel scoping | `hotel/overstay_views.py` |

### Medium Priority

| # | Area | Risk | Location |
|---|------|------|----------|
| 16 | Multi-tenant | **Header-based scoping** in guests app — client-controlled `x-hotel-slug` | `guests/views.py` |
| 17 | Booking | **Dual booking ID generators** with different formats | `hotel/models.py` vs `hotel/services/booking.py` |
| 18 | Token | **Scope mismatch** — `VIEW_STATUS` vs `STATUS_READ` after payment | `hotel/payment_views.py` |
| 19 | Attendance | **Two parallel clock-in codepaths** — may drift apart | `attendance/views.py`, `face_views.py` |
| 20 | Attendance | **Break time not deducted** from `hours_worked` | `attendance/models.py` |

---

## 14. Top 5 Backend Weaknesses

### 1. Inconsistent Multi-Tenant Isolation
The codebase has an excellent `HotelScopedViewSetMixin` pattern in `common/mixins.py`, but it's only used by 2 of ~15 apps. Multiple apps (maintenance, entertainment, stock_tracker, parts of staff) serve completely unscoped `objects.all()` querysets, enabling cross-hotel data leakage for any authenticated user. The `guests` app trusts an HTTP header (`x-hotel-slug`) that any client can forge.

### 2. RBAC Has Privilege Escalation Paths
Staff registration allows `is_superuser` override from request body. No access level restriction on staff creation means `regular_staff` can create `super_staff_admin` users. Combined, these allow full privilege escalation. Additionally, 30+ endpoints use `AllowAny` including mutation-capable room service and stock tracker views.

### 3. No Background Worker / Broken Scheduling
Only 1 of 7 operational management commands is configured to run. Without scheduling, bookings won't auto-expire, overstays won't be detected, attendance alerts won't fire, and survey emails won't send. All notifications are sent synchronously in request handlers — if Pusher/FCM/email is slow, every user request is delayed.

### 4. Realtime Channel Security
Most Pusher channels lack the `private-` prefix, meaning anyone with the Pusher app key (exposed to all frontend clients) can subscribe to staff chat conversations, booking updates, room status, and attendance events for any hotel. The channel naming also has dot vs dash inconsistencies causing split event delivery.

### 5. No Notification Persistence
There is no `Notification` model — no inbox, no read/unread tracking, no notification history, no audit trail. All notifications are fire-and-forget. If a Pusher/FCM call fails, the notification is permanently lost with no retry mechanism.

---

## 15. Top 5 Backend Strengths

### 1. Token Security Design
The guest token system is exceptionally well-designed. 256-bit entropy via `secrets.token_urlsafe(32)`, SHA-256 hash-only storage (raw token never persisted), atomic token rotation with revocation, scope-based access control, and anti-enumeration (identical 404 responses for all invalid states). Config snapshots on precheckin/survey tokens prevent TOCTOU issues.

### 2. Comprehensive Booking Lifecycle
The booking system covers the full lifecycle from availability check through payment, approval, check-in, overstay detection, and checkout. Stripe integration includes idempotent webhook processing (`StripeWebhookEvent` model), manual-capture support, and proper refund handling. Multi-tier cancellation policies (flexible, moderate, non-refundable, custom with time-based tiers) provide real-world flexibility.

### 3. Room Assignment Concurrency Safety
`RoomAssignmentService` uses `select_for_update()` on booking, room, AND potentially conflicting bookings simultaneously. The `assignment_version` field enables optimistic concurrency control. The 7-state room turnover machine with enforced transitions prevents invalid state changes.

### 4. Robust Roster & Attendance System
Full roster management with bulk save, copy operations, business rule validation (12h/day max, 48h/week, 30min break enforcement), period finalization with audit logging, and 3-tier progressive alerting (break → overtime → hard limit). Face recognition with consent tracking, audit trail, and proper encoding storage.

### 5. Structured Domain Separation
The codebase is well-organized into domain-specific Django apps with clear responsibilities. The `hotel` app serves as the central tenant with configuration models (AccessConfig, PrecheckinConfig, SurveyConfig, AttendanceSettings) as proper 1:1 relations. Services are extracted into dedicated modules (`hotel/services/`, `room_bookings/services/`). The tri-zone URL architecture (public/staff/guest) creates clear API boundaries.

---

*End of audit. All findings reference actual code in the HotelMateBackend repository. Items marked with severity levels are prioritized for remediation.*
