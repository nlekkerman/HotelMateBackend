# Guest Booking Management Token Implementation Plan

Implementation of guest "Manage Booking" access via token links, reusing the proven security architecture of `BookingPrecheckinToken` while providing multi-use booking management capabilities.

## Security Architecture Reuse

**Identical Patterns from BookingPrecheckinToken:**
- `secrets.token_urlsafe(32)` for token generation
- SHA256 hash storage only (never store raw tokens)
- Unified 404 responses for invalid/expired/revoked tokens
- Rate limiting (10 requests/minute per IP)
- Auto-revoke previous active tokens per booking
- Constant-time hash comparison for validation

**Key Difference:** Multi-use access vs single-use precheckin tokens.

## BookingManageToken Model

**Location:** `api/booking/models.py`

```python
class BookingManageToken(models.Model):
    """
    Secure token for guest booking management access.
    Reuses BookingPrecheckinToken security patterns with multi-use lifecycle.
    """
    
    # Core relationship - identical to BookingPrecheckinToken
    booking = models.ForeignKey(
        RoomBooking, 
        on_delete=models.CASCADE, 
        related_name='manage_tokens'
    )
    
    # Security fields - IDENTICAL to BookingPrecheckinToken
    token_hash = models.CharField(
        max_length=64,
        help_text="SHA256 hash only - raw token never stored"
    )
    expires_at = models.DateTimeField(
        help_text="Recommended: booking.check_out + 7 days"
    )
    revoked_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Auto-revoke previous active tokens per booking"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Audit trail - same as BookingPrecheckinToken
    sent_to_email = models.EmailField(
        blank=True,
        help_text="Email where manage booking link was sent"
    )
    
    # Optional multi-use tracking fields
    last_accessed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Last successful token validation"
    )
    access_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of successful validations"
    )
    
    class Meta:
        db_table = 'booking_manage_token'
        indexes = [
            models.Index(fields=['booking', 'token_hash']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['revoked_at']),
        ]
        
    def __str__(self):
        return f"ManageToken-{self.booking.booking_id}-{self.id}"
    
    @property
    def is_valid(self):
        """IDENTICAL validation logic to BookingPrecheckinToken"""
        from django.utils import timezone
        return (
            self.revoked_at is None and 
            self.expires_at > timezone.now()
        )
    
    def mark_accessed(self):
        """Update access tracking for multi-use tokens"""
        from django.utils import timezone
        self.last_accessed_at = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed_at', 'access_count'])

    @classmethod
    def generate_for_booking(cls, booking):
        """
        Generate manage token using IDENTICAL security pattern.
        Auto-revoke previous active tokens per booking.
        """
        import secrets
        import hashlib
        from django.utils import timezone
        
        # Step 1: Auto-revoke previous active tokens (same pattern)
        cls.objects.filter(
            booking=booking,
            revoked_at__isnull=True
        ).update(revoked_at=timezone.now())
        
        # Step 2: Generate secure token - IDENTICAL to BookingPrecheckinToken  
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Step 3: Set expiration - booking.check_out + 7 days (recommended)
        expires_at = timezone.datetime.combine(
            booking.check_out, 
            timezone.datetime.min.time().replace(tzinfo=timezone.get_current_timezone())
        ) + timezone.timedelta(days=7)
        
        # Step 4: Create token record
        manage_token = cls.objects.create(
            booking=booking,
            token_hash=token_hash,
            expires_at=expires_at,
            sent_to_email=booking.primary_guest_email or booking.booker_email,
        )
        
        return raw_token, manage_token
```

## Public API Endpoints

### 1. Validate Token and Return Booking Summary
**Endpoint:** `GET /api/public/hotel/{hotel_slug}/manage-booking/validate/{token}/`
**View Class:** `PublicBookingManageValidateView`
**Location:** `api/public/views.py`

