# PHASE 0 — Backend Repository Inventory

## Directories Inspected

### Core Django Project Structure
- `HotelMateBackend/` - Main Django project configuration
- `manage.py` - Django management script
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku deployment configuration

### Django Applications
Inspected all Django apps from `INSTALLED_APPS` in `HotelMateBackend/settings.py`:

**Core Business Logic Apps:**
- `hotel/` - Hotel configuration, policies, payment processing, booking lifecycle
- `bookings/` - Restaurant booking management system
- `rooms/` - Room and room type management
- `guests/` - Guest management and profiles
- `staff/` - Staff management and permissions
- `housekeeping/` - Room cleaning and status management
- `room_services/` - In-room service ordering
- `hotel_info/` - Hotel information and public pages
- `stock_tracker/` - Inventory and bar management
- `maintenance/` - Property maintenance tracking
- `notifications/` - Real-time messaging via Pusher
- `chat/` - Guest-staff messaging system
- `entertainment/` - Hotel entertainment features
- `staff_chat/` - Internal staff communications
- `voice_recognition/` - Voice-based inventory management
- `attendance/` - Staff attendance tracking
- `home/` - Landing/dashboard functionality
- `common/` - Shared utilities and base classes

**Support Directories:**
- `scripts/` - Utility scripts
- `templates/` - Django templates
- `static/` - Static assets
- `docs/` - Documentation (newly created)
- `venv/` - Python virtual environment
- `__pycache__/` - Python bytecode cache

## Framework Identification

**Framework:** Django 5.2.4 with Django REST Framework 3.16.0
- Evidence: `manage.py` contains Django management commands
- `HotelMateBackend/settings.py` contains Django configuration
- `HotelMateBackend/urls.py` contains URL routing
- `HotelMateBackend/wsgi.py` exists for WSGI deployment

**Architecture:** Django REST API with multi-tenant hotel management
- Uses Django REST Framework for API endpoints
- Token-based authentication via `rest_framework.authtoken`
- Multi-tenant architecture with hotel slug routing

## Installed Apps from Settings

From `HotelMateBackend/settings.py` lines 44-75:

**Django Core:**
```python
'django.contrib.admin',
'django.contrib.auth',
'django.contrib.contenttypes',
'django.contrib.sessions',
'django.contrib.messages',
'django.contrib.staticfiles',
```

**Third-party packages:**
```python
'django_filters',        # API filtering
'django_extensions',     # Django utilities
'rest_framework',        # REST API framework
'rest_framework.authtoken',  # Token auth
'corsheaders',          # CORS handling
'dal',                  # Django autocomplete
'dal_select2',          # Select2 integration
'cloudinary_storage',   # Cloud file storage
'cloudinary',           # Image processing
'channels',             # WebSocket support
```

**Custom Apps (business logic):**
```python
'rooms', 'guests', 'staff', 'housekeeping', 'room_services.apps.RoomServicesConfig',
'hotel', 'bookings', 'common', 'notifications', 'hotel_info.apps.HotelInfoConfig',
'stock_tracker', 'maintenance', 'channels', 'home', 'attendance', 'chat',
'entertainment', 'staff_chat', 'voice_recognition'
```

## Background Tasks & Automation

**Heroku Scheduler Configuration:**
- Script: `setup_heroku_scheduler.sh`
- Command: `python manage.py auto_clock_out_excessive`
- Frequency: Every 30 minutes
- Purpose: Automatic staff clock-out for excessive hours
- Evidence: Lines 19-20 in `setup_heroku_scheduler.sh`

**Django Management Commands:**
Found 40+ management commands across apps, including:

**Stock Tracker Commands:**
- `stock_tracker/management/commands/check_october_period.py`
- `stock_tracker/management/commands/close_october_period.py`
- `stock_tracker/management/commands/create_october_stocktake.py`
- `stock_tracker/management/commands/generate_analytics_data.py`

**Hotel Commands:**
- `hotel/management/commands/heal_booking_integrity.py`
- `hotel/management/commands/flag_overstay_bookings.py`
- `hotel/management/commands/fix_cloudinary_urls.py`

**Staff Commands:**
- `staff/management/commands/seed_navigation_items.py`

UNCLEAR IN CODE: No Celery, RQ, or other async task queue detected. Background processing appears to rely on Heroku Scheduler + Django management commands only.

## Integrations Identified

From `requirements.txt` analysis:

**Payment Processing:**
- `stripe==11.2.0` - Stripe payment processing
- Evidence: Stripe integration in payment views

**Real-time Communications:**
- `pusher==3.3.3` - Real-time notifications and messaging
- `channels==4.2.2` - Django Channels for WebSocket support
- `channels_redis` - Redis backend for Channels
- Evidence: Pusher client references in multiple files

**Cloud Services:**
- `cloudinary==1.44.0` - Image and file storage
- `firebase-admin==6.5.0` - Firebase integration
- `google-cloud-firestore==2.21.0` - Google Cloud database
- `google-cloud-storage==3.4.1` - Google Cloud file storage

**AI/ML Services:**
- `openai==2.8.1` - OpenAI API integration

**Database:**
- `psycopg2-binary==2.9.10` - PostgreSQL adapter
- `redis==6.3.0` - Redis for caching and channels

**Other Integrations:**
- `reportlab==4.4.3` - PDF generation
- `qrcode==8.2` - QR code generation
- Email via SMTP (Gmail) - configured in settings.py

## Entry Points

**WSGI Application:** `HotelMateBackend.wsgi.application`
**Main URL Configuration:** `HotelMateBackend.urls`

**API Routing Structure:**
```
/api/staff/ -> staff_urls.py (staff zone routing)
/api/guest/ -> guest_urls.py (guest zone routing)  
/api/public/ -> public_urls.py (public zone routing)
/api/hotel/ -> hotel.urls (admin hotel management)
/api/chat/ -> chat.urls (direct chat access)
/api/room_services/ -> room_services.urls (direct room services)
/api/bookings/ -> bookings.urls (restaurant bookings)
/api/notifications/ -> notifications.urls (Pusher auth)
```

Evidence: `HotelMateBackend/urls.py` lines 47-68

## Authentication & Authorization

**Authentication:** Token-based authentication via Django REST Framework
- `rest_framework.authentication.TokenAuthentication`
- Evidence: `HotelMateBackend/settings.py` lines 218-228

**Authorization:** Permission-based with custom hotel-scoped permissions
- Custom middleware and permission classes
- Multi-tenant hotel isolation via hotel slug

**Session Management:** Standard Django sessions with database backend

UNCLEAR IN CODE: Specific permission class implementations need deeper analysis of permission files.