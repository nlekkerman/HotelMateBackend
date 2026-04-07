# HotelMate Backend

Multi-tenant Django REST API powering hotel operations, guest services, and staff workflows across independently scoped hotel properties.

## Overview

This backend serves as the central API layer for the HotelMate platform. It manages the full lifecycle of hotel operations — from public room booking and payment processing through guest check-in, in-house services, and post-stay surveys. Every request is scoped to a specific hotel via URL slug, and the API is segmented into three access zones: **staff** (authenticated hotel employees), **guest** (token-authenticated in-house guests), and **public** (unauthenticated visitors and booking flows).

The system is designed to support multiple independent hotel properties from a single deployment. Each hotel has its own configuration, staff, rooms, bookings, and operational data, isolated through foreign key scoping on all domain models.

## Core Responsibilities

- Manage the full room booking lifecycle: availability, pricing, creation, payment, approval, check-in, room assignment, check-out, and cancellation
- Provide a scoped guest portal with token-based access for in-house guests to use chat, room service, and pre-check-in
- Support staff operations across housekeeping, maintenance, attendance, restaurant bookings, stock tracking, and internal chat
- Deliver realtime event notifications to staff and guest clients via Pusher channels and Firebase Cloud Messaging
- Process payments through Stripe with webhook verification and idempotency enforcement
- Handle hotel provisioning with automatic creation of all required configuration objects
- Generate PDF reports, QR codes, and booking confirmation emails

## Architecture Concepts

### Hotel-Scoped Tenant Isolation

All domain models carry a `hotel` foreign key. Staff profiles are bound to a single hotel. URL routing enforces hotel context via `<hotel_slug>` path parameters. Pusher channels and notification targeting are prefixed by hotel slug. There is no cross-hotel data access in normal operation.

### Three API Zones

| Zone | Path Prefix | Auth Method | Purpose |
|------|-------------|-------------|---------|
| Staff | `/api/staff/hotels/<hotel_slug>/` | DRF Token (`Authorization: Token`) | Hotel employee operations |
| Guest | `/api/guest/hotels/<hotel_slug>/` | Guest token (query param or `Authorization: GuestToken`) | In-house guest services |
| Public | `/api/public/` | None | Hotel directory, booking, payment |

### Dual-Token Guest Authentication

Guests authenticate using one of two SHA-256 hashed tokens resolved through `common.guest_access.resolve_guest_access()`:

- **GuestBookingToken** — Primary identity token, stable for the booking lifecycle. Used for guest portal access and mutations.
- **BookingManagementToken** — Fallback token embedded in email links. Read-only; rejected for state-changing operations.

Typed exceptions (`TokenRequiredError`, `InvalidTokenError`, `NotInHouseError`, `NoRoomAssignedError`) enforce access boundaries with appropriate HTTP status codes.

### Guest Chat Session Grants

Guest chat uses a separate signed credential: an HMAC-SHA256 token with a 4-hour TTL, issued per booking and transported via the `X-Guest-Chat-Session` header. This isolates chat auth from the broader guest token system.

### Role-Based Access and Navigation Permissions

Staff access is governed by `HasNavPermission`, which checks the staff member's `allowed_navigation_items` (M2M) against the requested resource. Staff chat enforces granular permissions: `IsStaffMember`, `IsConversationParticipant`, `IsMessageSender`, `IsSameHotel`, and `CanManageConversation`. Superusers bypass navigation restrictions.

### Booking Lifecycle State Machine

Room bookings follow a defined state flow:

```
PENDING_PAYMENT → PENDING_APPROVAL → CONFIRMED → IN_HOUSE → COMPLETED
                                   ↘ DECLINED
                 ↘ CANCELLED_DRAFT (expired unpaid)
CANCELLED (guest/staff initiated)
EXPIRED (timeout)
NO_SHOW
```

State transitions are handled through dedicated service modules in `hotel/services/` with integrity checks and notification side effects.

### Event-Driven Realtime

Realtime is implemented through **Pusher** (live in-app events) and **Firebase Cloud Messaging** (push notifications when the app is backgrounded). A unified `NotificationManager` dispatches both. Events follow a normalized envelope:

```json
{
  "category": "attendance|staff_chat|guest_chat|room_service|booking",
  "type": "event_type_name",
  "payload": {},
  "meta": { "hotel_slug": "...", "event_id": "uuid", "ts": "ISO-8601" }
}
```

