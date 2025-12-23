# HotelMate Cancellation Policy Implementation Plan

**Implement exactly the plan below. Do not change architecture decisions. Only make the two model tweaks: (1) allow penalty_type to be null/blank for CUSTOM policies, and (2) add unique constraint on (policy, hours_before_checkin). Everything else must match.**

## Executive Summary
Implement comprehensive cancellation policy system with templates (Flexible, Moderate, Non-Refundable, Custom Tiered) while preserving existing booking cancellation behavior through additive-only changes and DEFAULT/POLICY mode branching.

## Architecture Principles
- **Additive-only changes**: New tables + nullable fields. No renames, no removals
- **DEFAULT mode**: `RoomBooking.cancellation_policy IS NULL` → keep existing behavior unchanged
- **POLICY mode**: `RoomBooking.cancellation_policy IS NOT NULL` → use new fee calculation
- **Immutable policies**: Bookings snapshot policy at creation time, never compute from "current hotel policy"
- **Hotel scoping**: All endpoints enforce hotel_slug scoping (no cross-hotel access)
- **Stripe safety**: Preserve existing authorize/capture flow, only enhance cancellation safely

## Locked Decisions (Do Not Ask, Do Not Invent)

### Policy Snapshotting Strategy
- **Implementation**: Snapshot `RatePlan.cancellation_policy` into `RoomBooking.cancellation_policy` at booking creation time
- **Timing**: Once at booking creation/confirmation
- **Fallback**: If no rate plan policy, leave NULL (DEFAULT mode) unless hotel default exists

### Rate Plan Soft Delete Enforcement  
- **Rule**: NO hard delete of RatePlans in staff API
- **Reason**: CASCADE wipes `DailyRates` and `RoomTypeRatePlans`
- **Implementation**: Use `PATCH {is_active: false}` to disable (soft delete)
- **API**: Override DELETE to return 405 Method Not Allowed

### Room Number Validation Rules
- **Allow**: Any positive integer >= 1
- **Sanity limit**: <= 99999
- **Uniqueness**: Enforced per hotel by database constraint
- **NO business rules**: Hotels have weird numbering (1, 2, 2A, 1001, villas, cabins)
- **Future**: If "2A" needed later, add optional `display_label` field but keep `room_number` numeric

### Migration Strategy
- **NO auto-creation**: Do NOT auto-create policies for existing hotels
- **Manual setup**: Hotels must manually configure policies

### Refund Processing
- **Synchronous**: Keep refund processing synchronous with idempotency guards
- **No async**: No background job processing yet

## Implementation Plan: 7 Phases

### Phase 1: Cancellation Policy Models

**Location**: Add to `hotel/models.py` (or appropriate hotel app module)

#### CancellationPolicy Model
```python
class CancellationPolicy(models.Model):
    TEMPLATE_TYPE_CHOICES = [
        ('FLEXIBLE', 'Flexible'),
        ('MODERATE', 'Moderate'), 
        ('NON_REFUNDABLE', 'Non-Refundable'),
        ('CUSTOM', 'Custom Tiered'),
    ]
    
    PENALTY_TYPE_CHOICES = [
        ('NONE', 'No Penalty'),
        ('FIXED', 'Fixed Amount'),
        ('PERCENTAGE', 'Percentage'),
        ('FIRST_NIGHT', 'First Night'),
        ('FULL_STAY', 'Full Stay'),
    ]
    
    NO_SHOW_PENALTY_CHOICES = [
        ('SAME_AS_CANCELLATION', 'Same as Cancellation'),
        ('FIRST_NIGHT', 'First Night'),
        ('FULL_STAY', 'Full Stay'),
    ]
    
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    
    # Template fields (nullable for flexibility)
    free_until_hours = models.PositiveIntegerField(null=True, blank=True)
    penalty_type = models.CharField(max_length=20, choices=PENALTY_TYPE_CHOICES, null=True, blank=True)
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    penalty_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    no_show_penalty_type = models.CharField(max_length=20, choices=NO_SHOW_PENALTY_CHOICES, default='FULL_STAY')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('hotel', 'code')
        ordering = ['hotel', 'name']
```

#### CancellationPolicyTier Model (CUSTOM template only)
```python  
class CancellationPolicyTier(models.Model):
    PENALTY_TYPE_CHOICES = [
        ('FIXED', 'Fixed Amount'),
        ('PERCENTAGE', 'Percentage'), 
        ('FIRST_NIGHT', 'First Night'),
        ('FULL_STAY', 'Full Stay'),
    ]
    
    policy = models.ForeignKey('CancellationPolicy', on_delete=models.CASCADE, related_name='tiers')
    hours_before_checkin = models.PositiveIntegerField()
    penalty_type = models.CharField(max_length=20, choices=PENALTY_TYPE_CHOICES)
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    penalty_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-hours_before_checkin']  # Largest hours first
        constraints = [
            models.UniqueConstraint(fields=['policy', 'hours_before_checkin'], name='uniq_policy_hours')
        ]
```

