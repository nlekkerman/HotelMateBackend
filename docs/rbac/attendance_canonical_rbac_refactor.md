# Attendance Module — Canonical Capability-Based RBAC Refactor

This document records the refactor of the **`attendance`** backend module from
the legacy `HasNavPermission("attendance")` / `CanManageRoster` / tier-as-authority
pattern onto the canonical capability-based RBAC chain already used by `bookings`,
`rooms`, `housekeeping`, `maintenance`, `staff_management`, `chat`, and
`staff_chat`.

The refactor is **code-only**. No frontend changes were made. No tests were
edited. Tier still does **not** double as an authority engine — manage-class
authority lands on the `hotel_manager` role, while the three staff tiers
(`regular_staff`, `staff_admin`, `super_staff_admin`) only carry the
self-service base.

---

## 1. Files modified

| File | Change |
|------|--------|
| [staff/capability_catalog.py](staff/capability_catalog.py) | Added 38 attendance capability constants; added `_ATTENDANCE_SELF_SERVICE` and `_ATTENDANCE_MANAGE` bundles; added `_ATTENDANCE_SELF_SERVICE` to all three staff tiers; added `_ATTENDANCE_MANAGE` to `hotel_manager` role; added all new caps to `CANONICAL_CAPABILITIES`. |
| [staff/module_policy.py](staff/module_policy.py) | Added 38 attendance capability imports; added new `MODULE_POLICY['attendance']` block with `view_capability`, `read_capability`, and full per-action map. |
| [staff/permissions.py](staff/permissions.py) | Appended a new attendance import block plus 37 zero-arg permission classes (one per action capability + the module-view gate). |
| [attendance/views.py](attendance/views.py) | Removed legacy import (`HasNavPermission, CanManageRoster, resolve_tier, _tier_at_least`); added canonical imports; rewrote `get_permissions` on `ClockLogViewSet`, `RosterPeriodViewSet`, `StaffRosterViewSet`, `ShiftLocationViewSet`, `DailyPlanViewSet`, `DailyPlanEntryViewSet`, `CopyRosterViewSet`; added queryset scoping on `ClockLogViewSet`; added inline ownership checks on `stay_clocked_in`, `force_clock_out`, `unrostered_confirm`; replaced `_tier_at_least(resolve_tier(...))` in `finalize_period` with `has_capability(user, ATTENDANCE_PERIOD_FORCE_FINALIZE)`. |
| [attendance/views_analytics.py](attendance/views_analytics.py) | Removed `HasNavPermission` import; rewrote `RosterAnalyticsViewSet.get_permissions` to canonical chain ending in `CanReadAttendanceAnalytics`. |
| [attendance/face_views.py](attendance/face_views.py) | Removed `HasNavPermission` import; rewrote `FaceManagementViewSet.get_permissions` with per-action capability map; added inline `face.register_other` check inside `register_face`; replaced inline `HasNavPermission('attendance').has_permission(...)` blocks in three function-based views (`force_clock_in_unrostered`, `confirm_clock_out_view`, `toggle_break_view`) with class-based `permission_classes` chains. |

---

## 2. Capabilities added

All slugs added to [staff/capability_catalog.py](staff/capability_catalog.py)
and to `CANONICAL_CAPABILITIES`.

### Self-service (granted to every staff tier via `_ATTENDANCE_SELF_SERVICE`)

| Constant | Slug |
|---|---|
| `ATTENDANCE_MODULE_VIEW` | `attendance.module.view` |
| `ATTENDANCE_CLOCK_IN_OUT` | `attendance.clock.in_out` |
| `ATTENDANCE_BREAK_TOGGLE` | `attendance.break.toggle` |
| `ATTENDANCE_LOG_READ_SELF` | `attendance.log.read_self` |
| `ATTENDANCE_ROSTER_READ_SELF` | `attendance.roster.read_self` |
| `ATTENDANCE_FACE_REGISTER_SELF` | `attendance.face.register_self` |

### Management (granted to `hotel_manager` role via `_ATTENDANCE_MANAGE`)

