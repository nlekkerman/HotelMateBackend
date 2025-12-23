# Booking Cancellation Policy Implementation Plan

## Overview
This document analyzes the current booking payment flow and provides implementation recommendations for a comprehensive cancellation policy system that integrates with the existing Stripe authorize-capture payment architecture.

## Current Booking Payment Flow Analysis

### Existing Payment States & Architecture
The HotelMate system currently uses a robust authorize-capture payment flow:

```
PENDING_PAYMENT → PENDING_APPROVAL → CONFIRMED/DECLINED
```

#### Key Components:
1. **Payment Session Creation** (`hotel/payment_views.py`)
   - Creates Stripe checkout with `capture_method: 'manual'`
   - No immediate charge, only authorization

2. **Payment Authorization** (Stripe Webhook)
   - Updates booking to `PENDING_APPROVAL` status
   - Stores `payment_intent_id` for later capture/cancellation

3. **Staff Decision** (`hotel/staff_views.py`)
   - **Accept**: Captures payment via `stripe.PaymentIntent.capture()`
   - **Decline**: Cancels authorization via `stripe.PaymentIntent.cancel()`

### Current Cancellation Mechanisms

#### 1. Staff Booking Cancel (`StaffBookingCancelView`)
**Location**: `hotel/staff_views.py:1199`
- **Scope**: Traditional bookings without Stripe integration
- **Limitation**: Blocks Stripe bookings (redirects to approve/decline)
- **Payment Handling**: None (no refund processing)

#### 2. Staff Booking Decline (`StaffBookingDeclineView`) 
**Location**: `hotel/staff_views.py:3053`
- **Scope**: Stripe authorized bookings only
- **Process**: Cancels payment authorization before capture
- **Status**: `PENDING_APPROVAL` → `DECLINED`

#### 3. Rate Plan Refund Flags (`rooms/models.py:295`)
- Basic `is_refundable` boolean on RatePlan model
- Not currently integrated into booking/cancellation logic

## Cancellation Policy Implementation Strategy

### 1. **Cancellation Policy Model Architecture**

#### Core Model: `CancellationPolicy`
```python
# Location: hotel/models.py (or new cancellation/models.py)

class CancellationPolicy(models.Model):
    """
    Flexible cancellation policy system supporting various rule types.
    """
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # "Standard", "Non-Refundable", "Flexible"
    code = models.CharField(max_length=30)   # "STD", "NRF", "FLEX"
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    
    # Policy Rules
    allow_free_cancellation = models.BooleanField(default=True)
    free_cancellation_hours = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Hours before check-in for free cancellation"
    )
    cancellation_fee_type = models.CharField(
        max_length=20,
        choices=[
            ('NONE', 'No Fee'),
            ('FIXED', 'Fixed Amount'),
            ('PERCENTAGE', 'Percentage of Total'),
            ('FIRST_NIGHT', 'First Night Charge'),
            ('FULL_AMOUNT', 'Full Amount (Non-Refundable)'),
        ],
        default='NONE'
    )
    cancellation_fee_amount = models.DecimalField(
        max_digits=10, decimal_places=2, 
        null=True, blank=True
    )
    cancellation_fee_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    
    # Advanced Rules
    no_show_fee_type = models.CharField(max_length=20, default='FULL_AMOUNT')
    modification_allowed = models.BooleanField(default=True)
    modification_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class CancellationPolicyTier(models.Model):
    """
    Time-based cancellation tiers (e.g., 48h=free, 24h=50%, <24h=full charge).
    """
    policy = models.ForeignKey(CancellationPolicy, on_delete=models.CASCADE)
    hours_before_checkin = models.PositiveIntegerField()
    fee_type = models.CharField(max_length=20, choices=CancellationPolicy.FEE_CHOICES)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
```

#### Integration with RoomBooking
```python
# Add to RoomBooking model (hotel/models.py:574)

class RoomBooking(models.Model):
    # ... existing fields ...
    
    cancellation_policy = models.ForeignKey(
        'hotel.CancellationPolicy',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="Cancellation policy at time of booking"
    )
    
    # Cancellation tracking
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=100, blank=True)
    cancellation_fee = models.DecimalField(
        max_digits=10, decimal_places=2, 
        null=True, blank=True
    )
    refund_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    refund_processed_at = models.DateTimeField(null=True, blank=True)
```

### 2. **Integration Points in Payment Flow**

#### A. During Booking Creation
**Location**: Booking serializer or creation view
```python
# When creating booking, assign cancellation policy
booking.cancellation_policy = hotel.get_default_cancellation_policy()
# OR based on rate plan selection
booking.cancellation_policy = rate_plan.cancellation_policy
```

