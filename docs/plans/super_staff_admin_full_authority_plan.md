# Plan — `super_staff_admin` tier = ultimate hotel authority

Status: **PROPOSED — NOT YET APPLIED**
Scope: backend only (`staff/capability_catalog.py`) + tests inversion.
Risk: high (touches the SSOT for every RBAC decision); low diff (one mapping
edit + test updates).

---

## 1. Goal

Make `Staff.access_level == 'super_staff_admin'` (the **tier**) sufficient on
its own to grant full management authority within the staff member's own
hotel, **without requiring** the `hotel_manager` **role**.

After the change, sanja (`tier=super_staff_admin`, `role=front_office_manager`,
`hotel=no-way-hotel`) gets the same `rbac.*` payload as a user with
`role=hotel_manager`.

`super_user` (Django superuser) remains the only persona with cross-hotel /
platform authority. `super_staff_admin` stays scoped to one hotel.

---

## 2. Original RBAC contract — what we keep, what we soften

The Phase 5–6 contract is documented in
[`docs/rbac/`](../rbac) and the Phase 6 audit notes
([`RBAC_OPERATIONAL_REBALANCE_AUDIT.md`](../../RBAC_OPERATIONAL_REBALANCE_AUDIT.md)).
Core invariants:

| # | Invariant | Status after this change |
|---|-----------|--------------------------|
| 1 | **Capabilities are the only enforcement axis.** Endpoints check capability slugs; nav and tier are not authority. | **Preserved.** No endpoint logic changes. |
| 2 | **Resolver is a pure additive union.** `effective = tier ∪ role ∪ department`. No short-circuits except `super_user`. | **Preserved.** We only enlarge the `tier` term for `super_staff_admin`. |
| 3 | **Tier alone never grants manage bucket.** Manage requires role preset (Phase 6A.2). | **SOFTENED, scoped to one tier.** This invariant is explicitly relaxed for `super_staff_admin` only. `staff_admin` and `regular_staff` keep it. |
| 4 | **`hotel_manager` role is the canonical "full hotel power" preset.** | **Preserved.** Bundle on the role is unchanged; it still works as the way to grant full power to a non-`super_staff_admin` user (e.g. a department head we trust with full mgmt). |
| 5 | **`HOTEL_INFO_CATEGORY_MANAGE` is platform/superuser only** (global rows, not hotel-scoped). | **Preserved.** Explicitly excluded from the new tier bundle. |
| 6 | **Cross-hotel surfaces require `super_user`.** Hotel CRUD, NavigationItem CUD, global category CUD. | **Preserved.** All remain on `IsDjangoSuperUser`. |
| 7 | **Anti-escalation in `staff_management`** (cannot assign someone equal/higher than yourself unless you hold `authority.supervise`). | **Preserved.** `STAFF_MANAGEMENT_AUTHORITY_SUPERVISE` is in `_STAFF_MANAGEMENT_MANAGER`, included in the new tier bundle, so `super_staff_admin` can promote others — same authority as `hotel_manager` today. |
| 8 | **Department-scoped manager roles** (`front_office_manager`, `housekeeping_manager`, `kitchen_manager`, …) are department leads with limited mgmt power. | **Preserved.** Their role presets are untouched. |
| 9 | **Validation harnesses** (`validate_preset_maps`, `validate_module_policy`) return `[]`. | **Preserved.** New caps are already in `CANONICAL_CAPABILITIES`. |

The single conceptual change: invariant #3 carved out for the top hotel
tier. Justified because product owner declared `super_staff_admin` to mean
"the user who runs this hotel", and Phase 6's split was operational, not
authority-based.

---

## 3. The change — exact diff

### 3.1 New aggregate bundle

In [`staff/capability_catalog.py`](../../staff/capability_catalog.py),
**after** `_RESTAURANT_BOOKING_MANAGE` (around L1455) and **before**
`TIER_DEFAULT_CAPABILITIES`, add:

```python
# ---------------------------------------------------------------------------
# super_staff_admin tier ultimate-authority bundle.
#
# Contract carve-out (documented in
# docs/plans/super_staff_admin_full_authority_plan.md):
# the super_staff_admin tier carries the full hotel-scoped management
# authority. This is the ONLY tier carve-out from the
# "tier never grants manage" rule. staff_admin and regular_staff keep
# the original Phase 6 contract.
#
# Explicitly EXCLUDED:
#   - HOTEL_INFO_CATEGORY_MANAGE  (global rows; superuser-only)
#   - any cap not in CANONICAL_CAPABILITIES (drift protection via
#     resolve_capabilities filter step)
# ---------------------------------------------------------------------------

_HOTEL_FULL_AUTHORITY: frozenset[str] = (
    _BOOKING_MANAGE
    | _ROOM_MANAGE
    | _HOUSEKEEPING_MANAGE
    | _MAINTENANCE_MANAGE
    | _STAFF_MANAGEMENT_MANAGER         # full + authority.supervise
    | _GUESTS_OPERATE
    | _ATTENDANCE_MANAGE
    | _ROOM_SERVICE_MANAGE
    | _RESTAURANT_BOOKING_MANAGE
    | _CHAT_BASE
    | frozenset({
        CHAT_GUEST_RESPOND,
        CHAT_CONVERSATION_ASSIGN,
        CHAT_MESSAGE_MODERATE,
        BOOKING_GUEST_COMMUNICATE,
        GUEST_RECORD_UPDATE,
    })
    # Hotel info: read + entry CRUD + QR. Excludes category.manage.
    | frozenset({
        HOTEL_INFO_MODULE_VIEW,
        HOTEL_INFO_ENTRY_READ,
        HOTEL_INFO_ENTRY_CREATE,
        HOTEL_INFO_ENTRY_UPDATE,
        HOTEL_INFO_ENTRY_DELETE,
        HOTEL_INFO_CATEGORY_READ,
        HOTEL_INFO_QR_READ,
        HOTEL_INFO_QR_GENERATE,
    })
)
```

### 3.2 Update tier baseline

Replace the `super_staff_admin` entry of `TIER_DEFAULT_CAPABILITIES` (around
L1469):

```python
TIER_DEFAULT_CAPABILITIES: dict[str, frozenset[str]] = {
    'super_staff_admin': (
        _SUPERVISOR_AUTHORITY
        | _STAFF_CHAT_BASE
        | _ATTENDANCE_SELF_SERVICE
        | _HOTEL_FULL_AUTHORITY        # ← NEW: full hotel authority
    ),
    'staff_admin': (                   # unchanged
        _SUPERVISOR_AUTHORITY | _STAFF_CHAT_BASE
        | _ATTENDANCE_SELF_SERVICE | _ROOM_SERVICE_BASE
    ),
    'regular_staff': (                 # unchanged
        _STAFF_CHAT_BASE | _ATTENDANCE_SELF_SERVICE
        | _ROOM_SERVICE_BASE
    ),
}
```

Notes:
- `_BOOKING_SUPERVISE` was the pre-change addend on `super_staff_admin`;
  it is dropped because `_HOTEL_FULL_AUTHORITY` includes
  `_BOOKING_MANAGE ⊃ _BOOKING_SUPERVISE`.
- `_ROOM_SERVICE_BASE` removed for the same reason
  (`_ROOM_SERVICE_MANAGE ⊃ _ROOM_SERVICE_OPERATE ⊃ _ROOM_SERVICE_BASE`).
- `_SUPERVISOR_AUTHORITY` and `_STAFF_CHAT_BASE` kept verbatim — they are
  cross-cutting (chat moderation, staff-chat read/send), not "manage".
- `_ATTENDANCE_SELF_SERVICE` kept — every tier owns its own clock data.

### 3.3 No other code change

- `TIER_DEFAULT_NAVS['super_staff_admin']` already lists every canonical
  nav slug. **No change.**