| Constant | Slug |
|---|---|
| `ATTENDANCE_LOG_READ_ALL` | `attendance.log.read_all` |
| `ATTENDANCE_LOG_CREATE` | `attendance.log.create` |
| `ATTENDANCE_LOG_UPDATE` | `attendance.log.update` |
| `ATTENDANCE_LOG_DELETE` | `attendance.log.delete` |
| `ATTENDANCE_LOG_APPROVE` | `attendance.log.approve` |
| `ATTENDANCE_LOG_REJECT` | `attendance.log.reject` |
| `ATTENDANCE_LOG_RELINK` | `attendance.log.relink` |
| `ATTENDANCE_ANALYTICS_READ` | `attendance.analytics.read` |
| `ATTENDANCE_PERIOD_READ` | `attendance.period.read` |
| `ATTENDANCE_PERIOD_CREATE` | `attendance.period.create` |
| `ATTENDANCE_PERIOD_UPDATE` | `attendance.period.update` |
| `ATTENDANCE_PERIOD_DELETE` | `attendance.period.delete` |
| `ATTENDANCE_PERIOD_FINALIZE` | `attendance.period.finalize` |
| `ATTENDANCE_PERIOD_UNFINALIZE` | `attendance.period.unfinalize` |
| `ATTENDANCE_PERIOD_FORCE_FINALIZE` | `attendance.period.force_finalize` |
| `ATTENDANCE_SHIFT_READ` | `attendance.shift.read` |
| `ATTENDANCE_SHIFT_CREATE` | `attendance.shift.create` |
| `ATTENDANCE_SHIFT_UPDATE` | `attendance.shift.update` |
| `ATTENDANCE_SHIFT_DELETE` | `attendance.shift.delete` |
| `ATTENDANCE_SHIFT_BULK_WRITE` | `attendance.shift.bulk_write` |
| `ATTENDANCE_SHIFT_COPY` | `attendance.shift.copy` |
| `ATTENDANCE_SHIFT_EXPORT_PDF` | `attendance.shift.export_pdf` |
| `ATTENDANCE_SHIFT_LOCATION_READ` | `attendance.shift_location.read` |
| `ATTENDANCE_SHIFT_LOCATION_MANAGE` | `attendance.shift_location.manage` |
| `ATTENDANCE_DAILY_PLAN_READ` | `attendance.daily_plan.read` |
| `ATTENDANCE_DAILY_PLAN_MANAGE` | `attendance.daily_plan.manage` |
| `ATTENDANCE_DAILY_PLAN_ENTRY_MANAGE` | `attendance.daily_plan.entry_manage` |
| `ATTENDANCE_FACE_READ` | `attendance.face.read` |
| `ATTENDANCE_FACE_REGISTER_OTHER` | `attendance.face.register_other` |
| `ATTENDANCE_FACE_REVOKE` | `attendance.face.revoke` |
| `ATTENDANCE_FACE_AUDIT_READ` | `attendance.face.audit_read` |

### Preset bundles

```python
_ATTENDANCE_SELF_SERVICE = frozenset({
    ATTENDANCE_MODULE_VIEW, ATTENDANCE_CLOCK_IN_OUT,
    ATTENDANCE_BREAK_TOGGLE, ATTENDANCE_LOG_READ_SELF,
    ATTENDANCE_ROSTER_READ_SELF, ATTENDANCE_FACE_REGISTER_SELF,
})
_ATTENDANCE_MANAGE = _ATTENDANCE_SELF_SERVICE | frozenset({
    # all 32 management caps
})
```

### Preset wiring

- `TIER_DEFAULT_CAPABILITIES['regular_staff']` ← `_ATTENDANCE_SELF_SERVICE`
- `TIER_DEFAULT_CAPABILITIES['staff_admin']` ← `_ATTENDANCE_SELF_SERVICE`
- `TIER_DEFAULT_CAPABILITIES['super_staff_admin']` ← `_ATTENDANCE_SELF_SERVICE`
- `ROLE_PRESET_CAPABILITIES['hotel_manager']` ← `_ATTENDANCE_MANAGE` (union)

Tier never carries manage-class authority. A `super_staff_admin` who is **not**
also `hotel_manager` cannot finalize periods, write shifts, manage roster, or
read hotel-wide attendance logs unless explicitly granted via per-staff
overrides — exactly mirroring the bookings / rooms / housekeeping convention.

---

## 3. Module policy added

A new `MODULE_POLICY['attendance']` block was added at the top of
[staff/module_policy.py](staff/module_policy.py):

