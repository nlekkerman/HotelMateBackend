# Operations Admin Role Removal — Implementation Report

**Date:** 2026-04-25
**Status:** Complete

---

## 1. Goal

Completely remove the role slug `operations_admin` from the HotelMate
backend without breaking RBAC integrity or existing data.

---

## 2. Files Modified

| File | Change |
|------|--------|
| [staff/role_catalog.py](staff/role_catalog.py) | Removed `operations_admin` from `CANONICAL_ROLES`. Updated `LEGACY_ROLE_REMAP['admin']` → `hotel_manager`. Updated `_MANAGER_BY_DEPT['administration']` → `hotel_manager`. |
| [staff/capability_catalog.py](staff/capability_catalog.py) | Removed `'operations_admin'` entry from `ROLE_PRESET_CAPABILITIES`. Cleaned all docstring / comment references. |
| [staff/migrations/0028_remove_operations_admin_role.py](staff/migrations/0028_remove_operations_admin_role.py) | **NEW** — Data migration that reassigns existing Staff and deletes orphaned `operations_admin` Role rows. |
| [rooms/views.py](rooms/views.py) | Updated two comments (replaced `operations_admin` example with `maintenance_manager`, the remaining role that holds `room.out_of_order.set` without `room.inventory.update`). |
| [scripts/validation/rbac_phase6a_validation.py](scripts/validation/rbac_phase6a_validation.py) | Removed the `operations_admin` validation persona block. |
| [hotel/tests/test_rbac_bookings.py](hotel/tests/test_rbac_bookings.py) | Removed `test_operations_admin_role_carries_booking_supervise`, `test_overstay_acknowledge_allowed_for_operations_admin`, and the `cls.ops_admin` fixture. |
| [hotel/tests/test_rbac_housekeeping.py](hotel/tests/test_rbac_housekeeping.py) | Removed `test_operations_admin_supervises` and the `cls.ops_admin` fixture. |
| [hotel/tests/test_rbac_maintenance.py](hotel/tests/test_rbac_maintenance.py) | Removed `test_operations_admin_full_bundle`. |
| [hotel/tests/test_rbac_staff_management.py](hotel/tests/test_rbac_staff_management.py) | Removed `test_operations_admin_manager_bundle`. |

`hotel/tests/test_rbac_rooms.py` was checked: it contains **no**
`operations_admin` / `ops_admin` references after the cleanup, and all
51 tests in that suite pass.

---

## 3. References Removed (Inventory)

### Role definition / canonical catalog
- `CANONICAL_ROLES` entry — REMOVED.
- `LEGACY_ROLE_REMAP['admin']` — retargeted to `hotel_manager`.
- `_MANAGER_BY_DEPT['administration']` — retargeted to `hotel_manager`.

### `ROLE_PRESET_CAPABILITIES`
- `'operations_admin'` key — REMOVED. No other preset references it.

### Logic branches
- None in production code (no `if role_slug == 'operations_admin'`).
- Two comments in `rooms/views.py` mentioned the role as an example —
  updated to `maintenance_manager`.

### Tests removed
- `test_rbac_bookings.py::test_operations_admin_role_carries_booking_supervise`
- `test_rbac_bookings.py::test_overstay_acknowledge_allowed_for_operations_admin`
- `test_rbac_housekeeping.py::test_operations_admin_supervises`
- `test_rbac_maintenance.py::test_operations_admin_full_bundle`
- `test_rbac_staff_management.py::test_operations_admin_manager_bundle`
- Unused `cls.ops_admin` fixtures dropped from `test_rbac_bookings.py`
  and `test_rbac_housekeeping.py`.

### Migrations / seed scripts
- `staff/migrations/0027_seed_canonical_roles.py` imports
  `CANONICAL_ROLES` symbolically; no literal change required.
- `scripts/validation/rbac_phase6a_validation.py` — block removed.

### Documentation
- Markdown reports under `docs/` and the phase 6 reports at the
  repository root still mention `operations_admin` for historical
  reasons. **Per the cleanup brief, code is the source of truth — docs
  were left untouched.** They are not loaded at runtime and do not
  affect RBAC.

---

## 4. Migration Strategy (Existing Data)

Created [staff/migrations/0028_remove_operations_admin_role.py](staff/migrations/0028_remove_operations_admin_role.py).

**Fallback used:** `hotel_manager` (preferred fallback per the spec).

Reasoning:
- `hotel_manager` is the closest canonical persona that retains the
  bundle the legacy `operations_admin` carried
  (`_STAFF_MANAGEMENT_MANAGER` + `_MAINTENANCE_MANAGE` +
  housekeeping/booking authority via role preset).

Migration steps:
1. Iterate all `Role` rows with `slug='operations_admin'`.
2. For each affected `Staff`, find — or create when the `management`
   department exists — the canonical `hotel_manager` Role for that
   staff's hotel and reassign `staff.role`.
3. Defensive fallback: if the hotel is missing the `management`
   department (it should not — 0025 seeds it), set `staff.role` to
   `NULL` so the legacy row can be deleted cleanly.
4. Delete orphaned `operations_admin` Role rows.

Non-reversible (consistent with `0027_seed_canonical_roles`).

---

## 5. Validation Results

```
validate_preset_maps()    -> []
validate_module_policy()  -> []
```

Test command:
```
python manage.py test hotel.tests.test_rbac_bookings hotel.tests.test_rbac_rooms hotel.tests.test_rbac_housekeeping hotel.tests.test_rbac_maintenance hotel.tests.test_rbac_staff_management -v 2
```

Result: **223 tests passed, 0 failures.** All targeted module suites
covered: bookings, rooms, housekeeping, maintenance, staff_management.

---

## 6. Assumptions

- The `LEGACY_ROLE_REMAP['admin']` retarget changes the legacy `admin`
  fallback from `operations_admin` to `hotel_manager`. Since
  `0027_seed_canonical_roles` has already executed on existing
  databases (no remaining `admin` legacy rows), this only affects
  re-runs / fresh installs.
- Documentation files were intentionally left untouched (code is the
  source of truth).

---

## 7. Confirmation

- ✅ `operations_admin` role no longer exists in the canonical catalog.
- ✅ `operations_admin` removed from `ROLE_PRESET_CAPABILITIES`.
- ✅ Legacy remap targets retargeted to `hotel_manager`.
- ✅ Data migration in place to safely reassign existing Staff.
- ✅ No commented-out code, no dead imports, no partial references in
  production / test code.
- ✅ `validate_preset_maps()` and `validate_module_policy()` both
  return `[]`.
- ✅ All RBAC test suites pass (223/223).
