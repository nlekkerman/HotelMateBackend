# Stripe-Safe Guest Cancellation Implementation Plan

**Created:** December 26, 2025  
**Status:** Planning Phase  
**Priority:** High - Financial Integrity Critical

## OVERVIEW

Implement financially-correct guest cancellation system that properly handles Stripe authorization voids and refunds while maintaining idempotency and supporting all cancellation policies through existing CancellationCalculator.

### CURRENT STATE PROBLEMS
- BookingStatusView (POST) updates DB but does NOT call Stripe for void/refund → financial desync
- Duplicate CancelBookingView with similar logic
- Missing idempotency protection for Stripe operations
- No proper handling of authorized vs captured payments

### FINANCIAL REQUIREMENTS
- **PENDING_APPROVAL** (authorized only): Void PaymentIntent via `stripe.PaymentIntent.cancel()`
- **CONFIRMED** (captured): Refund correct amount via `stripe.Refund.create()`
- **No Stripe/Pending**: DB-only cancellation
- **Idempotent**: No double-refunds, safe retry behavior

---

## IMPLEMENTATION TASKS

### 1. SHARED SERVICE CREATION

**File:** `hotel/services/guest_cancellation.py`

#### Core Function Signature
```python
def cancel_booking_with_token(*, booking, token_obj, reason="Guest cancellation via management link") -> dict:
```

#### Validation Rules
- **Allow cancellation ONLY if:** `booking.status in ["PENDING_PAYMENT", "PENDING_APPROVAL", "CONFIRMED"]`
- **Block if:** `booking.status in ["CANCELLED", "DECLINED", "COMPLETED"]` OR `booking.cancelled_at` is set
- **Idempotent behavior:** If already cancelled, return success response (do NOT error)

#### Cancellation Calculation
- **ALWAYS** recalculate using `CancellationCalculator(booking).calculate()` inside service
- **NEVER** trust preview amounts from GET requests
- Use calculated `fee_amount` and `refund_amount` for all operations

#### Database Updates
```python
# Booking fields
booking.status = "CANCELLED"
booking.cancelled_at = timezone.now()
booking.cancellation_reason = reason
booking.cancellation_fee = result["fee_amount"]
booking.refund_amount = result["refund_amount"]

# Token management  
token_obj.record_action("CANCEL")
token_obj.used_at = timezone.now()
```

#### Return Structure
```python
{
    "fee_amount": Decimal,
    "refund_amount": Decimal, 
    "description": str,
    "applied_rule": str,  # if available
    "refund_reference": str,  # if refund created
    "cancelled_at": str  # ISO format
}
```

### 2. STRIPE INTEGRATION LOGIC

#### Conditions for Stripe Operations
- **ONLY when:** `booking.payment_provider == "stripe"` AND `booking.payment_intent_id` exists and is not empty
- **Safe fallback:** If `payment_intent_id` is missing/empty, treat as non-Stripe (DB-only cancellation allowed)

#### Payment State Handling

**A) PENDING_APPROVAL (Authorization Void)**
```python
if booking.status == "PENDING_APPROVAL" and booking.paid_at is None:
    stripe.PaymentIntent.cancel(
        booking.payment_intent_id, 
        cancellation_reason="requested_by_customer"
    )
    # No refund object created - this is a void
```

**B) CONFIRMED (Captured Refund)**  
```python
if booking.status == "CONFIRMED" and booking.paid_at is not None:
    refund_amount = result["refund_amount"]
    if refund_amount > 0:
        # Call Stripe refund with idempotency protection
        refund = stripe.Refund.create(
            payment_intent=booking.payment_intent_id,
            amount=int(Decimal(refund_amount) * 100),  # Convert to cents
            idempotency_key=f"guest_cancel_refund:{booking.booking_id}"
        )
        # Update DB fields after successful Stripe operation
        booking.refund_reference = refund.id
        booking.refund_processed_at = timezone.now()
    # If refund_amount == 0: DB cancel only, no Stripe call
```

#### Non-Stripe Payments
- **If** `booking.payment_provider != "stripe"`: Skip all Stripe operations

### 3. IDEMPOTENCY & TRANSACTION SAFETY

#### Refund Protection
- **Guard:** If `booking.refund_processed_at` is already set, do NOT call `stripe.Refund.create()` again
- **Idempotency Key:** `f"guest_cancel_refund:{booking.booking_id}"`

#### Transaction Management
- **Wrap in:** `transaction.atomic()` to prevent partial DB commits on Stripe failures
- **Operation Order:** Call Stripe operations FIRST, then update DB fields within same transaction
- **Stripe Failures:**
  - Log with `logger.exception()`
  - Return controlled error to view
  - Booking must NOT be marked CANCELLED if required Stripe operation failed

#### Stripe Idempotency
- **Use Stripe's idempotency mechanism** following your project's existing Stripe call patterns
- **Key format:** `f"guest_cancel_refund:{booking.booking_id}"` for refunds
- **Implementation:** May vary by Stripe library version - use your existing Stripe wrapper style