```python
'attendance': {
    'view_capability': ATTENDANCE_MODULE_VIEW,
    'read_capability': ATTENDANCE_LOG_READ_SELF,
    'actions': {
        'clock_in_out':            ATTENDANCE_CLOCK_IN_OUT,
        'break_toggle':            ATTENDANCE_BREAK_TOGGLE,
        'log_read_self':           ATTENDANCE_LOG_READ_SELF,
        'log_read_all':            ATTENDANCE_LOG_READ_ALL,
        'log_create':              ATTENDANCE_LOG_CREATE,
        'log_update':              ATTENDANCE_LOG_UPDATE,
        'log_delete':              ATTENDANCE_LOG_DELETE,
        'log_approve':             ATTENDANCE_LOG_APPROVE,
        'log_reject':              ATTENDANCE_LOG_REJECT,
        'log_relink':              ATTENDANCE_LOG_RELINK,
        'analytics_read':          ATTENDANCE_ANALYTICS_READ,
        'period_read':             ATTENDANCE_PERIOD_READ,
        'period_create':           ATTENDANCE_PERIOD_CREATE,
        'period_update':           ATTENDANCE_PERIOD_UPDATE,
        'period_delete':           ATTENDANCE_PERIOD_DELETE,
        'period_finalize':         ATTENDANCE_PERIOD_FINALIZE,
        'period_unfinalize':       ATTENDANCE_PERIOD_UNFINALIZE,
        'period_force_finalize':   ATTENDANCE_PERIOD_FORCE_FINALIZE,
        'shift_read':              ATTENDANCE_SHIFT_READ,
        'shift_create':            ATTENDANCE_SHIFT_CREATE,
        'shift_update':            ATTENDANCE_SHIFT_UPDATE,
        'shift_delete':            ATTENDANCE_SHIFT_DELETE,
        'shift_bulk_write':        ATTENDANCE_SHIFT_BULK_WRITE,
        'shift_copy':              ATTENDANCE_SHIFT_COPY,
        'shift_export_pdf':        ATTENDANCE_SHIFT_EXPORT_PDF,
        'shift_location_read':     ATTENDANCE_SHIFT_LOCATION_READ,
        'shift_location_manage':   ATTENDANCE_SHIFT_LOCATION_MANAGE,
        'daily_plan_read':         ATTENDANCE_DAILY_PLAN_READ,
        'daily_plan_manage':       ATTENDANCE_DAILY_PLAN_MANAGE,
        'daily_plan_entry_manage': ATTENDANCE_DAILY_PLAN_ENTRY_MANAGE,
        'face_read':               ATTENDANCE_FACE_READ,
        'face_register_self':      ATTENDANCE_FACE_REGISTER_SELF,
        'face_register_other':     ATTENDANCE_FACE_REGISTER_OTHER,
        'face_revoke':             ATTENDANCE_FACE_REVOKE,
        'face_audit_read':         ATTENDANCE_FACE_AUDIT_READ,
        'roster_read_self':        ATTENDANCE_ROSTER_READ_SELF,
    },
},
```

`validate_module_policy()` returns `[]`.

---

## 4. Permission classes added

Appended to [staff/permissions.py](staff/permissions.py) — 37 classes, all
zero-arg subclasses of `HasCapability`, mirroring the maintenance and
staff_management style. Read/visibility gates set `safe_methods_bypass = False`
so GETs are explicitly enforced.

```text
CanViewAttendanceModule
CanClockInOut
CanToggleAttendanceBreak
CanReadOwnAttendanceLog
CanReadAllAttendanceLogs
CanReadOwnRoster
CanCreateAttendanceLog
CanUpdateAttendanceLog
CanDeleteAttendanceLog
CanApproveAttendanceLog
CanRejectAttendanceLog
CanRelinkAttendanceLog
CanReadAttendanceAnalytics
CanReadAttendancePeriod
CanCreateAttendancePeriod
CanUpdateAttendancePeriod
CanDeleteAttendancePeriod
CanFinalizeAttendancePeriod
CanUnfinalizeAttendancePeriod
CanForceFinalizeAttendancePeriod
CanReadAttendanceShift
CanCreateAttendanceShift
CanUpdateAttendanceShift
CanDeleteAttendanceShift
CanBulkWriteAttendanceShift
CanCopyAttendanceShift
CanExportAttendanceShiftPdf
CanReadShiftLocation
CanManageShiftLocation
CanReadDailyPlan
CanManageDailyPlan
CanManageDailyPlanEntry
CanReadAttendanceFace
CanRegisterOwnAttendanceFace
CanRegisterOtherAttendanceFace
CanRevokeAttendanceFace
CanReadAttendanceFaceAudit
```

---

## 5. Endpoint mapping summary

Every endpoint chains:
`IsAuthenticated → CanViewAttendanceModule → IsStaffMember → IsSameHotel → <action capability>`

### `ClockLogViewSet` ([attendance/views.py](attendance/views.py))

