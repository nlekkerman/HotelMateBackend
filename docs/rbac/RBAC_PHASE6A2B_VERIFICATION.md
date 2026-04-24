# Phase 6A.2.B — Bookings RBAC Post-Implementation Verification

All findings derived from live registry execution (`staff/capability_catalog.py`,
`staff/module_policy.py`, `staff/permissions.py`) and a direct call to
`resolve_capabilities()` + `resolve_module_policy()` for the 6 personas.
Not read from docs.

---

## A. Capability distribution per persona

Buckets are derived from the preset containment relation:
- **read** = `booking.module.view` + `booking.record.read`
- **operate** = read ∪ `record.update, record.cancel, room.assign, stay.checkin, stay.checkout, stay.extend, guest.communicate`
- **supervise** = operate ∪ `booking.override.supervise`
- **manage** = supervise ∪ `booking.config.manage`

| # | Persona (tier + dept + role) | read | operate | supervise | manage | Final `actions` TRUE |
|---|---|---|---|---|---|---|
| 1 | `regular_staff` + `front_office` + — | ✅ | ✅ | ❌ | ❌ | update, cancel, assign_room, checkin, checkout, extend, communicate |
| 2 | `regular_staff` + `housekeeping` + — | ❌ | ❌ | ❌ | ❌ | *(none)* — module not visible |
| 3 | `staff_admin` + — + — | ❌ | ❌ | ❌ | ❌ | *(none)* — module not visible |
| 4 | `super_staff_admin` + `food_beverage` + — | ✅ | ✅ | ✅ | ❌ | update, cancel, assign_room, checkin, checkout, extend, communicate, override_conflicts, force_checkin, force_checkout, resolve_overstay, modify_locked |
| 5 | `regular_staff` + `front_office` + `front_office_manager` | ✅ | ✅ | ✅ | ✅ | all 13 including `manage_rules` |
| 6 | `regular_staff` + — + `operations_admin` | ✅ | ✅ | ✅ | ❌ | same as persona 4 |

Key observations matching Phase 6A.2 intent:
- Persona 1 now gets operate via `DEPARTMENT_PRESET_CAPABILITIES['front_office']` —
  the critical audit break is fixed.
- Persona 3 (`staff_admin` alone) cannot see bookings — tier no longer grants
  booking caps; `staff_admin` tier baseline is pure supervisor authority
  (chat/housekeeping moderation), no `booking.*`.
- Persona 4 shows that `super_staff_admin` still carries `_BOOKING_SUPERVISE`,
  which by preset-union includes `_BOOKING_OPERATE`. This is intentional
  (supervise ⊇ operate) but means *any* department under `super_staff_admin`
  tier can operate bookings regardless of dept preset. The audit was accepted
  as-is (tier carries supervise, not manage).
- Persona 5 is the only persona with `manage_rules` = true, sourced from the
  `front_office_manager` role preset alone. Tier does not grant manage.
- Persona 6 (`operations_admin` on `regular_staff`) shows the audit downgrade
  took effect: `operations_admin` is now SUPERVISE, not MANAGE (no
  `manage_rules`).

---

## B. `/me → rbac.bookings` payload shape (computed live)

Payload is emitted by `resolve_effective_access()` →
`resolve_module_policy(allowed_capabilities)` in `staff/permissions.py`.
Shape is fixed: `{ visible, read, actions }`.

### Operate-only (Persona 1: front desk agent)
```json
{
  "visible": true,
  "read": true,
  "actions": {
    "update": true, "cancel": true, "assign_room": true,
    "checkin": true, "checkout": true, "extend": true, "communicate": true,
    "override_conflicts": false, "force_checkin": false, "force_checkout": false,
    "resolve_overstay": false, "modify_locked": false,
    "manage_rules": false
  }
}
```

### Supervise-only (Persona 6: operations_admin)
```json
{
  "visible": true,
  "read": true,
  "actions": {
    "update": true, "cancel": true, "assign_room": true,
    "checkin": true, "checkout": true, "extend": true, "communicate": true,
    "override_conflicts": true, "force_checkin": true, "force_checkout": true,
    "resolve_overstay": true, "modify_locked": true,
    "manage_rules": false
  }
}
```

### Manage (Persona 5: front_office_manager)
```json
{
  "visible": true,
  "read": true,
  "actions": {
    "update": true, "cancel": true, "assign_room": true,
    "checkin": true, "checkout": true, "extend": true, "communicate": true,
    "override_conflicts": true, "force_checkin": true, "force_checkout": true,
    "resolve_overstay": true, "modify_locked": true,
    "manage_rules": true
  }
}
```

Action keyset is exactly `BOOKINGS_ACTIONS` keys — no extra or orphaned keys.
No `actions.create` emitted.

