# Guest Cancellation Audit Report

## Executive Summary

This audit examines the current implementation of guest booking cancellation in the HotelMate backend to understand how the "Cancel booking" button should be connected to a real backend cancellation flow.

## Current Implementation Analysis

### 1. Guest Link Routes and Token Usage

#### A) BookingManagementToken System
**Model**: [hotel/models.py](hotel/models.py#L2053-L2131) - `BookingManagementToken`
**Key Fields**:
- `token_hash` - SHA256 hash of raw token
- `expires_at` - Token expiry timestamp  
- `used_at` - When token was used for cancellation
- `actions_performed` - JSON list of actions (view, cancel, etc.)

#### B) Current Guest Booking URLs
**Format**: `https://hotelsmates.com/booking/status/{hotel_slug}/{booking_id}?token=XYZ`

**Public API Endpoints** ([public_urls.py](public_urls.py#L100-L122)):
- `GET /api/public/hotels/{hotel_slug}/booking/status/{booking_id}/?token={token}` - BookingStatusView
- `POST /api/public/booking/cancel/` - CancelBookingView  
- `GET /api/public/booking/validate-token/` - ValidateBookingManagementTokenView

### 2. Existing Public Endpoints Analysis

#### A) BookingStatusView ([hotel/public_views.py](hotel/public_views.py#L1133-L1371))
**GET Method**: Returns booking details with mandatory token validation
- Validates token via SHA256 hash lookup
- Shows cancellation preview with fees if `can_cancel = True` 
- Uses `CancellationCalculator` to preview fees
- Records 'VIEW' action on token

**POST Method**: Processes booking cancellation  
- Same token validation as GET
- Checks booking status in `['CONFIRMED', 'PENDING_PAYMENT']`
- Calculates cancellation fees via `CancellationCalculator`
- Updates booking atomically:
  - `status = 'CANCELLED'`
  - `cancelled_at = timezone.now()`
  - `cancellation_fee` and `refund_amount` from calculator
- Marks token as used

#### B) CancelBookingView ([hotel/public_views.py](hotel/public_views.py#L1030-L1128))
**Separate endpoint with similar logic to BookingStatusView.post()**
- Uses same token validation pattern
- Same atomic cancellation logic
- Records 'CANCEL' action on token

#### C) ValidateBookingManagementTokenView ([hotel/public_views.py](hotel/public_views.py#L916-L1028))
- Validates token and returns booking summary
- Same structure as BookingStatusView.get() but different URL pattern

### 3. Existing Staff Cancellation Endpoints

#### A) StaffBookingCancelView ([hotel/staff_views.py](hotel/staff_views.py#L1220-L1342))
**Current Limitations**: 
- **BLOCKS Stripe bookings** - redirects to approve/decline endpoints
- Only handles traditional bookings without Stripe integration
- No refund processing capability
- Status change: Any valid status → `CANCELLED`

#### B) StaffBookingDeclineView ([hotel/staff_views.py](hotel/staff_views.py#L3038-L3173))
**Stripe Authorization Cancellation**:
- Only handles `PENDING_APPROVAL` status bookings
- Cancels Stripe authorization via `stripe.PaymentIntent.cancel()`
- Status change: `PENDING_APPROVAL` → `DECLINED`
- No refund needed (authorization never captured)

#### C) Missing: Post-Confirmation Cancellation Endpoint
**Gap Identified**: No staff endpoint exists for cancelling `CONFIRMED` bookings with Stripe refund processing.

### 4. Current Booking Payment States

#### A) Payment Status Progression
```
PENDING_PAYMENT → PENDING_APPROVAL → CONFIRMED/DECLINED
                                    ↓
                                 CANCELLED (guest/staff)
```

#### B) Key Database Fields ([hotel/models.py](hotel/models.py#L584-L730))
**Payment Tracking**:
- `payment_provider` - "stripe", "paypal", etc.
- `payment_reference` - Checkout session ID 
- `payment_intent_id` - Stripe PaymentIntent ID for auth/capture
- `paid_at` - When payment was **captured** (not authorized)
- `payment_authorized_at` - When authorization hold was created

**Authorization vs Capture**:
- `PENDING_APPROVAL`: `payment_authorized_at != null`, `paid_at == null`
- `CONFIRMED`: `payment_authorized_at != null`, `paid_at != null`
- `DECLINED`: `payment_authorized_at != null`, `paid_at == null`

#### C) Stripe Integration Points
**Authorization** ([hotel/payment_views.py](hotel/payment_views.py#L424-L460)):
- Webhook sets `payment_authorized_at` and `PENDING_APPROVAL`
- Uses `capture_method: 'manual'` in Stripe sessions

**Capture** ([hotel/staff_views.py](hotel/staff_views.py#L2905-L2978)):
- Staff accept calls `stripe.PaymentIntent.capture()`
- Sets `paid_at` and `CONFIRMED` status

**Void/Cancel** ([hotel/staff_views.py](hotel/staff_views.py#L3088-L3124)):
- Staff decline calls `stripe.PaymentIntent.cancel()`
- Sets `DECLINED` status, no `paid_at`

### 5. What "Cancel" Means Today

#### A) Current Cancellation Scenarios

**Scenario 1: Pre-Authorization Cancellation**
- Status: `PENDING_PAYMENT` 
- Action: Simple status update to `CANCELLED`
- Payment: No Stripe interaction needed

**Scenario 2: Authorization Void**  
- Status: `PENDING_APPROVAL`
- Action: `stripe.PaymentIntent.cancel()` + status to `DECLINED`
- Payment: Authorization hold released

**Scenario 3: Post-Capture Refund**
- Status: `CONFIRMED` 
- Action: **NOT IMPLEMENTED** - No refund processing exists
- Payment: Would require `stripe.Refund.create()`

#### B) Guest Cancellation Capabilities
**Current Guest Powers**:
- Can cancel `CONFIRMED` and `PENDING_PAYMENT` bookings 
- Uses `CancellationCalculator` for fee calculation
- **Gap**: No actual Stripe refund processing in guest flow

#### C) Cancellation Fee Logic
**CancellationCalculator** ([hotel/services/cancellation.py](hotel/services/cancellation.py) - referenced but implementation not audited):
- Calculates `fee_amount` and `refund_amount`
- Based on cancellation policies (time-based rules)
- Used by both guest and staff flows

## Key Findings

### ✅ What's Working
1. **Token Security**: Robust SHA256-based token system with expiration
2. **Guest UI Integration**: Booking status page with cancellation preview  
3. **Authorization Handling**: Staff decline properly voids Stripe authorizations
4. **Fee Calculation**: `CancellationCalculator` provides preview and actual fees

### ❌ Critical Gaps
1. **No Stripe Refund Processing**: Guest cancellation updates database but doesn't process refunds
2. **Staff Refund Gap**: No staff endpoint for post-confirmation cancellations with refunds
3. **Payment State Mismatch**: Guest can cancel `CONFIRMED` bookings but payment remains captured

### ⚠️ Potential Issues
1. **Inconsistent Guest Cancellation**: Two endpoints (`BookingStatusView.post()` and `CancelBookingView`) with similar logic
2. **Token Action Tracking**: Actions recorded but not consistently used for business logic
3. **Email Integration**: Cancellation emails triggered but refund details may be misleading

## Implementation Recommendations

### Priority 1: Stripe Refund Integration
Add Stripe refund processing to guest cancellation flow:
```python
# In BookingStatusView.post() and CancelBookingView.post()
if booking.status == 'CONFIRMED' and booking.payment_intent_id:
    refund_amount = cancellation_result['refund_amount']
    if refund_amount > 0:
        stripe.Refund.create(
            payment_intent=booking.payment_intent_id,
            amount=int(refund_amount * 100)  # Convert to cents
        )
```

### Priority 2: Staff Post-Confirmation Cancellation
Create new staff endpoint for cancelling `CONFIRMED` bookings with refunds:
```python
class StaffBookingRefundView(APIView):
    """Cancel CONFIRMED booking with Stripe refund processing"""
    # Similar to StaffBookingDeclineView but for captured payments
```

### Priority 3: Consolidate Guest Endpoints  
**Recommendation**: Use `BookingStatusView` for both GET and POST, deprecate `CancelBookingView`
- Reduces code duplication
- Maintains URL consistency with booking status page

### Priority 4: Enhanced Error Handling
- Add Stripe error handling for refund failures
- Implement partial refund scenarios  
- Add idempotency for refund operations

## Current Flow Diagram

```mermaid
graph TD
    A[Guest clicks cancel button] --> B[Frontend calls BookingStatusView.post()]
    B --> C{Token Valid?}
    C -->|No| D[403 Forbidden]
    C -->|Yes| E{Booking Status?}
    E -->|PENDING_PAYMENT| F[Simple cancellation]
    E -->|CONFIRMED| G[Calculate fees]
    G --> H[Update DB: CANCELLED]
    H --> I[❌ NO STRIPE REFUND]
    F --> H
    I --> J[Return success response]
```

## Proposed Enhanced Flow

```mermaid
graph TD
    A[Guest clicks cancel button] --> B[Frontend calls BookingStatusView.post()]
    B --> C{Token Valid?}
    C -->|No| D[403 Forbidden] 
    C -->|Yes| E{Booking Status?}
    E -->|PENDING_PAYMENT| F[Simple cancellation]
    E -->|CONFIRMED| G[Calculate fees]
    G --> H{Refund Amount > 0?}
    H -->|Yes| I[Process Stripe Refund]
    H -->|No| J[Update DB: CANCELLED]
    I --> K{Refund Success?}
    K -->|Yes| J
    K -->|No| L[Return error]
    F --> J
    J --> M[Send confirmation email]
```

## Next Steps

1. **Audit CancellationCalculator** - Review fee calculation logic
2. **Test Current Guest Flow** - Verify what happens with real Stripe bookings
3. **Implement Stripe Refund Logic** - Add to existing guest cancellation endpoints
4. **Create Staff Refund Endpoint** - Handle post-confirmation staff cancellations
5. **Update Email Templates** - Include accurate refund information
6. **Add Comprehensive Tests** - Cover all payment states and edge cases

---
*Audit completed: December 26, 2025*