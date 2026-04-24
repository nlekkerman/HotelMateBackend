# Phase 6B.1 — Rooms RBAC Implementation Report

Source of truth: **actual backend code**. Every claim below is verified against
`staff/capability_catalog.py`, `staff/module_policy.py`, `staff/permissions.py`,
`rooms/views.py`, `rooms/urls.py`, `hotel/staff_views.py`, `hotel/staff_urls.py`,
and `housekeeping/services.py` + `housekeeping/policy.py`. Where documentation
disagreed with code, **code won**.

---

## 1. Files Modified

| File | Change |
| --- | --- |
| `staff/capability_catalog.py` | +17 `ROOM_*` canonical capability constants; 4 nested `_ROOM_*` bucket frozensets; preset updates for `operations_admin`, `hotel_manager`, `front_office_manager`, new `housekeeping_supervisor`, `housekeeping_manager`, `maintenance_supervisor`, `maintenance_manager`; dept updates for `front_office`, `housekeeping`, new `maintenance`. |
| `staff/module_policy.py` | +`MODULE_POLICY['rooms']` entry with `view_capability`, `read_capability`, and 12 action keys. |
| `staff/permissions.py` | Deleted tier-based `CanManageRooms` class. Added 17 `HasCapability` subclasses. |
| `rooms/views.py` | Removed imports/uses of `HasNavPermission`, `HasRoomsNav`, `CanManageRooms`. Added capability imports. Rewired `StaffRoomViewSet`, `RoomImageViewSet`, `checkout_rooms`, `start_cleaning`, `mark_cleaned`, `inspect_room`, `mark_maintenance`, `complete_maintenance`, `turnover_rooms`, `turnover_stats`, `bulk_create_rooms` to capability classes. Added `_payload_changes_out_of_order` helper for PATCH `is_out_of_order` escalation. Removed `request.user.is_superuser` shortcut in `checkout_rooms`. |
| `hotel/staff_views.py` | Dropped `CanManageRooms` import. Added `CanViewRooms`, `CanReadRoomTypes`, `CanManageRoomTypes`. Rewired `StaffRoomTypeViewSet.get_permissions`. |
| `hotel/tests/test_rbac_rooms.py` | **NEW** — 4 test classes, 48 tests total. |

No other rooms-touching modules required changes: `rooms/urls.py`, `hotel/staff_urls.py`,
`room_bookings/*`, `room_services/*` were verified by grep and left as-is.

---

## 2. Capabilities Added

All 17 are registered in `CANONICAL_CAPABILITIES` and validated by
`validate_preset_maps()`:

| Constant | Slug |
| --- | --- |
| `ROOM_MODULE_VIEW` | `room.module.view` |
| `ROOM_INVENTORY_READ` | `room.inventory.read` |
| `ROOM_INVENTORY_CREATE` | `room.inventory.create` |
| `ROOM_INVENTORY_UPDATE` | `room.inventory.update` |
| `ROOM_INVENTORY_DELETE` | `room.inventory.delete` |
| `ROOM_TYPE_READ` | `room.type.read` |
| `ROOM_TYPE_MANAGE` | `room.type.manage` |
| `ROOM_MEDIA_READ` | `room.media.read` |
| `ROOM_MEDIA_MANAGE` | `room.media.manage` |
| `ROOM_STATUS_READ` | `room.status.read` |
| `ROOM_STATUS_TRANSITION` | `room.status.transition` |
| `ROOM_INSPECTION_PERFORM` | `room.inspection.perform` |
| `ROOM_MAINTENANCE_FLAG` | `room.maintenance.flag` |
| `ROOM_MAINTENANCE_CLEAR` | `room.maintenance.clear` |
| `ROOM_OUT_OF_ORDER_SET` | `room.out_of_order.set` |
| `ROOM_CHECKOUT_BULK` | `room.checkout.bulk` |
| `ROOM_CHECKOUT_DESTRUCTIVE` | `room.checkout.destructive` |

