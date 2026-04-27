# Backend RBAC Canonical Alignment Audit — All Modules

**Scope:** Audit-only. Verifies that every module currently mounted in
`MODULE_POLICY` follows the single canonical pattern:

> *capability = final endpoint authority • nav = visibility only • tier /
> role / department presets are the only ways capabilities are assigned*

Source-of-truth = actual code. Documentation, comments, READMEs and
prior summaries were not consulted.

---

## 1. Files inspected

Canonical infrastructure
- [staff/capability_catalog.py](staff/capability_catalog.py)
- [staff/module_policy.py](staff/module_policy.py)
- [staff/permissions.py](staff/permissions.py)
- [hotel/provisioning.py](hotel/provisioning.py)

Per-module enforcement surfaces
- [bookings/views.py](bookings/views.py) (restaurant bookings — separate domain)
- [hotel/staff_views.py](hotel/staff_views.py) (room-bookings module = canonical `bookings`)
- [hotel/views/rate_plans/views.py](hotel/views/rate_plans/views.py)
- [hotel/views/cancellation_policies/views.py](hotel/views/cancellation_policies/views.py)
- [rooms/views.py](rooms/views.py)
- [housekeeping/views.py](housekeeping/views.py)
- [maintenance/views.py](maintenance/views.py)
- [staff/views.py](staff/views.py)
- [guests/views.py](guests/views.py)
- [hotel_info/views.py](hotel_info/views.py)
- [chat/views.py](chat/views.py)
- [staff_chat/views.py](staff_chat/views.py)
- [attendance/views.py](attendance/views.py)
- [attendance/views_analytics.py](attendance/views_analytics.py)
- [room_services/views.py](room_services/views.py)

---

## 2. MODULE_POLICY alignment

`MODULE_POLICY` keys:
`attendance`, `bookings`, `chat`, `guests`, `hotel_info`, `housekeeping`,
`maintenance`, `room_services`, `rooms`, `staff_chat`, `staff_management`.

| Module | view_capability present? | read_capability present? | actions present? | All caps in CANONICAL_CAPABILITIES? | Result |
|---|---|---|---|---|---|
| attendance | ✓ `ATTENDANCE_MODULE_VIEW` | ✓ `ATTENDANCE_LOG_READ_SELF` | ✓ 32 actions | ✓ | OK |
| bookings | ✓ `BOOKING_MODULE_VIEW` | ✓ `BOOKING_RECORD_READ` | ✓ 12 actions | ✓ | OK |
| chat | ✓ `CHAT_MODULE_VIEW` | ✓ `CHAT_CONVERSATION_READ` | ✓ 7 actions | ✓ | OK |
| guests | ✓ `GUEST_RECORD_READ` (view_cap == read_cap) | ✓ `GUEST_RECORD_READ` | ✓ 1 action | ✓ | OK |
| hotel_info | ✓ `HOTEL_INFO_MODULE_VIEW` | ✓ `HOTEL_INFO_ENTRY_READ` | ✓ 8 actions | ✓ | OK |
| housekeeping | ✓ `HOUSEKEEPING_MODULE_VIEW` | ✓ `HOUSEKEEPING_TASK_READ` | ✓ 11 actions | ✓ | OK |
| maintenance | ✓ `MAINTENANCE_MODULE_VIEW` | ✓ `MAINTENANCE_REQUEST_READ` | ✓ 12 actions | ✓ | OK |
| room_services | ✓ `ROOM_SERVICE_MODULE_VIEW` | ✓ `ROOM_SERVICE_ORDER_READ` | ✓ 17 actions | ✓ | OK |
| rooms | ✓ `ROOM_MODULE_VIEW` | ✓ `ROOM_INVENTORY_READ` | ✓ 12 actions | ✓ | OK |
| staff_chat | ✓ `STAFF_CHAT_MODULE_VIEW` | ✓ `STAFF_CHAT_CONVERSATION_READ` | ✓ 8 actions | ✓ | OK |
| staff_management | ✓ `STAFF_MANAGEMENT_MODULE_VIEW` | ✓ `STAFF_MANAGEMENT_STAFF_READ` | ✓ 19 actions | ✓ | OK |

