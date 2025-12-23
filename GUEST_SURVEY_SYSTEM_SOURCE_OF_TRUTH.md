# Guest Survey System - Source of Truth Implementation Plan

**Date Created**: December 23, 2025  
**Objective**: Implement a Guest Survey Email + Link system that is structurally identical to the existing Pre-Check-in system, including hotel-level configuration, field registry, token-based security with snapshots, staff endpoints, and automatic + manual sending controls.

## 🔒 Frozen Design Decisions

### Survey Send Timing
**Default survey send delay is 24 hours after checkout unless overridden by hotel config.**
- Reason: Guests are home, calm, and more likely to respond thoughtfully than at checkout or late night
- Hotels can customize this timing via configuration

### Token Expiry Duration  
**Survey tokens expire after 7 days (168 hours) by default.**
- Surveys are not time-critical like pre-check-in
- Provides reasonable window for completion without security risks

### Survey Response Storage
**overall_rating is duplicated as a column for analytics; full response stored in payload.**
- Store full response in `payload` (JSON) for flexibility
- ALSO store `overall_rating` as top-level column for fast dashboard queries
- Prevents performance issues from JSON-only queries

### Idempotency Rule
**A survey email must be sent once per booking by default. Resending requires an explicit staff action and revokes previous tokens.**
- Prevents accidental spam
- Staff can manually resend which creates new token and revokes previous ones
- Clear audit trail maintained

---

## Architecture Overview

This system mirrors the proven Pre-Check-in architecture for consistency, security, and maintainability. All patterns, security measures, and integration points follow established precheckin conventions.

## 1. Survey Configuration Model (Mirror Precheckin)

### HotelSurveyConfig Model
**Location**: `hotel/models.py`

```python
class HotelSurveyConfig(models.Model):
    hotel = models.OneToOneField(Hotel, related_name="survey_config", on_delete=models.CASCADE)
    fields_enabled = models.JSONField(default=dict, blank=True)  # Which fields are visible
    fields_required = models.JSONField(default=dict, blank=True)  # Which fields are mandatory
    
    # Survey Email Send Policy Fields
    send_mode = models.CharField(max_length=20, choices=[
        ('AUTO_IMMEDIATE', 'Send immediately after checkout'),
        ('AUTO_DELAYED', 'Send after delay'),
        ('MANUAL_ONLY', 'Manual sending only')
    ], default='AUTO_DELAYED')
    
    delay_hours = models.PositiveIntegerField(default=24)  # 24-hour default delay
    token_expiry_hours = models.PositiveIntegerField(default=168)  # 7 days
    email_subject_template = models.TextField(blank=True)  # Optional customization
    email_body_template = models.TextField(blank=True)     # Optional customization
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_or_create_default(cls, hotel):
        # Auto-creates default config with high completion rate defaults
        
    def clean(self):
        # Validates required fields are subset of enabled fields
```

**Auto-Creation**: Similar to precheckin, auto-create default config on hotel creation or via `get_or_create_default` method.

### Default Configuration (High Completion Rate)
```python
DEFAULT_SURVEY_CONFIG = {
    "enabled": {
        "overall_rating": True,
        "comment": True, 
        "contact_permission": True
    },
    "required": {
        "overall_rating": True  # Only rating required by default
    },
    "send_mode": "AUTO_DELAYED",
    "delay_hours": 24
}
```

## 2. Survey Field Registry (Mirror Precheckin)

### Field Registry Structure
**Location**: `hotel/survey/field_registry.py`

```python
SURVEY_FIELD_REGISTRY = {
    "overall_rating": {
        "label": "Overall Rating",
        "type": "rating", 
        "scope": "survey",
        "choices": [(1, "1 - Poor"), (2, "2 - Fair"), (3, "3 - Good"), (4, "4 - Very Good"), (5, "5 - Excellent")],
        "required": True  # Default required field
    },
    "comment": {
        "label": "Comments & Feedback",
        "type": "textarea",
        "scope": "survey",
        "placeholder": "Share your experience with us..."
    },
    "contact_permission": {
        "label": "May we contact you about your feedback?",
        "type": "checkbox", 
        "scope": "survey"
    }
    # Future expansion fields (disabled by default):
    # "cleanliness_rating", "staff_rating", "breakfast_rating"
}
```