#### Template Validation Rules (Enforce in serializer/service)
- **NON_REFUNDABLE**: `free_until_hours = 0`, `penalty_type = 'FULL_STAY'`
- **FLEXIBLE**: `free_until_hours` required; `penalty_type` in `{'FIRST_NIGHT', 'FULL_STAY'}`
- **MODERATE**: `free_until_hours` required; `penalty_type` in `{'FIRST_NIGHT', 'PERCENTAGE'}`; if `PERCENTAGE` then `penalty_percentage` required
- **CUSTOM**: `tiers >= 1`, all tiers valid, `hours_before_checkin` positive

### Phase 2: Extend Existing Models (Additive Only)

#### Update `rooms/models.py` RatePlan
Add nullable FK to CancellationPolicy:
```python
# Add to RatePlan model
cancellation_policy = models.ForeignKey(
    'hotel.CancellationPolicy',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='rate_plans',
    help_text='Default cancellation policy for bookings using this rate plan'
)
```

#### Update RoomBooking Model (hotel app)
Add nullable cancellation tracking fields:
```python
# Add to RoomBooking model  
cancellation_policy = models.ForeignKey(
    'hotel.CancellationPolicy',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    help_text='Snapshot of cancellation policy at booking time'
)
cancelled_at = models.DateTimeField(null=True, blank=True)
cancellation_reason = models.CharField(max_length=255, blank=True)
cancellation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
refund_processed_at = models.DateTimeField(null=True, blank=True)

# Optional but recommended for debugging
rate_plan = models.ForeignKey(
    'rooms.RatePlan',
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    help_text='Rate plan used for this booking (for policy/price debugging)'
)
```

**IMPORTANT**: These fields must be optional in serializers to maintain backward compatibility.

### Phase 3: Staff CRUD Endpoints (hotel_slug scoped)

#### Cancellation Policies Management
**File**: Create `hotel/views/cancellation_policies.py`

**Endpoints**:
- `GET/POST /api/staff/hotel/{hotel_slug}/cancellation-policies/`
- `GET/PUT/PATCH /api/staff/hotel/{hotel_slug}/cancellation-policies/{policy_id}/`

**Rules**:
- Resolve hotel by slug and enforce scoping: `policy.hotel` must equal that hotel
- On create/update, force `policy.hotel = hotel`
- PATCH allows toggling `is_active` and editing fields
- Return nested tiers in response for CUSTOM template
- Validate template field rules in serializer
- Disallow cross-hotel access

#### Rate Plans Management  
**File**: Extend existing or create `hotel/views/rate_plans.py`

**Endpoints**:
- `GET/POST /api/staff/hotel/{hotel_slug}/rate-plans/`
- `GET/PUT/PATCH /api/staff/hotel/{hotel_slug}/rate-plans/{id}/`

**Rules**:
- Enforce hotel scoping and unique `(hotel, code)`
- **NO DELETE endpoint** or override to return 405 Method Not Allowed
- Use `PATCH {is_active: false}` for soft disable
- Allow setting `cancellation_policy_id` on RatePlan (nullable)
- Auto-uppercase code on save (optional)

### Phase 4: Bulk Room Creation

**Endpoint**: `POST /api/staff/hotel/{hotel_slug}/room-types/{room_type_id}/rooms/bulk-create/`

**File**: Add to rooms staff views

**Payload Support**:
1. `{"room_numbers": [101, 102, 201]}`
2. `{"ranges": [{"start": 101, "end": 110}, {"start": 201, "end": 205}]}`

**Implementation Rules**:
- Expand ranges inclusive, dedupe all numbers
- Validate positive integers (>= 1, <= 99999)
- Ensure RoomType belongs to hotel_slug
- Skip existing room numbers for that hotel
- Create remaining Room instances in transaction
- Set `room_type` FK and default `room_status = 'READY_FOR_GUEST'`

**Response Format**:
```json
{
  "created_count": 5,
  "skipped_existing": [101, 102],
  "created_rooms": [
    {"id": 123, "room_number": 103, "room_type_id": 456},
    {"id": 124, "room_number": 104, "room_type_id": 456}
  ]
}
```

### Phase 5: Cancellation Calculator Service (Pure Logic)

**File**: Create `hotel/services/cancellation.py`

#### CancellationCalculator Class
```python
class CancellationCalculator:
    def __init__(self, booking):
        self.booking = booking
    
    def calculate(self):
        """
        Returns: {
            'fee_amount': Decimal,
            'refund_amount': Decimal, 
            'description': str,
            'applied_rule': str
        }
        """
```

#### Calculation Rules
- **No Stripe calls** inside calculator
- **DEFAULT mode** (`booking.cancellation_policy is None`):
  - Return preview only: `fee_amount = 0`, `refund_amount = booking.total_amount`
  - Do NOT apply automatically
- **POLICY mode**:
  - Compute `hours_until_checkin` using `booking.check_in + 15:00` (or hotel config)
  - If CUSTOM: pick tier where `hours_before_checkin <= hours_until_checkin`, ordered desc
  - Calculate fee:
    - `FULL_STAY` → `booking.total_amount`
    - `FIRST_NIGHT` → first night price (use breakdown if exists, fallback `total/nights` with Decimal rounding)
    - `PERCENTAGE` → `total_amount * penalty_percentage/100`  
    - `FIXED` → `penalty_amount` clamped to `total_amount`
  - `refund_amount = max(total_amount - fee_amount, 0)`

