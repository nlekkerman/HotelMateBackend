# PHASE: Stripe Authorize-Capture + DB Idempotency - Source of Truth

## Purpose & Scope

Transform HotelMate's payment flow from immediate capture to authorize-then-capture, where guest payments create authorization holds that require staff approval before funds are captured.

**Key Changes:**
- Stripe Checkout uses manual capture (`capture_method: "manual"`)
- 🚨 **CRITICAL**: Webhook sets `PENDING_APPROVAL` + `payment_authorized_at` (NOT `paid_at` or `CONFIRMED`)
- Staff endpoints provide Accept (capture) and Decline (cancel authorization) operations
- 🚨 **CRITICAL**: Staff endpoints must be hotel-scoped in URL: `/api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/accept|decline/`
- Replace cache-only webhook idempotency with durable DB-backed system
- Multi-hotel safe: all operations scoped by `Hotel.slug`

## State Machine & Invariants

### Booking Status Definitions

```
PENDING_PAYMENT    → Guest has not started or completed checkout
PENDING_APPROVAL   → Payment authorized, awaiting staff decision  
CONFIRMED          → Payment captured, booking accepted
DECLINED           → Authorization cancelled, booking denied
CANCELLED          → Guest cancelled before payment/authorization
EXPIRED            → Authorization expired (optional, future enhancement)
```

### Status Invariants (CRITICAL)

```python
# HARD INVARIANTS - Must be enforced in code
status == CONFIRMED      ⟹ paid_at != null AND payment_authorized_at != null
status == PENDING_APPROVAL ⟹ payment_authorized_at != null AND paid_at == null  
status == DECLINED       ⟹ payment_authorized_at != null AND paid_at == null
status == PENDING_PAYMENT ⟹ payment_authorized_at == null AND paid_at == null

# STRIPE CONSISTENCY  
payment_intent_id != null ⟹ payment_authorized_at != null
paid_at != null ⟹ payment_intent_id != null
```

### State Transitions

```
PENDING_PAYMENT → PENDING_APPROVAL  (webhook: checkout.session.completed + requires_capture)
PENDING_PAYMENT → CANCELLED         (guest cancels checkout)
PENDING_APPROVAL → CONFIRMED        (staff accepts → Stripe capture)  
PENDING_APPROVAL → DECLINED         (staff declines → Stripe cancel)
PENDING_APPROVAL → EXPIRED          (authorization timeout, future)
```

## DB Schema Changes

### RoomBooking Model Additions

```python
class RoomBooking(models.Model):
    # Existing fields: booking_id, confirmation_number, hotel, etc.
    
    # PAYMENT FIELDS (existing)
    payment_reference = models.CharField(max_length=200, blank=True)  # session_id
    payment_provider = models.CharField(max_length=50, blank=True)    # "stripe"  
    paid_at = models.DateTimeField(null=True, blank=True)             # capture timestamp
    
    # NEW AUTHORIZATION FIELDS
    payment_intent_id = models.CharField(
        max_length=200, blank=True, null=True, db_index=True,
        help_text="Stripe PaymentIntent ID for authorization/capture"
    )
    payment_authorized_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When payment was authorized (hold created)"
    )
    
    # STATUS FIELD (enhanced)
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('PENDING_APPROVAL', 'Pending Staff Approval'),  # NEW
        ('CONFIRMED', 'Confirmed'),
        ('DECLINED', 'Declined'),                         # NEW  
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    
    # STAFF DECISION TRACKING (NEW)
    decision_by = models.ForeignKey(
        'staff.StaffMember', null=True, blank=True, 
        on_delete=models.SET_NULL, related_name='booking_decisions'
    )
    decision_at = models.DateTimeField(null=True, blank=True)
    decline_reason_code = models.CharField(max_length=50, blank=True)
    decline_reason_note = models.TextField(blank=True)
```

### StripeWebhookEvent Model (NEW)

```python
class StripeWebhookEvent(models.Model):
    """DB-backed webhook idempotency and debugging"""
    
    event_id = models.CharField(max_length=255, unique=True, primary_key=True)
    event_type = models.CharField(max_length=100)
    
    # STRIPE IDENTIFIERS
    checkout_session_id = models.CharField(max_length=200, blank=True)  
    payment_intent_id = models.CharField(max_length=200, blank=True)
    
    # BOOKING CONTEXT
    booking_id = models.CharField(max_length=50, blank=True)  # BK-2025-XXXX
    hotel_slug = models.CharField(max_length=100, blank=True)
    
    # PROCESSING STATUS
    STATUS_CHOICES = [
        ('PROCESSED', 'Successfully Processed'),
        ('FAILED', 'Processing Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSED')
    error_message = models.TextField(blank=True)
    
    # TIMESTAMPS
    processed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stripe_webhook_events'
        indexes = [
            models.Index(fields=['booking_id', 'hotel_slug']),
            models.Index(fields=['checkout_session_id']),
            models.Index(fields=['payment_intent_id']),
            models.Index(fields=['processed_at']),
        ]
```

