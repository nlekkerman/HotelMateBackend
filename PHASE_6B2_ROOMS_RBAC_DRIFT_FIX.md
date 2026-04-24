# Phase 6B.2 — Rooms RBAC Drift Fix Report

Targeted fix for the `room.out_of_order.set` capability advertised in
Phase 6B.1 but unusable in practice for `operations_admin` (and any future
role that holds `room.out_of_order.set` without `room.inventory.update`).

Source of truth: actual code in `rooms/views.py`, `rooms/serializers.py`,
`staff/permissions.py`, `staff/capability_catalog.py`,
`staff/module_policy.py`. No documentation was trusted.

---

## 1. Root Cause

Inspected — pre-fix state of `rooms/views.py::StaffRoomViewSet.get_permissions`
(actions `update` / `partial_update`):

```python
elif self.action in ('update', 'partial_update'):
    perms.append(CanUpdateRoomInventory())          # required ALWAYS
    if _payload_changes_out_of_order(self.request):
        perms.append(CanSetRoomOutOfOrder())         # added ON TOP
```

`_payload_changes_out_of_order(request)` only checked **presence** of
`is_out_of_order` on POST/PUT/PATCH. The serializer
(`rooms/serializers.py::RoomStaffSerializer`) treats `is_out_of_order` as
a normal writable field — there is no separate action endpoint and no
dedicated field-level permission gate.

Because `CanUpdateRoomInventory` was added unconditionally, every PATCH
required `room.inventory.update`. Capability resolution
(`resolve_capabilities('regular_staff', 'operations_admin', 'administration')`):

```
operations_admin = _SUPERVISOR_AUTHORITY
                 | _BOOKING_SUPERVISE
                 | _ROOM_SUPERVISE
                 | {ROOM_OUT_OF_ORDER_SET, ROOM_CHECKOUT_DESTRUCTIVE}
```

`_ROOM_SUPERVISE` does **not** include `ROOM_INVENTORY_UPDATE` (only
`_ROOM_MANAGE` does). Result: `operations_admin` was advertised
`out_of_order_set: true` in `rbac.rooms.actions`, but every PATCH that
toggled `is_out_of_order` returned 403 — the capability was decorative.

Drift confirmed and tracked as Risk #2 in `PHASE_6B1_ROOMS_RBAC_REPORT.md`.

---

## 2. Code Changes

### 2.1 `rooms/views.py` — new helper

Added `_payload_changes_only_out_of_order(request)` next to the existing
`_payload_changes_out_of_order(request)`. Returns `True` iff the PATCH/PUT
body contains `is_out_of_order` and no other writable Room field
(`csrfmiddlewaretoken` is ignored as form noise). Pure inspection — no
side effects. PUT is included so a full-body update with only this field
behaves identically.

### 2.2 `rooms/views.py` — `StaffRoomViewSet.get_permissions`

Single decision point inside the existing `update`/`partial_update`
branch. Diff:

```python
# BEFORE
elif self.action in ('update', 'partial_update'):
    perms.append(CanUpdateRoomInventory())
    if _payload_changes_out_of_order(self.request):
        perms.append(CanSetRoomOutOfOrder())

# AFTER
elif self.action in ('update', 'partial_update'):
    if _payload_changes_only_out_of_order(self.request):
        perms.append(CanReadRoomInventory())
        perms.append(CanSetRoomOutOfOrder())
    elif _payload_changes_out_of_order(self.request):
        perms.append(CanUpdateRoomInventory())
        perms.append(CanSetRoomOutOfOrder())
    else:
        perms.append(CanUpdateRoomInventory())
```

No other site changed. No new permission classes, no new endpoints, no
serializer changes, no capability-catalog changes. The fix is entirely
within the existing DRF `get_permissions` hook.

### 2.3 `hotel/tests/test_rbac_rooms.py`

Replaced the placeholder `test_patch_is_out_of_order_requires_out_of_order_cap`
(which only validated the bug-as-then-was) with five focused assertions
covering all cells of the new decision matrix.

---

## 3. Authorization Flow — Before vs After

`payload` = the writable subset of the PATCH/PUT body (excluding
`csrfmiddlewaretoken`). Writable fields per `RoomStaffSerializer.Meta`:
`room_number, room_type, is_occupied, room_status, is_active,
is_out_of_order, maintenance_required, maintenance_priority`.

| Payload composition | BEFORE — required caps | AFTER — required caps |
| --- | --- | --- |
| `{is_out_of_order}` only | `inventory.update` + `out_of_order.set` (drift: ops_admin denied) | `inventory.read` + `out_of_order.set` |
| `{is_out_of_order, …other}` | `inventory.update` + `out_of_order.set` | `inventory.update` + `out_of_order.set` (unchanged) |
| `{…other only}` | `inventory.update` | `inventory.update` (unchanged) |

Module-view (`CanViewRooms`) and the auth/staff/hotel chain
(`IsAuthenticated, IsStaffMember, IsSameHotel`) apply in every case
unchanged.

### Persona impact (after)

| Persona | `is_out_of_order`-only PATCH | Other-fields PATCH | Mixed PATCH |
| --- | --- | --- | --- |
| `front_office` regular staff | 403 (no `out_of_order.set`) | 403 (no `inventory.update`) | 403 |
| `housekeeping` regular staff | 403 | 403 | 403 |
| `housekeeping_supervisor` | 403 | 403 | 403 |
| `maintenance` regular staff | 403 | 403 | 403 |
| `operations_admin` | **200** ← drift fixed | 403 | 403 |
| `hotel_manager` | 200 | 200 | 200 |