`validate_module_policy()` returns `[]` (see §Validation).

---

## 3. Endpoint authority alignment

| Module | Capability-gated? | Nav-as-authority? | Tier-as-authority? | Role/access_level authority? | Status |
|---|---|---|---|---|---|
| bookings (room) — `hotel/staff_views.py` | YES (`CanViewBookings`, `CanReadBookings`, `CanUpdateBooking`, `CanCancelBooking`, `CanAssignBookingRoom`, `CanCheckInBooking`, `CanCheckOutBooking`, `CanCommunicateWithBookingGuest`, `CanSuperviseBooking`, `CanManageBookingConfig`) | NO | NO | NO | OK |
| bookings — `hotel/views/rate_plans/views.py`, `hotel/views/cancellation_policies/views.py` | YES (`CanManageBookingConfig` for POST/PUT/PATCH) | Used as visibility gate alongside (e.g. `HasNavPermission('room_bookings').has_permission(...)` in `rate_plan_delete`, `cancellation_policy_templates`); not authority on mutating writes | NO | NO | OK (visibility-only use of nav) |
| rooms | YES (`CanViewRooms`, `CanReadRoomInventory`, `CanCreateRoomInventory`, `CanUpdate/DeleteRoomInventory`, `CanManageRoomTypes`, `CanManageRoomMedia`, `CanTransitionRoomStatus`, `CanInspectRoom`, `CanFlag/ClearRoomMaintenance`, `CanSetRoomOutOfOrder`, `CanBulkCheckoutRooms`, `CanDestructiveCheckoutRooms`) | NO | NO | NO | OK |
| housekeeping | YES (`CanViewHousekeepingModule`, `CanReadHousekeepingDashboard`, `CanReadHousekeepingTasks`, `CanCreate/Update/Delete/Assign/Execute/CancelHousekeepingTask`, `CanTransition/FrontDesk/OverrideHousekeepingRoomStatus`, `CanReadHousekeepingStatusHistory`) | NO | NO | NO | OK |
| maintenance | YES (`CanViewMaintenanceModule`, `CanReadMaintenanceRequests`, `CanCreate/Accept/Resolve/Update/Reassign/Reopen/Close/DeleteMaintenanceRequest`, `CanCreate/ModerateMaintenanceComment`, `CanUpload/DeleteMaintenancePhoto`) | NO | NO | NO | OK |
| staff_management — `staff/views.py` | YES (`CanViewStaffManagementModule`, `CanReadStaff`, `CanReadStaffUsers`, `CanReadPendingRegistrations`, `CanCreate/Deactivate/DeleteStaff`, `CanUpdateStaffProfile`, `CanViewStaffAuthority`, `CanAssignStaff{Role,Department,AccessLevel,Navigation}`, `CanRead/ManageStaffRoles`, `CanRead/ManageStaffDepartments`, `CanRead/Create/Email/PrintRegistrationPackages`) | NO (`HasStaffManagementNav` imported but unused on mutating endpoints) | NO (`resolve_tier`/`_tier_at_least` referenced only inside anti-escalation helpers `assert_access_level_allowed`/`_access_level_rank`, gated on absence of `STAFF_MANAGEMENT_AUTHORITY_SUPERVISE` capability — these run **after** the capability check, not as the primary gate) | `access_level` and `role.slug` are read for *anti-escalation comparison* against the requester's own resolved capabilities; never used as final authority | OK |
| guests | YES (`CanReadGuests`, `CanUpdateGuests`) | NO | NO | NO | OK |
| hotel_info | YES (`CanViewHotelInfoModule`, `CanReadHotelInfo`, `CanCreate/Update/DeleteHotelInfo`, `CanRead/ManageHotelInfoCategory`, `CanRead/GenerateHotelInfoQR`) | NO | NO | NO | OK |
| chat | YES (`CanViewChatModule`, `CanReadChatConversation`, `CanSendChatMessage`, `CanModerateChatMessage`, `CanUpload/DeleteChatAttachment`, `CanAssignChatConversation`, `CanRespondToGuest`) | NO | NO | NO | OK |
| staff_chat | YES (`CanViewStaffChatModule`, `CanReadStaffChatConversation`, `CanCreate/DeleteStaffChatConversation`, `CanSendStaffChatMessage`, `CanUploadStaffChatAttachment`, `CanManageStaffChatReaction`) | NO | NO | NO | OK |
| attendance | YES (`CanViewAttendanceModule`, `CanClockInOut`, `CanToggleAttendanceBreak`, `CanReadOwn/AllAttendanceLogs`, `CanReadOwnRoster`, `CanCreate/Update/Delete/Approve/Reject/RelinkAttendanceLog`, `CanReadAttendanceAnalytics`, `CanRead/Create/Update/Delete/Finalize/Unfinalize/ForceFinalizeAttendancePeriod`, `CanRead/Create/Update/Delete/BulkWrite/Copy/ExportPdfAttendanceShift`, `CanRead/ManageShiftLocation`, `CanRead/Manage{DailyPlan,DailyPlanEntry}`, `CanReadAttendanceFace`, `CanRegisterOwn/OtherAttendanceFace`, `CanRevokeAttendanceFace`, `CanReadAttendanceFaceAudit`) | NO | NO | NO | OK |
| room_services | YES (`CanViewRoomServicesModule`, `CanReadRoomServiceMenu`, `CanCreate/Update/DeleteRoomServiceMenuItem`, `CanManageRoomServiceMenuItemImage`, `CanRead/Create/Update/Delete/Accept/CompleteRoomServiceOrder`, `CanRead/Create/Update/Delete/Accept/CompleteBreakfastOrder`) | NO | NO | NO | OK |