#### B. Staff Cancellation Enhancement
**Current**: `StaffBookingCancelView` (hotel/staff_views.py:1199)
**Enhancement**: Add cancellation policy calculations

```python
def post(self, request, hotel_slug, booking_id):
    # ... existing validation ...
    
    # CALCULATE CANCELLATION FEES
    from .services.cancellation import CancellationCalculator
    
    calculator = CancellationCalculator(booking)
    cancellation_result = calculator.calculate_fees()
    
    # PROCESS PAYMENT REFUND (if applicable)
    if booking.status == 'CONFIRMED' and booking.payment_intent_id:
        refund_amount = cancellation_result['refund_amount']
        if refund_amount > 0:
            # Process partial/full refund via Stripe
            stripe.Refund.create(
                payment_intent=booking.payment_intent_id,
                amount=int(refund_amount * 100)  # Convert to cents
            )
    
    # UPDATE BOOKING STATUS
    booking.status = 'CANCELLED'
    booking.cancelled_at = timezone.now()
    booking.cancellation_fee = cancellation_result['fee_amount']
    booking.refund_amount = cancellation_result['refund_amount']
```

#### C. Guest-Initiated Cancellation (New)
**Endpoint**: `POST /api/public/hotel/{slug}/room-bookings/{booking_id}/cancel/`
**Location**: New view in `hotel/payment_views.py` or separate `hotel/cancellation_views.py`

```python
class GuestBookingCancellationView(APIView):
    """Allow guests to cancel their own bookings within policy terms."""
    
    def post(self, request, hotel_slug, booking_id):
        # Validate guest access (email verification or unique token)
        # Apply cancellation policy rules
        # Process refunds automatically for confirmed bookings
        # Send email notifications
```

### 3. **Cancellation Fee Calculation Service**

#### Service Class Architecture
**Location**: `hotel/services/cancellation.py` (new file)

```python
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta

class CancellationCalculator:
    """Calculate cancellation fees and refunds based on policy rules."""
    
    def __init__(self, booking):
        self.booking = booking
        self.policy = booking.cancellation_policy
        self.now = timezone.now()
        
    def calculate_fees(self):
        """
        Returns dict with fee_amount, refund_amount, and policy_details
        """
        if not self.policy:
            return self._default_calculation()
            
        hours_until_checkin = self._hours_until_checkin()
        applicable_tier = self._get_applicable_tier(hours_until_checkin)
        
        if applicable_tier:
            return self._calculate_tier_fees(applicable_tier)
        else:
            return self._calculate_base_fees(hours_until_checkin)
    
    def _hours_until_checkin(self):
        checkin_datetime = datetime.combine(
            self.booking.check_in, 
            time(15, 0)  # 3 PM default check-in
        )
        return (checkin_datetime - self.now).total_seconds() / 3600
    
    def _get_applicable_tier(self, hours_until):
        return self.policy.cancellation_tiers.filter(
            hours_before_checkin__lte=hours_until
        ).order_by('-hours_before_checkin').first()
    
    def _calculate_tier_fees(self, tier):
        total_amount = self.booking.total_amount
        
        if tier.fee_type == 'NONE':
            return {
                'fee_amount': Decimal('0.00'),
                'refund_amount': total_amount,
                'policy_description': f"Free cancellation (more than {tier.hours_before_checkin}h before check-in)"
            }
        elif tier.fee_type == 'PERCENTAGE':
            fee = total_amount * (tier.fee_percentage / 100)
            return {
                'fee_amount': fee,
                'refund_amount': total_amount - fee,
                'policy_description': f"{tier.fee_percentage}% cancellation fee"
            }
        # ... handle other fee types
```

### 4. **API Endpoint Enhancements**

#### Enhanced Staff Endpoints
```
POST /api/staff/hotel/{slug}/room-bookings/{booking_id}/cancel/
```
**Enhancements**:
- Add cancellation policy fee calculation
- Automatic refund processing for confirmed bookings
- Enhanced cancellation reason tracking

#### New Guest Endpoints
```
GET  /api/public/hotel/{slug}/room-bookings/{booking_id}/cancellation-preview/
POST /api/public/hotel/{slug}/room-bookings/{booking_id}/cancel/
```

#### Policy Management Endpoints (Staff)
```
GET    /api/staff/hotel/{slug}/cancellation-policies/
POST   /api/staff/hotel/{slug}/cancellation-policies/
PUT    /api/staff/hotel/{slug}/cancellation-policies/{policy_id}/
DELETE /api/staff/hotel/{slug}/cancellation-policies/{policy_id}/
```