`operations_admin` is the persona unblocked by this patch; nothing else
moves.

---

## 4. Tests Added / Updated

`hotel/tests/test_rbac_rooms.py::RoomEndpointEnforcementTest`:

| Test | Cell of decision matrix | Expected |
| --- | --- | --- |
| `test_patch_is_out_of_order_only_allowed_for_ops_admin` | ops_admin, ooo-only | 200 + `room.is_out_of_order == True` |
| `test_ops_admin_cannot_patch_non_ooo_fields` | ops_admin, other-only | 403 |
| `test_ops_admin_mixed_payload_requires_inventory_update` | ops_admin, mixed | 403 |
| `test_hk_supervisor_cannot_toggle_out_of_order` | hk_supervisor, ooo-only | 403 |
| `test_patch_is_out_of_order_allowed_for_hotel_manager` | hotel_manager, ooo-only | 200 (existing, kept) |
| `test_hotel_manager_mixed_payload_allowed` | hotel_manager, mixed | 200 |
| `test_patch_normal_field_does_not_require_out_of_order_cap` | hotel_manager, other-only | 200 (existing, kept — still passes) |

Removed the now-obsolete `test_patch_is_out_of_order_requires_out_of_order_cap`
because its sole assertion (ops_admin → 403 on ooo-only PATCH) was
documenting the bug being fixed. The new
`test_hk_supervisor_cannot_toggle_out_of_order` provides the inverse
guard (a role with neither cap is still rejected on an ooo-only payload),
which is the genuine regression risk.

Total rooms RBAC tests: **52** (was 48; +5 added, −1 removed).

---

## 5. Validation Results

```
$ python manage.py test hotel.tests.test_rbac_rooms hotel.tests.test_rbac_bookings --verbosity=2 --keepdb
Ran 82 tests.
OK
```

- `hotel.tests.test_rbac_rooms` — **52/52 pass**
- `hotel.tests.test_rbac_bookings` (Phase 6A regression) — **30/30 pass**

Capability registry & module policy were not touched, so the existing
validators remain green:

- `validate_preset_maps()` → `[]`
- `validate_module_policy()` → `[]`

No-drift verification (`rbac.rooms.actions` keys ↔ enforcement):

| Action key | Capability | Enforcement site |
| --- | --- | --- |
| `inventory_create` | `room.inventory.create` | `StaffRoomViewSet` create + `bulk_create_rooms` |
| `inventory_update` | `room.inventory.update` | `StaffRoomViewSet` update/partial_update (other-fields branches) |
| `inventory_delete` | `room.inventory.delete` | `StaffRoomViewSet` destroy |
| `type_manage` | `room.type.manage` | `StaffRoomTypeViewSet` |
| `media_manage` | `room.media.manage` | `RoomImageViewSet` |
| `out_of_order_set` | `room.out_of_order.set` | `StaffRoomViewSet` update/partial_update (ooo-only **and** mixed branches) ✅ now reachable |
| `checkout_destructive` | `room.checkout.destructive` | `checkout_rooms` imperative branch |
| `status_transition` | `room.status.transition` | `start_cleaning`, `mark_cleaned` |
| `maintenance_flag` | `room.maintenance.flag` | `mark_maintenance` |
| `inspect` | `room.inspection.perform` | `inspect_room` |
| `maintenance_clear` | `room.maintenance.clear` | `complete_maintenance` |
| `checkout_bulk` | `room.checkout.bulk` | `checkout_rooms` |

Grep over `rooms/views.py` confirms exactly two callers of the
out-of-order helpers — both inside the same `get_permissions` block — and
no leftover references to the previous unconditional
`CanUpdateRoomInventory()` PATCH gate.

---

## 6. Remaining Risks

1. **Body-content-driven permission decision.** The PATCH branch consults
   `request.data`, which DRF parses before `get_permissions` runs, but
   means the gate can be bypassed only by a serializer that silently
   accepts unknown keys. `RoomStaffSerializer` is a `ModelSerializer`
   with explicit `Meta.fields` — extra keys are ignored at validation
   time, but extra-key payloads will still be classified as "mixed" by
   `_payload_changes_only_out_of_order` (any non-ignored key that isn't
   `is_out_of_order` flips the branch to require `inventory.update`).
   That is the safe direction.
2. **PUT semantics.** A full PUT carrying every field will require
   `inventory.update`, which is correct for a true replacement. A PUT
   that happens to carry only `is_out_of_order` will route through the
   ooo-only branch — also correct.
3. **No new endpoint** was introduced even though "PATCH-only-OOO" is
   semantically a sub-action; the user explicitly forbade adding
   endpoints, and the DRF permission hook is the canonical surface for
   this kind of conditional gate.
4. Phase 6B.1 Risk #2 ("ops_admin cannot toggle is_out_of_order") is now
   **closed**. Risks #1, #3, #4, #5 from that report are unaffected by
   this change.

---

## 7. Final Status — GO / NO-GO

**GO.**

- Drift closed: `room.out_of_order.set` is enforceable end-to-end for the
  exact persona that holds it (`operations_admin`).
- No regression in inventory CRUD, room types, media, turnover,
  maintenance, or checkout flows (52/52 + 30/30 green).
- No new capabilities, no new endpoints, no preset reshuffle, no
  serializer changes — the patch is surgical.
- No "advertised but unusable" capability remains in `rbac.rooms.actions`.
