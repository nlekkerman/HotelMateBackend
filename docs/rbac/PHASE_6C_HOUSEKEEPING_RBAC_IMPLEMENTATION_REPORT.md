# Phase 6C — Housekeeping RBAC Implementation Report

**Status:** ✅ **GO**
**Module:** `housekeeping`
**Predecessor audit:** `PHASE_6C_HOUSEKEEPING_RBAC_AUDIT.md` (NO-GO, 7 blockers)
**Verdict:** All 7 blockers cleared; capabilities are the sole authority; tier
no longer grants any housekeeping action; nav no longer grants any mutation.

---

## 1. Files changed

| File | Change |
|------|--------|
| [staff/capability_catalog.py](staff/capability_catalog.py) | +9 housekeeping capability constants, +4 bundle constants, role/department preset distribution, tier-leak removal |
| [staff/module_policy.py](staff/module_policy.py) | New `'housekeeping'` `MODULE_POLICY` block with 11 actions, all canonical |
| [staff/permissions.py](staff/permissions.py) | +13 housekeeping permission classes (read + mutation) |
| [housekeeping/views.py](housekeeping/views.py) | Removed `HasHousekeepingNav` / `HasNavPermission` / `CanManageHousekeeping` from all viewsets; capability-only enforcement; PATCH/PUT split helper `_required_task_update_caps`; dashboard `open_tasks` gated by `HOUSEKEEPING_TASK_ASSIGN`; `assign` action hotel-scopes the `Staff` lookup |
| [housekeeping/serializers.py](housekeeping/serializers.py) | `HousekeepingTaskSerializer.read_only_fields` now pins `created_by`, `started_at`, `completed_at`; `HousekeepingTaskAssignSerializer.validate_assigned_to_id` uses a hotel-scoped lookup with a single generic error |
| [hotel/tests/test_rbac_housekeeping.py](hotel/tests/test_rbac_housekeeping.py) | New file, 46 tests, mirrors `test_rbac_rooms.py` structure |

---

## 2. Capabilities

### Added (9, canonical)

| Constant | Slug |
|---|---|
| `HOUSEKEEPING_MODULE_VIEW` | `housekeeping.module.view` |
| `HOUSEKEEPING_DASHBOARD_READ` | `housekeeping.dashboard.read` |
| `HOUSEKEEPING_TASK_READ` | `housekeeping.task.read` |
| `HOUSEKEEPING_TASK_CREATE` | `housekeeping.task.create` |
| `HOUSEKEEPING_TASK_UPDATE` | `housekeeping.task.update` |
| `HOUSEKEEPING_TASK_DELETE` | `housekeeping.task.delete` |
| `HOUSEKEEPING_TASK_EXECUTE` | `housekeeping.task.execute` |
| `HOUSEKEEPING_TASK_CANCEL` | `housekeeping.task.cancel` |
| `HOUSEKEEPING_ROOM_STATUS_HISTORY_READ` | `housekeeping.room_status.history.read` |

### Reused (4, pre-existing)

`HOUSEKEEPING_ROOM_STATUS_TRANSITION`, `HOUSEKEEPING_ROOM_STATUS_OVERRIDE`,
`HOUSEKEEPING_ROOM_STATUS_FRONT_DESK`, `HOUSEKEEPING_TASK_ASSIGN`.

All 13 are present in `CANONICAL_CAPABILITIES`.

---

## 3. Module policy (`MODULE_POLICY['housekeeping']`)

```
view_capability = HOUSEKEEPING_MODULE_VIEW
read_capability = HOUSEKEEPING_TASK_READ
actions:
    dashboard_read       -> housekeeping.dashboard.read
    task_create          -> housekeeping.task.create
    task_update          -> housekeeping.task.update
    task_delete          -> housekeeping.task.delete
    task_assign          -> housekeeping.task.assign
    task_execute         -> housekeeping.task.execute
    task_cancel          -> housekeeping.task.cancel
    status_transition    -> housekeeping.room_status.transition
    status_front_desk    -> housekeeping.room_status.front_desk
    status_override      -> housekeeping.room_status.override
    status_history_read  -> housekeeping.room_status.history.read
```

`validate_module_policy() == []` — every action key maps to a canonical capability.

---

## 4. Preset distribution

Bundles (defined in `staff/capability_catalog.py`):