**Deliberately OMITTED:** `room.qr.generate`. Verified by grep — no endpoint
in `rooms/` or `hotel/` declares a `generate_qr` action. `hotel_info` and
`entertainment` apps have their own `generate_qr` handlers; those are
gated by their own module policies, not rooms. Adding a rooms QR capability
here would create advertised-vs-enforced drift.

---

## 3. Module Policy Added

`staff/module_policy.py::MODULE_POLICY['rooms']`:

```python
'rooms': {
    'view_capability': ROOM_MODULE_VIEW,
    'read_capability': ROOM_INVENTORY_READ,
    'actions': {
        'inventory_create':     ROOM_INVENTORY_CREATE,
        'inventory_update':     ROOM_INVENTORY_UPDATE,
        'inventory_delete':     ROOM_INVENTORY_DELETE,
        'type_manage':          ROOM_TYPE_MANAGE,
        'media_manage':         ROOM_MEDIA_MANAGE,
        'out_of_order_set':     ROOM_OUT_OF_ORDER_SET,
        'checkout_destructive': ROOM_CHECKOUT_DESTRUCTIVE,
        'status_transition':    ROOM_STATUS_TRANSITION,
        'maintenance_flag':     ROOM_MAINTENANCE_FLAG,
        'inspect':              ROOM_INSPECTION_PERFORM,
        'maintenance_clear':    ROOM_MAINTENANCE_CLEAR,
        'checkout_bulk':        ROOM_CHECKOUT_BULK,
    },
},
```

`validate_module_policy()` returns `[]` — every advertised key maps to a
canonical capability backed by enforcement code.

---

## 4. Distribution Model — Tiers / Departments / Roles

**Nested bucket definitions** (`staff/capability_catalog.py`):

```
_ROOM_READ      = {MODULE_VIEW, INVENTORY_READ, TYPE_READ, MEDIA_READ, STATUS_READ}
_ROOM_OPERATE   = _ROOM_READ      ∪ {STATUS_TRANSITION, MAINTENANCE_FLAG}
_ROOM_SUPERVISE = _ROOM_OPERATE   ∪ {INSPECTION_PERFORM, MAINTENANCE_CLEAR,
                                     CHECKOUT_BULK}
_ROOM_MANAGE    = _ROOM_SUPERVISE ∪ {INVENTORY_CREATE, INVENTORY_UPDATE,
                                     INVENTORY_DELETE, TYPE_MANAGE,
                                     MEDIA_MANAGE, OUT_OF_ORDER_SET,
                                     CHECKOUT_DESTRUCTIVE}
```

**Tier presets — no room capabilities:**

| Tier | Rooms contribution |
| --- | --- |
| `super_staff_admin` | ∅ |
| `staff_admin` | ∅ |
| `regular_staff` | ∅ |

Verified by `RoomPolicyRegistryTest.test_no_room_capability_in_any_tier_preset`.

**Department presets:**

| Department | Rooms contribution |
| --- | --- |
| `front_office` | `_ROOM_READ` |
| `housekeeping` | `_ROOM_OPERATE` (+ `HOUSEKEEPING_ROOM_STATUS_TRANSITION`) |
| `maintenance` | `_ROOM_READ ∪ {ROOM_MAINTENANCE_FLAG, HOUSEKEEPING_ROOM_STATUS_TRANSITION}` |
| `kitchen` | ∅ |
| `food_beverage` | ∅ |

**Role presets (additive):**