## Stripe Integration Rules

### Payment Session Creation (`CreatePaymentSessionView`)

```python
# MANUAL CAPTURE CONFIGURATION
session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=line_items,
    mode='payment',
    
    # 🔑 KEY CHANGE: Manual capture
    payment_intent_data={
        "capture_method": "manual",
        "description": f"Hotel booking {booking_id} - {hotel_name}"
    },
    
    success_url=success_url,
    cancel_url=cancel_url,
    customer_email=guest_email,
    
    metadata={
        'booking_id': booking_id,
        'hotel_slug': hotel_slug,
        'guest_email': guest_email,
        'total_amount': str(total_amount),
        'currency': currency,
    }
)

# IDEMPOTENCY: Stable key (no date rotation)
idempotency_key = f"booking-{booking_id}-{guest_email}-{total_amount}-{currency}"
```

### What We Store During Session Creation

```python
# IMMEDIATE: Store session reference (existing pattern)
booking.payment_provider = "stripe"
booking.payment_reference = session.id
booking.save(update_fields=['payment_provider', 'payment_reference'])

# DO NOT set payment_intent_id yet (comes from webhook)
# DO NOT change status from PENDING_PAYMENT (comes from webhook)
```

## Webhook Processing Contract

### 🚨 CRITICAL: Webhook Behavior Changes

**Before (Current):**
```python
# OLD: Immediate confirmation in webhook
booking.paid_at = timezone.now()
booking.status = 'CONFIRMED'
```

**After (New):**
```python
# NEW: Authorization only in webhook
booking.payment_authorized_at = timezone.now()  # NEW FIELD
booking.status = 'PENDING_APPROVAL'             # NEW STATUS
# DO NOT SET: paid_at (stays NULL until staff accept)
```

**Staff Accept Flow:**
```python
# Only staff accept sets these:
stripe.PaymentIntent.capture(payment_intent_id)  # Capture first
booking.paid_at = timezone.now()                 # Then set timestamp
booking.status = 'CONFIRMED'                     # Then confirm
```

### Webhook Idempotency (DB-Backed)

```python
def handle_stripe_webhook(request):
    event = stripe.Event.construct_from(json.loads(request.body), stripe.api_key)
    
    # 1. DB IDEMPOTENCY CHECK (before any processing)
    try:
        webhook_event = StripeWebhookEvent.objects.create(
            event_id=event['id'],
            event_type=event['type'],
            # ... populate other fields during processing
        )
    except IntegrityError:
        # Already processed - return success immediately  
        return JsonResponse({'status': 'already_processed'}, status=200)
    
    # 2. Process event (update webhook_event record on success/failure)
    try:
        if event['type'] == 'checkout.session.completed':
            process_checkout_completed(event, webhook_event)
        webhook_event.status = 'PROCESSED'
    except Exception as e:
        webhook_event.status = 'FAILED'
        webhook_event.error_message = str(e)
        # ❗ CRITICAL: Still return 200 to prevent Stripe retry storms
    finally:
        webhook_event.save()
    
    return JsonResponse({'status': 'success'}, status=200)
```

### Checkout Session Completed Processing

