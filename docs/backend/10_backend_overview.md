# 10. Backend Overview

## System Architecture

HotelMate is a **multi-tenant hotel management platform** built on Django 5.2.4 with Django REST Framework 3.16.0. The system provides comprehensive hotel operations management including room bookings, staff management, guest services, inventory tracking, and real-time communications.

**Evidence:** Framework identification from `manage.py` and `HotelMateBackend/settings.py`

## Multi-Tenant Architecture

### Tenant Isolation Strategy
- **URL-based isolation:** Hotel slug in API paths (`/api/{zone}/hotels/{hotel_slug}/`)
- **Database-level isolation:** Foreign key relationships to `Hotel` model
- **Token-scoped access:** Authentication tokens contain hotel context
- **Custom headers:** `x-hotel-id`, `x-hotel-slug`, `x-hotel-identifier` for hotel identification

**Evidence:** URL routing patterns in `staff_urls.py`, `guest_urls.py`, and CORS headers configuration

### Zone-Based API Architecture

The system organizes endpoints into distinct zones based on user roles:

1. **Staff Zone** (`/api/staff/`) - Hotel staff operations and management
2. **Guest Zone** (`/api/guest/`) - Guest-facing booking and services  
3. **Public Zone** (`/api/public/`) - Unauthenticated hotel discovery and booking
4. **Hotel Admin Zone** (`/api/hotel/`) - Superuser hotel configuration
5. **Direct Access Zones** - Legacy compatibility for specific services

**Evidence:** Zone definitions in `HotelMateBackend/urls.py` lines 47-69

## Core Business Domains

### 1. Hotel Operations (`hotel/`)
- **Responsibility:** Core hotel configuration, booking lifecycle, payment processing
- **Key Models:** `Hotel`, `RoomBooking`, `GuestBookingToken`, `CancellationPolicy`
- **Features:** Multi-phase booking workflow, payment authorization/capture, overstay management

### 2. Room Management (`rooms/`)
- **Responsibility:** Room inventory, status tracking, turnover workflow
- **Key Models:** `Room`, `RoomType`
- **Features:** Room status state machine, availability calculations, housekeeping integration

### 3. Guest Services (`guests/`)
- **Responsibility:** Guest profiles and service management
- **Features:** Guest registration, profile management, service history

### 4. Staff Management (`staff/`)
- **Responsibility:** Staff authentication, permissions, attendance tracking
- **Key Models:** `Staff`, `Department`, `Role`, `NavigationItem`
- **Features:** Role-based access control, attendance automation, staff chat

### 5. Housekeeping Operations (`housekeeping/`)
- **Responsibility:** Room cleaning workflow, status management
- **Features:** Turnover task creation, status tracking, maintenance flagging

### 6. Room Services (`room_services/`)
- **Responsibility:** In-room service ordering and delivery
- **Key Models:** `RoomServiceItem`, `Order`, `OrderItem`, `BreakfastItem`
- **Features:** Menu management, order processing, breakfast service

### 7. Inventory Management (`stock_tracker/`)
- **Responsibility:** Bar inventory, cocktail recipes, stock movements
- **Key Models:** `StockItem`, `CocktailRecipe`, `Ingredient`, `StockMovement`, `Stocktake`
- **Features:** Recipe-based consumption tracking, period-based inventory control

### 8. Real-time Communications (`chat/`, `staff_chat/`, `notifications/`)
- **Responsibility:** Guest-staff messaging, staff communications, push notifications
- **Features:** Pusher integration, file attachments, message reactions

## Technology Stack

### Core Framework
- **Django 5.2.4** - Web framework and ORM
- **Django REST Framework 3.16.0** - API framework
- **PostgreSQL** - Primary database (via `psycopg2-binary`)
- **Redis 6.3.0** - Caching and real-time features

### Real-time & Communications  
- **Pusher 3.3.3** - Real-time messaging and notifications
- **Django Channels 4.2.2** - WebSocket support
- **channels_redis** - Redis backend for Channels

### Cloud Services & Integrations
- **Stripe 11.2.0** - Payment processing
- **Cloudinary 1.44.0** - Image and file storage
- **Firebase Admin 6.5.0** - Push notifications
- **Google Cloud Firestore 2.21.0** - Additional data storage
- **OpenAI 2.8.1** - AI integration