| Role | Rooms contribution |
| --- | --- |
| `operations_admin` | `_ROOM_SUPERVISE ∪ {OUT_OF_ORDER_SET, CHECKOUT_DESTRUCTIVE}` |
| `hotel_manager` | `_ROOM_MANAGE` |
| `front_office_manager` | `_ROOM_SUPERVISE` |
| `housekeeping_supervisor` | `_ROOM_SUPERVISE ∪ {HOUSEKEEPING_ROOM_STATUS_OVERRIDE}` |
| `housekeeping_manager` | `_ROOM_SUPERVISE ∪ {HOUSEKEEPING_ROOM_STATUS_OVERRIDE}` |
| `maintenance_supervisor` | `{ROOM_MAINTENANCE_CLEAR, HOUSEKEEPING_ROOM_STATUS_OVERRIDE}` |
| `maintenance_manager` | `{ROOM_MAINTENANCE_CLEAR, ROOM_OUT_OF_ORDER_SET, HOUSEKEEPING_ROOM_STATUS_OVERRIDE}` |

**Why `HOUSEKEEPING_ROOM_STATUS_OVERRIDE/TRANSITION` leak into rooms presets**:
`rooms/views.py::mark_maintenance` and `complete_maintenance` call the
canonical `housekeeping.services.set_room_status`, which consults
`housekeeping.policy.can_change_room_status`. That policy gates on
`housekeeping.room_status.*`. Without these caps attached, a user with
`room.maintenance.flag` but no housekeeping cap would hit a 400 at the
state machine. Attaching them here eliminates advertised-vs-enforced drift.
Code won over docs here: the housekeeping policy matrix does **not** allow
`MAINTENANCE_REQUIRED → CHECKOUT_DIRTY` via `TRANSITION`, only via
`OVERRIDE` — so every role that clears maintenance carries `OVERRIDE`.

---

## 5. Permission Classes Added / Removed

### Removed

- `staff.permissions.CanManageRooms` — the tier-based class. Its only
  two callsites (`rooms/views.py::StaffRoomViewSet`, `RoomImageViewSet`)
  were both rewired. Verified absent by
  `RoomLegacyGateRemovalTest.test_CanManageRooms_class_removed_from_staff_permissions`.

### Added (17)

All subclasses of `HasCapability` with `required_capability` pointing to a
canonical slug. Read/view gates (`CanViewRooms`, `CanReadRoomInventory`,
`CanReadRoomTypes`, `CanReadRoomMedia`, `CanReadRoomStatus`) use
`safe_methods_bypass = False` — reads must hold the read capability.

`CanViewRooms`, `CanReadRoomInventory`, `CanCreateRoomInventory`,
`CanUpdateRoomInventory`, `CanDeleteRoomInventory`, `CanReadRoomTypes`,
`CanManageRoomTypes`, `CanReadRoomMedia`, `CanManageRoomMedia`,
`CanReadRoomStatus`, `CanTransitionRoomStatus`, `CanInspectRoom`,
`CanFlagRoomMaintenance`, `CanClearRoomMaintenance`, `CanSetRoomOutOfOrder`,
`CanBulkCheckoutRooms`, `CanDestructiveCheckoutRooms`.

---

## 6. Endpoint Mapping

Every URL reachable under the rooms module, with the exact permission
chain from source.