**Field Types Supported**: `rating`, `textarea`, `checkbox`, `text`, `select`  
**Scope**: All survey fields use `scope = "survey"` (booking-level)

## 3. Survey Token Model With Snapshots (Mirror Precheckin)

### BookingSurveyToken Model
**Location**: `hotel/models.py`

```python
class BookingSurveyToken(models.Model):
    booking = models.ForeignKey(RoomBooking, related_name='survey_tokens', on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64)  # SHA256 hash only - never store raw
    expires_at = models.DateTimeField()  # Configurable expiry (default 7 days)
    used_at = models.DateTimeField(null=True, blank=True)  # One-time use enforcement
    revoked_at = models.DateTimeField(null=True, blank=True)  # Security revocation
    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_email = models.EmailField(blank=True)  # Audit trail
    
    # Config snapshots for stable validation (CRITICAL PATTERN)
    config_snapshot_enabled = models.JSONField(default=dict, blank=True)
    config_snapshot_required = models.JSONField(default=dict, blank=True)
    config_snapshot_send_mode = models.CharField(max_length=20, blank=True)  # Snapshot of send settings
    
    @property
    def is_valid(self):
        # Checks expiry, usage, and revocation status
        
    @property  
    def is_expired(self):
        return timezone.now() > self.expires_at
        
    @property
    def is_used(self):
        return self.used_at is not None
        
    @property
    def is_revoked(self):
        return self.revoked_at is not None
```

**Critical Rule**: When token is created, snapshot current hotel survey config into the token. Public guest endpoints must use snapshot if present to ensure consistency.

### BookingSurveyResponse Model
**Location**: `hotel/models.py`

```python
class BookingSurveyResponse(models.Model):
    booking = models.OneToOneField(RoomBooking, related_name='survey_response', on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, related_name='survey_responses', on_delete=models.CASCADE)
    
    # Dual storage approach (frozen decision)
    payload = models.JSONField(default=dict)  # Full survey response
    overall_rating = models.PositiveSmallIntegerField(null=True, blank=True)  # Analytics column
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    token_used = models.ForeignKey(BookingSurveyToken, on_delete=models.CASCADE)  # Audit trail
```

### RoomBooking Extensions
**Location**: `hotel/models.py` - Add to existing RoomBooking model

```python
# Survey-related fields to add to RoomBooking model
survey_sent_at = models.DateTimeField(null=True, blank=True)  # Idempotency tracking
survey_last_sent_to = models.EmailField(blank=True)  # Audit trail  
survey_send_at = models.DateTimeField(null=True, blank=True)  # For delayed sending scheduling
```

## 4. Staff Config API Endpoints (Mirror precheckin-config)

### Staff API Endpoints
**Location**: `hotel/staff_views.py`

#### HotelSurveyConfigView
- **GET** `/api/staff/hotel/{hotel_slug}/survey-config/`
- **POST** `/api/staff/hotel/{hotel_slug}/survey-config/`
- **Permission**: `IsStaffMember`
- **Response Format**:
```json
{
    "enabled": {"overall_rating": true, "comment": true},
    "required": {"overall_rating": true}, 
    "send_mode": "AUTO_DELAYED",
    "delay_hours": 24,
    "token_expiry_hours": 168,
    "field_registry": {/* subset of enabled fields */}
}
```

#### SendSurveyLinkView  
- **POST** `/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/send-survey-link/`
- **Permission**: `IsStaffMember`
- **Rules**: Only allowed if `booking.status == COMPLETED` or `checked_out_at` is set
- **Behavior**: Revokes previous tokens, creates new token with config snapshot, sends email
- **Response**: `{"sent_to": "email@example.com", "expires_at": "2025-12-30T10:00:00Z"}`

**Validation Rules**:
- Required fields ⊆ Enabled fields
- All field keys must exist in SURVEY_FIELD_REGISTRY
- Same validation patterns as precheckin

## 5. Public Guest Endpoints (Mirror Precheckin)