#### Decimal Safety
- **Use:** `Decimal` type throughout, never `float` for monetary calculations
- **Quantize** as needed for cent precision
- **Conversion:** `int(Decimal(amount) * 100)` for Stripe cents

### 4. ENDPOINT REFACTORING

#### BookingStatusView.post Updates

**Token Acceptance:**
- Accept token from `request.data["token"]` OR `request.query_params["token"]` (support both)

**Validation Flow:**
- **Views retain full responsibility** for hotel + booking + token validation
- Keep existing validation logic unchanged (hotel slug, booking exists, token.is_valid)
- **Service assumption:** Receives pre-validated booking and token objects
- Then call `cancel_booking_with_token(...)`

**Response Format:**
```json
{
  "success": true,
  "message": "Booking cancelled successfully",
  "cancellation": {
    "cancelled_at": "2025-12-26T10:30:00Z",
    "cancellation_fee": "50.00",
    "refund_amount": "450.00", 
    "description": "Cancellation with 10% fee",
    "refund_reference": "re_1ABC123def456"
  }
}
```

**Error Handling:**
- **Already cancelled:** Return 200 with same success structure
- **Stripe error:** Return 502 with safe message (no Stripe details leaked)
- **Token validation errors:** Views handle these BEFORE calling service
  - Invalid token: 403 response (existing behavior)
  - Missing token: 401 response (existing behavior)
  - Expired token: 403 response (existing behavior)

#### CancelBookingView.post Decision
**Recommended Approach:** Keep both endpoints calling the same service (no breaking changes)
- **Short-term:** Both endpoints use `cancel_booking_with_token()` service
- **Long-term:** Deprecate CancelBookingView in favor of BookingStatusView
- **Response consistency:** Both must return identical JSON structure

**Alternative:** Return 410 Gone immediately (breaking change - requires frontend updates)

### 5. MODEL CHANGES

#### Required Fields Check
Ensure `RoomBooking` model has:
```python
refund_processed_at = models.DateTimeField(null=True, blank=True)
refund_reference = models.CharField(max_length=255, blank=True, default="")
```

#### Migration Creation
- Create migration if `refund_reference` field missing
- Verify `refund_processed_at` exists from previous implementations

### 6. TESTING REQUIREMENTS

#### Test Categories (pytest or Django TestCase)

**A) CONFIRMED Stripe Booking Cancellation**
- Mock `stripe.Refund.create`
- Verify called once with correct idempotency key
- Ensure `refund_processed_at` guards against double-refund
- Confirm `booking.status = "CANCELLED"` and `refund_reference` stored

**B) PENDING_APPROVAL Stripe Booking Cancellation**  
- Mock `stripe.PaymentIntent.cancel`
- Verify called with correct parameters
- Confirm booking marked CANCELLED (no refund objects)

**C) Token Validation**
- Invalid token: 403 response maintained
- Missing token: 401 response maintained
- Used token: Appropriate error handling

**D) Idempotency**
- Second cancellation attempt returns success (no error)
- No duplicate Stripe calls on retry

---

## CONSTRAINTS & REQUIREMENTS

### UNCHANGED BEHAVIOR
- **GET Response:** Keep current shape (optional: allow `can_cancel` for PENDING_APPROVAL)
- **Hotel Scoping:** Maintain hotel_slug validation
- **Token Validation:** Keep existing validation logic
- **Error Messages:** Safe messages only (no Stripe details to users)

### FINANCIAL INTEGRITY
- **Never trust frontend amounts** - always recalculate server-side
- **Support all cancellation policies** via CancellationCalculator automatically
- **Atomic operations** - DB and Stripe must stay in sync
- **Idempotent by design** - safe for retries and network issues

### SECURITY
- Maintain token-based authorization model
- Log failures but don't expose internal errors
- Validate hotel context for all operations

---

## DELIVERABLES CHECKLIST

- [ ] `hotel/services/guest_cancellation.py` - Shared service implementation
- [ ] Updated `BookingStatusView.post` to use service
- [ ] Updated `CancelBookingView.post` to use service OR deprecate  
- [ ] Model field `refund_reference` + migration if needed
- [ ] Comprehensive test suite covering all scenarios
- [ ] Documentation updates for API consumers

---

## IMPLEMENTATION NOTES

### Phase Approach
1. **Phase 1:** Create service + model changes + tests
2. **Phase 2:** Refactor BookingStatusView to use service  
3. **Phase 3:** Handle CancelBookingView (deprecate or refactor)
4. **Phase 4:** End-to-end testing with Stripe test environment

### Risk Mitigation
- Test thoroughly in Stripe test mode before production
- Monitor refund operations for any edge cases
- Have rollback plan for DB schema changes
- Consider feature flag for gradual rollout

### Success Criteria
- All guest cancellations properly void/refund in Stripe
- No financial discrepancies between DB and Stripe
- Idempotent behavior confirmed under retry scenarios
- All existing cancellation policies continue working
- Performance impact negligible (service calls are atomic)