# State Machines

> All status fields with their allowed transitions, as observed in code.

---

## 1. Room Status State Machine

**Model:** `rooms.Room.status`  
**Canonical transition function:** `housekeeping/services.py:set_room_status()`  
**Valid transitions defined in:** `rooms/models.py` (`VALID_TRANSITIONS` dict inside `Room.set_status()`)

### Statuses

| Status | Code | Description |
|--------|------|-------------|
| Ready for Guest | `READY_FOR_GUEST` | Clean, inspected, available for assignment |
| Occupied | `OCCUPIED` | Guest checked in |
| Checkout Dirty | `CHECKOUT_DIRTY` | Guest departed, room needs cleaning |
| Cleaning In Progress | `CLEANING_IN_PROGRESS` | Housekeeping actively cleaning |
| Cleaned Uninspected | `CLEANED_UNINSPECTED` | Cleaned, awaiting manager inspection |
| Maintenance Required | `MAINTENANCE_REQUIRED` | Needs maintenance work |
| Out of Order | `OUT_OF_ORDER` | Fully out of service |

### Transition Map

```
READY_FOR_GUEST ──────► OCCUPIED
                ──────► MAINTENANCE_REQUIRED
                ──────► OUT_OF_ORDER

OCCUPIED ─────────────► CHECKOUT_DIRTY
                ──────► MAINTENANCE_REQUIRED

CHECKOUT_DIRTY ───────► CLEANING_IN_PROGRESS
                ──────► CLEANED_UNINSPECTED
                ──────► MAINTENANCE_REQUIRED
                ──────► READY_FOR_GUEST

CLEANING_IN_PROGRESS ─► CLEANED_UNINSPECTED
                ──────► CHECKOUT_DIRTY
                ──────► MAINTENANCE_REQUIRED
                ──────► READY_FOR_GUEST

CLEANED_UNINSPECTED ──► READY_FOR_GUEST
                ──────► CHECKOUT_DIRTY
                ──────► MAINTENANCE_REQUIRED

MAINTENANCE_REQUIRED ─► CHECKOUT_DIRTY
                ──────► OUT_OF_ORDER
                ──────► READY_FOR_GUEST

OUT_OF_ORDER ─────────► CHECKOUT_DIRTY
                ──────► READY_FOR_GUEST
```

### Side Effects on Transition (in `housekeeping/services.py`)

| Target Status | Side Effects |
|---------------|-------------|
| `CLEANING_IN_PROGRESS` | Appends turnover note to `maintenance_notes` |
| `CLEANED_UNINSPECTED` | Sets `cleaned_at`, `cleaned_by` |
| `READY_FOR_GUEST` | Sets `inspected_at`, `inspected_by`; clears `is_occupied`, `has_maintenance_issue`, `maintenance_priority`, `maintenance_notes`; ensures `is_active=True`, `is_bookable=True` |
| `MAINTENANCE_REQUIRED` | Sets `has_maintenance_issue=True`; appends timestamped maintenance note |
| Any transition | Creates `RoomStatusLog` audit record; emits realtime event via `notification_manager.realtime_room_updated()` |

### RBAC Policy (`housekeeping/permissions.py`)

| Role | Allowed Transitions |
|------|-------------------|
| **Manager** (staff_admin/super_staff_admin) | Any valid transition; note required for overrides |
| **Housekeeping** (department.slug = housekeeping) | Workflow only: `CHECKOUT_DIRTY → CLEANING_IN_PROGRESS → CLEANED_UNINSPECTED → READY_FOR_GUEST`; can always flag `MAINTENANCE_REQUIRED` |
| **Front Desk** | Limited: `OCCUPIED → CHECKOUT_DIRTY` or `→ MAINTENANCE_REQUIRED` |

---

## 2. Room Booking Status State Machine

**Model:** `hotel.RoomBooking.status`  
**Defined in:** `hotel/models.py`  
**Transitions observed in:** `hotel/payment_views.py`, `hotel/staff_views.py`, `room_bookings/services/checkout.py`, `hotel/services/guest_cancellation_service.py`, management commands