### Development & Operations
- **Gunicorn 23.0.0** - WSGI server
- **WhiteNoise 6.9.0** - Static file serving
- **Heroku** - Platform deployment
- **ReportLab 4.4.3** - PDF generation
- **QRCode 8.2** - QR code generation

**Evidence:** Complete dependency list from `requirements.txt`

## Deployment Architecture

### Heroku Configuration
- **Web Process:** Gunicorn WSGI server
- **Background Jobs:** Heroku Scheduler with Django management commands
- **Static Files:** WhiteNoise for static file serving
- **Database:** PostgreSQL add-on with connection pooling

### Background Processing
- **Scheduler:** Heroku Scheduler (no Celery or RQ detected)
- **Auto Clock-out:** Every 30 minutes via `python manage.py auto_clock_out_excessive`
- **Management Commands:** 40+ commands across apps for data management

**Evidence:** `Procfile`, `setup_heroku_scheduler.sh`, and management command directories

## Authentication & Authorization

### Authentication Methods
- **Token Authentication:** Django REST Framework tokens
- **Session Authentication:** Django sessions for admin interface
- **Custom Token System:** Guest booking tokens with scoped permissions

### Authorization Strategy
- **Role-based Access Control:** Staff roles and departments
- **Permission Classes:** Django REST Framework permissions
- **Multi-tenant Isolation:** Hotel-scoped data access
- **Scoped Tokens:** Limited permissions per token purpose

**Evidence:** REST Framework configuration in `settings.py` lines 210-228

## Data Flow Architecture

### Request Processing Flow
```
Client Request → CORS Middleware → Auth Middleware → URL Routing → 
Zone-based Routing → App-specific URLs → ViewSets/Views → 
Serializers → Services → Models → Database
```

### Real-time Data Flow
```
Business Logic → Pusher Events → WebSocket Channels → 
Client Applications → Real-time UI Updates
```

## Configuration Management

### Environment Variables
- **Database:** `DATABASE_URL` for PostgreSQL connection
- **Security:** `SECRET_KEY` for Django security
- **Email:** SMTP configuration for notifications
- **Cloud Services:** Cloudinary, Stripe, Firebase API keys
- **Real-time:** Pusher and Redis configuration

### Feature Toggles
- **Hotel-level Configuration:** Per-hotel feature enabling/disabling
- **Access Controls:** Portal availability, PIN requirements
- **Timing Controls:** Checkout times, approval SLAs
- **Survey Settings:** Automation policies, field requirements

**Evidence:** Hotel configuration models and environment variable usage

## Monitoring & Observability

### Logging Configuration
```python
LOGGING = {
    "loggers": {
        "room_services": {"level": "INFO"},
        "channels": {"level": "INFO"}, 
        "redis": {"level": "WARNING"},
    }
}
```

### Error Handling
- **Custom 404 Handler:** `common.views.custom_404`
- **CORS Error Handling:** Comprehensive CORS configuration
- **Database Health Checks:** Connection health monitoring

**Evidence:** Logging configuration in `settings.py` lines 319-363

## Scalability Considerations

### Database Optimization
- **Connection Pooling:** `conn_max_age=600` for persistent connections
- **Health Checks:** `conn_health_checks=True` for connection monitoring
- **Indexing:** Database indexes on frequently queried fields

### Caching Strategy
- **Database Cache:** `django.core.cache.backends.db.DatabaseCache`
- **Redis Integration:** For real-time features and session storage
- **Static File Caching:** WhiteNoise with compression

### File Upload Limits
- **Max Memory Size:** 50MB per file upload
- **Cloud Storage:** Cloudinary for media file handling
- **Field Limits:** 10,000 fields per request for admin forms

**Evidence:** Cache and upload configurations in `settings.py`

## Security Features

### Data Protection
- **CSRF Protection:** Django CSRF middleware
- **SQL Injection Prevention:** Django ORM parameter binding
- **XSS Protection:** Django template auto-escaping
- **Clickjacking Protection:** X-Frame-Options middleware

### API Security
- **Token Authentication:** Secure token generation and validation
- **CORS Control:** Restricted origin allowlists
- **Request Rate Limiting:** Through Django middleware stack
- **Input Validation:** Django REST Framework serializers

**Evidence:** Middleware configuration and security settings

This backend architecture supports a comprehensive hotel management platform with strong multi-tenancy, real-time features, and scalable deployment on Heroku.