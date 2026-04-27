# Attendance RBAC Cleanup Audit

**Scope:** review of the recently merged attendance canonical-capability
refactor. Code-only verification. No code changes proposed below the
"Implementation plan" section — those are recommendations.

---

## 1. Files inspected

| File | Reason |
|---|---|
| [staff/capability_catalog.py](staff/capability_catalog.py) | Capability constants, `_ATTENDANCE_*` bundles, tier/role/department presets, `resolve_capabilities`, `validate_preset_maps`. |
| [staff/module_policy.py](staff/module_policy.py) | `MODULE_POLICY['attendance']` action map. |
| [staff/permissions.py](staff/permissions.py) | Attendance permission classes appended at the bottom + `has_capability` helper definition. |
| [staff/role_catalog.py](staff/role_catalog.py) | `CANONICAL_ROLES` list (verified `hotel_manager` is present); `LEGACY_ROLE_REMAP` and `resolve_legacy_manager_target`. |
| [staff/management/commands/seed_canonical_roles.py](staff/management/commands/seed_canonical_roles.py) | Seeds `CANONICAL_ROLES` per hotel. |
| [staff/migrations/0027_seed_canonical_roles.py](staff/migrations/0027_seed_canonical_roles.py) | Data migration that materializes the canonical roles + reassigns legacy `manager`/`admin` rows. |
| [staff/migrations/0028_remove_operations_admin_role.py](staff/migrations/0028_remove_operations_admin_role.py) | Reassigns existing `operations_admin` staff onto `hotel_manager`. |
| [hotel/provisioning.py](hotel/provisioning.py) | Hotel + primary admin atomic provisioning (where `access_level="super_staff_admin"` is hard-coded for the primary admin). |
| [hotel/provisioning_serializers.py](hotel/provisioning_serializers.py) | Confirms `role_id` on the primary admin is **optional / nullable**. |
| [attendance/views.py](attendance/views.py) | `get_permissions` / `get_queryset` / inline `has_capability` calls. |
| [attendance/views_analytics.py](attendance/views_analytics.py) | `RosterAnalyticsViewSet.get_permissions`. |
| [attendance/face_views.py](attendance/face_views.py) | `FaceManagementViewSet.get_permissions` + 3 FBVs + inline ownership check on `register_face`. |
| Existing peer modules: bookings/rooms/housekeeping/maintenance/staff_management capability declarations and `ROLE_PRESET_CAPABILITIES['hotel_manager']` to derive the established granularity convention. |

---

## 2. Capability granularity recommendation

### 2.1 Comparison with peer modules (verified from code)

| Module | Granularity style observed |
|---|---|
| `bookings` | Coarse: `BOOKING_RECORD_READ/UPDATE`, `BOOKING_CONFIG_MANAGE`. |
| `rooms` | Mixed: `ROOM_INVENTORY_READ/CREATE/UPDATE/DELETE` (fine), `ROOM_TYPE_MANAGE` and `ROOM_MEDIA_MANAGE` (coarse). |
| `housekeeping` | Action-fine: `TASK_READ/CREATE/UPDATE/DELETE/EXECUTE/CANCEL/ASSIGN`, plus per-action `ROOM_STATUS_TRANSITION/OVERRIDE/FRONT_DESK/HISTORY_READ`. |
| `maintenance` | Action-fine: `REQUEST_READ/CREATE/ACCEPT/RESOLVE/UPDATE/REASSIGN/REOPEN/DELETE`. |
| `staff_management` | Mixed: `STAFF_READ/CREATE/UPDATE/DELETE` (fine for the primary entity), `ROLE_MANAGE`, `DEPARTMENT_MANAGE` (coarse for config entities). |

**Established convention:** primary work objects (Task, Request, Staff)
get **action-fine** capabilities so that authority can be split between
operate / supervise / manage personas. Config / lookup entities (Type,
Media, Role, Department, Category) get **coarse `_MANAGE`** caps.

### 2.2 Attendance audit against that convention