| Method | URL (under `/api/staff/hotel/<slug>/`) | Permission chain |
| --- | --- | --- |
| GET | `room-management/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomInventory |
| GET | `room-management/<room_number>/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomInventory |
| POST | `room-management/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomInventory, CanCreateRoomInventory |
| PUT/PATCH | `room-management/<room_number>/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomInventory, CanUpdateRoomInventory, **+CanSetRoomOutOfOrder iff `is_out_of_order` in payload** |
| DELETE | `room-management/<room_number>/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomInventory, CanDeleteRoomInventory |
| GET | `room-types/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomTypes |
| POST/PUT/PATCH/DELETE | `room-types/<id>/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomTypes, CanManageRoomTypes |
| GET | `room-images/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomMedia |
| POST/PUT/PATCH/DELETE | `room-images/<id>/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomMedia, CanManageRoomMedia |
| POST | `rooms/checkout/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanBulkCheckoutRooms. **Destructive branch**: imperatively checks `CanDestructiveCheckoutRooms().has_permission()`; 403 without it. The old `request.user.is_superuser` shortcut has been removed. |
| POST | `rooms/<room_number>/start-cleaning/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanTransitionRoomStatus |
| POST | `rooms/<room_number>/mark-cleaned/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanTransitionRoomStatus |
| POST | `rooms/<room_number>/inspect/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanInspectRoom |
| POST | `rooms/<room_number>/mark-maintenance/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanFlagRoomMaintenance (no more `HasNavPermission('maintenance')`) |
| POST | `rooms/<room_number>/complete-maintenance/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanClearRoomMaintenance |
| GET | `turnover/rooms/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomStatus |
| GET | `turnover/stats/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanReadRoomStatus |
| POST | `room-types/<id>/rooms/bulk-create/` | Auth, IsStaffMember, IsSameHotel, CanViewRooms, CanCreateRoomInventory |

No nav-based gate (`HasNavPermission('rooms')`, `HasNavPermission('maintenance')`,
`HasRoomsNav`) remains on any rooms endpoint. Verified by
`RoomLegacyGateRemovalTest`.

---

## 7. Tests Added

`hotel/tests/test_rbac_rooms.py`:

| Class | Tests | Purpose |
| --- | --- | --- |
| `RoomPolicyRegistryTest` | 5 | Validators clean; rooms module registered; no decorative action keys; tier presets contain zero `room.*` caps. |
| `RoomPolicyPersonaTest` | 12 | Persona → `rbac.rooms` resolution for every canonical department & role combination. |
| `RoomEndpointEnforcementTest` | 26 | Live API tests via `APIClient` + Token auth: module visibility gate on every endpoint; inventory CRUD; room types; turnover transitions (start/mark/inspect); maintenance flag/clear; checkout bulk & destructive; PATCH `is_out_of_order` escalation; cross-hotel denial. |
| `RoomLegacyGateRemovalTest` | 5 | Grep-style guards: no `CanManageRooms`, no `HasNavPermission('rooms')`, no `HasNavPermission('maintenance')`, no `is_superuser` in `checkout_rooms`, `CanManageRooms` removed from `staff.permissions`. |

Total: **48 tests.**

---

## 8. Validation Results

```
$ python manage.py check
System check identified no issues (0 silenced).

$ python -c "from staff.capability_catalog import validate_preset_maps; print(validate_preset_maps())"
[]

$ python -c "from staff.module_policy import validate_module_policy; print(validate_module_policy())"
[]

$ python manage.py test hotel.tests.test_rbac_rooms --verbosity=2 --keepdb
Ran 48 tests.
OK

