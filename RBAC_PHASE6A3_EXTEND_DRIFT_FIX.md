# Phase 6A.3 — Booking Extend Capability Drift: FIXED

## Contract Problem

Before this pass there was a live mismatch:

- `rbac.bookings.actions.extend` was `true` for **operate** users
  (front_office dept preset granted `booking.stay.extend`).
- BUT the only real endpoint, `POST /api/staff/hotel/{slug}/room-bookings/{id}/overstay/extend/`
  (`OverstayExtendView`), required `booking.override.supervise` via
  `CanSuperviseBooking`.

Frontend rendered an Extend button for operate users; backend rejected
the click as 403. Alignment strategy chosen: **collapse `extend` into
the supervise bucket** (option a/b from the 6A.2b verification doc) —
because the overstay-extend flow is an override action, not a
day-to-day operate action.

---

## Files Modified

| File | Change |
|------|--------|
| [staff/capability_catalog.py](staff/capability_catalog.py) | Deleted `BOOKING_STAY_EXTEND` slug constant + docstring; removed from `CANONICAL_CAPABILITIES`; removed from `_BOOKING_OPERATE` preset bundle. |
| [staff/module_policy.py](staff/module_policy.py) | Dropped `BOOKING_STAY_EXTEND` import. Remapped `'extend' → BOOKING_OVERRIDE_SUPERVISE` under the Supervise bucket in `BOOKINGS_ACTIONS`. |
| [staff/permissions.py](staff/permissions.py) | Deleted `CanExtendBooking` permission class; removed `BOOKING_STAY_EXTEND` import. |
| [hotel/tests/test_rbac_bookings.py](hotel/tests/test_rbac_bookings.py) | Removed `BOOKING_STAY_EXTEND` import; `test_front_office_dept_preset_grants_operate` now asserts `extend=False` (supervise-only); removed from `operate_only` synthetic capability set in `test_bucket_non_implication_via_capability_sets`. |
| [rbac_phase6a_validation.py](rbac_phase6a_validation.py) | Removed `BOOKING_STAY_EXTEND` import & scenario cap; moved `'extend'` from the operate-action list to the supervise-action list in the bucket-separation checks. |

---

## Alignment Confirmation

- `OverstayExtendView` remains gated by `CanSuperviseBooking`
  ([hotel/overstay_views.py](hotel/overstay_views.py#L105)) — not
  touched by this pass.
- No endpoint references `CanExtendBooking`. Class is gone from
  [staff/permissions.py](staff/permissions.py); repo-wide grep returns
  zero code hits (only historical audit docs).
- `BOOKING_STAY_EXTEND` slug is gone from
  [staff/capability_catalog.py](staff/capability_catalog.py) — any
  import site outside tests would now fail loudly at import time.
  Grep confirms no remaining code references.
- `validate_module_policy()` → `[]`
- `validate_preset_maps()`  → `[]`
- `hotel.tests.test_rbac_bookings` — **30 / 30 pass**.
- Persona probe (`rbac_phase6a_probe.py`) across all active staff:
  - every `super_staff_admin` persona (front_office_manager,
    fnb_manager, bare super_staff_admin) → `actions.extend = true`.
  - every operate-only / regular_staff persona (waiter,
    front_office regular_staff) → `actions.extend = false`.
  - **No operate-only user receives `extend = true`.**

---

## `rbac.bookings` Example Payloads

### Operate user (e.g. `front_office` `regular_staff`, `front_desk_agent`)

```json
{
  "visible": true,
  "read": true,
  "actions": {
    "update": true,
    "cancel": true,
    "assign_room": true,
    "checkin": true,
    "checkout": true,
    "communicate": true,
    "extend": false,
    "override_conflicts": false,
    "force_checkin": false,
    "force_checkout": false,
    "resolve_overstay": false,
    "modify_locked": false,
    "manage_rules": false
  }
}
```

### Supervise user (e.g. `super_staff_admin`, `operations_admin`, `front_office_manager`)

```json
{
  "visible": true,
  "read": true,
  "actions": {
    "update": true,
    "cancel": true,
    "assign_room": true,
    "checkin": true,
    "checkout": true,
    "communicate": true,
    "extend": true,
    "override_conflicts": true,
    "force_checkin": true,
    "force_checkout": true,
    "resolve_overstay": true,
    "modify_locked": true,
    "manage_rules": false
  }
}
```

`actions.extend` now flips `true` **iff and only iff** the resolved
capability set contains `booking.override.supervise` — exactly what
`OverstayExtendView` enforces server-side. Zero contract drift in the
`bookings` module.