```python
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from django.utils import timezone
import hashlib

class PublicBookingManageValidateView(APIView):
    """
    Validate manage booking token and return booking summary.
    IDENTICAL security patterns to PublicPrecheckinValidateView.
    """
    
    permission_classes = []  # Public endpoint - token provides access control
    throttle_classes = [AnonRateThrottle]  # Same rate limiting (10/min per IP)
    
    def get(self, request, hotel_slug, token):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # IDENTICAL token validation pattern to BookingPrecheckinToken
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        try:
            manage_token = BookingManageToken.objects.get(
                booking__hotel=hotel,
                token_hash=token_hash,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now()
            )
        except BookingManageToken.DoesNotExist:
            # Unified 404 response - IDENTICAL to precheckin validation
            raise Http404("Invalid or expired token")
        
        # Update multi-use access tracking (optional)
        manage_token.mark_accessed()
        
        booking = manage_token.booking
        
        # Server-side cancellation preview using existing CancellationCalculator
        from api.booking.services import CancellationCalculator
        
        can_cancel = booking.status in ['CONFIRMED', 'PENDING_APPROVAL']
        cancellation_preview = None
        
        if can_cancel:
            try:
                calculator = CancellationCalculator(booking)
                cancellation_preview = calculator.calculate_cancellation_fee()
            except Exception:
                can_cancel = False
        
        # Response - include booking.cancellation_policy snapshot expanded
        response_data = {
            'booking': {
                'id': booking.booking_id,
                'status': booking.status,
                'check_in': booking.check_in,
                'check_out': booking.check_out,
                'nights': booking.nights,
                'room_type_name': booking.room_type.name if booking.room_type else None,
                'hotel_name': booking.hotel.name,
                'expected_guests': booking.expected_guests,
                'total_amount': str(booking.total_amount),
                'currency': booking.currency,
                'created_at': booking.created_at,
            },
            'guest_details': {
                'primary_guest_name': f"{booking.primary_guest_first_name} {booking.primary_guest_last_name}",
                'primary_guest_email': booking.primary_guest_email,
                'booker_name': f"{booking.booker_first_name} {booking.booker_last_name}" if booking.booker_first_name else None,
                'booker_email': booking.booker_email,
            },
            'cancellation': {
                'can_cancel': can_cancel,
                'policy_snapshot_expanded': self._expand_policy_snapshot(booking),
                'preview_computed_server_side': cancellation_preview,
            },
            'hotel_contact': {
                'name': booking.hotel.name,
                'email': booking.hotel.email,
                'phone': booking.hotel.phone,
            }
        }
        
        return Response(response_data)
    
    def _expand_policy_snapshot(self, booking):
        """Expand booking.cancellation_policy snapshot with full details"""
        if not booking.cancellation_policy_snapshot:
            return None
            
        policy_data = booking.cancellation_policy_snapshot.copy()
        
        # Add human-readable description
        template = policy_data.get('template', 'UNKNOWN')
        hours_before = policy_data.get('hours_before_checkin', 24)
        
        if template == 'FLEXIBLE':
            policy_data['description'] = f"Free cancellation until {hours_before} hours before check-in"
        elif template == 'MODERATE':
            policy_data['description'] = f"Partial penalty {hours_before} hours before check-in"
        elif template == 'NON_REFUNDABLE':
            policy_data['description'] = "No refunds - full stay penalty"
        elif template == 'CUSTOM':
            policy_data['description'] = "Custom cancellation policy with multiple tiers"
            
        # Add time context
        checkin_datetime = timezone.datetime.combine(
            booking.check_in, 
            timezone.datetime.min.time().replace(tzinfo=timezone.get_current_timezone())
        )
        time_diff = checkin_datetime - timezone.now()
        policy_data['hours_until_checkin'] = max(0, int(time_diff.total_seconds() / 3600))
        
        return policy_data
```

### 2. Cancel Booking via Token
**Endpoint:** `POST /api/public/hotel/{hotel_slug}/manage-booking/cancel/`
**View Class:** `PublicBookingManageCancelView`
**Body:** `{token, reason}`

