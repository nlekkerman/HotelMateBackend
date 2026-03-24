# Audit Remediation — Next Steps

**Date:** March 24, 2026  
**Based on:** [BACKEND_AUDIT.md](BACKEND_AUDIT.md) cross-referenced against current codebase  
**Fixed so far:** ~18 of ~49 findings

---

## Priority 1 — CRITICAL (Fix Immediately)

### 1.1 `current_booking` NameError in Guest Message Deletion

**File:** `notifications/notification_manager.py` — `realtime_guest_chat_message_deleted()`  
**Problem:** `current_booking` is referenced but never defined. Every guest message delete crashes with a `NameError`.  
**Fix:** Resolve `current_booking` from the `room` parameter's active booking, or pass it explicitly from the call sites in `chat/views.py`.

### 1.2 `stock_tracker/views.py` — 15 ViewSets With No Permissions

**File:** `stock_tracker/views.py`  
**Problem:** None of the 15 ViewSets define `permission_classes`. Falls through to DRF default (`IsAuthenticated` if configured globally, otherwise `AllowAny`). Any authenticated user from any hotel can read/write stock data.  
**Fix:** Add `permission_classes = [IsAuthenticated]` to every ViewSet at minimum. Ideally use `IsSuperStaffAdminForHotel` or a new `IsStaffForHotel` permission to match `report_views.py`.

### 1.3 `MaintenanceRequestViewSet` — No Hotel Filtering

**File:** `maintenance/views.py`  
**Problem:** `queryset = MaintenanceRequest.objects.all()` — any authenticated user sees all hotels' maintenance requests.  
**Fix:** Override `get_queryset()` to filter by `request.user.staff_profile.hotel`, or adopt `HotelScopedViewSetMixin`.

### 1.4 PII Logging in Pre-Check-In Submission

**File:** `hotel/public_views.py` — `SubmitPrecheckinDataView`  
**Problem:** `print(json.dumps(request.data))` outputs guest names, emails, ID document numbers, dates of birth to stdout/logs.  
**Fix:** Remove all `print()` statements that dump `request.data`. Replace with structured `logger.info()` that logs only non-PII metadata (booking_id, field count, party size).

### 1.5 `DepartmentViewSet` / `RoleViewSet` — No Hotel Filtering

**File:** `staff/views.py`  
**Problem:** Both use `objects.all()` — cross-hotel department/role data visible to any authenticated user.  
**Fix:** Override `get_queryset()` to filter by `request.user.staff_profile.hotel`.

---

## Priority 2 — HIGH (Fix This Sprint)

### 2.1 Staff Chat Channels Lack `private-` Prefix

**Files:** `notifications/notification_manager.py`, `chat/views.py`  
**Problem:** `{slug}-conversation-{cid}-chat` channels have no `private-` prefix. Anyone with the Pusher app key can subscribe without authentication.  
**Fix:** Rename to `private-{slug}-conversation-{cid}-chat` across all trigger sites. Update `PusherAuthView` allowed patterns. Coordinate with frontend.

### 2.2 Hotel-Wide Channels Unprefixed

**File:** `notifications/notification_manager.py`  
**Problem:** `{slug}.room-bookings`, `{slug}.rooms`, `{slug}.attendance`, `{slug}.room-service` broadcast sensitive operational data on public channels.  
**Fix:** Add `private-` prefix. Update `PusherAuthView` allowed patterns. Coordinate with frontend.

### 2.3 Staff Notification Channel Naming Inconsistency

**File:** `notifications/notification_manager.py` line ~1476  
**Problem:** Uses dot format `{slug}.staff-{sid}-notifications` while all other occurrences use dash format `{slug}-staff-{sid}-notifications`. Events split across two channels — some never reach clients.  
**Fix:** Change line 1476 to use dash format to match the rest of the codebase.

### 2.4 No Availability Re-Check at Booking Creation

**File:** `hotel/services/booking.py` — `create_room_booking_from_request()`  
**Problem:** Never calls `is_room_type_available()`. Two concurrent bookings for the last room of a type can both succeed.  
**Fix:** Add `is_room_type_available()` check inside `create_room_booking_from_request()` with a `select_for_update()` lock on concurrent bookings for the same room type + date range.

### 2.5 Booking ID Race Condition

**File:** `hotel/models.py` — `_generate_unique_booking_id()`  
**Problem:** Uses `count()` + `exists()` without row locking. Concurrent creates can generate the same ID.  
**Fix:** Use database-level sequence or `select_for_update()` on the latest booking row, or switch entirely to the service-level `generate_booking_id()`.

### 2.6 Dual Booking ID Formats

**Files:** `hotel/models.py` (`BK-{YEAR}-NNNN`), `hotel/services/booking.py` (`BK-{HOTEL}-{YEAR}-NNNN`)  
**Problem:** Two different formats can coexist in the database depending on code path.  
**Fix:** Standardize on `BK-{HOTEL}-{YEAR}-NNNN` everywhere. Remove the model-level generator or make it delegate to the service.

### 2.7 `extend_overstay()` Updates Dates Before Payment

**File:** `room_bookings/services/overstay.py`  
**Problem:** Sets `booking.check_out` immediately while `BookingExtension.status` is `PENDING_PAYMENT`. If payment fails, extended dates persist.  
**Fix:** Only update `booking.check_out` in the Stripe webhook callback after payment succeeds, or implement a rollback on payment failure.

### 2.8 Overstay Views Missing Hotel-Level Permissions