### Public API Endpoints
**Location**: `hotel/public_views.py`

#### ValidateSurveyTokenView
- **GET** `/api/public/hotel/{hotel_slug}/survey/validate-token/?token=...`
- **Permission**: `AllowAny` (token-based security)
- **Response**: Hotel info, booking data, field registry subset, config snapshot
- **Security**: Unified 404 for all invalid tokens, constant-time hash comparison

#### SubmitSurveyDataView
- **POST** `/api/public/hotel/{hotel_slug}/survey/submit/`
- **Permission**: `AllowAny` (token-based security)
- **Validation**: Required fields per config snapshot, enabled fields per snapshot
- **Behavior**: Atomic transaction - validate → store response → mark token used
- **Storage**: Both JSON payload + extracted overall_rating column

**URL Integration**: 
- Public URLs included via `hotel/public_urls.py`
- Integrated into main urls via `path("", include("hotel.public_urls"))`

## 6. Survey Email Sending (Reuse precheckin email infra)

### Email Infrastructure
**Location**: Following precheckin patterns in `hotel/staff_views.py`

#### Recipient Selection
Same as prechecin:
1. `booking.primary_email` (preferred)
2. Fallback to `booking.booker_email`  
3. Error if neither exists

#### Survey URL Format
```
{FRONTEND_BASE_URL}/guest/hotel/{hotel_slug}/survey?token={raw_token}
```

#### Email Content Template
```
Subject: Share your experience at {hotel_name}

Dear {guest_name},

Thank you for staying with us at {hotel_name}. We'd love to hear about your experience.

Please take a moment to share your feedback: {survey_url}

This survey takes less than a minute and helps us improve our service.

Your feedback link expires in 7 days.

Best regards,
{hotel_name}
```

**Settings Required**:
- `FRONTEND_BASE_URL`
- `DEFAULT_FROM_EMAIL` 

## 7. Triggering Survey Emails (Auto + Manual)

### Auto Trigger Integration
**Location**: `room_bookings/services/checkout.py`

Integrate into `checkout_booking()` function after commit:

```python
def checkout_booking(booking, checkout_data):
    # ... existing checkout logic ...
    
    # After successful checkout commit
    try:
        from hotel.services.survey import trigger_auto_survey_email
        trigger_auto_survey_email(booking)
    except Exception as e:
        logger.error(f"Survey email trigger failed for booking {booking.id}: {e}")
        # Do not break checkout if email fails
```

#### Auto Survey Logic
```python
def trigger_auto_survey_email(booking):
    hotel_config = HotelSurveyConfig.get_or_create_default(booking.hotel)
    
    if hotel_config.send_mode == 'AUTO_IMMEDIATE':
        send_survey_email_now(booking)
    elif hotel_config.send_mode == 'AUTO_DELAYED':  
        schedule_survey_email(booking, delay_hours=hotel_config.delay_hours)
    # MANUAL_ONLY: do nothing
```

### Manual Send Implementation
Staff endpoint (already covered in section 4) handles manual sending with proper token management.

## 8. Scheduling for Delayed Sending

### Delayed Sending Infrastructure

#### Management Command Pattern
**Location**: `hotel/management/commands/send_scheduled_surveys.py`

```python
class Command(BaseCommand):
    help = 'Send scheduled survey emails that are due'
    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--hotel-slug', help='Target specific hotel')
    
    def handle(self, *args, **options):
        # Find bookings where survey_send_at <= now and survey_sent_at is None
        # Send emails and update survey_sent_at
```

#### Scheduling Logic
```python  
def schedule_survey_email(booking, delay_hours):
    booking.survey_send_at = timezone.now() + timedelta(hours=delay_hours)
    booking.save(update_fields=['survey_send_at'])
```

#### Heroku Scheduler Setup
Add to `Procfile` or scheduler:
```
python manage.py send_scheduled_surveys
```

### Idempotency Implementation
- Check `survey_sent_at` field to prevent duplicate sends
- Manual resend explicitly sets new `survey_sent_at` and revokes old tokens
- Clear audit trail with `survey_last_sent_to` field

## 9. Security Implementation (Mirror Precheckin)