### Phase 6: Policy Snapshotting at Booking Creation

**Location**: Where RoomBooking is created/confirmed (public or staff flow)

**Logic**:
```python
# At booking creation time
if booking.rate_plan and booking.rate_plan.cancellation_policy:
    booking.cancellation_policy = booking.rate_plan.cancellation_policy
else:
    booking.cancellation_policy = None  # DEFAULT mode
    
booking.save()
```

**Timing**: Must happen once at booking creation/confirmation time for immutable policy enforcement.

### Phase 7: Staff Cancel Integration (DEFAULT/POLICY Branching)

**File**: Modify `StaffBookingCancelView` in `hotel/views/room_bookings.py` (or current location)

#### Strict Branching Logic
```python
def cancel_booking(self, booking, reason=""):
    if booking.cancellation_policy_id is None:
        # DEFAULT mode: execute existing cancellation logic EXACTLY as before
        return self.execute_legacy_cancellation(booking, reason)
    else:
        # POLICY mode: use calculator + Stripe refund processing
        return self.execute_policy_cancellation(booking, reason)
```

#### POLICY Mode Implementation
- `result = CancellationCalculator(booking).calculate()`
- **If payment captured**: create Stripe refund for `result.refund_amount` (partial/full)
- **If only authorized**: follow existing approve/decline paths (do NOT change)
- Write cancellation fields: `cancelled_at`, `cancellation_reason`, `cancellation_fee`, `refund_amount`
- Set `refund_processed_at` only after successful refund call
- **Idempotency guard**: if `refund_processed_at` already set, do NOT refund again

#### Important Notes
- **Do NOT modify** approve/decline endpoints
- Preserve existing status transitions and notifications
- Maintain existing real-time events

## Testing Requirements

### Unit Tests Required
1. **CancellationPolicy template validation**:
   - NON_REFUNDABLE enforces FULL_STAY + free_until_hours=0
   - FLEXIBLE requires free_until_hours + correct penalty_type
   - MODERATE validation rules
   - CUSTOM requires valid tiers

2. **Calculator calculations**:  
   - Each template type calculation accuracy
   - Hours until check-in computation
   - Tier selection for CUSTOM policies
   - Edge cases (same-day cancellation, past check-in)

3. **Staff CRUD endpoints**:
   - Hotel_slug scoping enforcement
   - Cross-hotel access prevention
   - Rate plan soft delete (no hard delete)
   - Nested tiers serialization

4. **Bulk room creation**:
   - Range expansion and deduplication
   - Skipping existing room numbers
   - Room type hotel ownership validation
   - Transaction rollback on errors

5. **Cancel integration**:
   - DEFAULT mode unchanged behavior
   - POLICY mode calculator application  
   - Stripe refund processing
   - Idempotency guard functionality

## File Structure
```
hotel/
├── models.py                     # Add CancellationPolicy + CancellationPolicyTier
├── serializers/
│   ├── cancellation_policies.py  # New serializers
│   └── rate_plans.py             # Updated serializers  
├── services/
│   └── cancellation.py          # New calculator service
├── views/
│   ├── cancellation_policies.py  # New CRUD views
│   ├── rate_plans.py             # Updated views
│   └── room_bookings.py          # Modified cancel view
└── tests/
    ├── test_cancellation_policies.py
    ├── test_cancellation_calculator.py
    └── test_cancel_integration.py

rooms/
├── models.py                     # Update RatePlan model
├── views/
│   └── staff_rooms.py           # Add bulk create endpoint
└── tests/
    └── test_bulk_room_creation.py
```

## Migration Strategy
1. Create new models (CancellationPolicy, CancellationPolicyTier)  
2. Add nullable fields to existing models (RatePlan, RoomBooking)
3. No data migration required (nullable fields default to NULL)
4. Hotels must manually configure policies through staff interface

## Deliverables Checklist
- [ ] Database migrations for new models and fields
- [ ] Model definitions with proper constraints
- [ ] Admin registration for new models  
- [ ] Serializers for cancellation policies and updated rate plans
- [ ] Staff API views with hotel_slug scoping
- [ ] URL routing for new endpoints
- [ ] Cancellation calculator service class
- [ ] Policy snapshotting integration
- [ ] Safe cancel endpoint integration with DEFAULT/POLICY branching
- [ ] Comprehensive unit test coverage
- [ ] Bulk room creation endpoint
- [ ] Rate plan soft delete enforcement

## Success Criteria
1. **Backward compatibility**: Existing bookings (policy NULL) cancel with no regression
2. **Policy enforcement**: New bookings with policies compute fees deterministically
3. **Security**: Hotel scoping prevents cross-hotel access
4. **Data integrity**: Template validations enforced, soft deletes working
5. **Stripe safety**: Refund processing works with idempotency guards
6. **Performance**: Calculator service performs calculations without external calls