| Action | Capability |
|---|---|
| `register_face` | `face.register_self` |
| `face_clock_in` | `clock.in_out` |
| `current_status` | `clock.in_out` |
| `detect_face_only` | `clock.in_out` |
| `stay_clocked_in` | `log.read_self` + inline owner-or-`log.update` |
| `force_clock_out` | `log.read_self` + inline owner-or-`log.update` |
| `unrostered_confirm` | `log.read_self` + inline self-or-`log.create` |
| `currently_clocked_in` | `log.read_all` |
| `department_logs` | `log.read_all` |
| `department_status` | `log.read_all` |
| `create` | `log.create` |
| `update` / `partial_update` | `log.update` |
| `destroy` | `log.delete` |
| `approve_log` | `log.approve` |
| `reject_log` | `log.reject` |
| `auto_attach_shift` | `log.relink` |
| `relink_day` | `log.relink` |
| `list` / `retrieve` | `log.read_self` (queryset scoped to own-staff unless user has `log.read_all`) |

### `RosterPeriodViewSet` ([attendance/views.py](attendance/views.py))

| Action | Capability |
|---|---|
| `list` / `retrieve` / `finalization_status` / `finalized_rosters_by_department` | `period.read` |
| `create` / `create_for_week` / `create_custom_period` / `duplicate_period` / `add_shift` / `create_department_roster` | `period.create` |
| `update` / `partial_update` | `period.update` |
| `destroy` | `period.delete` |
| `finalize_period` | `period.finalize` (force-override path uses `has_capability(..., period.force_finalize)`) |
| `unfinalize_period` | `period.unfinalize` |
| `export_pdf` | `shift.export_pdf` |

### `StaffRosterViewSet` ([attendance/views.py](attendance/views.py))

| Action | Capability |
|---|---|
| `list` / `retrieve` | `shift.read` |
| `create` | `shift.create` |
| `update` / `partial_update` | `shift.update` |
| `destroy` | `shift.delete` |
| `bulk_save` | `shift.bulk_write` |
| `daily_pdf` / `staff_pdf` | `shift.export_pdf` |

### `ShiftLocationViewSet` ([attendance/views.py](attendance/views.py))

| Action | Capability |
|---|---|
| `list` / `retrieve` | `shift_location.read` |
| `create` / `update` / `partial_update` / `destroy` | `shift_location.manage` |

### `DailyPlanViewSet` ([attendance/views.py](attendance/views.py))

| Action | Capability |
|---|---|
| `list` / `retrieve` / `prepare_daily_plan` / `download_pdf` | `daily_plan.read` |
| `create` / `update` / `partial_update` / `destroy` | `daily_plan.manage` |

### `DailyPlanEntryViewSet` ([attendance/views.py](attendance/views.py))

| Action | Capability |
|---|---|
| `list` / `retrieve` | `daily_plan.read` |
| `create` / `update` / `partial_update` / `destroy` | `daily_plan.entry_manage` |

### `CopyRosterViewSet` ([attendance/views.py](attendance/views.py))

| Action | Capability |
|---|---|
| All | `shift.copy` |

### `RosterAnalyticsViewSet` ([attendance/views_analytics.py](attendance/views_analytics.py))

| Action | Capability |
|---|---|
| All (`kpis`, etc.) | `analytics.read` |

### `FaceManagementViewSet` ([attendance/face_views.py](attendance/face_views.py))

| Action | Capability |
|---|---|
| `register_face` | `face.register_self` (+ inline `face.register_other` if `staff_id` ≠ self) |
| `revoke_face` | `face.revoke` |
| `list_faces` | `face.read` |
| `face_clock_in` | `clock.in_out` |
| `detect_staff_with_status` | `clock.in_out` |
| `audit_logs` | `face.audit_read` |
| `face_status` | `face.register_self` |
| `force_clock_in_unrostered` (action) | `clock.in_out` |
| `confirm_clock_out` (action) | `clock.in_out` |
| `toggle_break` (action) | `break.toggle` |

### Function-based views ([attendance/face_views.py](attendance/face_views.py))

| FBV | `permission_classes` |
|---|---|
| `force_clock_in_unrostered` | `IsAuthenticated, CanViewAttendanceModule, IsStaffMember, IsSameHotel, CanClockInOut` |
| `confirm_clock_out_view` | `IsAuthenticated, CanViewAttendanceModule, IsStaffMember, IsSameHotel, CanClockInOut` |
| `toggle_break_view` | `IsAuthenticated, CanViewAttendanceModule, IsStaffMember, IsSameHotel, CanToggleAttendanceBreak` |

---

## 6. Ownership rules added / fixed