```
_HOUSEKEEPING_BASE      = {module_view, dashboard_read, task_read, history_read}
_HOUSEKEEPING_OPERATE   = _BASE | {task_execute, room_status_transition}
_HOUSEKEEPING_SUPERVISE = _OPERATE | {task_create, task_update, task_assign,
                                      task_cancel, room_status_override}
_HOUSEKEEPING_MANAGE    = _SUPERVISE | {task_delete}
```

| Persona | Bundle | Notes |
|---|---|---|
| `front_office` department | `module_view + history_read + room_status_front_desk` (existing) | Sees module + history + can do front-desk transitions; cannot read tasks |
| `housekeeping` department | `_HOUSEKEEPING_OPERATE` | Operate floor (execute + transition) |
| `housekeeping_supervisor` role | `_HOUSEKEEPING_SUPERVISE` | + create/update/assign/cancel + override |
| `housekeeping_manager` role | `_HOUSEKEEPING_MANAGE` | + delete |
| `front_office_manager` role | `_HOUSEKEEPING_SUPERVISE` | Same as HK supervisor for HK actions |
| `operations_admin` role | `_HOUSEKEEPING_SUPERVISE` | |
| `hotel_manager` role | `_HOUSEKEEPING_MANAGE` | Full HK ladder except department-scoped `status_front_desk` |
| `_SUPERVISOR_AUTHORITY` tier add-on | `{CHAT_MESSAGE_MODERATE, STAFF_CHAT_CONVERSATION_MODERATE}` only | **Housekeeping caps removed** |

`validate_preset_maps() == []`.
**No tier preset carries any `housekeeping.*` capability** (verified by
`test_no_housekeeping_capability_in_any_tier_preset`).

---

## 5. Endpoint enforcement

| Endpoint | Method | Permission classes (Phase 6C) |
|---|---|---|
| `/housekeeping/dashboard/` | GET | `IsAuthenticated, IsStaffMember, IsSameHotel, CanViewHousekeepingModule, CanReadHousekeepingDashboard` |
| `/housekeeping/tasks/` | GET | `…, CanViewHousekeepingModule, CanReadHousekeepingTasks` |
| `/housekeeping/tasks/` | POST | `…, CanReadHousekeepingTasks, CanCreateHousekeepingTask` |
| `/housekeeping/tasks/{id}/` | GET | `…, CanReadHousekeepingTasks` |
| `/housekeeping/tasks/{id}/` | PATCH/PUT | `…, CanReadHousekeepingTasks` + payload-aware classes (see §6) |
| `/housekeeping/tasks/{id}/` | DELETE | `…, CanDeleteHousekeepingTask` |
| `/housekeeping/tasks/{id}/assign/` | POST | `…, CanReadHousekeepingTasks, CanAssignHousekeepingTask` |
| `/housekeeping/tasks/{id}/start/` | POST | `…, CanReadHousekeepingTasks, CanExecuteHousekeepingTask` |
| `/housekeeping/tasks/{id}/complete/` | POST | `…, CanReadHousekeepingTasks, CanExecuteHousekeepingTask` |
| `/housekeeping/rooms/{id}/status/` | POST | `…, CanViewHousekeepingModule` + capability check inside `policy.can_change_room_status` (transition / front_desk / override) |
| `/housekeeping/rooms/{id}/manager_override/` | POST | `…, CanOverrideHousekeepingRoomStatus` (no tier check) |
| `/housekeeping/rooms/{id}/status-history/` | GET | `…, CanReadHousekeepingStatusHistory` |

Dashboard `open_tasks` (the hotel-wide queue) is conditionally populated:
`if has_capability(request.user, HOUSEKEEPING_TASK_ASSIGN)`. Tier no longer
participates anywhere in the response shape.

---

## 6. PATCH/PUT split (`_required_task_update_caps`)

Mirrors the Phase 6B.2 rooms split. The helper inspects `request.data` and
returns the set of permission classes the body actually requires:

| Body contents | Required class(es) |
|---|---|
| `assigned_to` present | `CanAssignHousekeepingTask` |
| `status == 'CANCELLED'` | `CanCancelHousekeepingTask` |
| `status in ('IN_PROGRESS','DONE')` | `CanExecuteHousekeepingTask` |
| Any of `room / booking / task_type / priority / note` | `CanUpdateHousekeepingTask` |
| Empty body / unknown keys only | `CanUpdateHousekeepingTask` |
| Mixed | Union of all of the above |