### Statuses

| Status | Code | Description |
|--------|------|-------------|
| Pending Payment | `PENDING_PAYMENT` | Initial state; awaiting Stripe payment |
| Pending Approval | `PENDING_APPROVAL` | Paid; awaiting staff review |
| Confirmed | `CONFIRMED` | Staff approved; room assignable |
| In House | `IN_HOUSE` | Guest checked in |
| Completed | `COMPLETED` | Guest checked out |
| Declined | `DECLINED` | Staff rejected booking |
| Cancelled | `CANCELLED` | Cancelled by guest or staff |
| Cancelled Draft | `CANCELLED_DRAFT` | Auto-expired unpaid booking |
| Expired | `EXPIRED` | Auto-expired past approval deadline |
| No Show | `NO_SHOW` | Guest never arrived |

### Transition Map

```
                    ┌──────────────────┐
                    │ PENDING_PAYMENT  │ (initial state)
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐  ┌──────────────┐  ┌────────────────┐
     │ CANCELLED  │  │CANCELLED_DRAFT│  │PENDING_APPROVAL│
     │            │  │(auto-expire) │  │ (Stripe paid)  │
     └────────────┘  └──────────────┘  └───────┬────────┘
                                               │
                            ┌──────────────────┼──────────────┐
                            │                  │              │
                            ▼                  ▼              ▼
                     ┌───────────┐      ┌──────────┐   ┌──────────┐
                     │ DECLINED  │      │ EXPIRED  │   │CONFIRMED │
                     │           │      │(auto)    │   │          │
                     └───────────┘      └──────────┘   └────┬─────┘
                                                            │
                                         ┌──────────────────┼──────────┐
                                         │                  │          │
                                         ▼                  ▼          ▼
                                  ┌───────────┐     ┌──────────┐  ┌────────┐
                                  │ CANCELLED │     │ IN_HOUSE │  │NO_SHOW │
                                  └───────────┘     └────┬─────┘  └────────┘
                                                         │
                                                         ▼
                                                  ┌───────────┐
                                                  │ COMPLETED │
                                                  └───────────┘
```

### Transition Triggers

| Transition | Trigger | File |
|-----------|---------|------|
| PENDING_PAYMENT → PENDING_APPROVAL | Stripe `checkout.session.completed` webhook | `hotel/payment_views.py` |
| PENDING_PAYMENT → CANCELLED | Guest cancellation | `hotel/services/guest_cancellation_service.py` |
| PENDING_PAYMENT → CANCELLED_DRAFT | Auto-expire by management command | `hotel/management/commands/auto_expire_overdue_bookings.py` |
| PENDING_APPROVAL → CONFIRMED | Staff approve action | `hotel/staff_views.py:AcceptBookingView` |
| PENDING_APPROVAL → DECLINED | Staff decline action | `hotel/staff_views.py:DeclineBookingView` |
| PENDING_APPROVAL → EXPIRED | Auto-expire past `approval_deadline` | `hotel/management/commands/auto_expire_overdue_bookings.py` |
| PENDING_APPROVAL → CANCELLED | Guest or staff cancellation | `hotel/staff_views.py:CancelBookingView` |
| CONFIRMED → IN_HOUSE | Staff check-in action | `hotel/staff_views.py:StaffCheckInView` |
| CONFIRMED → CANCELLED | Staff or guest cancellation | `hotel/staff_views.py:CancelBookingView` |
| CONFIRMED → NO_SHOW | Staff marks no-show | `hotel/staff_views.py` |
| IN_HOUSE → COMPLETED | Checkout service | `room_bookings/services/checkout.py:perform_checkout()` |

### Terminal States
`COMPLETED`, `CANCELLED`, `CANCELLED_DRAFT`, `DECLINED`, `EXPIRED`, `NO_SHOW` — no further transitions observed.

### Inventory Blocking Rules (`room_bookings/constants.py`)