- `staff/permissions.py` permission classes (`CanManageRoster`, `CanManageStaff`,
  `CanManageRoomBookings`, `CanConfigureHotel`, `IsSuperStaffAdminOrAbove`,
  `IsAdminTier`) already pass for `super_staff_admin` tier. **No change.**
- `hotel/permissions.py::IsSuperStaffAdminForHotel` already lets
  `super_staff_admin` of the URL hotel pass. **No change.**
- `staff/views.py` login + `/me/` already emit `allowed_capabilities` and
  `rbac` from the resolver. Frontend payload shape **unchanged**; only the
  contents of the booleans flip.

---

## 4. Surfaces explicitly NOT granted

These remain superuser-only / scoped (sanity check):

| Surface | Gate | Why kept |
|---|---|---|
| Hotel CRUD ([hotel/provisioning_views.py](../../hotel/provisioning_views.py)) | `IsDjangoSuperUser` | Cross-tenant. |
| `NavigationItem` CUD ([staff/views.py L1868](../../staff/views.py#L1868)) | `IsDjangoSuperUser` | Platform schema. |
| `HotelInfoCategory` global rows | view-level superuser check + `HOTEL_INFO_CATEGORY_MANAGE` not in tier | Global rows shared across hotels. |
| Cross-hotel staff list / by_hotel filters ([staff/views.py L1362](../../staff/views.py#L1362)) | view-level scoping by `staff.hotel` | Already scoped per request. |
| `Staff.access_level` validator ([staff/views.py L1990](../../staff/views.py#L1990)) | view-level | Already enforced; tier change does not bypass anti-escalation because we keep the validator and `STAFF_MANAGEMENT_AUTHORITY_SUPERVISE` only lifts it relative to *requester's* level. `super_staff_admin` can still only assign ≤ `super_staff_admin` (no superuser promotion). |

---

## 5. Concrete cap diff (`super_staff_admin` tier, role=None, dept=None)

**Before** (current Phase 6A.2):
```
chat.message.moderate, chat.conversation.assign,
staff_chat.conversation.moderate, staff_chat.conversation.delete,
staff_chat.{module.view, conversation.read, conversation.create,
            message.send, attachment.upload, attachment.delete,
            reaction.manage},
booking.module.view, booking.record.read, booking.record.update,
booking.record.cancel, booking.room.assign, booking.stay.checkin,
booking.stay.checkout, booking.guest.communicate,
booking.override.supervise,
attendance.module.view, attendance.clock.in_out, attendance.break.toggle,
attendance.log.read_self, attendance.roster.read_self,
attendance.face.register_self,
room_service.{module.view, menu.read, order.read,
              breakfast_order.read, breakfast_order.create}
```
(35 caps, no manage bucket anywhere.)

**After** (with `_HOTEL_FULL_AUTHORITY` union):
Every canonical capability **except** `hotel_info.category.manage` (1 of
~155). Frontend `rbac.*` payload: every `visible/read/actions.*` flag for
the staff member's hotel = `true` except that one global category cap.

---

## 6. Test impact

These tests assert the Phase 6A "tier alone has no manage" rule. They will
**fail** after the change and must be **inverted** in the same commit:

| File | Test | Inversion |
|------|------|-----------|
| [hotel/tests/test_rbac_bookings.py](../../hotel/tests/test_rbac_bookings.py) | `test_super_staff_admin_gets_supervise_not_manage` | Now grants manage; rename + assert `BOOKING_CONFIG_MANAGE` ∈ caps. |
|  | `test_rate_plans_post_forbidden_for_super_staff_admin` | Should now be **allowed**. |
|  | `test_super_staff_admin_payload` | Update expected cap set. |
|  | `test_overstay_extend_allowed_for_super_staff_admin` | Already passes; verify still does. |
| [hotel/tests/test_rbac_housekeeping.py](../../hotel/tests/test_rbac_housekeeping.py) | `test_tier_only_super_staff_admin_has_no_housekeeping_caps` | Invert. |
|  | "tier-only super_staff_admin must NOT pass the override gate" (~L611) | Invert. |
| [hotel/tests/test_rbac_maintenance.py](../../hotel/tests/test_rbac_maintenance.py) | `test_tier_only_super_staff_admin_has_no_maintenance_authority` | Invert. |
| [hotel/tests/test_rbac_rooms.py](../../hotel/tests/test_rbac_rooms.py) | `test_super_staff_admin_tier_alone_has_no_room_caps` | Invert. |
| [hotel/tests/test_rbac_nav_consistency.py](../../hotel/tests/test_rbac_nav_consistency.py) | nav assertions | Read-through; should already pass (visibility already granted). |

For each inverted test, retain a **negative** counterpart with `staff_admin`
tier so we keep coverage of the "tier alone (non-top) has no manage"
contract for the lower tier (regression guard against accidentally
granting manage to `staff_admin` later).

Add a new test:
- `test_super_staff_admin_tier_alone_grants_full_hotel_authority` — assert
  `resolve_capabilities('super_staff_admin', None, None)` equals
  `CANONICAL_CAPABILITIES - {HOTEL_INFO_CATEGORY_MANAGE}`.
- `test_super_staff_admin_does_not_grant_category_manage` — assert
  `HOTEL_INFO_CATEGORY_MANAGE` NOT in caps.

---

## 7. Validation steps (post-apply, before commit)

1. `python manage.py shell -c "from staff.capability_catalog import resolve_capabilities, validate_preset_maps, CANONICAL_CAPABILITIES, HOTEL_INFO_CATEGORY_MANAGE; print(validate_preset_maps()); caps = set(resolve_capabilities('super_staff_admin', None, None)); print('missing:', sorted(CANONICAL_CAPABILITIES - caps)); assert caps == CANONICAL_CAPABILITIES - {HOTEL_INFO_CATEGORY_MANAGE}; print('OK')"`
   Expected: `[] / missing: ['hotel_info.category.manage'] / OK`.
2. `python manage.py shell -c "from staff.module_policy import validate_module_policy; print(validate_module_policy())"` → `[]`.
3. Run the four updated test files: `python manage.py test hotel.tests.test_rbac_bookings hotel.tests.test_rbac_housekeeping hotel.tests.test_rbac_maintenance hotel.tests.test_rbac_rooms hotel.tests.test_rbac_nav_consistency`.
4. Live smoke (sanja, `tier=super_staff_admin`, `role=front_office_manager`):
   - login → inspect `rbac.staff_management.actions.staff_create` → expect `true`.
   - `POST /api/staff/hotel/no-way-hotel/staff/<id>/role/` → expect 200.
   - `POST /api/staff/hotel/no-way-hotel/staff/` (create) → expect 201.
   - Anti-escalation guard: try assigning another staff `access_level=super_staff_admin` → still allowed (sanja IS super_staff_admin); try assigning Django superuser flag → still rejected at view layer (independent of capabilities).
5. Re-run live cap probe for the four active staff (`nikola`, `George`,
   `sajkodog` — already super_staff_admin; `sanja` — was front_office_manager
   only). Expect `nikola/George/sajkodog/sanja` all to land on the same
   ~154-cap bundle.

---

## 8. Rollback

Revert the change to `TIER_DEFAULT_CAPABILITIES['super_staff_admin']` and
delete `_HOTEL_FULL_AUTHORITY`. No data migrations, no model changes, no
permission-class changes. Tests revert with the same commit.

---

## 9. Out of scope

- Demoting `hotel_manager` role preset — kept as a way to grant manager
  authority to non-tier users.
- Per-staff capability overrides (future M2M field).
- Restoring/altering Phase 6 manage rule for `staff_admin` tier.
- Frontend changes — payload shape unchanged.
- Removing `IsSuperStaffAdminOrAbove` / `CanManage*` tier-gated permission
  classes — they keep working and are read-throughs to the same tier.