```python
def process_checkout_completed(event, webhook_event):
    session = event['data']['object']
    
    # EXTRACT METADATA
    booking_id = session['metadata']['booking_id'] 
    hotel_slug = session['metadata']['hotel_slug']
    payment_intent_id = session.get('payment_intent')
    
    # UPDATE WEBHOOK EVENT RECORD
    webhook_event.checkout_session_id = session['id']
    webhook_event.payment_intent_id = payment_intent_id
    webhook_event.booking_id = booking_id
    webhook_event.hotel_slug = hotel_slug
    
    # PAYMENT STATE VALIDATION (CRITICAL)
    if session['payment_status'] != 'paid':
        raise ValueError(f"Unexpected payment_status: {session['payment_status']}")
    
    if payment_intent_id:
        # Verify PaymentIntent is actually requires_capture
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if payment_intent['status'] != 'requires_capture':
            raise ValueError(
                f"Expected requires_capture, got {payment_intent['status']}. "
                f"Check manual capture configuration!"
            )
    
    # ATOMIC BOOKING UPDATE
    with transaction.atomic():
        booking = RoomBooking.objects.select_for_update().get(
            booking_id=booking_id,
            hotel__slug=hotel_slug
        )
        
        # UPDATE TO AUTHORIZATION STATE
        booking.payment_provider = 'stripe'
        booking.payment_intent_id = payment_intent_id  
        booking.payment_reference = payment_intent_id or session['id']
        booking.payment_authorized_at = timezone.now()
        booking.status = 'PENDING_APPROVAL'  # NOT CONFIRMED!
        
        # DO NOT SET paid_at (only set during capture)
        
        booking.save(update_fields=[
            'payment_provider', 'payment_intent_id', 'payment_reference',
            'payment_authorized_at', 'status'
        ])
    
    # SEND AUTHORIZATION EMAIL (not confirmation)
    send_payment_authorized_email(booking)
```

## Staff Accept/Decline Endpoint Contracts

### URL Patterns

```python
# staff_urls.py additions - MUST be hotel-scoped
urlpatterns = [
    # ... existing patterns
    
    # 🚨 CRITICAL: Hotel-scoped URLs (multi-tenant safety)
    path('room-bookings/<str:booking_id>/accept/', 
         StaffBookingAcceptView.as_view(), name='staff_booking_accept'),
    path('room-bookings/<str:booking_id>/decline/', 
         StaffBookingDeclineView.as_view(), name='staff_booking_decline'),
    
    # Full URL will be: /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/accept/
]
```

### Staff Accept (Capture) Endpoint

```python
class StaffBookingAcceptView(StaffRequiredMixin, View):
    """
    POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/accept/
    
    Captures authorized payment and confirms booking.
    """
    
    def post(self, request, hotel_slug, booking_id):
        # 🚨 CRITICAL: Multi-tenant safety - validate hotel first
        hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
        
        with transaction.atomic():
            # ATOMIC LOAD WITH LOCK (hotel-scoped)
            booking = get_object_or_404(
                RoomBooking.objects.select_for_update(),
                hotel=hotel,
                booking_id=booking_id
            )
            
            # VALIDATION
            if booking.status != 'PENDING_APPROVAL':
                return JsonResponse({
                    'error': f'Cannot accept booking with status {booking.status}'
                }, status=400)
                
            if not booking.payment_intent_id:
                return JsonResponse({
                    'error': 'No payment intent found for capture'
                }, status=400)
            
            # STRIPE CAPTURE (must happen before DB update)
            try:
                captured_intent = stripe.PaymentIntent.capture(
                    booking.payment_intent_id
                )
            except stripe.StripeError as e:
                return JsonResponse({
                    'error': f'Stripe capture failed: {str(e)}'
                }, status=502)
            
            # UPDATE BOOKING TO CONFIRMED
            booking.status = 'CONFIRMED'
            booking.paid_at = timezone.now()
            booking.decision_by = request.user.staff_member
            booking.decision_at = timezone.now()
            
            booking.save(update_fields=[
                'status', 'paid_at', 'decision_by', 'decision_at'
            ])
        
        # TRIGGER POST-CONFIRMATION WORKFLOWS
        send_booking_confirmation_email(booking)
        trigger_precheckin_creation(booking)  # If applicable
        
        return JsonResponse({'status': 'accepted', 'booking_id': booking_id})
```

### Staff Decline (Cancel) Endpoint

```python
class StaffBookingDeclineView(StaffRequiredMixin, View):
    """
    POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/decline/
    
    Body: {"reason_code": "AVAILABILITY", "reason_note": "Room no longer available"}
    """
    
    def post(self, request, hotel_slug, booking_id):
        data = json.loads(request.body)
        reason_code = data.get('reason_code', '')
        reason_note = data.get('reason_note', '')
        
        # 🚨 CRITICAL: Multi-tenant safety - validate hotel first
        hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
        
        with transaction.atomic():
            # ATOMIC LOAD WITH LOCK (hotel-scoped)
            booking = get_object_or_404(
                RoomBooking.objects.select_for_update(),
                hotel=hotel,
                booking_id=booking_id
            )
            
            # VALIDATION
            if booking.status != 'PENDING_APPROVAL':
                return JsonResponse({
                    'error': f'Cannot decline booking with status {booking.status}'
                }, status=400)
            
            # STRIPE AUTHORIZATION CANCEL (release hold)
            if booking.payment_intent_id:
                try:
                    cancelled_intent = stripe.PaymentIntent.cancel(
                        booking.payment_intent_id
                    )
                except stripe.StripeError as e:
                    return JsonResponse({
                        'error': f'Stripe cancellation failed: {str(e)}'
                    }, status=502)
            
            # UPDATE BOOKING TO DECLINED
            booking.status = 'DECLINED'
            booking.decision_by = request.user.staff_member  
            booking.decision_at = timezone.now()
            booking.decline_reason_code = reason_code
            booking.decline_reason_note = reason_note
            
            booking.save(update_fields=[
                'status', 'decision_by', 'decision_at', 
                'decline_reason_code', 'decline_reason_note'
            ])
        
        # SEND DECLINE NOTIFICATION
        send_booking_declined_email(booking, reason_code, reason_note)
        
        return JsonResponse({'status': 'declined', 'booking_id': booking_id})
```

