# Booking Management System - Source of Truth

## Overview
A comprehensive secure booking management system that allows guests to view, manage, and cancel their hotel bookings through token-based authenticated URLs. The system integrates with the frontend React application and provides a complete workflow from booking creation to cancellation.

## System Components

### 1. BookingManagementToken Model
**File**: `hotel/models.py`

```python
class BookingManagementToken(models.Model):
    booking = models.ForeignKey(RoomBooking, on_delete=models.CASCADE, related_name='management_tokens')
    token_hash = models.CharField(max_length=64, unique=True)  # SHA256 hash
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    last_action = models.CharField(max_length=50, blank=True)
    action_history = models.JSONField(default=list)
    
    @property
    def is_valid(self):
        # Status-based validity - no time expiry
        return self.booking.status not in ['COMPLETED', 'CANCELLED', 'DECLINED']
```

**Key Features**:
- ✅ SHA256 token hashing for security
- ✅ Status-based validity (no arbitrary time limits)
- ✅ Action tracking and history
- ✅ Linked to RoomBooking for automatic invalidation

### 2. API Endpoints

#### A. Booking Status View
**Endpoint**: `GET/POST /api/public/booking/status/{booking_id}/`
**File**: `hotel/public_views.py` - `BookingStatusView`

**GET Response**:
```json
{
  "booking": {
    "id": "BK-2025-0023",
    "confirmation_number": "CNF-123456",
    "status": "CONFIRMED",
    "check_in": "2025-12-28",
    "check_out": "2025-12-30",
    "room_type_name": "Deluxe Room",
    "hotel_name": "Hotel Killarney",
    "nights": 2,
    "adults": 2,
    "children": 0,
    "total_amount": "200.00",
    "currency": "EUR",
    "primary_guest_name": "John Doe",
    "primary_email": "john@example.com",
    "created_at": "2025-12-26T10:00:00Z",
    "cancelled_at": null,
    "cancellation_reason": ""
  },
  "hotel": {
    "name": "Hotel Killarney",
    "slug": "hotel-killarney",
    "phone": "+353-64-123-4567",
    "email": "info@hotelkillarney.ie"
  },
  "cancellation_policy": {
    "id": 1,
    "code": "FLEX48",
    "name": "Flexible 48 Hours",
    "description": "Free cancellation up to 48 hours before check-in...",
    "template_type": "FLEXIBLE",
    "free_until_hours": 48,
    "penalty_type": "PERCENTAGE",
    "no_show_penalty_type": "FULL_AMOUNT"
  },
  "can_cancel": true,
  "cancellation_preview": {
    "fee_amount": "0.00",
    "refund_amount": "200.00",
    "description": "Full refund available - cancellation is free until 48 hours before check-in."
  }
}
```

**POST (Cancellation)**:
```json
{
  "token": "raw_token_value",
  "reason": "Change of plans"
}
```

#### B. Token Validation
**Endpoint**: `POST /api/public/booking/validate-token/`
**File**: `hotel/public_views.py` - `ValidateBookingManagementTokenView`

#### C. Direct Cancellation
**Endpoint**: `POST /api/public/booking/cancel/`
**File**: `hotel/public_views.py` - `CancelBookingView`

#### D. Hotel Cancellation Policy
**Endpoint**: `GET /api/public/hotels/{hotel_slug}/cancellation-policy/`
**File**: `hotel/public_views.py` - `HotelCancellationPolicyView`

### 3. URL Routing
**File**: `public_urls.py`

```python
# Booking Management URLs
path('booking/validate-token/', ValidateBookingManagementTokenView.as_view(), name='validate_booking_token'),
path('booking/cancel/', CancelBookingView.as_view(), name='cancel_booking'),
path('booking/status/<str:booking_id>/', BookingStatusView.as_view(), name='booking_status'),

# Hotel Information URLs  
path('hotels/<slug:hotel_slug>/cancellation-policy/', HotelCancellationPolicyView.as_view(), name='hotel_cancellation_policy'),
```

### 4. Booking Management Service
**File**: `hotel/services/booking_management.py`

**Key Functions**:
- `generate_booking_management_token(booking)` - Creates secure token
- `send_booking_management_email(booking, token)` - Sends management email
- `cancel_booking_programmatically(booking, reason, token=None)` - Handles cancellation

### 5. Automatic Integration
**File**: `hotel/services/booking.py`

The system automatically generates tokens and sends emails when bookings are created:

```python
# Auto-generate management token and send email
try:
    from hotel.services.booking_management import generate_booking_management_token, send_booking_management_email
    token = generate_booking_management_token(booking)
    send_booking_management_email(booking, token)
except Exception as e:
    logger.error(f"Failed to send booking management email for {booking.booking_id}: {str(e)}")
```

### 6. Email Template
**File**: `templates/emails/booking_management.html`

**Email Content**:
- Professional hotel branding
- Booking confirmation details
- Management link with token
- Clear instructions for guests
- Hotel contact information

**Management URL Format**:
```
https://hotelsmates.com/booking/status/{{booking.booking_id}}?token={{raw_token}}
```

### 7. Pricing Quote Integration
**File**: `hotel/services/pricing.py`

Cancellation policy information is included in all pricing quotes:

```python
def build_pricing_quote_data(hotel, room_type, check_in, check_out, adults, children):
    # ... existing pricing logic ...
    
    # Add cancellation policy
    cancellation_policy = None
    if hotel.default_cancellation_policy:
        policy = hotel.default_cancellation_policy
        cancellation_policy = {
            'id': policy.id,
            'code': policy.code,
            'name': policy.name,
            'description': policy.description,
            'template_type': policy.template_type,
            # ... additional policy fields
        }
    
    return {
        # ... existing quote data ...
        'cancellation_policy': cancellation_policy
    }
```

## Frontend Integration

### React Frontend URLs
The system is designed to work with React frontend expecting these URL patterns:

1. **Booking Status Page**: `https://hotelsmates.com/booking/status/BK-2025-0023?token=abc123`
2. **API Calls**: 
   - GET `/api/public/booking/status/BK-2025-0023/?token=abc123`
   - POST `/api/public/booking/status/BK-2025-0023/` with token in body

### Frontend Implementation Guide

```javascript
// Extract booking ID and token from URL
const bookingId = window.location.pathname.split('/').pop();
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');

// Fetch booking details
const response = await fetch(`/api/public/booking/status/${bookingId}/?token=${token}`);
const bookingData = await response.json();

// Cancel booking
const cancelResponse = await fetch(`/api/public/booking/status/${bookingId}/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ token, reason: 'User requested cancellation' })
});
```

## Security Features

### Token Security
- ✅ **SHA256 Hashing**: Raw tokens never stored in database
- ✅ **Unique Generation**: Cryptographically secure random tokens
- ✅ **Action Tracking**: Full audit trail of token usage
- ✅ **Status-Based Validity**: Tokens automatically invalid when booking status changes

### Access Control
- ✅ **Token Required**: All operations require valid token
- ✅ **Booking Validation**: Token must match specific booking
- ✅ **Status Checks**: Operations only allowed on valid booking states
- ✅ **Automatic Invalidation**: Tokens become invalid when booking completed/cancelled

## Operational Workflow

### 1. Booking Creation
1. Guest creates booking through normal process
2. System automatically generates `BookingManagementToken`
3. Management email sent with secure link
4. Guest receives email with booking details and management URL

### 2. Guest Access
1. Guest clicks link from email: `https://hotelsmates.com/booking/status/BK-2025-0023?token=abc123`
2. React frontend extracts booking ID and token from URL
3. Frontend calls API: `GET /api/public/booking/status/BK-2025-0023/?token=abc123`
4. System validates token and returns booking details

### 3. Cancellation Process
1. Guest decides to cancel booking
2. Frontend shows cancellation preview with fees/refunds
3. Guest confirms cancellation
4. Frontend posts to: `POST /api/public/booking/status/BK-2025-0023/`
5. System processes cancellation and updates booking status
6. Token automatically becomes invalid

## Configuration Notes

### Hotel Setup
- **Default Cancellation Policy**: Each hotel should have a default policy set
- **Email Templates**: Customize email branding per hotel if needed
- **Contact Information**: Ensure hotel phone/email are populated for guest support

### Environment Variables
- **Email Service**: Ensure email backend is properly configured
- **Frontend URL**: Update management link base URL for production
- **Security**: Consider rate limiting for token validation endpoints

## Testing Examples

### Hotel Killarney Test Data
- **Hotel**: Hotel Killarney (slug: `hotel-killarney`)
- **Policy**: FLEX48 (48-hour flexible cancellation)
- **Test Booking**: BK-2025-0023

### API Testing
```bash
# Get booking status
curl -X GET "http://localhost:8000/api/public/booking/status/BK-2025-0023/?token=your_token_here"

# Cancel booking
curl -X POST "http://localhost:8000/api/public/booking/status/BK-2025-0023/" \
  -H "Content-Type: application/json" \
  -d '{"token":"your_token_here","reason":"Test cancellation"}'

# Get hotel policy
curl -X GET "http://localhost:8000/api/public/hotels/hotel-killarney/cancellation-policy/"
```

## Migration Status
- ✅ **Models**: BookingManagementToken model migrated
- ✅ **Views**: All API endpoints implemented
- ✅ **URLs**: Public URL routing configured
- ✅ **Services**: Booking management service created
- ✅ **Templates**: Email template created
- ✅ **Integration**: Auto-email sending on booking creation

## Implementation Checklist
- ✅ Token-based booking management system
- ✅ Secure SHA256 token hashing
- ✅ Status-based token validity (no time expiry)
- ✅ Automatic email sending on booking creation
- ✅ Complete REST API for frontend integration
- ✅ Cancellation fee calculation and preview
- ✅ Hotel cancellation policy endpoints
- ✅ React frontend compatibility
- ✅ Professional email templates
- ✅ Comprehensive error handling

## Future Enhancements
- 📋 **Multi-language Support**: Translate email templates
- 📋 **SMS Integration**: Optional SMS notifications
- 📋 **Advanced Analytics**: Track token usage patterns  
- 📋 **Hotel Customization**: Per-hotel email templates
- 📋 **Guest Preferences**: Remember guest notification preferences

---
*This document serves as the authoritative reference for the HotelMate booking management system implementation. Last updated: December 26, 2025*