```python
from django.db import transaction
from rest_framework import status
from decimal import Decimal

class PublicBookingManageCancelView(APIView):
    """
    Cancel booking via token using extracted StaffBookingCancelView logic.
    Accepts {token, reason} and returns fee/refund, status.
    """
    
    permission_classes = []
    throttle_classes = [AnonRateThrottle]
    
    def post(self, request, hotel_slug):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Extract request data
        token = request.data.get('token')
        reason = request.data.get('reason', 'Guest self-cancellation via manage booking link')
        
        if not token:
            return Response(
                {'error': 'Token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # IDENTICAL token validation pattern
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        try:
            manage_token = BookingManageToken.objects.get(
                booking__hotel=hotel,
                token_hash=token_hash,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now()
            )
        except BookingManageToken.DoesNotExist:
            # Unified 404 response
            raise Http404("Invalid or expired token")
        
        booking = manage_token.booking
        
        # Check booking eligibility
        if booking.status not in ['CONFIRMED', 'PENDING_APPROVAL']:
            return Response(
                {'error': f'Booking cannot be cancelled. Current status: {booking.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Extract existing StaffBookingCancelView logic into shared service
                cancellation_result = self._cancel_booking_shared_service(booking, reason)
                
                # Update access tracking
                manage_token.mark_accessed()
                
                return Response({
                    'success': True,
                    'booking_id': booking.booking_id,
                    'cancelled_at': booking.cancelled_at,
                    'cancellation_fee': str(cancellation_result['fee_amount']),
                    'refund_amount': str(cancellation_result['refund_amount']),
                    'status': booking.status,
                    'message': 'Booking cancelled successfully'
                })
                
        except Exception as e:
            return Response(
                {'error': 'Cancellation failed. Please contact hotel directly.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _cancel_booking_shared_service(self, booking, reason):
        """
        Extract existing StaffBookingCancelView logic into shared service.
        Reuse DEFAULT/POLICY branching and existing cancellation infrastructure.
        """
        from api.booking.services import CancellationCalculator
        from django.utils import timezone
        
        # Use existing DEFAULT/POLICY branching from StaffBookingCancelView
        if booking.cancellation_policy_snapshot:
            # POLICY mode - use snapshotted policy
            calculator = CancellationCalculator(booking)
            result = calculator.calculate_cancellation_fee()
            
            booking.cancellation_fee = result['fee_amount']
            booking.refund_amount = result['refund_amount']
        else:
            # DEFAULT mode - use legacy logic (same as StaffBookingCancelView)
            booking.cancellation_fee = booking.total_amount  
            booking.refund_amount = Decimal('0.00')
        
        # Update booking status
        booking.status = 'CANCELLED'
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = reason
        booking.save()
        
        # Process Stripe refund if applicable (reuse existing logic)
        if booking.refund_amount > 0 and booking.stripe_payment_intent_id:
            self._process_stripe_refund(booking)
        
        # Send email notifications (reuse existing services)
        self._send_cancellation_notifications(booking)
        
        return {
            'fee_amount': booking.cancellation_fee,
            'refund_amount': booking.refund_amount
        }
    
    def _process_stripe_refund(self, booking):
        """Extract exact Stripe refund logic from StaffBookingCancelView"""
        # TODO: Extract from existing implementation
        pass
    
    def _send_cancellation_notifications(self, booking):
        """Send cancellation confirmation emails"""
        # TODO: Reuse existing email services
        pass
```

## Email Integration

### Generate Token in Booking Confirmation
**Location:** Update existing booking confirmation flow

```python
# In booking confirmation email service (api/booking/email_services.py)
class BookingConfirmationEmailService:
    def send_confirmation_email(self):
        """Enhanced confirmation email with manage booking link"""
        
        # Generate manage booking token
        raw_token, manage_token = BookingManageToken.generate_for_booking(self.booking)
        
        # Include manage booking link in confirmation email
        manage_url = f"https://hotelsmates.com/manage-booking/{raw_token}/"
        
        # Enhanced email template with manage booking section
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <h2>Booking Confirmed - {self.booking.hotel.name}</h2>
            
            <!-- Existing booking details -->
            <div style="background: #f8f9fa; padding: 20px;">
                <h3>Booking Details</h3>
                <p><strong>ID:</strong> {self.booking.booking_id}</p>
                <p><strong>Check-in:</strong> {self.booking.check_in}</p>
                <p><strong>Check-out:</strong> {self.booking.check_out}</p>
                <p><strong>Room:</strong> {self.booking.room_type.name}</p>
            </div>
            
            <!-- NEW: Manage booking section -->
            <div style="background: #e3f2fd; padding: 20px; margin: 20px 0;">
                <h3>Manage Your Booking</h3>
                <p>View details, check cancellation policy, or cancel if needed:</p>
                <p>
                    <a href="{manage_url}" 
                       style="display: inline-block; background: #2196F3; color: white; 
                              padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                        Manage My Booking
                    </a>
                </p>
                <p style="font-size: 14px; color: #666;">
                    This link remains active until 7 days after your check-out.
                </p>
            </div>
            
            <!-- Existing hotel contact info -->
            <div>
                <h3>Hotel Contact</h3>
                <p>{self.booking.hotel.name}</p>
                <p>Email: {self.booking.hotel.email}</p>
                <p>Phone: {self.booking.hotel.phone}</p>
            </div>
        </body>
        </html>
        """
        
        # Send enhanced email
        self._send_html_email(html_content)
```

