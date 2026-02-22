# Services & Business Rules

> Documents the service layer, business logic, validation rules, and invariants.

---

## 1. Room Booking Lifecycle Services (`room_bookings/services/`)

### Room Assignment — `room_bookings/services/room_assignment.py`

**Class:** `RoomAssignmentService`

| Method | Purpose |
|--------|---------|
| `get_available_rooms(hotel, room_type, check_in, check_out)` | Returns rooms matching hotel, type, `is_active=True`, `is_bookable=True`, no overlap with blocking bookings |
| `validate_assignment(booking, room)` | Full validation before assignment |
| `assign_room(booking, room, assigned_by)` | Atomic assignment with `select_for_update` locking |

**Validation rules (`validate_assignment`):**
- Room's hotel must match booking's hotel → `HOTEL_MISMATCH`
- Room type must match room type's hotel → `ROOM_TYPE_HOTEL_MISMATCH`
- Booking status must be in `ASSIGNABLE_STATUSES` (`["CONFIRMED"]`) → `BOOKING_STATUS_NOT_ASSIGNABLE`
- Booking must not be `IN_HOUSE` → `BOOKING_ALREADY_CHECKED_IN`
- Room's type must match booking's room_type → `ROOM_TYPE_MISMATCH`
- Room must be bookable (`is_bookable=True`) → `ROOM_NOT_BOOKABLE`
- No date overlap with other blocking bookings for same room → `ROOM_OVERLAP_CONFLICT`

**Assignment behavior:**
- Uses `select_for_update()` on booking + room + conflicting bookings
- Supports idempotent re-assignment (same room = no-op success)
- Blocks reassignment for `IN_HOUSE` guests
- Sets `assigned_room`, `room_assigned_at`, `room_assigned_by`, increments `assignment_version`
- Stores previous room in `previous_room`, `previous_room_unassigned_at`, `previous_room_unassigned_by`

**Error type:** `RoomAssignmentError(message, code, details_dict)`  
**Source:** `room_bookings/exceptions.py`

---

### Checkout — `room_bookings/services/checkout.py`

**Function:** `perform_checkout(booking, staff_user=None)`

Single centralized checkout function used by all checkout paths.

**Sequence:**
1. Atomic transaction with `select_for_update()` on booking + room
2. Detect all guests: booking-linked (`source_booking=booking`) + orphaned (in room with `source_booking=None`)
3. Detach each guest: set `room=None`, `check_out_date=today`
4. **Consistency assertion**: if any guests remain in room after cleanup → abort with error
5. Set `booking.status = COMPLETED`, `booking.actual_check_out = now()`
6. Revoke all active `GuestBookingToken` records for this booking
7. Room cleanup: set `is_occupied=False`, transition to `CHECKOUT_DIRTY` via `housekeeping.services.set_room_status()`
8. Cleanup conversations: delete `Conversation`, `RoomMessage`, `Order`, `BreakfastOrder` for room
9. **Post-commit:** emit realtime notifications
10. Trigger survey email based on `HotelSurveyConfig.send_policy`:
    - `AUTO_IMMEDIATE` → send now
    - `AUTO_DELAYED` → schedule for `delay_hours` later
    - `MANUAL_ONLY` → no action

---

### Room Move — `room_bookings/services/room_move.py`

**Function:** `move_guest_to_room(booking, new_room, moved_by)`

**Validations:**
- Booking must be `IN_HOUSE` → `BOOKING_NOT_CHECKED_IN`
- Booking must not be `COMPLETED` → `BOOKING_ALREADY_CHECKED_OUT`
- Must have assigned room → `NO_ROOM_ASSIGNED`
- New room hotel must match → `HOTEL_MISMATCH`
- New room must be `is_active` → `ROOM_NOT_ACTIVE`
- New room must not be `OUT_OF_ORDER` → `ROOM_OUT_OF_ORDER`
- New room must not be occupied → `ROOM_OCCUPIED`
- Party count ≤ room type `max_occupancy` → `ROOM_CAPACITY_EXCEEDED`
- No blocking booking overlap → `ROOM_NOT_AVAILABLE`

**Behavior:**
- Moves all guests from old room to new room
- Old room → `CHECKOUT_DIRTY` via `set_room_status()`
- New room → `OCCUPIED` via `set_room_status()`
- Cleanup old room conversations/orders
- Updates booking `assigned_room` + audit fields