Pusher channels are hotel-scoped strings (e.g., `{hotelSlug}.room-bookings`, `private-hotel-{slug}-guest-chat-booking-{id}`). Signal handlers use `transaction.on_commit()` to defer event dispatch until the database transaction succeeds.

> **Note:** Django Channels and Daphne are installed but realtime delivery to clients is Pusher-based. There are no WebSocket consumer classes in the codebase.

### Idempotent Hotel Provisioning

A `post_save` signal on `Hotel` automatically creates all required one-to-one configuration objects: `HotelAccessConfig`, `HotelPublicPage`, `BookingOptions`, `AttendanceSettings`, `ThemePreference`, `HotelPrecheckinConfig`, and `HotelSurveyConfig`. This runs idempotently on every save.

### Service Layer

Business logic is separated from views into service modules. Key service areas:

- `hotel/services/` — availability, booking creation, pricing, cancellation, guest tokens, booking state management, integrity checks, survey analytics
- `room_bookings/services/` — room assignment, room moves, checkout processing, overstay detection
- `housekeeping/services.py` — room turnover workflows
- `staff/services.py` — staff creation, navigation permissions
- `notifications/` — notification dispatch, FCM delivery, Pusher channel logic, email delivery

### Rate Limiting

Public and guest endpoints are throttled:

| Scope | Burst | Sustained |
|-------|-------|-----------|
| Public | 30/min | 200/hour |
| Guest | 60/min | 600/hour |

### Payment Idempotency

Payment operations use a database-backed cache keyed on the `Idempotency-Key` request header, with a 30-minute TTL and 10,000 max entries, preventing duplicate charge processing.

## Main Domain Areas

### Public Booking Portal
Hotel directory listing with filters, room availability checks, pricing quotes, booking creation, Stripe payment sessions, payment verification, webhook handling, and guest-initiated cancellation.

### Room Booking Management (Staff)
Booking list/detail views, approval/decline, room assignment and reassignment, room moves, guest check-in and check-out, overstay acknowledgment and extension, pre-check-in link distribution, and post-stay survey link dispatch.

### Guest Portal
Bootstrap context endpoint providing the guest's booking, room, and hotel data. In-room service ordering (menu browsing, order placement). Guest-to-staff chat with Pusher-authenticated realtime messaging and read receipts.

### Rooms
Room and room type CRUD. Room status tracking tied to housekeeping events.

### Housekeeping
Immutable `RoomStatusEvent` audit trail for room state changes. Task assignment and tracking via `HousekeepingTask`.

### Maintenance
Ticket lifecycle (open → in_progress → resolved → closed) with comments and Cloudinary-hosted photo attachments.

### Staff Management
Staff profiles linked to users via OneToOne. Department and role assignment. Navigation permission control. Face recognition data storage (128-dimensional encodings) for attendance verification.

### Attendance & Roster
Clock in/out logging, shift definitions, roster periods, daily plans, and staff-to-shift assignment. Scheduled commands for break/overtime alerts and auto clock-out enforcement. PDF report generation via ReportLab.

### Staff Chat
1-on-1 and group conversations with message delivery status (pending/delivered/read), read-by tracking, reply threading, emoji reactions, file attachments (Cloudinary), soft-delete, and realtime unread count updates.

### Guest Chat
Guest-to-staff conversations scoped by booking. Messages typed as guest, staff, or system. Read tracking. Pusher channel auth validates guest tokens and restricts channel access to the guest's own booking.

### Restaurant Bookings
Separate from room bookings. Restaurant entities with booking categories and subcategories. Time-slotted reservation management.

### Room Services
Menu items with category, pricing, and availability. Guest-facing order placement with quantity and notes. Breakfast items and orders as a separate flow. Signal-driven porter and kitchen notifications on order creation.

### Stock & Inventory
Stock items with categories (cocktails, mixers, juices, syrups, others). Periodic stocktake workflows with snapshots. Cocktail recipes with linked ingredients and quantity tracking.

### Voice Commands
Voice-to-text pipeline for stock management: audio upload → OpenAI Whisper transcription → LLM-based command parsing → RapidFuzz fuzzy matching against inventory items. Staff confirm parsed commands before execution.

### Entertainment
Global game registry with per-hotel high scores and QR code access.

### Hotel Info & QR
Categorized hotel information items with auto-generated QR codes per category per hotel.

### Staff Social Feed
Internal post feed with likes, comments, and comment replies. Scoped per hotel.