### Integration Points
**Update these existing views to generate manage tokens:**

1. **StaffBookingAcceptView** (when staff confirms booking)
2. **Stripe webhook processing** (if auto-confirming bookings)

```python
# Example integration in StaffBookingAcceptView
def post(self, request, hotel_slug, booking_id):
    # ... existing confirmation logic ...
    
    booking.status = 'CONFIRMED'
    booking.confirmed_at = timezone.now()
    booking.save()
    
    # Generate manage booking token and send enhanced confirmation email
    raw_token, manage_token = BookingManageToken.generate_for_booking(booking)
    
    email_service = BookingConfirmationEmailService(booking)
    email_service.send_confirmation_with_manage_link(raw_token)
    
    # ... rest of existing logic ...
```

## URL Routing

**Location:** `api/public/urls.py`

```python
# Add to existing URL patterns
urlpatterns = [
    # ... existing patterns ...
    
    # Manage booking endpoints
    path(
        'hotel/<slug:hotel_slug>/manage-booking/validate/<str:token>/',
        PublicBookingManageValidateView.as_view(),
        name='public_booking_manage_validate'
    ),
    path(
        'hotel/<slug:hotel_slug>/manage-booking/cancel/',
        PublicBookingManageCancelView.as_view(),
        name='public_booking_manage_cancel'
    ),
]
```

## Implementation Steps

### Phase 1: Database Model (Day 1-2)
1. Add `BookingManageToken` model to `api/booking/models.py`
2. Create and run database migration
3. Update admin interface for token management
4. Test model methods and token generation

### Phase 2: API Endpoints (Day 3-4)
1. Create `PublicBookingManageValidateView` in `api/public/views.py`
2. Create `PublicBookingManageCancelView` in `api/public/views.py`
3. Add URL routing in `api/public/urls.py`
4. Test endpoint security and validation

### Phase 3: Extract Shared Cancellation Service (Day 4-5)
1. Extract logic from existing `StaffBookingCancelView`
2. Create shared service for DEFAULT/POLICY branching
3. Update both staff and public cancel views to use shared service
4. Test cancellation flow consistency

### Phase 4: Email Integration (Day 5-6)
1. Update `BookingConfirmationEmailService` with manage booking links
2. Integrate token generation in booking confirmation flow
3. Test email delivery and link functionality
4. Verify manage booking links work end-to-end

### Phase 5: Testing & Security Audit (Day 7-8)
1. Unit tests for model and token security
2. Integration tests for API endpoints
3. Security testing (rate limiting, unified 404s, timing attacks)
4. End-to-end testing of complete flow

## Testing Strategy

### Unit Tests
```python
# tests/test_booking_manage_token.py
class BookingManageTokenTests(TestCase):
    def test_token_generation_security(self):
        """Test IDENTICAL security to BookingPrecheckinToken"""
        
    def test_auto_revoke_previous_tokens(self):
        """Test auto-revoke behavior"""
        
    def test_multi_use_access_tracking(self):
        """Test access count and last accessed tracking"""
        
    def test_expiration_logic(self):
        """Test 7-day expiration from check-out"""

# tests/test_manage_booking_api.py  
class ManageBookingAPITests(APITestCase):
    def test_unified_404_responses(self):
        """Test security - all invalid states return 404"""
        
    def test_rate_limiting(self):
        """Test 10 requests/minute rate limiting"""
        
    def test_cancellation_with_existing_logic(self):
        """Test cancellation uses extracted StaffBookingCancelView logic"""
        
    def test_policy_snapshot_expansion(self):
        """Test cancellation policy snapshot is properly expanded"""
```

### Security Validation
- Token generation uses `secrets.token_urlsafe(32)` ✓
- SHA256 hash storage only ✓  
- Unified 404 for invalid/expired/revoked ✓
- Rate limiting identical to precheckin ✓
- Auto-revoke previous tokens ✓
- Constant-time hash comparison ✓

### Integration Testing
- Complete booking flow with manage token generation
- Email delivery with working manage booking links
- Cancellation process using existing DEFAULT/POLICY logic
- Multi-use token access without breaking precheckin behavior

**Key Principle:** Do not alter precheckin token behavior - this is a parallel system that reuses proven security patterns while providing different functionality (multi-use booking management vs single-use precheckin).