| Endpoint | Rule |
|---|---|
| `ClockLogViewSet.stay_clocked_in` | Caller must own the log (`log.staff_id == request.user.staff_profile.id`) **or** have `ATTENDANCE_LOG_UPDATE`. |
| `ClockLogViewSet.force_clock_out` | Caller must own the log **or** have `ATTENDANCE_LOG_UPDATE`. |
| `ClockLogViewSet.unrostered_confirm` | `staff_id` payload must equal caller's own staff id **or** caller must have `ATTENDANCE_LOG_CREATE`. |
| `ClockLogViewSet` list/retrieve | Queryset scoped to caller's own logs unless caller has `ATTENDANCE_LOG_READ_ALL`. |
| `FaceManagementViewSet.register_face` | If `staff_id` payload differs from caller's own staff id, caller must have `ATTENDANCE_FACE_REGISTER_OTHER`. |
| `RosterPeriodViewSet.finalize_period` | `force=true` path requires `ATTENDANCE_PERIOD_FORCE_FINALIZE` (replacement for `_tier_at_least(... 'super_staff_admin')`). |

All ownership checks use `has_capability(user, CAP)` for the manager-override
fallback — the canonical authority engine, never tier-string comparison.

---

## 7. Legacy gates removed

| Removed pattern | Replacement |
|---|---|
| `from staff.permissions import HasNavPermission` (in 3 files) | Removed |
| `from staff.permissions import CanManageRoster, resolve_tier, _tier_at_least` | Removed |
| `HasNavPermission('attendance')` in viewset `get_permissions` (8 viewsets) | Per-action capability map |
| `CanManageRoster()` in viewset `get_permissions` (6 viewsets) | Action-specific capability classes |
| Inline `HasNavPermission('attendance').has_permission(request, None)` in 3 FBVs | Class-based `permission_classes` decorator |
| `_tier_at_least(resolve_tier(request.user), 'super_staff_admin')` in `finalize_period` | `has_capability(request.user, ATTENDANCE_PERIOD_FORCE_FINALIZE)` |

Final grep sweep within `attendance/`:

```
$ grep -rE 'HasNavPermission|CanManageRoster|_tier_at_least|resolve_tier\(' attendance/
(no matches)
```

`role.slug` and `access_level` do not appear anywhere in `attendance/`.
`department.slug` only appears in serializer output and dataset filtering
(non-security contexts: log payload `dept_slug`, queryset `.filter(...)`).

---

## 8. Validation results

All three validators were run via `venv\Scripts\python.exe`:

```
$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py shell -c "from staff.module_policy import validate_module_policy; print(validate_module_policy())"
[]

$ python manage.py shell -c "from staff.capability_catalog import validate_preset_maps; print(validate_preset_maps())"
[]
```

✅ `manage.py check` — clean.
✅ `validate_module_policy()` — `[]` (every action capability resolves to a known constant).
✅ `validate_preset_maps()` — `[]` (every tier / role / department preset references only canonical capabilities).

---

## 9. Notes & follow-ups

- **`CanForceFinalizeAttendancePeriod`** is registered as a permission class
  but is currently enforced inline in `finalize_period` via `has_capability(...)`
  to preserve the existing UX (`force=true` path returns a structured error if
  the caller lacks the override). It is reserved for a future dedicated
  endpoint if one is ever introduced.
- **`CanReadOwnRoster`** is registered against `ATTENDANCE_ROSTER_READ_SELF`
  but no current endpoint maps to it directly — it exists as a primitive for
  the future "own-roster" self-service screens already covered by
  `StaffRosterViewSet` queryset filtering on `staff` query param. No frontend
  change is required at this time.
- The `Daily plan`/`download_pdf` action key on `DailyPlanViewSet` is mapped
  defensively in `get_permissions` even though no `download_pdf` action is
  currently defined; the mapping is harmless and ready if the action is added.
- No tests were edited as part of this refactor. Existing attendance tests
  that exercise non-RBAC behaviour continue to pass `manage.py check`. Any
  test that mocks `HasNavPermission` or `CanManageRoster` directly will need
  updating in a follow-up dedicated test pass — out of scope for this code-only
  refactor as instructed.
- Frontend RBAC alignment: the new capability slugs (`attendance.module.view`,
  `attendance.clock.in_out`, …) are emitted automatically by `resolve_capabilities`
  and surfaced through the existing `/me/effective-capabilities/` and module-policy
  endpoints. No frontend code change is part of this task; alignment of the
  existing `rbac.attendance` object on the client is a separate, out-of-scope
  effort.

---

**Status:** ✅ Complete.
The attendance module is now on the canonical capability-based RBAC chain,
with no legacy nav-as-security or tier-as-authority patterns remaining in the
module's source.