### Out-of-scope domain found in code (not in MODULE_POLICY)

| Module (Django app) | Capability-gated? | Nav-as-authority? | Tier-as-authority? | Status |
|---|---|---|---|---|
| restaurant bookings — `bookings/views.py` | NO (no canonical `restaurant_booking.*` capabilities exist) | YES — `HasNavPermission('restaurant_bookings')` is used inside `get_permissions()` as the primary gate (e.g. [bookings/views.py:49](bookings/views.py#L49), [:68](bookings/views.py#L68), [:289](bookings/views.py#L289), [:363](bookings/views.py#L363), [:410](bookings/views.py#L410), [:455](bookings/views.py#L455), [:559](bookings/views.py#L559)) and class-level on table viewsets ([:579](bookings/views.py#L579), [:615](bookings/views.py#L615), [:650](bookings/views.py#L650)) | YES — `CanManageRestaurantBookings` (tier `staff_admin+`) at [staff/permissions.py:368](staff/permissions.py#L368) | NOT canonical; this domain is *not* registered in `MODULE_POLICY` and has no capability slugs |

---

## 4. Preset consistency

Capability assignment sources (no enforcement here — assignment only):

### Tier presets (`TIER_DEFAULT_CAPABILITIES`)
- `super_staff_admin` → `_SUPERVISOR_AUTHORITY ∪ _BOOKING_SUPERVISE ∪ _CHAT_BASE ∪ _STAFF_CHAT_BASE ∪ _ATTENDANCE_SELF_SERVICE ∪ _ROOM_SERVICE_MANAGE`
- `staff_admin` → `_SUPERVISOR_AUTHORITY ∪ _CHAT_BASE ∪ _STAFF_CHAT_BASE ∪ _ATTENDANCE_SELF_SERVICE ∪ _ROOM_SERVICE_MANAGE`
- `regular_staff` → `_CHAT_BASE ∪ _STAFF_CHAT_BASE ∪ _ATTENDANCE_SELF_SERVICE ∪ _ROOM_SERVICE_BASE`

### Role presets (`ROLE_PRESET_CAPABILITIES`)
- `staff_admin` → `_STAFF_MANAGEMENT_BASIC`
- `super_staff_admin` → `_STAFF_MANAGEMENT_FULL`
- `hotel_manager` → `_BOOKING_MANAGE ∪ _ROOM_MANAGE ∪ _HOUSEKEEPING_MANAGE ∪ _MAINTENANCE_MANAGE ∪ _STAFF_MANAGEMENT_MANAGER ∪ _GUESTS_OPERATE ∪ _HOTEL_INFO_MANAGE ∪ _ATTENDANCE_MANAGE`
- `front_office_manager` → `_BOOKING_MANAGE ∪ _ROOM_SUPERVISE ∪ _HOUSEKEEPING_SUPERVISE ∪ _MAINTENANCE_REPORTER ∪ _GUESTS_OPERATE ∪ _HOTEL_INFO_READ`
- `front_desk_agent` → `{ROOM_SERVICE_ORDER_FULFILL_PORTER} ∪ _MAINTENANCE_REPORTER ∪ _GUESTS_OPERATE ∪ _HOTEL_INFO_READ`
- `housekeeping_supervisor` → `_ROOM_SUPERVISE ∪ _HOUSEKEEPING_SUPERVISE`
- `housekeeping_manager` → `_ROOM_SUPERVISE ∪ _HOUSEKEEPING_MANAGE`
- `maintenance_supervisor` → `{ROOM_MAINTENANCE_CLEAR, HOUSEKEEPING_ROOM_STATUS_OVERRIDE} ∪ _MAINTENANCE_SUPERVISE`
- `maintenance_manager` → `{ROOM_MAINTENANCE_CLEAR, ROOM_OUT_OF_ORDER_SET, HOUSEKEEPING_ROOM_STATUS_OVERRIDE} ∪ _MAINTENANCE_MANAGE`

### Department presets (`DEPARTMENT_PRESET_CAPABILITIES`)
- `front_office` → `{CHAT_GUEST_RESPOND, CHAT_CONVERSATION_ASSIGN, HOUSEKEEPING_MODULE_VIEW, HOUSEKEEPING_ROOM_STATUS_FRONT_DESK, HOUSEKEEPING_ROOM_STATUS_HISTORY_READ} ∪ _BOOKING_READ ∪ _BOOKING_OPERATE ∪ _ROOM_READ ∪ _MAINTENANCE_REPORTER`
- `housekeeping` → `_ROOM_OPERATE ∪ _HOUSEKEEPING_OPERATE ∪ _MAINTENANCE_REPORTER`
- `kitchen` → `{ROOM_SERVICE_ORDER_FULFILL_KITCHEN}`
- `maintenance` → `_ROOM_READ ∪ {ROOM_MAINTENANCE_FLAG, HOUSEKEEPING_ROOM_STATUS_TRANSITION} ∪ _MAINTENANCE_OPERATE`

### Orphans / inconsistencies

`validate_preset_maps()` returns `[]` — every preset capability is canonical.

Coverage analysis of canonical capabilities vs presets (i.e. which slugs are
defined and registered but NOT granted by *any* preset, so are reachable
only via Django superuser):

| Capability | Reachable via | Notes |
|---|---|---|
| `HOTEL_INFO_CATEGORY_MANAGE` | superuser only | **By design** — catalog explicitly states this is platform/superuser-only. Not an inconsistency. |

All other capabilities in `CANONICAL_CAPABILITIES` appear in at least one
tier/role/department preset. No accidental orphans.

### Manage / destructive capability conflicts

None observed. Destructive caps are scoped to deliberate role bundles:

- `ROOM_CHECKOUT_DESTRUCTIVE`, `ROOM_INVENTORY_DELETE`, `ROOM_TYPE_MANAGE`, `ROOM_MEDIA_MANAGE`, `ROOM_OUT_OF_ORDER_SET` → `_ROOM_MANAGE` (only `hotel_manager` and `maintenance_manager` for `OUT_OF_ORDER_SET`)
- `HOUSEKEEPING_TASK_DELETE` → `_HOUSEKEEPING_MANAGE` (only `hotel_manager`, `housekeeping_manager`)
- `MAINTENANCE_REQUEST_DELETE`, `MAINTENANCE_REQUEST_CLOSE` → `_MAINTENANCE_MANAGE` (`hotel_manager`, `maintenance_manager`)
- `BOOKING_CONFIG_MANAGE` → `_BOOKING_MANAGE` (`hotel_manager`, `front_office_manager`)
- `STAFF_MANAGEMENT_STAFF_DELETE`, `STAFF_MANAGEMENT_AUTHORITY_*` → `_STAFF_MANAGEMENT_FULL`/`_MANAGER` (role-only; never on tier)
- `STAFF_CHAT_CONVERSATION_DELETE`, `STAFF_CHAT_CONVERSATION_MODERATE` → `_SUPERVISOR_AUTHORITY` (tiers `super_staff_admin`, `staff_admin`)
- `ROOM_SERVICE_*_DELETE`, `ROOM_SERVICE_MENU_ITEM_*` → `_ROOM_SERVICE_MANAGE` (tiers `super_staff_admin`, `staff_admin`)

---

## 5. Room services specific check

- Pattern match: `room_services/views.py` matches the canonical pattern used
  by `rooms`, `housekeeping`, `maintenance`, `attendance`, `staff` —
  `get_permissions()` returns a base chain (`IsAuthenticated`,
  `IsStaffMember`, `IsSameHotel`, `CanViewRoomServicesModule`) plus
  per-action `Can*` capability classes via a `_STAFF_ACTION_PERMISSIONS`
  dispatch dict ([room_services/views.py:151](room_services/views.py#L151), [:602](room_services/views.py#L602)).
- Manage caps assignment (`_ROOM_SERVICE_MANAGE`) is granted via **tier**
  (`super_staff_admin`, `staff_admin`) — this is the **only manage bundle in
  the codebase that is granted via tier rather than role**. Every other
  manage bundle (`_BOOKING_MANAGE`, `_ROOM_MANAGE`, `_HOUSEKEEPING_MANAGE`,
  `_MAINTENANCE_MANAGE`, `_STAFF_MANAGEMENT_FULL/MANAGER`,
  `_HOTEL_INFO_MANAGE`, `_ATTENDANCE_MANAGE`) is granted strictly via the
  `hotel_manager` (and per-domain manager) role presets. Tier intentionally
  no longer doubles as the permission engine for those modules — see
  catalog comments stating exactly that ("Tier intentionally never carries
  any … capability"). For room_services, tier still does carry the manage
  bundle.
- This is a divergence from the majority pattern. It is documented in
  `capability_catalog.py` ("Tier no longer doubles as the room-services
  permission engine: legacy `CanManageRoomServices` (tier ≥ staff_admin) is
  replaced by capability gates… Read/visibility caps are granted broadly to
  every tier"), but the *manage* bundle still rides on tier rather than on
  a role preset, which is opposite to bookings/rooms/housekeeping/etc.

---

## 6. Provisioning / primary admin check

YES — the primary admin receives the canonical role/capabilities required
to manage every canonical module.

Evidence ([hotel/provisioning.py:170-183](hotel/provisioning.py#L170-L183)):

```python
if role is None:
    role = Role.objects.filter(hotel=hotel, slug='hotel_manager').first()

staff = Staff.objects.create(
    user=admin_user,
    hotel=hotel,
    ...
    role=role,
    access_level="super_staff_admin",
    is_active=True,
)
```

`hotel_manager` role preset (capability_catalog.py) =
`_BOOKING_MANAGE ∪ _ROOM_MANAGE ∪ _HOUSEKEEPING_MANAGE ∪ _MAINTENANCE_MANAGE
∪ _STAFF_MANAGEMENT_MANAGER ∪ _GUESTS_OPERATE ∪ _HOTEL_INFO_MANAGE ∪
_ATTENDANCE_MANAGE`. Combined with the `super_staff_admin` tier bundle
(supervisor authority + chat/staff_chat/attendance self-service +
room_service manage), the resolved capability set covers every canonical
module's manage authority.

---

## 7. Final verdict

**CANONICAL ALIGNED: NO** — one out-of-policy domain and one preset-shape
divergence; otherwise every module in `MODULE_POLICY` is correctly aligned.

| Mismatch | File | Why inconsistent | Minimal fix |
|---|---|---|---|
| Restaurant bookings (`bookings` Django app) is enforced via `HasNavPermission('restaurant_bookings')` + tier-based `CanManageRestaurantBookings`; not registered in `MODULE_POLICY` and has no canonical `restaurant_booking.*` capabilities | [bookings/views.py:49](bookings/views.py#L49), [:68](bookings/views.py#L68), [:289](bookings/views.py#L289), [:363](bookings/views.py#L363), [:410](bookings/views.py#L410), [:455](bookings/views.py#L455), [:559](bookings/views.py#L559), [:579](bookings/views.py#L579), [:615](bookings/views.py#L615), [:650](bookings/views.py#L650); class at [staff/permissions.py:368](staff/permissions.py#L368) | Uses nav-as-authority and tier-as-authority; violates the canonical "capability = final endpoint authority" rule. Frontend `rbac` payload has no `restaurant_bookings` entry. | Add `restaurant_booking.*` capabilities to `CANONICAL_CAPABILITIES`, register a `restaurant_bookings` entry in `MODULE_POLICY`, define `Can*` classes mirroring the bookings module, and replace the `HasNavPermission(...) + CanManageRestaurantBookings` chain in [bookings/views.py](bookings/views.py) with the new `Can*` classes. |
| `_ROOM_SERVICE_MANAGE` is granted via tier (`super_staff_admin`, `staff_admin`) instead of via the `hotel_manager` role preset like every other manage bundle | [staff/capability_catalog.py](staff/capability_catalog.py) (`TIER_DEFAULT_CAPABILITIES`) | Diverges from the majority preset shape — bookings, rooms, housekeeping, maintenance, staff_management, hotel_info, attendance all grant manage via role only. Tier still doubling as the room-services permission engine. | Move `_ROOM_SERVICE_MANAGE` from `TIER_DEFAULT_CAPABILITIES['super_staff_admin']`/`['staff_admin']` into `ROLE_PRESET_CAPABILITIES['hotel_manager']` (or a dedicated `room_service_manager` role), keeping `_ROOM_SERVICE_BASE` on tiers for module visibility. |

Notes (not mismatches):

- `HasNavPermission('room_bookings')` calls in [hotel/views/rate_plans/views.py:126](hotel/views/rate_plans/views.py#L126) and [hotel/views/cancellation_policies/views.py:127](hotel/views/cancellation_policies/views.py#L127) are used purely as visibility gates on a 405 stub and a static template list; mutating endpoints in those files use `CanManageBookingConfig` (capability) at [rate_plans/views.py:35](hotel/views/rate_plans/views.py#L35), [:83](hotel/views/rate_plans/views.py#L83) and [cancellation_policies/views.py:39](hotel/views/cancellation_policies/views.py#L39), [:85](hotel/views/cancellation_policies/views.py#L85). This is the canonical pattern.
- `staff/views.py` references `resolve_tier`, `_tier_at_least`, `access_level` and `role.slug` only inside the anti-escalation helper functions (`assert_access_level_allowed`, `assert_role_department_ceiling`, etc. defined in [staff/permissions.py](staff/permissions.py)), which run **after** the capability check has passed and gate strictly on the absence of the `STAFF_MANAGEMENT_AUTHORITY_SUPERVISE` capability. They are anti-escalation comparators, not the primary authority gate.
- `HasStaffManagementNav` is imported in `staff/views.py` but not used as enforcement; safe to remove (cosmetic, not an authority leak).

---

## Validation commands

Executed against the live workspace:

```text
$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py shell -c "from staff.module_policy import validate_module_policy; print(validate_module_policy())"
[]

$ python manage.py shell -c "from staff.capability_catalog import validate_preset_maps; print(validate_preset_maps())"
[]
```

All three return clean: registry references only canonical capabilities,
preset maps only contain canonical capabilities, and Django's system
check passes.
