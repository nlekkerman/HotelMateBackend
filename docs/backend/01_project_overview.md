# 01 — Project Overview

> Auto-generated from codebase audit. Every claim references a source file.

---

## 1. What Is HotelMate?

HotelMate is a **multi-tenant hotel management platform** built with Django 5.2 and Django REST Framework 3.16. It provides a unified backend for:

- **Front desk operations** — bookings, check-in/out, room assignment, guest management
- **Housekeeping** — room status tracking, task management, inspection workflow
- **Food & beverage** — room service orders, restaurant bookings, menu management
- **Inventory** — full stock tracking with stocktakes, sales, voice-controlled commands
- **Staff management** — attendance, rosters, clock-in (including facial recognition), departments, roles
- **Guest engagement** — entertainment (quizzes, memory match, tournaments), chat, social feed, surveys
- **Maintenance** — request tracking with priorities and photo attachments
- **Communications** — push notifications (FCM), realtime events (Pusher), email, staff chat

The backend serves a **separate React/mobile frontend** via a REST API.

**Source:** `README.md`

---

## 2. Technology Stack

| Layer | Technology | Version | Source |
|-------|-----------|---------|--------|
| **Framework** | Django | 5.2.4 | `requirements.txt` |
| **API** | Django REST Framework | 3.16.0 | `requirements.txt` |
| **Database** | PostgreSQL | (Heroku addon) | `HotelMateBackend/settings.py` |
| **Realtime** | Pusher | 3.3.3 | `requirements.txt` |
| **Push notifications** | Firebase Admin (FCM) | 6.5.0 | `requirements.txt` |
| **Payments** | Stripe | 11.2.0 | `requirements.txt` |
| **Media storage** | Cloudinary | 1.44.0 | `requirements.txt` |
| **Voice recognition** | OpenAI (Whisper) | 2.8.1 | `requirements.txt` |
| **PDF generation** | ReportLab | 4.4.3 | `requirements.txt` |
| **Excel export** | OpenPyXL | 3.1.5 | `requirements.txt` |
| **Face recognition** | face-recognition + NumPy | — | `requirements.txt` |
| **Fuzzy matching** | RapidFuzz | 3.14.3 | `requirements.txt` |
| **QR codes** | qrcode | 8.2 | `requirements.txt` |
| **Task scheduling** | Heroku Scheduler | — | `setup_heroku_scheduler.sh` |
| **Static files** | WhiteNoise | 6.9.0 | `requirements.txt` |
| **WSGI server** | Gunicorn | 23.0.0 | `Procfile` |
| **Caching** | Django DatabaseCache | — | `HotelMateBackend/settings.py` |
| **Env config** | django-environ | 0.12.0 | `requirements.txt` |

---

## 3. Repository Layout

```
HotelMateBackend/                 ← Project root
├── HotelMateBackend/             ← Django project package
│   ├── settings.py               ← All configuration (363 lines)
│   ├── urls.py                   ← Root URL dispatcher
│   ├── wsgi.py                   ← WSGI entry point (used in prod)
│   └── asgi.py                   ← ASGI entry point (not used in prod)
│
├── staff_urls.py                 ← ⚠️ Source missing, only .pyc cached
├── guest_urls.py                 ← Guest-zone URL routing (580 lines)
├── public_urls.py                ← Public-zone URL routing (131 lines)
│
├── apps/
│   └── booking/                  ← Booking services (deadlines, stay rules)
│
├── rooms/                        ← Room models, types, rates, promotions
├── guests/                       ← Guest profiles
├── staff/                        ← Staff, departments, roles, permissions
├── hotel/                        ← Core: Hotel, RoomBooking, payments, CMS, views
├── housekeeping/                 ← Room status services, tasks, permissions
├── room_services/                ← Menus, orders, kitchen/porter workflow
├── bookings/                     ← Restaurant bookings, table management
├── stock_tracker/                ← Inventory: items, stocktakes, sales, reports
├── attendance/                   ← Clock-in/out, rosters, face recognition, analytics
├── entertainment/                ← Quizzes, memory match, tournaments
├── chat/                         ← Guest ↔ staff chat
├── staff_chat/                   ← Staff ↔ staff chat
├── notifications/                ← FCM, Pusher hub, email delivery
├── maintenance/                  ← Maintenance requests
├── hotel_info/                   ← Hotel info pages, QR codes
├── home/                         ← Homepage/dashboard endpoints
├── common/                       ← Shared mixins, utilities, theme
├── voice_recognition/            ← Whisper-based voice commands
├── room_bookings/                ← Service layer (not in INSTALLED_APPS)
│
├── templates/emails/             ← Email templates (1 file)
├── static/                       ← Static assets
├── staticfiles/                  ← Collected static files (WhiteNoise)
├── scripts/                      ← Utility scripts & archive
├── tests/                        ← Project-level test suite
├── docs/                         ← Documentation (this suite)
│
├── manage.py                     ← Django CLI entry point
├── Procfile                      ← Heroku process definition
├── requirements.txt              ← Python dependencies (100+ packages)
├── setup_heroku_scheduler.sh     ← Scheduler setup script
└── .gitignore                    ← 185 lines
```