---

### Overstay — `room_bookings/services/overstay.py`

| Function | Purpose |
|----------|---------|
| `calculate_checkout_deadline(booking)` | UTC deadline = `check_out_date` at hotel's `check_out_time` + `checkout_grace_minutes` |
| `flag_overstay_bookings()` | Scan IN_HOUSE bookings past deadline; create `OverstayIncident` with `get_or_create` for idempotency |
| `acknowledge_or_dismiss_overstay(incident, staff, action, note)` | Set status to ACKED or DISMISSED |
| `extend_overstay_booking(incident, new_checkout, staff, idempotency_key)` | Extend dates; check room conflicts; calculate pricing; create Stripe `PaymentIntent`; create `BookingExtension`; resolve incident |
| `find_alternative_rooms(booking)` | Available rooms for conflict resolution |

**Pusher events emitted:** `booking_overstay_flagged`, `booking_overstay_acknowledged`, `booking_overstay_extended`, `booking_updated`

---

## 2. Pricing & Cancellation Services (`hotel/services/`)

### Pricing — `hotel/services/pricing_service.py`

**Nightly rate resolution priority:**
1. `DailyRate` for the specific date + room type + rate plan
2. `RoomTypeRatePlan.base_price` override
3. `RoomType.starting_price_from` (fallback)

**VAT:** 9% (Ireland accommodation rate, hardcoded)  
**Default rate plan:** Code `"STD"`, lazy-created per hotel if missing.

### Cancellation Fee Calculation — `hotel/services/cancellation_service.py`

**Function:** `calculate_cancellation_fee(booking)` → returns `(fee_amount, refund_amount)`

| Mode | Behavior |
|------|----------|
| **DEFAULT** (no policy) | Full refund, zero fee |
| **FLEXIBLE** | Free if `hours_until_checkin > free_cancellation_hours`; else apply penalty |
| **MODERATE** | Same logic, different `free_cancellation_hours` |
| **NON_REFUNDABLE** | Always full penalty |
| **CUSTOM** | Tiered: check `CancellationPolicyTier` records sorted by `hours_before_checkin` desc; apply matching tier's penalty |