This makes `task.update` strictly insufficient to mutate any action field.
Verified by 6 dedicated tests including
`test_housekeeper_cannot_patch_assigned_to`,
`test_housekeeper_cannot_patch_status_to_cancelled`,
`test_supervisor_mixed_payload_requires_all_caps`,
`test_housekeeper_mixed_payload_blocked_when_any_cap_missing`.

---

## 7. Serializer writable-surface changes

`HousekeepingTaskSerializer.Meta.read_only_fields` now includes
`created_by`, `started_at`, `completed_at` in addition to the previously
declared identifiers and display fields. `assigned_to` and `status`
remain writable but are gated by the PATCH/PUT split above.

---

## 8. Cross-hotel staff existence leak fix

`HousekeepingTaskAssignSerializer.validate_assigned_to_id` now performs a
hotel-scoped lookup:

```python
Staff.objects.get(id=value, hotel_id=requesting_staff.hotel_id)
```

Both `DoesNotExist` (truly missing) and "exists but in another hotel"
raise the **same** `ValidationError("Staff member not found.")`. No
differential disclosure. Verified by
`test_assign_does_not_leak_cross_hotel_staff_existence`, which asserts
the API response payloads are byte-identical for both inputs. The same
hotel-scoping was applied to the post-validation `Staff.objects.get(...)`
in `HousekeepingTaskViewSet.assign` for defense-in-depth.

---

## 9. Test matrix

`hotel/tests/test_rbac_housekeeping.py` — **46 tests, all passing**:

- `HousekeepingPolicyRegistryTest` (4): `validate_preset_maps`,
  `validate_module_policy`, registration, no decorative keys, no tier leak.
- `HousekeepingPolicyPersonaTest` (10): front_office, housekeeping,
  supervisor, manager, hotel_manager, operations_admin,
  front_office_manager, super_staff_admin (tier-only), staff_admin
  (tier-only), kitchen.
- `HousekeepingEndpointEnforcementTest` (32): module-view gate sweep,
  tier-only sweep, dashboard variants, list/create/delete personas,
  start/assign personas, all 6 PATCH-split permutations, room status
  transition + front-desk source + no-caps denial, manager_override
  tier-removal proof + supervisor-allow + housekeeper-deny, status
  history negative + 2 positive, cross-hotel assign leak regression.

---

## 10. Validation results

```
$ python manage.py test hotel.tests.test_rbac_housekeeping --verbosity=2 --keepdb
Ran 46 tests in ~5s — OK

$ python manage.py test hotel.tests.test_rbac_housekeeping \
                       hotel.tests.test_rbac_rooms \
                       hotel.tests.test_rbac_bookings --verbosity=2 --keepdb
Ran 128 tests in 15.760s — OK
```

`validate_module_policy() == []` — all action keys canonical.
`validate_preset_maps() == []` — every cap in every preset is canonical.
**No regressions** in `rooms` (Phase 6B) or `bookings` (Phase 5).

---

## 11. Remaining risks / follow-ups

1. **`status_front_desk` on `hotel_manager`**: by design, it is a
   department-scoped capability granted only via `front_office`.
   Hotel managers performing front-desk transitions must carry the
   `front_office` department, OR use `manager_override`. Documented in
   the persona test (`test_hotel_manager_manages_full` skips that key).
2. **Dead code**: `HasHousekeepingNav`, `HasNavPermission`, and the
   tier-based `CanManageHousekeeping` remain defined in
   `staff/permissions.py` but are no longer imported by housekeeping.
   Removal is deferred to a cleanup pass once Phase 6 covers all modules.
3. **Existing PEP-8 lint noise** in `housekeeping/views.py` (trailing
   whitespace, line-length) is pre-existing and not introduced by this
   change. `python -m py_compile housekeeping/views.py` succeeds.

---

## 12. Final verdict

✅ **GO** — Phase 6C Housekeeping RBAC is complete. Capabilities are the
only source of authority; tier carries zero housekeeping capabilities;
nav carries zero mutation authority; PATCH/PUT cannot bypass per-field
authority; cross-hotel staff existence does not leak via the assign
endpoint. All validators clean, all 128 RBAC tests pass.