---

## 4. App Registry

**Source:** `HotelMateBackend/settings.py` — `INSTALLED_APPS`

### 4.1 Custom Apps (19)

| App | Primary Concern | Approximate Size |
|-----|----------------|-----------------|
| `hotel` | Core booking, payments, CMS, hotel config | models: 3042 lines, staff_views: 3475 lines |
| `stock_tracker` | Inventory management system | models: 2633 lines, views: 4374 lines |
| `entertainment` | Guest games, quizzes, tournaments | models: 1499 lines |
| `notifications` | Pusher + FCM + email delivery hub | notification_manager: 2417 lines |
| `attendance` | Staff clock-in/out, rosters, face recognition | 15 files, analytics suite |
| `rooms` | Room models, types, rates, daily pricing | State machine with 7 statuses |
| `staff` | Staff profiles, departments, roles, permissions | Canonical permission system |
| `housekeeping` | Room cleaning workflow, tasks | Service layer + RBAC |
| `room_services` | Menu items, guest orders, kitchen workflow | Order state machine |
| `bookings` | Restaurant reservations, tables, floor plans | Pusher-integrated |
| `chat` | Guest ↔ staff messaging | Pusher realtime |
| `staff_chat` | Staff ↔ staff messaging | Department-based channels |
| `guests` | Guest profiles | Lightweight model |
| `maintenance` | Maintenance request tracking | Priority-based workflow |
| `hotel_info` | Hotel info pages, QR codes | Public-facing content |
| `home` | Dashboard/homepage data | Minimal |
| `common` | Shared utilities, mixins, theme | Cross-app helpers |
| `voice_recognition` | Whisper voice-to-stock commands | OpenAI integration |
| `room_bookings` | Service layer (checkout, room moves, overstay) | **Not in INSTALLED_APPS** |

### 4.2 Third-Party Apps

| App | Purpose |
|-----|---------|
| `rest_framework` | Django REST Framework |
| `rest_framework.authtoken` | Token authentication |
| `corsheaders` | CORS header management |
| `django_filters` | Queryset filtering for API |
| `django_extensions` | Management command extras |
| `cloudinary_storage` / `cloudinary` | Media file storage |
| `channels` | ASGI/WebSocket support (configured but unused in prod) |
| `dal` / `dal_select2` | Admin autocomplete widgets |

---

## 5. Key Metrics

| Metric | Value |
|--------|-------|
| Custom Django apps | 19 |
| Serializer classes | ~140+ |
| Management commands | 33 |
| API endpoints | ~200+ |
| Model classes | ~80+ |
| Database migrations | Multiple per app |
| Test files | 42 (`tests.py` + `test_*.py`) |
| Lines in largest model file | 3,042 (`hotel/models.py`) |
| Lines in largest view file | 4,374 (`stock_tracker/views.py`) |

---

## 6. Documentation Map

This documentation suite consists of 23 files organized in two tiers:

### Tier 1 — Orientation (01–09)

| # | File | Purpose |
|---|------|---------|
| 01 | `01_project_overview.md` | What the project is, tech stack, repo layout ← *you are here* |
| 02 | `02_quick_start.md` | Local setup, running the server, running tests |
| 03 | `03_architecture.md` | High-level system architecture, layers, zones |
| 04 | `04_data_model_overview.md` | Core entities and relationships (conceptual ERD) |
| 05 | `05_api_conventions.md` | URL patterns, pagination, filtering, error formats |
| 06 | `06_auth_overview.md` | Authentication flows for staff, guest, and public |
| 07 | `07_realtime_events.md` | Pusher architecture, channel naming, event catalog |
| 08 | `08_testing.md` | Test framework, patterns, coverage, how to run |
| 09 | `09_glossary_and_conventions.md` | Domain terms, code conventions, naming rules |

### Tier 2 — Deep Dive (10–23)

| # | File | Purpose |
|---|------|---------|
| 10 | `10_backend_overview.md` | Detailed backend architecture |
| 11 | `11_domain_map.md` | All 19 apps with ownership and dependencies |
| 12 | `12_models_and_relationships.md` | Every model, every field, every FK |
| 13 | `13_state_machines.md` | Booking, room, order, task state diagrams |
| 14 | `14_services_and_business_rules.md` | Service layer, canonical functions, validation |
| 15 | `15_auth_tokens_and_scopes.md` | Token types, permission classes, scopes |
| 16 | `16_api_reference.md` | Complete endpoint inventory |
| 17 | `17_serializers_and_validation.md` | All serializers, validation rules |
| 18 | `18_background_jobs_and_schedulers.md` | Management commands, scheduler, signals |
| 19 | `19_configuration_env.md` | Environment variables, settings breakdown |
| 20 | `20_integrations.md` | Stripe, Pusher, Firebase, Cloudinary, etc. |
| 21 | `21_observability_logging.md` | Logging config, audit trails, gaps |
| 22 | `22_failure_modes_edge_cases.md` | Known issues, security risks, edge cases |
| 23 | `23_deployment_runbook.md` | Heroku deployment, env setup, troubleshooting |
