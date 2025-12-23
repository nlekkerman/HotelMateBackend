# Guest Pre-Check-In Email & Link System Documentation

## Overview

The HotelMate system provides a secure, automated way for staff to send pre-check-in links to guests via email. This allows guests to complete their party information remotely before arrival, streamlining the check-in process.

## System Architecture

### Core Components

1. **Token-Based Security**: Secure SHA256-hashed tokens with 72-hour expiration
2. **Email Integration**: Django SMTP with professional templates
3. **Staff Interface**: One-click link sending from booking management
4. **Guest Interface**: Mobile-friendly public forms with validation

## Email Sending Process

### 1. Staff Initiates Link Send

**Trigger**: Staff clicks "Send Pre-Check-In Link" button in booking management interface

**API Endpoint**:
```http
POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/send-precheckin-link/
```

**Authentication**: Staff authentication + hotel scope validation required

### 2. Token Generation & Security

```python
# Generate secure token (never stored raw)
raw_token = secrets.token_urlsafe(32)  # 43-character URL-safe string
token_hash = hashlib.sha256(raw_token.encode()).hexdigest()  # SHA256 hash stored

# Token expiration (72 hours)
expires_at = timezone.now() + timedelta(hours=72)
```

**Security Features**:
- ✅ Raw tokens never stored in database
- ✅ Only SHA256 hashes stored for validation
- ✅ Previous tokens automatically revoked for security
- ✅ One-time use tokens (marked `used_at` after submission)
- ✅ Time-based expiration (72 hours)

### 3. Email Address Determination