$ python manage.py test hotel.tests.test_rbac_bookings --verbosity=1 --keepdb
Ran 30 tests.
OK
```

Phase 6A booking regression suite passes unchanged.

---

## 9. Payload Examples — `rbac.rooms`

Resolved via
`resolve_module_policy(resolve_capabilities(tier, role, dept))['rooms']`.

**A. Front-office regular staff** — `('regular_staff', None, 'front_office')`:

```json
{
  "visible": true, "read": true,
  "actions": {
    "inventory_create": false, "inventory_update": false,
    "inventory_delete": false, "type_manage": false,
    "media_manage": false, "out_of_order_set": false,
    "checkout_destructive": false, "status_transition": false,
    "maintenance_flag": false, "inspect": false,
    "maintenance_clear": false, "checkout_bulk": false
  }
}
```

**B. Housekeeping regular staff** — `('regular_staff', None, 'housekeeping')`:

```json
{
  "visible": true, "read": true,
  "actions": {
    "inventory_create": false, "inventory_update": false,
    "inventory_delete": false, "type_manage": false,
    "media_manage": false, "out_of_order_set": false,
    "checkout_destructive": false,
    "status_transition": true, "maintenance_flag": true,
    "inspect": false, "maintenance_clear": false,
    "checkout_bulk": false
  }
}
```

**C. Housekeeping supervisor** — `('regular_staff', 'housekeeping_supervisor', 'housekeeping')`:

```json
{
  "visible": true, "read": true,
  "actions": {
    "inventory_create": false, "inventory_update": false,
    "inventory_delete": false, "type_manage": false,
    "media_manage": false, "out_of_order_set": false,
    "checkout_destructive": false,
    "status_transition": true, "maintenance_flag": true,
    "inspect": true, "maintenance_clear": true,
    "checkout_bulk": true
  }
}
```

**D. Maintenance regular staff** — `('regular_staff', None, 'maintenance')`:

```json
{
  "visible": true, "read": true,
  "actions": {
    "inventory_create": false, "inventory_update": false,
    "inventory_delete": false, "type_manage": false,
    "media_manage": false, "out_of_order_set": false,
    "checkout_destructive": false, "status_transition": false,
    "maintenance_flag": true, "inspect": false,
    "maintenance_clear": false, "checkout_bulk": false
  }
}
```

**E. Hotel manager** — `('regular_staff', 'hotel_manager', 'management')`:

```json
{
  "visible": true, "read": true,
  "actions": {
    "inventory_create": true, "inventory_update": true,
    "inventory_delete": true, "type_manage": true,
    "media_manage": true, "out_of_order_set": true,
    "checkout_destructive": true, "status_transition": true,
    "maintenance_flag": true, "inspect": true,
    "maintenance_clear": true, "checkout_bulk": true
  }
}
```

**F. `super_staff_admin` tier with no role/department**:

```json
{
  "visible": false, "read": false,
  "actions": {
    "inventory_create": false, "inventory_update": false,
    "inventory_delete": false, "type_manage": false,
    "media_manage": false, "out_of_order_set": false,
    "checkout_destructive": false, "status_transition": false,
    "maintenance_flag": false, "inspect": false,
    "maintenance_clear": false, "checkout_bulk": false
  }
}
```

This is the intended contract: tier alone grants **no** room authority.

---

## 10. Remaining Risks / Follow-ups

1. **Stale `HasRoomsNav` import in `hotel/staff_views.py`.** The symbol is
   unused; left untouched to keep the patch surgical. Should be removed in
   a follow-up cleanup.
2. **`operations_admin` cannot toggle `is_out_of_order` via PATCH.** Because
   the PATCH chain requires `CanUpdateRoomInventory` first, and that role
   lacks `ROOM_INVENTORY_UPDATE`. Intentional — inventory mutation is
   reserved for `hotel_manager`. Ops-admins flipping OOO must go through
   a dedicated action endpoint if one is added later.
3. **`housekeeping.room_status.*` coupling leaks into rooms role presets.**
   Because `mark_maintenance` / `complete_maintenance` defer to the
   canonical housekeeping state-machine service. The alternative
   (refactoring `housekeeping.policy`) is out of scope for 6B.1.
4. **Rooms checkout destructive mode** is checked imperatively inside
   `checkout_rooms` (after the permission classes run). Kept that way
   because the permission depends on request body content. Any regression
   here would be caught by
   `test_hk_supervisor_cannot_destructive_checkout` /
   `test_ops_admin_can_destructive_checkout`.
5. **`room.qr.generate` not added.** No rooms-app endpoint produces QR.
   If such an endpoint is added in the future, mint the capability then.

---

## 11. Go / No-Go

**Go.**

- `python manage.py check` → clean.
- `validate_preset_maps()` → `[]`.
- `validate_module_policy()` → `[]`.
- New rooms RBAC suite: **48/48 pass**.
- Phase 6A bookings regression suite: **30/30 pass**.
- No advertised capability without real enforcement.
- No residual `CanManageRooms`, `HasNavPermission('rooms')`,
  `HasNavPermission('maintenance')`, or `is_superuser` gate in
  `rooms/views.py`.
- Tier presets free of room capabilities.