| Constant | Value | Purpose |
|----------|-------|---------|
| `BLOCKING_STATUSES` | `["CONFIRMED"]` | These bookings block room inventory (combined with date overlap + assignment timestamps) |
| `ASSIGNABLE_STATUSES` | `["CONFIRMED"]` | Only these statuses allow room assignment |
| `NON_BLOCKING_STATUSES` | `["CANCELLED", "COMPLETED", "NO_SHOW"]` | Never block inventory |

---

## 3. Housekeeping Task Status

**Model:** `housekeeping.HousekeepingTask.status`  
**Transitions observed in:** `housekeeping/views.py`

### Statuses
`OPEN` → `IN_PROGRESS` → `DONE` | `CANCELLED`

### Transition Actions

| Action | Endpoint | Behavior |
|--------|----------|----------|
| Assign | `tasks/<id>/assign/` | Sets `assigned_to`; status stays `OPEN` |
| Start | `tasks/<id>/start/` | `OPEN → IN_PROGRESS`; sets `started_at` |
| Complete | `tasks/<id>/complete/` | `IN_PROGRESS → DONE`; sets `completed_at` |

### SLA Tracking
| Priority | SLA Hours |
|----------|-----------|
| HIGH | 2 hours |
| MED | 4 hours |
| LOW | 8 hours |

Property `is_overdue`: True if `created_at + SLA hours < now` and status not DONE/CANCELLED.

---

## 4. Room Service / Breakfast Order Status

**Model:** `room_services.Order.status`, `room_services.BreakfastOrder.status`  
**File:** `room_services/models.py`

### Statuses
`pending` → `accepted` → `completed`

Transitions are direct field updates in views; no state machine validation observed.

---

## 5. Maintenance Request Status

**Model:** `maintenance.MaintenanceRequest.status`  
**File:** `maintenance/models.py`

### Statuses
`open` → `in_progress` → `resolved` → `closed`

Transitions are direct field updates; no formal state machine.

---

## 6. Stocktake Status

**Model:** `stock_tracker.Stocktake.status`  
**File:** `stock_tracker/models.py`

### Statuses
`DRAFT` → `APPROVED`

| Transition | Trigger | Side Effects |
|-----------|---------|-------------|
| DRAFT → APPROVED | `stocktakes/<pk>/approve/` action | Sets `approved_by`, creates `StockSnapshot` records, closes associated `StockPeriod` |
| APPROVED → DRAFT | `stocktakes/<pk>/reopen/` action | Clears `approved_by`; requires reopen permission |

---

## 7. Stock Period Status

**Model:** `stock_tracker.StockPeriod.is_closed`  
**File:** `stock_tracker/models.py`

Open (`is_closed=False`) → Closed (`is_closed=True`).  
Reopen requires `PeriodReopenPermission` granted to the requesting staff.

---

## 8. Overstay Incident Status

**Model:** `hotel.OverstayIncident.status`  
**File:** `hotel/models.py`, `room_bookings/services/overstay.py`

### Statuses
`OPEN` → `ACKED` (acknowledged) → `RESOLVED` | `DISMISSED`

| Transition | Trigger | Side Effects |
|-----------|---------|-------------|
| OPEN → ACKED | Staff acknowledges | Sets `acknowledged_by`, `acknowledged_at` |
| ACKED → RESOLVED | Booking extended | Sets `resolved_by`, `resolved_at`; creates `BookingExtension` |
| OPEN/ACKED → DISMISSED | Staff dismisses | Sets `dismissed_by`, `dismissed_at` |

---

## 9. GuestBookingToken Status

**Model:** `hotel.GuestBookingToken.status`  
**File:** `hotel/models.py`

### Statuses
`ACTIVE` → `REVOKED`

Revocation occurs on:
- Checkout (`room_bookings/services/checkout.py`)
- Guest cancellation (`hotel/services/guest_cancellation_service.py`)
- New token generation (only one active per booking)

---

## 10. Tournament Status (Entertainment)

**Model:** `entertainment.MemoryTournament.status`, `entertainment.QuizTournament.status`  
**File:** `entertainment/models.py`

### Statuses
`UPCOMING` → `ACTIVE` → `COMPLETED`

Transitions by management command `update_tournament_statuses` (based on start/end dates) and manual start/end actions in views.