**File:** `hotel/overstay_views.py`  
**Problem:** `OverstayAcknowledgeView`, `OverstayExtendView`, `OverstayStatusView` have only `IsAuthenticated` — any staff from any hotel can attempt access. Hotel scoping is done via dynamic lookup but not enforced at permission level.  
**Fix:** Add `IsSameHotel` or `IsStaffMember` + hotel cross-check to permission classes.

### 2.9 Scheduled Commands Not Deployed

**Files:** `Procfile`, `setup_heroku_scheduler.sh`  
**Problem:** 6 of 7 management commands are not in Heroku Scheduler. `auto_expire_overdue_bookings` and `flag_overstay_bookings` are essential for core business logic.  
**Fix:** Add to Heroku Scheduler:

| Command | Frequency |
|---------|-----------|
| `auto_expire_overdue_bookings` | Every 10 min |
| `flag_overstay_bookings` | Every 30 min |
| `send_scheduled_surveys` | Every hour |
| `cleanup_survey_tokens` | Daily |

### 2.10 Guest-Scoped Required Fields Not Validated in Pre-Check-In

**File:** `hotel/public_views.py` — `SubmitPrecheckinDataView`  
**Problem:** Required-field enforcement only checks top-level `request.data`, not per-guest `precheckin_payload` fields (nationality, DOB, ID docs, address).  
**Fix:** Loop over each guest's `precheckin_payload` and validate required guest-scoped fields against the config.

---

## Priority 3 — MEDIUM (Fix Next Sprint)

### 3.1 Precheckin Config Snapshot Empty Dict Fallback

**File:** `hotel/public_views.py`  
**Problem:** `if token.config_snapshot_enabled` is falsy for `{}` — falls through to current config instead of respecting the empty snapshot.  
**Fix:** Change condition to `if token.config_snapshot_enabled is not None`.

### 3.2 `NavigationItemViewSet` Optional Hotel Filtering

**File:** `staff/views.py`  
**Problem:** Filters by hotel only if `?hotel_slug=` query param is sent. Without it, returns all hotels' nav items.  
**Fix:** Make hotel filtering mandatory — return empty queryset if no hotel context.

### 3.3 `entertainment/views.py` — Mutations Open to Anyone

**Problem:** Game/tournament create/update/delete available to anonymous users. Read-only is correctly public (guest tablet).  
**Fix:** Use `IsAuthenticatedOrReadOnly` on ViewSets that allow mutations. Keep `AllowAny` only on truly read-only ViewSets.

### 3.4 `room_services/views.py` — Order Creation Open

**Problem:** `OrderViewSet` is `AllowAny` — anyone can place orders without authentication.  
**Fix:** Consider guest token validation for order creation, or at minimum require a valid room/booking context.

### 3.5 Webhook Fallback Cross-Hotel Match

**File:** Stripe webhook handler  
**Problem:** If metadata lookup fails, `payment_reference` search may match wrong booking across hotels.  
**Fix:** Add hotel scoping to the fallback query.

### 3.6 FCM Token Per-Room Not Per-Booking

**Problem:** Room reassignment overwrites guest FCM token. Multi-occupancy or quick turnover loses push notification delivery.  
**Fix:** Move FCM tokens to `BookingGuest` or a dedicated `GuestFCMToken` model.

---

## Priority 4 — LOW (Backlog)

| Finding | Detail |
|---------|--------|
| No rate limiting on token validation | Add DRF throttling to token endpoints |
| Management token never time-expires | Add configurable TTL |
| `VIEW_STATUS` vs `STATUS_READ` scope mismatch | Align scope names in webhook + resolver |
| Token in URL query parameter | Move to POST body or short-lived redirect tokens |
| Attendance: no actual-vs-planned analytics | Implement shift adherence comparison |
| Attendance: O(n) face matching | Add spatial indexing (ball tree / kd-tree) if scale requires |
| Attendance: two parallel clock-in codepaths | Consolidate legacy + enhanced paths |
| Attendance: break time not deducted from hours_worked | Subtract breaks in `ClockLog.save()` |
| No worker process (Celery/background) | Add worker dyno for async tasks |
| `clean()` not auto-called on precheckin config `save()` | Call `full_clean()` in model `save()` |

---

## Recommended Order of Attack

```
Week 1 (Critical + Quick Wins)
├── 1.1  Fix current_booking NameError          (~15 min)
├── 1.4  Remove PII print() statements          (~10 min)
├── 2.3  Fix channel naming inconsistency       (~5 min)
├── 1.2  Add permissions to stock_tracker views  (~30 min)
├── 1.3  Add hotel filtering to maintenance      (~20 min)
└── 1.5  Add hotel filtering to dept/role        (~20 min)

Week 2 (High-Impact Business Logic)
├── 2.4  Availability check at booking creation  (~1-2 hours)
├── 2.5  Fix booking ID race condition           (~1 hour)
├── 2.6  Standardize booking ID format           (~1 hour)
├── 2.7  Fix extend_overstay payment ordering    (~1-2 hours)
├── 2.8  Add permissions to overstay views       (~30 min)
└── 2.10 Fix guest-scoped field validation       (~1 hour)

Week 3 (Realtime Security + Deployment)
├── 2.1  Add private- prefix to staff chat       (~2 hours, needs frontend)
├── 2.2  Add private- prefix to hotel channels   (~2 hours, needs frontend)
├── 2.9  Deploy scheduled commands               (~30 min)
└── 3.1-3.6 Medium priority items                (~4 hours total)
```