## Email Trigger Matrix

| Event | Recipient | Template | Content |
|-------|-----------|----------|---------|
| `checkout.session.completed` | Guest | `payment_authorized.html` | "Payment authorized - awaiting hotel confirmation" |  
| Staff Accept | Guest | `booking_confirmed.html` | "Booking confirmed - payment processed" |
| Staff Decline | Guest | `booking_declined.html` | "Booking declined - authorization released" + reason |
| Staff Accept | Hotel | `booking_accepted_staff.html` | Internal notification of acceptance |
| Staff Decline | Hotel | `booking_declined_staff.html` | Internal notification with reason |

### Email Content Rules

**Authorization Email (NOT confirmation):**
- MUST NOT say "payment complete" or "charged"  
- MUST say "authorized", "pending confirmation", "hold placed"
- Include estimated confirmation timeline

**Decline Email:**
- MUST mention authorization release
- Include human-readable decline reason
- Provide rebooking guidance if applicable

## Error Handling & Reconciliation Rules

### Webhook Error Handling

```python
# ALWAYS return 200 after signature verification
# Record failure in StripeWebhookEvent for debugging
# Never let booking lookup failures crash webhook processing

def handle_webhook_error(webhook_event, error):
    webhook_event.status = 'FAILED'
    webhook_event.error_message = str(error)[:1000]  # Truncate long errors
    webhook_event.save()
    
    # Optional: Alert via Slack/email for critical failures
    if 'booking not found' in str(error).lower():
        alert_booking_lookup_failure(webhook_event)
```

### Staff Operation Error Handling

```python
# Accept/Decline operations:
# - Stripe call fails → return 4xx/5xx, do NOT change DB
# - Stripe succeeds but DB fails → log reconciliation needed

def handle_stripe_db_mismatch(booking, stripe_action, db_error):
    """When Stripe succeeds but DB update fails"""
    PaymentReconciliationLog.objects.create(
        booking_id=booking.booking_id,
        stripe_action=stripe_action,  # 'capture' or 'cancel'
        stripe_status='success',
        db_error=str(db_error),
        needs_manual_review=True
    )
    # Alert ops team for manual resolution
```

### Partial Failure Recovery

- **Stripe capture succeeds, DB update fails**: Log for manual reconciliation
- **DB update succeeds, email fails**: Retry email via background task  
- **Webhook signature invalid**: Return 400 immediately
- **Booking not found in webhook**: Log as FAILED, return 200

## Test Matrix

### Webhook Idempotency Tests

```python
def test_webhook_idempotency():
    """Same event_id processed twice should only update booking once"""
    # Send identical webhook twice
    # Assert: booking updated once, second call returns 200 but no changes

def test_webhook_payment_state_validation():
    """Webhook should reject non-requires_capture PaymentIntents"""  
    # Mock PaymentIntent with status != 'requires_capture'
    # Assert: webhook fails gracefully, records error
```

### Authorization Flow Tests

```python  
def test_checkout_completed_creates_authorization():
    """Webhook sets PENDING_APPROVAL, not CONFIRMED"""
    # Send checkout.session.completed webhook
    # Assert: status=PENDING_APPROVAL, payment_authorized_at set, paid_at=null

def test_authorization_email_wording():
    """Authorization email must not claim payment is complete"""
    # Trigger authorization email
    # Assert: email contains 'authorized', not 'charged' or 'paid'
```

### Staff Operation Tests

