# Backend Overview

> Generated: 2026-02-19 — Evidence-based audit of the HotelMateBackend repository.

## Framework & Stack

| Layer | Technology | Evidence |
|-------|-----------|----------|
| Framework | Django 5.2.4 + Django REST Framework 3.16.0 | `requirements.txt`, `HotelMateBackend/settings.py` |
| Database | PostgreSQL (via `dj-database-url`, `psycopg2-binary`) | `settings.py` line ~132 |
| Realtime (WebSocket) | Pusher (`pusher==3.3.3`) | `settings.py` lines 152-155; `notifications/notification_manager.py` |
| Realtime (Channels) | Django Channels 4.2.2 + channels_redis | `settings.py` CHANNEL_LAYERS; `requirements.txt` |
| Push Notifications | Firebase Cloud Messaging (`firebase-admin==6.5.0`) | `notifications/fcm_service.py` |
| Payments | Stripe (`stripe==11.2.0`) | `hotel/payment_views.py` |
| File Storage | Cloudinary (`cloudinary==1.44.0`, `django-cloudinary-storage`) | `settings.py` CLOUDINARY_URL |
| Voice/AI | OpenAI Whisper (`openai==2.8.1`) | `voice_recognition/speech_transcriber.py` |
| Face Recognition | Custom Euclidean matching on 128-dim descriptors | `attendance/face_views.py` |
| WSGI Server | Gunicorn | `Procfile` |
| Static Files | WhiteNoise | `settings.py` STATICFILES_STORAGE |
| Hosting | Heroku | `Procfile`, `setup_heroku_scheduler.sh` |
| Cache | Database-backed (`payment_cache_table`) | `settings.py` CACHES |
| PDF/Excel | ReportLab, openpyxl | `requirements.txt` |
| Fuzzy Matching | RapidFuzz | `voice_recognition/fuzzy_matcher.py` |

## Repository Structure

```
HotelMateBackend/
├── HotelMateBackend/          # Django project config (settings, urls, wsgi, asgi)
├── hotel/                     # Core domain: hotels, room bookings, payments, public pages
├── rooms/                     # Room inventory, room types, rate plans, turnover workflow
├── guests/                    # Guest records (walk-in and booking-linked)
├── staff/                     # Staff profiles, auth, registration, navigation permissions
├── bookings/                  # Restaurant/dining bookings and floor plans
├── room_bookings/             # Room booking lifecycle services (assignment, checkout, overstay)
├── housekeeping/              # Room status state machine, tasks, audit trail
├── chat/                      # Guest ↔ staff chat (per-room conversations)
├── staff_chat/                # Staff ↔ staff messaging (group, 1:1)
├── notifications/             # Unified notification hub (Pusher + FCM + email)
├── attendance/                # Clock-in/out, rosters, face recognition, analytics
├── entertainment/             # Guest games (memory match, quiz, tournaments)
├── room_services/             # In-room dining orders (room service + breakfast)
├── maintenance/               # Maintenance request tracking
├── stock_tracker/             # Bar/restaurant inventory (2600+ line models)
├── hotel_info/                # Hotel information pages with QR codes
├── home/                      # Staff noticeboard / social feed
├── common/                    # Shared mixins, theme, cloudinary utilities
├── voice_recognition/         # Voice-to-stock-command pipeline (Whisper → parser → matcher)
├── apps/booking/services/     # Booking deadline & stay-time business rule engines
├── scripts/                   # One-time migration/debug scripts
├── tools/                     # Debug utilities
├── issues/                    # GitHub issue creation scripts
├── templates/                 # Django templates (admin, emails)
├── static/ & staticfiles/     # Static file directories
├── guest_urls.py              # Guest zone URL routing wrapper
├── public_urls.py             # Public zone URL routing wrapper
├── manage.py                  # Django management entry point
└── requirements.txt           # Python dependencies (93 packages)
```

## Three API Zones

The API is split into three routing zones defined in `HotelMateBackend/urls.py`:

| Zone | URL Prefix | Auth | Router File |
|------|-----------|------|-------------|
| **Staff** | `/api/staff/` | DRF TokenAuth + `IsStaffOfHotel` | `staff_urls.py` (⚠️ source deleted, .pyc cached) |
| **Guest** | `/api/guest/` | GuestBookingToken (custom) | `guest_urls.py` |
| **Public** | `/api/public/` | `AllowAny` | `public_urls.py` |

Legacy direct mounts also exist: `/api/hotel/`, `/api/chat/`, `/api/room_services/`, `/api/bookings/`, `/api/notifications/`.

## Multi-Tenancy Model

Every domain model has a FK to `hotel.Hotel`. Scoping is enforced at three levels:

1. **Middleware** — `SubdomainMiddleware` (`hotel/middleware.py`) resolves `hotel_slug` from request subdomain → sets `request.hotel`.
2. **URL path** — `<hotel_slug>` captured in URL kwargs, validated by permission classes.
3. **Guest tokens** — `GuestBookingToken` embeds hotel FK; no URL-level hotel needed.

## Installed Django Apps

From `settings.py` INSTALLED_APPS:

| App | Type |
|-----|------|
| `rooms` | Custom |
| `guests` | Custom |
| `staff` | Custom |
| `housekeeping` | Custom |
| `room_services` | Custom |
| `hotel` | Custom |
| `bookings` | Custom |
| `common` | Custom |
| `notifications` | Custom |
| `hotel_info` | Custom |
| `stock_tracker` | Custom |
| `maintenance` | Custom |
| `home` | Custom |
| `attendance` | Custom |
| `chat` | Custom |
| `entertainment` | Custom |
| `staff_chat` | Custom |
| `voice_recognition` | Custom |
| `channels` | Third-party |
| `rest_framework` | Third-party |
| `rest_framework.authtoken` | Third-party |
| `corsheaders` | Third-party |
| `django_filters` | Third-party |
| `django_extensions` | Third-party |
| `dal` / `dal_select2` | Third-party (autocomplete) |
| `cloudinary_storage` / `cloudinary` | Third-party |

## Key Design Decisions

1. **No Celery** — Background tasks run via Heroku Scheduler invoking Django management commands.
2. **No custom User model** — Uses `django.contrib.auth.User` with `Staff` as a profile model (`OneToOneField`).
3. **Centralized notifications** — All realtime + push routed through `notifications/notification_manager.py` (2417 lines).
4. **Canonical room status** — All room status changes go through `housekeeping/services.py:set_room_status()`.
5. **Token-scoped guest access** — Guests receive hashed tokens with JSON capability scopes (`STATUS_READ`, `CHAT`, `ROOM_SERVICE`).

## Known Issues Found During Audit

| Issue | Location | Impact |
|-------|----------|--------|
| `staff_urls.py` source file deleted; only .pyc bytecode remains | Project root | Risk: bytecode invalidation breaks all `/api/staff/` routes |
| `DEBUG = True` hardcoded | `settings.py` line 31 | Production security risk |
| 5 scheduled commands missing from Heroku Scheduler | `setup_heroku_scheduler.sh` | Bookings don't auto-expire; overstays undetected; surveys unsent |
| `AddGuestToRoomView` has no permission class | `rooms/views.py` | Open endpoint (DRF global default may apply) |
| Double hotel_slug in some staff URLs | `staff_urls.py` STAFF_APPS loop | URLs like `/api/staff/hotel/x/stock_tracker/x/...` |