### 5. **Integration with Existing Components**

#### A. Rate Plans Integration
**Location**: `rooms/models.py:277` (`RatePlan` model)
```python
# Add to RatePlan model
cancellation_policy = models.ForeignKey(
    'hotel.CancellationPolicy',
    null=True, blank=True,
    on_delete=models.SET_NULL
)
```

#### B. Booking Options Integration  
**Location**: `hotel/models.py:510` (`BookingOptions` model)
```python
# Add to BookingOptions for public display
cancellation_policies_url = models.URLField(
    blank=True,
    help_text="URL to detailed cancellation policies"
)
show_cancellation_preview = models.BooleanField(
    default=True,
    help_text="Show cancellation policy preview during booking"
)
```

#### C. Email Notifications Enhancement
**Location**: `notifications/email_service.py:199`
**Enhancement**: Include refund details in cancellation emails

```python
def send_booking_cancellation_email(booking, reason=None, cancelled_by=None, refund_details=None):
    # ... existing code ...
    
    # ADD REFUND INFORMATION
    refund_info = ""
    if refund_details and refund_details['refund_amount'] > 0:
        refund_info = f"""
        <div class="refund-info">
            <h3>Refund Information:</h3>
            <p>Cancellation Fee: {refund_details['fee_amount']}</p>
            <p>Refund Amount: {refund_details['refund_amount']}</p>
            <p>Estimated Processing Time: 5-7 business days</p>
        </div>
        """
```

## Implementation Phases

### Phase 1: Core Models & Services (Week 1-2)
1. Create `CancellationPolicy` and `CancellationPolicyTier` models
2. Add cancellation fields to `RoomBooking` model  
3. Implement `CancellationCalculator` service
4. Create database migrations

### Phase 2: Staff Interface Integration (Week 2-3)
1. Enhance `StaffBookingCancelView` with policy calculations
2. Add automatic refund processing for confirmed bookings
3. Create policy management endpoints for staff
4. Update booking detail serializers to include policy info

### Phase 3: Guest Self-Service Cancellation (Week 3-4)
1. Implement guest cancellation preview endpoint
2. Create secure guest cancellation endpoint
3. Add email verification/token system for guest access
4. Update booking confirmation emails with cancellation links

### Phase 4: Frontend Integration & Testing (Week 4-5)
1. Update booking creation flow to show policy preview
2. Enhance staff dashboard with refund tracking
3. Add guest portal cancellation interface
4. Comprehensive testing with various policy scenarios

## Best Practices & Recommendations

### 1. **Policy Enforcement Priority**
- **Database-Stored Policies**: Always use the policy assigned at booking time, not current hotel policy
- **Immutable Rules**: Once a booking is created, its cancellation policy should not change
- **Audit Trail**: Log all cancellation decisions and refund calculations

### 2. **Payment Integration Safeguards**
- **Idempotency**: Prevent duplicate refund processing
- **Stripe Webhook Monitoring**: Track refund status from Stripe
- **Manual Review**: Flag large refunds for staff approval

### 3. **User Experience Considerations**
- **Clear Communication**: Show cancellation policies prominently during booking
- **Grace Periods**: Allow brief "cooling off" periods for immediate cancellations
- **Flexible Staff Override**: Allow staff to override policies in exceptional cases

### 4. **Compliance & Legal**
- **Jurisdiction Rules**: Consider local consumer protection laws
- **Terms Integration**: Link cancellation policies to hotel terms & conditions
- **Dispute Resolution**: Maintain clear records for payment disputes

## Technical Implementation Files

### New Files to Create:
1. `hotel/services/cancellation.py` - Cancellation calculation service
2. `hotel/cancellation_views.py` - Guest cancellation endpoints
3. `hotel/management/commands/migrate_cancellation_policies.py` - Data migration

### Files to Modify:
1. `hotel/models.py` - Add CancellationPolicy models and RoomBooking fields
2. `hotel/staff_views.py` - Enhance StaffBookingCancelView
3. `hotel/payment_views.py` - Add policy preview endpoints
4. `notifications/email_service.py` - Add refund details to emails
5. `rooms/models.py` - Link RatePlan to CancellationPolicy

### Database Migrations Required:
1. Create CancellationPolicy tables
2. Add cancellation fields to RoomBooking
3. Add policy references to RatePlan and BookingOptions

This implementation plan provides a comprehensive, production-ready cancellation policy system that integrates seamlessly with the existing Stripe authorize-capture payment architecture while maintaining backward compatibility and ensuring robust refund processing.