---

## C. Endpoint map — final enforced capability bucket

All at `/api/staff/hotel/{slug}/room-bookings/…`. Every entry chains
`IsAuthenticated + IsStaffMember + IsSameHotel + CanViewBookings +
CanReadBookings`. The "Bucket" column lists the additional gate.

Mount file: `room_bookings/staff_urls.py`

| Method + Path | View | Extra gate | Bucket |
|---|---|---|---|
| GET `` | `StaffBookingsListView` | *(read only)* | read |
| GET `<id>/` | `StaffBookingDetailView` | *(read only)* | read |
| POST `<id>/mark-seen/` | `StaffBookingMarkSeenView` | *(read only)* | read |
| POST `<id>/confirm/` | `StaffBookingConfirmView` | `CanUpdateBooking` | operate |
| POST `<id>/cancel/` | `StaffBookingCancelView` | `CanCancelBooking` | operate |
| GET `<id>/party/` | `BookingPartyManagementView.get` | *(read only)* | read |
| PUT `<id>/party/companions/` | `BookingPartyManagementView.put` | `CanUpdateBooking` (method-gated) | operate |
| GET `<id>/available-rooms/` | `AvailableRoomsView` | *(read only)* | read |
| POST `<id>/safe-assign-room/` | `SafeAssignRoomView` | `CanAssignBookingRoom` | operate |
| POST `<id>/unassign-room/` | `UnassignRoomView` | `CanAssignBookingRoom` | operate |
| POST `<id>/move-room/` | `MoveRoomView` | `CanAssignBookingRoom` | operate |
| POST `<id>/check-in/` | `BookingCheckInView` | `CanCheckInBooking` | operate |
| POST `<id>/check-out/` | `BookingCheckOutView` | `CanCheckOutBooking` | operate |
| POST `<id>/send-precheckin-link/` | `SendPrecheckinLinkView` | `CanCommunicateWithBookingGuest` | operate |
| POST `<id>/send-survey-link/` | `SendSurveyLinkView` | `CanCommunicateWithBookingGuest` | operate |
| POST `<id>/approve/` | `StaffBookingAcceptView` | `CanSuperviseBooking` | supervise |
| POST `<id>/decline/` | `StaffBookingDeclineView` | `CanSuperviseBooking` | supervise |
| POST `<id>/overstay/acknowledge/` | `OverstayAcknowledgeView` | `CanSuperviseBooking` | supervise |
| POST `<id>/overstay/extend/` | `OverstayExtendView` | `CanSuperviseBooking` | **supervise** |
| GET `<id>/overstay/status/` | `OverstayStatusView` | *(read only)* | read |

**Legacy gate scan on booking operational endpoints** — grep for
`HasAdminSettingsNav`, `HasRoomBookingsNav`, `IsSuperStaffAdminForHotel`,
`IsStaffAdminOrAbove`, `HasNavPermission('room_bookings')`: zero matches on any
of the 20 routed booking-operational views. **Clean.** The dead
`BookingAssignmentView` from the original audit no longer exists in the code.

---

## D. Booking-config surface — final inventory

All booking-scoped config endpoints now route through `CanManageBookingConfig`
(slug `booking.config.manage`) on mutating methods, and `CanViewBookings +
CanReadBookings` on GET.

| Path | View | GET gate | Mutation gate |
|---|---|---|---|
| `/api/staff/hotel/<slug>/precheckin-config/` | `HotelPrecheckinConfigView` (`hotel/staff_views.py`) | read | `CanManageBookingConfig` |
| `/api/staff/hotel/<slug>/survey-config/` | `HotelSurveyConfigView` (`hotel/staff_views.py`) | read | `CanManageBookingConfig` |
| `/api/staff/hotel/<slug>/rate-plans/` (list+detail) | `hotel/views/rate_plans/views.py` | read | `CanManageBookingConfig` |
| `/api/staff/hotel/<slug>/cancellation-policies/` (list+detail+templates) | `hotel/views/cancellation_policies/views.py` | read | `CanManageBookingConfig` |

**Legacy-gated or ungated siblings:** none within the booking-config scope.
The two remaining `HasAdminSettingsNav` callers are `StaffAccessConfigViewSet`
(hotel access/theme config) and `HotelSettingsView` (hotel basic info/theme),
both in `hotel/staff_views.py`. Both are **hotel-level, not booking-level**,
so they correctly remain outside the booking capability namespace.

---

## E. Leftover semantic loose ends

Strict scan against the implementation:

1. **`booking.stay.extend` / `CanExtendBooking` — LIVE CONTRACT DRIFT.**
   - Capability `BOOKING_STAY_EXTEND` is still in `CANONICAL_CAPABILITIES`,
     still in `_BOOKING_OPERATE`, still mapped as
     `'extend': BOOKING_STAY_EXTEND` in `BOOKINGS_ACTIONS`.
   - Permission class `CanExtendBooking` is defined in
     `staff/permissions.py` but **imported by zero views** (verified via
     grep).
   - The only extend endpoint (`OverstayExtendView`) was re-gated to
     `CanSuperviseBooking` per the audit fix.
   - **Effect**: the frontend sees `rbac.bookings.actions.extend = true` for
     any operate-bucket persona (Persona 1), but calling
     `POST /overstay/extend/` will 403 because the endpoint requires
     supervise. This is exactly the kind of action-vs-endpoint misalignment
     Phase 6A was designed to eliminate.
   - **Required fix (Phase 6A.3, pre-rooms):** choose one:
     - (a) Remove `'extend'` from `BOOKINGS_ACTIONS`, delete
       `CanExtendBooking`, delete `BOOKING_STAY_EXTEND` from canonical +
       `_BOOKING_OPERATE`; OR
     - (b) Re-map `'extend'` → `BOOKING_OVERRIDE_SUPERVISE` in
       `BOOKINGS_ACTIONS` and remove `BOOKING_STAY_EXTEND` entirely; OR
     - (c) Split into two caps (`extend` regular vs `extend_overstay`
       supervise) and wire a non-overstay extend endpoint — only if product
       actually wants a regular-stay extend.

2. **`booking.record.create` — gone.** Not in catalog, not in actions, not
   in any preset. Clean. No `actions.create` key reaches the frontend
   payload.

3. **`BookingAssignmentView` dead-code import — gone.** Confirmed by grep;
   no matches in any `.py` file outside `promo_docs/`.

4. **`MarkSeen` semantic over-gating — FIXED.** `StaffBookingMarkSeenView`
   now requires only `CanViewBookings + CanReadBookings` (not
   `CanUpdateBooking`). Matches dashboard-metadata intent.

5. **`Stripe approve/decline` re-gating — FIXED.**
   `StaffBookingAcceptView` / `StaffBookingDeclineView` now require
   `CanSuperviseBooking` (financial-decision bucket), not
   `record.update`/`record.cancel`.

6. **Namespace risk (`booking.*` vs `bookings/` app vs `room_bookings/`
   app):** still present. Not a bug per se but one pattern-match away from
   a future contributor wiring a restaurant-`bookings/` endpoint to a
   `CanManageBookingConfig`. Recommend renaming capability namespace to
   `room_booking.*` as a Phase 6A.3 item.

7. **`BOOKINGS_ACTIONS` key integrity:** all 13 keys (`update, cancel,
   assign_room, checkin, checkout, extend, communicate, override_conflicts,
   force_checkin, force_checkout, resolve_overstay, modify_locked,
   manage_rules`) map to a canonical capability. `validate_module_policy()`
   = []. Aside from the `extend` drift in (1), every action boolean the
   frontend reads corresponds to a real enforced endpoint gate.

---

## F. Final readiness decision

1. **Is bookings now clean enough to be the backend reference module?**
   **No, not yet.** It is 95% there, but item E-1 (`booking.stay.extend` /
   `CanExtendBooking` / `actions.extend`) is a live contract drift between
   `module_policy` (advertises operate) and the sole routed endpoint
   (enforces supervise). A reference module must have zero
   advertised-vs-enforced gap.

2. **Can frontend F2 bookings capability consumption begin?** **Yes, with
   one caveat.** The payload shape is stable, the 12 other action booleans
   are trustworthy end-to-end, and consuming
   `rbac.bookings.{visible, read, actions.*}` in the UI is safe. Caveat:
   the frontend must either (a) not render an "Extend" button off
   `actions.extend`, or (b) skip that key until E-1 is resolved, because
   clicking it on an operate-only user will 403.

3. **Can backend Phase 6B rooms begin?** **No.** Phase 6A.3 (below) must
   land first — otherwise rooms will inherit the same
   advertised-vs-enforced drift pattern and we lose the ability to call
   bookings the reference.

4. **Is Phase 6A.3 naming / cleanup required before rooms?** **Yes.**
   Minimum scope:
   - Resolve E-1 (pick option a, b, or c).
   - Delete `CanExtendBooking` if not wired by (c).
   - Optional but recommended: rename namespace `booking.*` →
     `room_booking.*` (E-6) now while only one module uses it; doing this
     after Phase 6B will churn rooms too.
   - Re-run `validate_module_policy()` and `validate_preset_maps()` — both
     must remain [] — and re-run the persona probe to confirm action
     booleans match enforcement.