**Primary Target**: `booking.primary_email` (guest's email)
**Fallback**: `booking.booker_email` (person who made the booking)

```python
target_email = booking.primary_email or booking.booker_email
```

**Error Handling**: Returns 400 error if no email address found

### 4. Email Composition & Delivery

#### Email Template

**Subject**: `Complete your check-in details - {hotel_name}`

**Body**:
```
Dear {guest_name},

Please complete your party details before your stay at {hotel_name}.

Booking: {booking_id}
Dates: {check_in} to {check_out}

Complete your details here: {precheckin_url}

This link expires in 72 hours.

Best regards,
{hotel_name} Team
```

#### Pre-Check-In URL Construction

```python
base_domain = settings.FRONTEND_BASE_URL  # https://hotelsmates.com
precheckin_url = f"{base_domain}/guest/hotel/{hotel_slug}/precheckin?token={raw_token}"
```

**Example Link**: 
```
https://hotelsmates.com/guest/hotel/marriott-downtown/precheckin?token=Xy9kP8mQ7rL3zF6tN2wE1sA4vB8cD9fG6hJ5kM3nP0qR
```

## Hotel Pre-Check-In Configuration System

### How Pre-Check-In Config Works

Each hotel can customize which fields guests see and which fields are required during the pre-check-in process. This is controlled by the **HotelPrecheckinConfig** model that stores configuration per hotel.

### Configuration Structure

#### HotelPrecheckinConfig Model

**Location**: `hotel/models.py`

```python
class HotelPrecheckinConfig(models.Model):
    hotel = models.OneToOneField(Hotel, on_delete=models.CASCADE, related_name="precheckin_config")
    fields_enabled = models.JSONField(default=dict, blank=True)  # Which fields are visible
    fields_required = models.JSONField(default=dict, blank=True)  # Which fields are mandatory
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### Field Registry System

**Location**: `hotel/precheckin/field_registry.py`

All available precheckin fields are defined in a centralized registry:

```python
PRECHECKIN_FIELD_REGISTRY = {
    "eta": {
        "label": "Estimated Time of Arrival",
        "type": "text",
        "scope": "booking"
    },
    "special_requests": {
        "label": "Special Requests",
        "type": "textarea",
        "scope": "booking"  
    },
    "consent_checkbox": {
        "label": "I agree to the terms and conditions",
        "type": "checkbox",
        "scope": "booking"
    },
    "nationality": {
        "label": "Nationality", 
        "type": "select",
        "scope": "booking",
        "choices": ["US", "UK", "CA", "AU", "DE", "FR", "ES", "IT", "NL", "Other"]
    }
    // ... additional fields
}
```

### Configuration Management

#### Default Configuration

When a hotel is first created, it gets a minimal, high-completion-rate default configuration:

```python
DEFAULT_CONFIG = {
    "enabled": {
        "eta": True,                    # Show ETA field
        "special_requests": True,       # Show special requests
        "consent_checkbox": True        # Show consent checkbox
    },
    "required": {
        "consent_checkbox": True        # Only consent is mandatory
    }
}
```

#### Auto-Creation

```python
# Automatically creates default config if none exists
config = HotelPrecheckinConfig.get_or_create_default(hotel)
```

### Staff Configuration Interface

#### Get Current Configuration

```http
GET /api/staff/hotel/{hotel_slug}/precheckin-config/
```

**Response**:
```json
{
    "enabled": {
        "eta": true,
        "special_requests": true,
        "nationality": false,
        "consent_checkbox": true
    },
    "required": {
        "consent_checkbox": true
    },
    "field_registry": {
        "eta": {"label": "Estimated Time of Arrival", "type": "text"},
        "special_requests": {"label": "Special Requests", "type": "textarea"},
        "nationality": {"label": "Nationality", "type": "select", "choices": ["US", "UK", ...]},
        "consent_checkbox": {"label": "I agree to terms", "type": "checkbox"}
    }
}
```

#### Update Configuration

```http
POST /api/staff/hotel/{hotel_slug}/precheckin-config/
```

**Request Body**:
```json
{
    "enabled": {
        "eta": true,
        "special_requests": true,
        "nationality": true,
        "consent_checkbox": true
    },
    "required": {
        "nationality": true,
        "consent_checkbox": true
    }
}
```

**Permissions**: Super Staff Admin access required

### Validation Rules

#### 1. Subset Rule
**Required fields must be subset of enabled fields**
```python
# ❌ INVALID: Can't require a field that's not enabled
{
    "enabled": {"eta": false, "consent_checkbox": true},
    "required": {"eta": true}  # ERROR: eta required but not enabled
}

# ✅ VALID: Required fields are subset of enabled
{
    "enabled": {"eta": true, "consent_checkbox": true},
    "required": {"consent_checkbox": true}  # OK: consent is enabled
}
```

#### 2. Registry Key Validation
**All field keys must exist in the registry**
```python
# ❌ INVALID: Unknown field key
{
    "enabled": {"unknown_field": true}  # ERROR: not in registry
}

# ✅ VALID: All keys exist in registry
{
    "enabled": {"eta": true, "nationality": true}  # OK: both in registry
}
```

#### 3. Guest Name Fields
**Party member names are always required and not configurable**
- First name, last name are enforced separately via the party system
- Cannot be disabled or made optional

### Configuration Snapshots

#### Why Snapshots?
When a pre-check-in token is created, the current hotel configuration is **"frozen"** as a snapshot. This ensures:

- ✅ Guests see consistent fields even if hotel changes config later
- ✅ Validation rules remain stable for the token's lifetime
- ✅ No confusion from mid-process configuration changes

#### Snapshot Storage

```python
# When token is created, config is captured
token = BookingPrecheckinToken.objects.create(
    booking=booking,
    token_hash=token_hash,
    expires_at=expires_at,
    config_snapshot_enabled=hotel_config.fields_enabled.copy(),  # Frozen state
    config_snapshot_required=hotel_config.fields_required.copy()  # Frozen state
)
```

#### Snapshot Usage

```python
# When guest accesses the form, use snapshot (not current config)
if token.config_snapshot_enabled:
    # Use snapshot from token creation time
    config_enabled = token.config_snapshot_enabled
    config_required = token.config_snapshot_required
else:
    # Fallback for old tokens without snapshots
    hotel_config = HotelPrecheckinConfig.get_or_create_default(booking.hotel)
    config_enabled = hotel_config.fields_enabled
    config_required = hotel_config.fields_required
```

### Guest Experience Impact

#### Dynamic Form Generation

Based on the configuration, the guest sees different fields:

**Hotel A Config** (Minimal):
```json
{
    "enabled": {"eta": true, "consent_checkbox": true},
    "required": {"consent_checkbox": true}
}
```
→ Guest sees: ETA (optional), Consent (required)

**Hotel B Config** (Comprehensive):
```json
{
    "enabled": {"eta": true, "nationality": true, "special_requests": true, "consent_checkbox": true},
    "required": {"nationality": true, "consent_checkbox": true}
}
```
→ Guest sees: ETA (optional), Nationality (required), Special Requests (optional), Consent (required)

#### Field Type Rendering

Different field types render appropriately:
- **text**: `<input type="text">`
- **textarea**: `<textarea>`
- **checkbox**: `<input type="checkbox">`
- **select**: `<select><option>` with choices from registry
- **date**: Date picker component

### Data Storage

#### Where Configuration Data Goes

**Booking-Level Storage**: All precheckin field data is stored in `RoomBooking.precheckin_payload`:

```python
# Example stored data
booking.precheckin_payload = {
    "eta": "3:00 PM",
    "nationality": "US", 
    "special_requests": "Late checkout if possible",
    "consent_checkbox": true
}
```

#### Party vs Config Fields

- **Party Fields**: Names, emails, phone → Stored in `BookingGuest` records
- **Config Fields**: ETA, nationality, requests → Stored in `precheckin_payload`

### Backend Validation Flow

#### When Guest Submits Form

1. **Token Validation**: Verify token is valid and not expired
2. **Config Retrieval**: Get snapshot config or current hotel config
3. **Required Field Check**: Ensure all required fields are provided
4. **Registry Validation**: Reject unknown field keys
5. **Enabled Field Check**: Only store fields that are enabled
6. **Data Storage**: Save to `precheckin_payload`

```python
# Validation example
for field_key, is_required in config_required.items():
    if is_required and field_key not in submitted_data:
        return Response({'error': f'Field {field_key} is required'}, status=400)

# Only store enabled fields
for field_key in submitted_data.keys():
    if field_key not in config_enabled or not config_enabled[field_key]:
        continue  # Skip disabled fields
    if field_key not in PRECHECKIN_FIELD_REGISTRY:
        return Response({'error': f'Unknown field: {field_key}'}, status=400)
```

### Integration with Email System

#### Configuration Impact on Email Links

When staff sends a pre-check-in link:

1. **Token Creation**: Current hotel config is captured as snapshot
2. **Email Sent**: Guest receives link with frozen configuration
3. **Form Access**: Guest sees fields based on snapshot, not current config
4. **Validation**: Form submission validates against same snapshot

This ensures consistency throughout the guest's experience, even if hotel staff change configuration after sending the link.

## Configuration Requirements

### Django Settings

```python
# Frontend domain for pre-check-in links
FRONTEND_BASE_URL = "https://hotelsmates.com"

# Email configuration
DEFAULT_FROM_EMAIL = "noreply@hotelsmates.com"
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com' 
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## Database Schema

### BookingPrecheckinToken Model

**Location**: `hotel/models.py`

```python
class BookingPrecheckinToken(models.Model):
    booking = models.ForeignKey(RoomBooking, on_delete=models.CASCADE, related_name='precheckin_tokens')
    token_hash = models.CharField(max_length=64)  # SHA256 hash only
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True) 
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_email = models.EmailField(blank=True)  # Audit trail
    
    # Configuration snapshots for stable validation
    config_snapshot_enabled = models.JSONField(default=dict, blank=True)
    config_snapshot_required = models.JSONField(default=dict, blank=True)
```

## API Response Format

### Success Response

```json
{
    "success": true,
    "sent_to": "guest@example.com",
    "expires_at": "2025-12-26T10:00:00Z",
    "booking_id": "BK-2025-0001"
}
```

### Error Responses

```json
// Booking not found
{
    "error": "Booking not found"
}

// No email address
{
    "error": "No email address found for this booking"
}

// Email delivery failure
{
    "error": "Failed to send email"
}
```

## Guest Experience Flow

### 1. Email Reception
- Guest receives professional email from hotel
- Email contains secure link with clear instructions
- Link expires in 72 hours for security

### 2. Link Access
- Guest clicks link → Redirects to public pre-check-in form
- No login required → Token-based authentication
- Mobile-friendly interface

### 3. Party Information Completion
- Guest fills out party member details
- Required fields based on hotel configuration
- Real-time validation and error handling

### 4. Submission Confirmation
- Data saved to booking records
- Token marked as used (one-time security)
- Confirmation message displayed
- Optional confirmation email sent

## Technical Implementation

### Staff View Implementation

**File**: `hotel/staff_views.py`
**Class**: `SendPrecheckinLinkView`

```python
class SendPrecheckinLinkView(APIView):
    """Send pre-check-in link to guest via email"""
    permission_classes = [IsAuthenticated]

    def post(self, request, hotel_slug, booking_id):
        # 1. Validate booking exists
        # 2. Generate secure token
        # 3. Revoke previous tokens
        # 4. Create new token record
        # 5. Send email
        # 6. Return success response
```

### URL Configuration

**File**: `room_bookings/staff_urls.py`

```python
path(
    '<str:booking_id>/send-precheckin-link/',
    SendPrecheckinLinkView.as_view(),
    name='room-bookings-send-precheckin-link'
)
```

### Public Guest Endpoints

**Token Validation**: 
```http
GET /api/public/hotel/{hotel_slug}/precheckin/validate-token/?token={raw_token}
```

**Data Submission**:
```http
POST /api/public/hotel/{hotel_slug}/precheckin/submit/
```

## Error Handling & Security

### Token Security
- ✅ Raw tokens never logged or stored
- ✅ Constant-time comparison prevents timing attacks
- ✅ Automatic revocation of previous tokens
- ✅ One-time use enforcement

### Email Delivery
- ✅ Automatic token revocation if email fails
- ✅ Graceful fallback to booker email
- ✅ Error logging for debugging
- ✅ Audit trail of sent emails

### Rate Limiting
- ✅ Staff endpoints protected by authentication
- ✅ Public endpoints rate-limited (10 req/min)
- ✅ Token validation protected against brute force

## Integration Points

### Real-Time Updates
```python
# Notify staff when guest completes pre-check-in
from notifications.notification_manager import notification_manager
notification_manager.realtime_booking_updated(booking)
```

### Room Assignment Enforcement
```python
# Block room assignment until party is complete
if not booking.party_complete:
    raise ValidationError("Party information must be complete before room assignment")
```

### Audit Logging
```python
# Track all pre-check-in activities
logger.info(f"Pre-check-in link sent to {target_email} for booking {booking.booking_id}")
logger.info(f"Pre-check-in completed for booking {booking.booking_id} by {target_email}")
```

## Monitoring & Analytics

### Key Metrics
- **Link Send Rate**: Number of links sent per day
- **Completion Rate**: Percentage of links that result in completed forms
- **Expiration Rate**: Percentage of links that expire unused
- **Email Delivery Rate**: Success rate of email delivery

### Tracking Points
1. Token generation and email sending
2. Guest link access and form views  
3. Form completion and submission
4. Room assignment improvements (faster check-ins)

## Troubleshooting

### Common Issues

**Links Not Working**:
- Check `FRONTEND_BASE_URL` setting
- Verify token hasn't expired (72 hours)
- Confirm token hasn't been used already

**Emails Not Sending**:
- Verify SMTP configuration
- Check `DEFAULT_FROM_EMAIL` setting
- Review email server logs
- Confirm guest email addresses are valid

**Form Submission Errors**:
- Check hotel precheckin configuration
- Verify required fields are properly set
- Review public API rate limits

## Future Enhancements

### Planned Features
- **SMS Delivery**: Option to send links via SMS for better reach
- **Email Templates**: Rich HTML templates with hotel branding
- **Partial Completion**: Allow incremental updates to party information
- **Analytics Dashboard**: Staff visibility into completion rates
- **Webhook Notifications**: Real-time alerts for completed pre-check-ins

### Security Improvements
- **JWT Tokens**: Consider stateless token validation
- **CAPTCHA Protection**: Add bot protection if needed
- **Enhanced Logging**: More detailed audit trails

## Production Checklist

- ✅ SMTP configuration tested and working
- ✅ Frontend domain properly configured
- ✅ SSL certificates valid for email domain
- ✅ Email delivery monitoring in place
- ✅ Token cleanup job scheduled (30 days)
- ✅ Rate limiting configured appropriately
- ✅ Error logging and monitoring active

---

**Status**: ✅ Production Ready  
**Last Updated**: December 23, 2025  
**Documentation**: Complete with security audit