### Token Security Measures
1. **Never store raw tokens** - only SHA256 hashes in database
2. **Automatic revocation** of previous tokens when creating new ones  
3. **One-time usage** enforcement via `used_at` timestamp
4. **Constant-time comparison** prevents timing attacks
5. **Config snapshots** preserve validation rules across time
6. **Token expiry** - 7 days default, configurable per hotel

### Token Lifecycle
1. **Creation**: Generate secure token → Hash → Store with config snapshot → Email  
2. **Validation**: Hash incoming token → Compare → Check expiry/usage/revocation
3. **Usage**: Atomic transaction → Validate data → Store response → Mark token used
4. **Cleanup**: Expired tokens remain for audit (recommend cleanup after 30 days)

## 10. Database Migrations Required

### Migration Sequence
1. Add `HotelSurveyConfig` model
2. Add `BookingSurveyToken` model  
3. Add `BookingSurveyResponse` model
4. Add survey fields to `RoomBooking` model (`survey_sent_at`, `survey_last_sent_to`, `survey_send_at`)
5. Create default survey configs for existing hotels (data migration)

## 11. URL Patterns

### Staff URLs (in `room_bookings/staff_urls.py`)
```python
path('hotel/<slug:hotel_slug>/survey-config/', HotelSurveyConfigView.as_view()),
path('hotel/<slug:hotel_slug>/room-bookings/<int:booking_id>/send-survey-link/', SendSurveyLinkView.as_view()),
```

### Public URLs (in `hotel/public_urls.py`) 
```python
path('hotel/<slug:hotel_slug>/survey/validate-token/', ValidateSurveyTokenView.as_view()),
path('hotel/<slug:hotel_slug>/survey/submit/', SubmitSurveyDataView.as_view()),
```

## 12. Acceptance Criteria

### Core Functionality
✅ Hotels can manage survey fields (enabled/required) via staff dashboard API  
✅ Survey tokens snapshot config at send time for stability  
✅ Guest sees consistent survey fields even if config changes later  
✅ One-time token use strictly enforced  
✅ Same security standards as precheckin system

### Survey Sending
✅ Surveys can be sent automatically on checkout (immediate or delayed)  
✅ Surveys can be sent manually for completed bookings  
✅ Idempotency prevents duplicate survey emails  
✅ Email failures don't break checkout process

### Data Storage  
✅ Full survey responses stored in JSON payload  
✅ Overall rating duplicated as column for analytics  
✅ Complete audit trail maintained (tokens, timestamps, email addresses)

### Configuration
✅ Hotel-level send policy configuration (auto/delayed/manual)  
✅ Configurable delay timing and token expiry  
✅ Field-level enabled/required configuration  
✅ Auto-creation of default configs for new hotels

## 13. Implementation Phase Ordering

### Phase 1: Core Models & Registry
1. Create survey models in `hotel/models.py`
2. Build field registry in `hotel/survey/field_registry.py` 
3. Create and run database migrations

### Phase 2: Staff API Endpoints
4. Implement survey config management endpoints
5. Implement manual survey sending endpoint  
6. Add staff URL routing

### Phase 3: Public Guest Endpoints  
7. Create token validation endpoint
8. Create survey submission endpoint
9. Add public URL routing

### Phase 4: Integration & Automation
10. Integrate checkout triggers
11. Build delayed sending infrastructure
12. Create management command for scheduled sends

### Phase 5: Testing & Validation
13. Test complete end-to-end flow
14. Validate security measures
15. Test email delivery and error handling

---

## Frontend Implementation Notes

**After backend completion**, implement:

### Staff Dashboard Integration
- `SurveyRequirementsConfig.jsx` inside `BookingManagementDashboard`
- Mirror precheckin config patterns
- Field registry UI for enabled/required toggles
- Send policy configuration (auto/delayed/manual timing)

### Guest Survey Page
- `GuestSurveyPage.jsx` reusing precheckin page patterns  
- Token validation flow
- Form rendering from field registry
- Submission handling with success/error states

---

**This Source of Truth document locks in all critical design decisions and provides complete implementation guidance following proven precheckin architecture patterns.**