| Cluster | Current attendance split | Style match | Verdict |
|---|---|---|---|
| `period.*` (read/create/update/delete/finalize/unfinalize/force_finalize) | Action-fine | Matches `maintenance.request.*` (`accept`, `resolve`, `reopen` are also "lifecycle transitions" similar to `finalize` / `unfinalize`). | **Keep current split.** `finalize` / `unfinalize` / `force_finalize` are distinct authorities (manager vs admin override). Collapsing them into `period.manage` would lose the force-finalize override gate that today is enforced via `has_capability(..., ATTENDANCE_PERIOD_FORCE_FINALIZE)`. |
| `shift.*` (read/create/update/delete/bulk_write/copy/export_pdf) | Action-fine | Matches `housekeeping.task.*` granularity. | **Keep current split.** `bulk_write` and `copy` are intentionally separable from individual CUD because they are batch / cross-period operations with different authority requirements (e.g., copy across hotels is the most-common audited action). `export_pdf` is also intentionally a separable cap (matches `staff_management` printable-document patterns and is reused by `period.export_pdf`). |
| `daily_plan.*` (`read`, `manage`, `entry_manage`) | Coarse + sub-coarse | Matches `room.type.read`/`room.type.manage` style. | **Keep.** `entry_manage` is a distinct authority because nested `DailyPlanEntry` mutations happen through a different URL hierarchy and may be granted to a sub-persona without granting whole-plan management. |
| `shift_location.*` (`read`, `manage`) | Coarse | Matches `room.media.read` / `room.media.manage`. | **Keep.** |
| `face.*` (`read`, `register_self`, `register_other`, `revoke`, `audit_read`) | Action-fine | No identical peer; closest is `staff_management.staff.create/update/delete` + audit reads. | **Keep current split.** `register_self` vs `register_other` is the canonical "self-service vs manager-on-behalf" split (used directly by `register_face`'s inline check); `audit_read` is independently meaningful (compliance personas). |
| `log.*` (`read_self`, `read_all`, `create`, `update`, `delete`, `approve`, `reject`, `relink`) | Action-fine | Matches `maintenance.request.*` precisely. | **Keep.** `approve`/`reject`/`relink` are distinct lifecycle transitions and are gated separately by their corresponding viewset actions. |
| `clock.in_out`, `break.toggle` | Coarse self-service | Matches `_BOOKING_OPERATE` style for tier-self-service. | **Keep.** |

### 2.3 Recommendation

**Keep current split.** No collapse is warranted. Every fine-grained
capability either:

1. Maps 1:1 to an exclusive viewset action (so it is observably gating a
   distinct endpoint), **or**
2. Is referenced from inline `has_capability(...)` ownership / override
   checks (force-finalize, register-other, log.create-on-behalf,
   log.update-override, log.read_all queryset scoping), **or**
3. Mirrors an established peer-module split (`maintenance.request.*`,
   `housekeeping.task.*`).

The only borderline cap is `ATTENDANCE_ROSTER_READ_SELF`. It is granted
in `_ATTENDANCE_SELF_SERVICE` and registered as a permission class
(`CanReadOwnRoster`) but **no current endpoint maps to it directly**
(roster-self read happens through `StaffRosterViewSet` filtered by
query param `staff`, gated by `ATTENDANCE_SHIFT_READ`). It is harmless
but cosmetic. Either:

- (a) Leave it as a forward-looking primitive (current state), or
- (b) Drop it and `CanReadOwnRoster` until a dedicated own-roster
  endpoint exists.

Recommendation: **(a)** — keep it as a primitive; removing it costs more
churn than it saves.

---

## 3. Preset / role-assignment findings

### 3.1 Where `_ATTENDANCE_MANAGE` is granted

[staff/capability_catalog.py:1210](staff/capability_catalog.py) —
`ROLE_PRESET_CAPABILITIES['hotel_manager']` includes `_ATTENDANCE_MANAGE`.

It is **not** granted by any `TIER_DEFAULT_CAPABILITIES` entry and
**not** granted by any `DEPARTMENT_PRESET_CAPABILITIES` entry. There is
no `'management'` or `'administration'` department preset at all.

Tier presets only carry `_ATTENDANCE_SELF_SERVICE` for all three tiers.

### 3.2 Is `hotel_manager` a real seeded role?

Yes — verified via:

- [staff/role_catalog.py:100](staff/role_catalog.py) — `hotel_manager` in `CANONICAL_ROLES`.
- [staff/migrations/0027_seed_canonical_roles.py](staff/migrations/0027_seed_canonical_roles.py) — data migration creates one `hotel_manager` row per hotel.
- [staff/management/commands/seed_canonical_roles.py](staff/management/commands/seed_canonical_roles.py) — repeatable management command.
- [staff/migrations/0028_remove_operations_admin_role.py](staff/migrations/0028_remove_operations_admin_role.py) — reassigns legacy `operations_admin` → `hotel_manager`.
- [staff/role_catalog.py:174,188-199](staff/role_catalog.py) — `LEGACY_ROLE_REMAP['admin'] = 'hotel_manager'` and `_MANAGER_BY_DEPT['management']/['administration'] = 'hotel_manager'` and `resolve_legacy_manager_target()` defaulting to `hotel_manager`.

So the role exists and is consistently the destination for "admin-like"
legacy rows.

### 3.3 Does the primary admin actually receive `hotel_manager`?

**No, not automatically.** Verified at
[hotel/provisioning.py:128-173](hotel/provisioning.py):

```python
role = None
role_id = admin_data.get("role_id")
…
if role_id is not None:
    role = Role.objects.get(id=role_id)
…
staff = Staff.objects.create(
    …
    role=role,                     # may be None
    access_level="super_staff_admin",
    is_active=True,
)
```

[hotel/provisioning_serializers.py:29](hotel/provisioning_serializers.py)
confirms `role_id = serializers.IntegerField(required=False, allow_null=True, default=None)`.

So the primary admin can land with **`access_level='super_staff_admin'`
and `role=NULL`**, in which case `resolve_capabilities(...)` returns
only `_SUPERVISOR_AUTHORITY | _BOOKING_SUPERVISE | _CHAT_BASE |
_STAFF_CHAT_BASE | _ATTENDANCE_SELF_SERVICE`. They would **not** carry
`_ATTENDANCE_MANAGE`.

### 3.4 Does `super_staff_admin` rely on role preset or tier preset?

**Role preset, exclusively.** [staff/capability_catalog.py:1163-1166](staff/capability_catalog.py):

```python
'super_staff_admin': (
    _SUPERVISOR_AUTHORITY | _BOOKING_SUPERVISE
    | _CHAT_BASE | _STAFF_CHAT_BASE | _ATTENDANCE_SELF_SERVICE
),
```

`_ATTENDANCE_MANAGE` is **not** in any tier bundle. This matches the
established Phase 6A.2 / 6B.1 / 6C / 6D.1 / 6E.1 convention: "tier no
longer grants ..._MANAGE caps". The new attendance refactor follows
the same convention.

### 3.5 Risk: would current `super_staff_admin` lose attendance management?

**Yes, if and only if they have no `hotel_manager` role.** This is the
**identical** risk that already applies to bookings, rooms, housekeeping,
maintenance, and staff_management since their respective Phase 6 cuts.
It is not a regression introduced by the attendance refactor; it is the
current canonical convention.

Concretely, the at-risk personas are any active `Staff` with:

- `access_level = 'super_staff_admin'` (or `staff_admin`, but those never had
  attendance management), AND
- `role_id IS NULL` OR `role.slug NOT IN { 'hotel_manager' }`.

`hotel_manager` is the only role preset that today carries
`_ATTENDANCE_MANAGE` (verified by full-file scan of
`ROLE_PRESET_CAPABILITIES`).

### 3.6 Minimal-fix recommendation

There is no code-level fix that "auto-grants" attendance management to
tier `super_staff_admin` without breaking the established
no-tier-as-authority rule. The minimal, code-derivable fixes are
**operational**, not code:

- **Run a one-shot SQL/data audit** to enumerate active staff at risk
  (filter above) and confirm they hold `hotel_manager` (or are
  intentionally non-managers). The same audit was the gate for shipping
  Phase 6A.2 onwards; reuse the same script:
  [scripts/validation/rbac_phase6a_validation.py](scripts/validation/rbac_phase6a_validation.py)
  is the reference pattern.
- **At provisioning time**, require `role_id` for the primary admin and
  default it to the seeded `hotel_manager` row for the new hotel. This
  is a one-line behavioural fix in `hotel/provisioning.py` (assign
  `role` to the seeded `hotel_manager` for the new hotel when
  `role_id is None`) — but it is **out of scope** for this attendance
  audit. Recommend filing as a separate ticket if not already tracked.

No code change is required to the **attendance refactor itself** to
mitigate this risk; the risk surface is identical to peer modules and
already governed by the existing operational gating.

---

## 4. Inline `has_capability()` findings

Verified inline call sites (excluding docstring references):

| File:Line | Action | Classification | Justification |
|---|---|---|---|
| [attendance/views.py:409](attendance/views.py) | `ClockLogViewSet.get_queryset` (`list`/`retrieve`) | **Required (queryset scoping)** | DRF permissions cannot rewrite a queryset; this scopes to own-staff unless caller has `ATTENDANCE_LOG_READ_ALL`. Cannot be expressed as a permission class. |
| [attendance/views.py:826](attendance/views.py) | `ClockLogViewSet.unrostered_confirm` (target staff != self) | **Required (runtime payload)** | Authority depends on the request body's `staff_id`. A static permission class cannot read action payload. |
| [attendance/views.py:991](attendance/views.py) | `ClockLogViewSet.stay_clocked_in` (log.staff != self) | **Required (object ownership)** | Authority depends on the looked-up `ClockLog.staff_id` vs caller's `staff_profile.id`. Could be moved to `has_object_permission`, but that would split the gate across two classes for one endpoint and lose the structured 403 message. Inline is more readable. |
| [attendance/views.py:1036](attendance/views.py) | `ClockLogViewSet.force_clock_out` (log.staff != self) | **Required (object ownership)** | Same as above. |
| [attendance/views.py:1529](attendance/views.py) | `RosterPeriodViewSet.finalize_period` (`force=True` branch) | **Required (runtime force flag)** | The same endpoint is used for both regular finalize and admin force-finalize; the discriminator is the `force` payload flag. Class-level gate is `CanFinalizeAttendancePeriod`; inline check escalates only when `force=True`. The structured response (`{"can_force": is_admin, "suggestion": …}`) requires the boolean to be visible inside the action body. |
| [attendance/face_views.py:140](attendance/face_views.py) | `FaceManagementViewSet.register_face` (target staff_id != self) | **Required (runtime payload)** | Identical pattern to `unrostered_confirm`. |

**None of the inline calls are replaceable with a static permission
class.** Two of them (`stay_clocked_in`, `force_clock_out`) could be
relocated to `has_object_permission`, but the cost (split gating
surface, less locally-readable 403 messages) is higher than the benefit;
the current inline form is consistent with how
[bookings/views.py / rooms/views.py / housekeeping/views.py / maintenance/views.py](.)
already handle the same "ownership-or-manager-override" pattern (verified
by spot-check of those modules' `has_capability` usage during the
preceding refactor).

**Verdict: leave all six inline checks in place.**

---

## 5. Risk summary — can current admins manage attendance?

| Persona | Outcome under current code |
|---|---|
| Staff with `access_level='super_staff_admin'` AND `role.slug='hotel_manager'` | ✅ Full attendance management. |
| Staff with `access_level='super_staff_admin'` AND `role.slug` ≠ `hotel_manager` | ❌ No attendance management. (Same as no booking/room/maintenance management — established convention.) |
| Staff with `access_level='super_staff_admin'` AND `role IS NULL` | ❌ No attendance management. |
| Newly provisioned primary admin with no `role_id` passed | ❌ No attendance management until a role is assigned. |
| Django superuser | ✅ All canonical capabilities (`is_superuser` short-circuit in `resolve_capabilities`). |

The two ❌ rows are the **same population** that lost booking/room/etc.
management at their respective Phase 6 cuts. No new risk surface is
introduced by this attendance refactor.

---

## 6. Implementation plan if changes are needed

Per the audit: **no code changes are required for the attendance
refactor itself.**

If the project decides to backstop the provisioning gap (out of scope
for this audit but recommended), the minimal code change is:

```python
# hotel/provisioning.py, inside provision_hotel(), after Hotel.objects.create(...)
if role is None:
    role = Role.objects.filter(hotel=hotel, slug='hotel_manager').first()
```

That single edit ensures every newly provisioned primary admin holds
`hotel_manager` and therefore inherits `_ATTENDANCE_MANAGE` (and the
other manager bundles for bookings/rooms/etc.). It does **not** affect
the attendance module's RBAC surface.

---

## 7. Validation commands

The same three commands used by the original refactor remain the canonical
checks. Re-run from the project root with the venv Python:

```powershell
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py shell -c "from staff.module_policy import validate_module_policy; print(validate_module_policy())"
venv\Scripts\python.exe manage.py shell -c "from staff.capability_catalog import validate_preset_maps; print(validate_preset_maps())"
```

Expected outputs (unchanged from the prior pass):

```
System check identified no issues (0 silenced).
[]
[]
```

Additional spot checks (read-only) to confirm assignment status of
real-world staff before/after deploying any change to provisioning:

```powershell
venv\Scripts\python.exe manage.py shell -c "
from staff.models import Staff
qs = Staff.objects.filter(is_active=True, access_level='super_staff_admin')
print('total super_staff_admin:', qs.count())
print('without hotel_manager role:', qs.exclude(role__slug='hotel_manager').count())
"
```

```powershell
venv\Scripts\python.exe manage.py shell -c "
from staff.capability_catalog import resolve_capabilities, ATTENDANCE_PERIOD_FINALIZE
caps = resolve_capabilities('super_staff_admin', None, None)
print('has period.finalize without role:', ATTENDANCE_PERIOD_FINALIZE in caps)
caps2 = resolve_capabilities('super_staff_admin', 'hotel_manager', 'management')
print('has period.finalize with hotel_manager:', ATTENDANCE_PERIOD_FINALIZE in caps2)
"
```

Expected:

```
has period.finalize without role: False
has period.finalize with hotel_manager: True
```

These two booleans together are the code-derived proof of the audit's
core claim: tier alone does not grant attendance management;
`hotel_manager` role does.