**Penalty types:** `FULL_STAY` (total booking amount), `FIRST_NIGHT` (first night's rate), `PERCENTAGE` (% of total), `FIXED` (flat amount), `NONE` (no fee).

### Guest Cancellation — `hotel/services/guest_cancellation_service.py`

**Function:** `cancel_booking_for_guest(booking, token)`

**Rules:**
- Allowed from: `PENDING_PAYMENT`, `PENDING_APPROVAL`, `CONFIRMED`
- Already `CANCELLED` → idempotent success (returns existing data)
- Other terminal states → error
- **Stripe first, then DB:** void/refund Stripe payment → atomic DB update → revoke tokens
- Calculates refund using `cancellation_service.calculate_cancellation_fee()`

---

## 3. Booking Deadline & Stay-Time Rules (`apps/booking/services/`)

### Booking Deadlines — `apps/booking/services/booking_deadlines.py`

**Function:** `calculate_approval_deadline(booking)` → datetime

- Formula: `booking.created_at + approval_deadline_minutes` (from `HotelAccessConfig`, default 30 min)
- Hard expiry: `check_in_date` at hotel's `check_in_time` in hotel timezone → UTC

**Risk levels:**
| Level | Condition |
|-------|-----------|
| `OK` | > 10 min remaining |
| `DUE_SOON` | ≤ 10 min remaining |
| `OVERDUE` | Past deadline, < 60 min |
| `CRITICAL` | > 60 min overdue |

### Stay-Time Rules — `apps/booking/services/stay_time_rules.py`

**Function:** `calculate_checkout_deadline(booking)` → datetime

- Formula: `check_out_date` at hotel's `check_out_time` (default 11:00 AM) + `checkout_grace_minutes` (default 30 min)

**Overstay risk levels:**
| Level | Condition |
|-------|-----------|
| `OK` | Before standard checkout time |
| `GRACE` | Past checkout, within grace period |
| `OVERDUE` | Past grace, < 2 hours |
| `CRITICAL` | > 2 hours overstay |

---

## 4. Booking Identity Service — `hotel/services/booking_service.py`

**Booking ID format:** `BK-{HOTEL_CODE}-{YEAR}-{SEQUENCE}`  
Example: `BK-NOWAY-2026-0001`

- Hotel code: derived from slug (uppercase, no hyphens, max 8 chars)
- Sequence: per-hotel per-year, using `select_for_update()` for concurrency
- Function: `generate_booking_id(hotel)` → unique booking ID string

---

## 5. Booking Party Integrity — `hotel/services/party_integrity_service.py`

**Function:** `heal_booking_party(booking)` → auto-fixes:
- Missing PRIMARY guest → promotes first COMPANION or creates from booking fields
- Duplicate PRIMARY guests → keeps first, demotes rest to COMPANION
- Role mismatches between booking data and party records

---

## 6. Survey Analytics — `hotel/services/survey_analytics_service.py`

**Class:** `SurveyAnalyticsService`

Methods: average ratings, completion rates, delayed vs immediate effectiveness analysis, low-rating alert detection.

---

## 7. Housekeeping Services — `housekeeping/services.py`

### set_room_status() — THE canonical room status function

**Signature:** `set_room_status(room, new_status, changed_by, trigger, notes="")`

**Behavior:**
1. Validates transition via `Room.set_status()` (checks `VALID_TRANSITIONS` dict)
2. Enforces RBAC via `housekeeping/permissions.py` (`can_transition()`)
3. Creates `RoomStatusLog` audit record
4. Applies status-specific side effects (see State Machines doc)
5. Emits realtime event via `notification_manager.realtime_room_updated()`

### Additional Functions

| Function | Purpose |
|----------|---------|
| `get_room_status_history(room, limit)` | N most recent `RoomStatusLog` records |
| `get_dashboard_data(hotel)` | Room counts + groupings by status with staff names |
| `create_turnover_task(room, hotel, created_by)` | Factory for TURNOVER-type housekeeping tasks |

---

## 8. Notification Manager — `notifications/notification_manager.py` (2417 lines)

**Singleton hub** routing all events through 5 domains:

| Domain | Event Types |
|--------|-------------|
| **attendance** | Clock in/out, break toggle, roster updates |
| **staff_chat** | New message, reaction, read receipt, conversation updates |
| **guest_chat** | New guest message, staff response, room-level events |
| **room_service** | New order, status change, porter/kitchen notifications |
| **booking** | New booking, status change, overstay, check-in/out, room assignment |

**Channels:**
- Pusher: realtime WebSocket events to frontend
- FCM: push notifications to staff mobile devices
- Email: booking confirmations, survey links, pre-checkin links

---

## 9. Bookings (Restaurant) — `bookings/services.py`

**Guest portal token auth for chat access** — validates `GuestBookingToken` scopes, hash lookup, expiry, in-house status.

Not related to restaurant booking business logic (despite file location).

---

## 10. Room Bookability Rules

**Source:** `rooms/models.py` (`Room.is_room_bookable` property)

A room is bookable when ALL of:
- `is_active = True`
- `is_bookable = True`
- `status` NOT in `['OUT_OF_ORDER', 'MAINTENANCE_REQUIRED']`

---

## 11. DinnerBooking Validation — `bookings/views.py`

**Rules enforced in `DinnerBookingListCreateView`:**
- Capacity check: max bookings per hour per restaurant
- Group size limit validation
- Duplicate room + date check
- Cross-hotel FK consistency (restaurant.hotel must match booking.hotel)

---

## 12. Stock Tracker Business Rules — `stock_tracker/stocktake_service.py`

| Function | Purpose |
|----------|---------|
| `populate_stocktake(stocktake)` | Generate `StocktakeLine` records with opening balances from previous period's closing |
| `approve_stocktake(stocktake, user)` | Create adjustment `StockMovement` records, close period |
| `reopen_stocktake(stocktake)` | Reverse closure; requires `PeriodReopenPermission` |

**Computed properties on `StocktakeLine`:**
- `closing_stock`: category-aware conversion (partial units → full units based on category-specific `servings_per_unit`)
- `variance`: counted - (opening + purchases - waste - transfers ± adjustments)
- `cost_of_goods_sold`: calculated from movement data