```python
def test_staff_accept_captures_payment():
    """Accept endpoint captures Stripe payment and sets CONFIRMED"""
    # Create PENDING_APPROVAL booking
    # POST to accept endpoint
    # Assert: Stripe capture called, status=CONFIRMED, paid_at set

def test_staff_decline_cancels_authorization():
    """Decline endpoint cancels Stripe authorization""" 
    # Create PENDING_APPROVAL booking
    # POST to decline endpoint with reason
    # Assert: Stripe cancel called, status=DECLINED, reason stored

def test_staff_operations_are_atomic():
    """Stripe success + DB failure should not leave inconsistent state"""
    # Mock DB failure after Stripe success
    # Assert: Either both succeed or both fail (no partial state)

def test_concurrent_staff_decisions():
    """Two staff members cannot both accept/decline same booking"""
    # Simulate concurrent accept/decline requests
    # Assert: Only one succeeds, other gets validation error
```

### Multi-Hotel Scoping Tests

```python
def test_webhook_hotel_scoping():
    """Webhook only updates booking for correct hotel"""
    # Create bookings for different hotels
    # Send webhook with specific hotel_slug
    # Assert: Only correct hotel's booking updated

def test_staff_endpoint_hotel_scoping():
    """Staff can only accept/decline bookings for their hotel"""
    # Create booking for Hotel A
    # Try to accept via Hotel B staff endpoint  
    # Assert: 404 or permission denied
```

## Rollout Notes

### Handling Existing Paid Bookings

```sql
-- Existing CONFIRMED bookings should be left as-is
-- They have paid_at set, which satisfies invariants
-- No migration needed for existing data

-- Optional: Backfill payment_authorized_at for existing CONFIRMED bookings
UPDATE room_bookings 
SET payment_authorized_at = paid_at 
WHERE status = 'CONFIRMED' 
  AND paid_at IS NOT NULL 
  AND payment_authorized_at IS NULL;
```

### Feature Flag Considerations

```python
# Optional: Feature flag for gradual rollout
FEATURE_MANUAL_CAPTURE_ENABLED = getattr(settings, 'STRIPE_MANUAL_CAPTURE', True)

# In CreatePaymentSessionView:
payment_intent_data = {}
if FEATURE_MANUAL_CAPTURE_ENABLED:
    payment_intent_data['capture_method'] = 'manual'
```

### Monitoring & Alerts

- **Critical**: Alert when webhook receives non-`requires_capture` PaymentIntent
- **Important**: Daily report of bookings stuck in `PENDING_APPROVAL` > 24 hours  
- **Useful**: Dashboard showing authorization → capture conversion rates by hotel

---

## Implementation Checklist

- [ ] Create migration for RoomBooking fields + StripeWebhookEvent model
- [ ] Update CreatePaymentSessionView for manual capture
- [ ] Refactor StripeWebhookView for DB idempotency + authorization state  
- [ ] Implement StaffBookingAcceptView + StaffBookingDeclineView
- [ ] Add URL patterns for staff endpoints
- [ ] Update email templates + service for authorization/decline flows
- [ ] Write comprehensive test suite covering all scenarios
- [ ] Add monitoring/alerting for webhook validation failures
- [ ] Document staff workflow for hotel operations teams

**Status Invariant Validation**: Add model clean() method to enforce status↔timestamp invariants across all booking updates.

---

## 🚨 CRITICAL IMPLEMENTATION SUMMARY

**Webhook Flow (checkout.session.completed):**
```python
# ✅ DO: Set authorization state
booking.payment_intent_id = session.payment_intent
booking.payment_authorized_at = timezone.now()
booking.status = 'PENDING_APPROVAL'

# ❌ DO NOT: Set payment completion
# paid_at = NULL (leave unset)
# status != 'CONFIRMED' (must be PENDING_APPROVAL)
```

**Staff Accept Endpoint:**
```python
# URL: POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/accept/

# ✅ DO: Hotel-scoped loading
hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
booking = get_object_or_404(RoomBooking.objects.select_for_update(), 
                           hotel=hotel, booking_id=booking_id)

# ✅ DO: Stripe capture first, then DB update
stripe.PaymentIntent.capture(booking.payment_intent_id)
booking.paid_at = timezone.now()
booking.status = 'CONFIRMED'
```

**Staff Decline Endpoint:**
```python
# URL: POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/decline/

# ✅ DO: Hotel-scoped loading (same as accept)
hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
booking = get_object_or_404(RoomBooking.objects.select_for_update(),
                           hotel=hotel, booking_id=booking_id)

# ✅ DO: Stripe cancel first, then DB update
stripe.PaymentIntent.cancel(booking.payment_intent_id)
booking.status = 'DECLINED'
# paid_at remains NULL
```

**Multi-Tenant Safety:** All staff operations MUST validate hotel ownership before booking access.