### Surveys
Configurable post-stay surveys with three delivery modes: auto-immediate, auto-delayed, or manual. Token-based guest survey access with configurable expiry. Response storage with overall rating for analytics.

### Pre-Check-In
Guest-submitted pre-check-in data with hotel-configurable field visibility rules. Staff-triggered distribution via token link.

### Theming
Per-hotel color theme configuration (main, secondary, button colors and variants).

### Email Notifications
Transactional emails for booking received, booking confirmed, and booking cancelled. Sent via SMTP (Gmail TLS).

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Django 5.2, Django REST Framework 3.16 |
| Database | PostgreSQL (via `dj-database-url`, 10-min connection pooling) |
| Realtime Events | Pusher (in-app), Firebase Cloud Messaging (push) |
| Payments | Stripe (sessions, verification, webhooks) |
| Media Storage | Cloudinary (conditional; falls back to local) |
| Voice Transcription | OpenAI Whisper API |
| Fuzzy Matching | RapidFuzz |
| PDF Generation | ReportLab |
| QR Codes | `qrcode` library |
| Static Files | WhiteNoise (compressed manifest) |
| Caching | Database-backed cache (payment idempotency) |
| Channel Layer | Redis (production) / In-memory (development) |
| CORS | django-cors-headers |
| Environment Config | django-environ (`.env` file) |
| WSGI Server | Gunicorn |
| Deployment | Heroku (Procfile, Heroku Scheduler for cron jobs) |
| Data Analysis | Pandas, NumPy (analytics modules) |

## Scheduled Commands

These management commands are designed for periodic execution via Heroku Scheduler:

| Command | Interval | Purpose |
|---------|----------|---------|
| `check_attendance_alerts` | Every 5–10 min | Detect break and overtime violations, send alerts |
| `auto_clock_out_excessive` | Every 30 min | Force clock-out for sessions exceeding hard limit |

## Local Development

```bash
# Clone and set up virtualenv
git clone <repository-url>
cd HotelMateBackend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\Activate.ps1 on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Edit with your local values
# Required: SECRET_KEY, DATABASE_URL
# Required for realtime: PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET, PUSHER_CLUSTER
# Optional: STRIPE_SECRET_KEY, OPENAI_API_KEY, CLOUDINARY_URL, REDIS_URL

# Run migrations
python manage.py migrate

# Seed navigation items (per hotel)
python manage.py seed_navigation_items

# Start development server
python manage.py runserver
```

The test suite uses an in-memory SQLite database (auto-configured in settings when running tests):

```bash
python manage.py test
```

## Project Structure

```
HotelMateBackend/          # Django project settings, root URL config, WSGI/ASGI
├── hotel/                 # Core: hotel config, room bookings, pricing, surveys, precheckin
│   └── services/          # Availability, booking, cancellation, pricing, tokens
├── rooms/                 # Physical rooms and room types
├── room_bookings/         # Room assignment, checkout, overstay services
│   └── services/
├── guests/                # In-house guest records
├── staff/                 # Staff profiles, departments, roles, navigation perms
├── chat/                  # Guest-to-staff chat
├── staff_chat/            # Staff-to-staff chat with reactions and attachments
├── bookings/              # Restaurant reservations
├── room_services/         # In-room ordering (food, breakfast)
├── housekeeping/          # Room status events and tasks
├── maintenance/           # Maintenance tickets with photos
├── attendance/            # Clock logs, shifts, rosters, face recognition
├── stock_tracker/         # Inventory, stocktakes, cocktail recipes
├── entertainment/         # Games and high scores
├── hotel_info/            # Hotel info categories and QR codes
├── home/                  # Staff social feed
├── common/                # Guest auth, chat grants, theming, shared utilities
├── notifications/         # NotificationManager, Pusher, FCM, email service
├── voice_recognition/     # Whisper transcription, command parsing, fuzzy matching
├── staff_urls.py          # Staff zone URL routing
├── guest_urls.py          # Guest zone URL routing
├── public_urls.py         # Public zone URL routing
└── requirements.txt
```

## Notes

This backend is a system-oriented implementation covering the operational surface of a hotel property management platform. It favors explicit service layers over fat views, hotel-scoped data isolation over shared-nothing multi-tenancy, and event-driven realtime over polling. Authentication is segmented by actor type (staff, guest, public) with distinct token schemes and permission boundaries for each. The codebase does not use Celery or background task queues — scheduled work runs via Heroku Scheduler management commands, and notification side effects are deferred to post-transaction commit hooks.
