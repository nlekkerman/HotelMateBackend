# Phase 6E.1 — Staff Management RBAC Implementation Report

**Audit source**: [PHASE_6E_STAFF_MANAGEMENT_RBAC_AUDIT.md](PHASE_6E_STAFF_MANAGEMENT_RBAC_AUDIT.md)
**Audit verdict (pre-work)**: NO-GO.
**Implementation verdict (this report)**: **GO**.
**Scope**: Backend only. No frontend changes were made.

---

## 1. Summary

Phase 6E.1 closes every gap identified by the audit. Staff Management
is now a fully capability-gated module:

- 22 canonical `staff_management.*` capabilities added, organised into
  three role-preset bundles (BASIC, FULL, MANAGER) — no other bundle,
  tier, or department leaks these capabilities.
- `staff_management` module registered in `MODULE_POLICY` with 20
  non-decorative action keys. Every action key maps to a canonical
  capability that is actually enforced in a view.
- Two canonical role slugs added: `staff_admin` (BASIC) and
  `super_staff_admin` (FULL). These role slugs are operationally
  disjoint from the `access_level` tier values of the same name — the
  tier values grant **zero** staff-management authority.
- `StaffSerializer` authority fields (`hotel`, `access_level`, `role`,
  `department`, `is_active`, `has_registered_face`, `allowed_navs`) are
  read-only on every generic PUT/PATCH. Authority changes must go
  through capability-gated `@action` endpoints.
- Six anti-escalation rules are enforced in every authority mutation
  path: not-self, same-hotel, strict-less-than access level, nav
  subset, role/department capability ceiling, hotel-scoped lookup.
- User enumeration is hotel-scoped.
- Superuser without `staff_profile` no longer 500s the registration
  package endpoint.
- 44 new tests in `hotel/tests/test_rbac_staff_management.py` plus the
  full RBAC regression suite (229 tests) pass under
  `--keepdb --verbosity=1`.

---

## 2. Files Changed

| File | Change |
|------|--------|
| [staff/capability_catalog.py](staff/capability_catalog.py) | 22 new `staff_management.*` constants; 3 bundles (`_STAFF_MANAGEMENT_BASIC`, `_FULL`, `_MANAGER`); `ROLE_PRESET_CAPABILITIES` extended for `staff_admin`, `super_staff_admin`, `operations_admin`, `hotel_manager`. `TIER_DEFAULT_CAPABILITIES` unchanged (tier leakage = 0). |
| [staff/role_catalog.py](staff/role_catalog.py) | Two new canonical roles added: `staff_admin` and `super_staff_admin` (department_slug `administration`). |
| [staff/module_policy.py](staff/module_policy.py) | New `staff_management` entry with `view_capability`, `read_capability`, and 20 action keys. |
| [staff/permissions.py](staff/permissions.py) | 20 new `HasCapability` subclasses (read gates use `safe_methods_bypass = False`). 5 anti-escalation helpers: `assert_not_self_authority`, `assert_same_hotel`, `assert_access_level_allowed`, `assert_nav_subset`, `assert_role_department_ceiling`. Supervise capability bypasses rules 4/5/6. Superusers bypass all rules. |
| [staff/serializers.py](staff/serializers.py) | `StaffSerializer` authority fields all read-only; `RegisterStaffSerializer` drops `hotel` from body in favour of `context['hotel']`. Six split write serializers added: profile, role, department, access level, navigation, deactivate. |
| [staff/views.py](staff/views.py) | Every endpoint rewired to capability gates with per-action permission map. `StaffViewSet` gains 6 new `@action`s for authority (`authority`, `assign_role`, `assign_department`, `assign_access_level`, `assign_navigation`, `deactivate`). Generic `update`/`partial_update` uses `StaffProfileUpdateSerializer` so authority can never be mutated by PATCH. `UserListAPIView` hotel-scoped. Superuser-no-profile regression fixed. |
| [hotel/tests/test_rbac_staff_management.py](hotel/tests/test_rbac_staff_management.py) | New — 44 tests. |

**No frontend files were modified.**

---

## 3. Capability Catalog Changes

`CANONICAL_CAPABILITIES` grew from 59 to **81** items. The 22 new
capabilities follow the audit's §7 proposal verbatim:

Module / staff / pending / authority / role / department /
registration-package namespaces:

```
staff_management.module.view
staff_management.user.read
staff_management.staff.read
staff_management.staff.create
staff_management.staff.update_profile
staff_management.staff.deactivate
staff_management.staff.delete
staff_management.pending_registration.read
staff_management.authority.view
staff_management.authority.role.assign
staff_management.authority.department.assign
staff_management.authority.access_level.assign
staff_management.authority.nav.assign
staff_management.authority.supervise
staff_management.role.read
staff_management.role.manage
staff_management.department.read
staff_management.department.manage
staff_management.registration_package.read
staff_management.registration_package.create
staff_management.registration_package.email
staff_management.registration_package.print
```

### Bundles (in `staff/capability_catalog.py`)

- **`_STAFF_MANAGEMENT_BASIC`** — `module.view`, `staff.read`,
  `pending_registration.read`, `staff.create`, `staff.update_profile`,
  `staff.deactivate`, `role.read`, `department.read`, all
  `registration_package.*`. **No `authority.*`, no `staff.delete`.**
- **`_STAFF_MANAGEMENT_FULL`** — `_BASIC` +
  `user.read`, `authority.view`, `authority.role.assign`,
  `authority.department.assign`, `authority.access_level.assign`,
  `authority.nav.assign`, `role.manage`, `department.manage`,
  `staff.delete`. **No `authority.supervise`.**
- **`_STAFF_MANAGEMENT_MANAGER`** — `_FULL` + `authority.supervise`.

### Preset assignment

| Role slug | Bundle |
|-----------|--------|
| `staff_admin` (role) | `_STAFF_MANAGEMENT_BASIC` |
| `super_staff_admin` (role) | `_STAFF_MANAGEMENT_FULL` |
| `operations_admin` | `_STAFF_MANAGEMENT_MANAGER` |
| `hotel_manager` | `_STAFF_MANAGEMENT_MANAGER` |

Tiers get nothing: the test
`test_no_staff_management_capability_in_any_tier_preset` verifies
`TIER_DEFAULT_CAPABILITIES` intersected with the
`staff_management.*` set is empty for every tier including
`super_staff_admin`.

---

## 4. Module Policy

`staff/module_policy.py::MODULE_POLICY['staff_management']`:

- `view_capability` — `staff_management.module.view`
- `read_capability` — `staff_management.staff.read`
- `actions` — 20 keys, each pointing at a **canonical capability that
  is enforced in a view** (no decorative keys). The test
  `test_no_decorative_action_keys` verifies this and
  `validate_module_policy()` returns `[]`.

The frontend-facing `rbac.staff_management` dict now carries
`{visible, read, actions{...20 booleans}}` derived entirely from
resolved capabilities.

---

## 5. Permissions

All 20 new capability classes are appended to
[staff/permissions.py](staff/permissions.py). Read-gate classes
(`CanReadStaff`, `CanReadStaffUsers`,
`CanReadPendingRegistrations`, `CanReadStaffRoles`,
`CanReadStaffDepartments`, `CanReadRegistrationPackages`,
`CanViewStaffAuthority`) set `safe_methods_bypass = False` so even
`GET` is denied when the capability is missing.

### Anti-escalation helpers

| Helper | Rule |
|--------|------|
| `assert_not_self_authority(requester, target)` | Rule 1 — cannot mutate your own authority fields. Superusers bypass. |
| `assert_same_hotel(requester, target)` | Rule 2 — target must be in requester's hotel. Superusers bypass. |
| `assert_access_level_allowed(requester, caps, r_level, t_level)` | Rule 4 — target access level must be **strictly below** requester's. `authority.supervise` bypasses. |
| `assert_nav_subset(requester, caps, r_navs, requested_navs)` | Rule 5 — requested nav slugs must be a subset of requester's own navs. `authority.supervise` bypasses. |
| `assert_role_department_ceiling(requester, caps, role_slug, dept_slug)` | Rule 6 — the target role/department preset caps must not exceed requester's capability set. `authority.supervise` bypasses. |

Every helper returns `None` on pass, or a short `str` error on fail.
The view layer raises `HTTP_403_FORBIDDEN` with the error string.

---

## 6. Serializer Hardening

`StaffSerializer` is now **display-only** for authority fields:

```python
read_only_fields = (
    'hotel', 'access_level', 'role', 'department',
    'is_active', 'has_registered_face', 'allowed_navs',
)
```

Generic `PUT/PATCH /api/staff/<hotel_slug>/<pk>/` uses the new
`StaffProfileUpdateSerializer` which only exposes
`first_name`, `last_name`, `email`, `phone`, `profile_image`,
`duty_status`, `is_on_duty`. Any attempt to change authority through
PATCH is either silently dropped (DRF default) or rejected by the
serializer; the targeted `@action`s are the **only** way to change
authority.

`RegisterStaffSerializer` no longer accepts `hotel` in the body — it
pulls it from `self.context['hotel']`. It validates the consumed
`RegistrationCode.hotel_slug` matches. This closes the
cross-hotel identity assignment risk flagged by the audit.

Six write serializers added:

- `StaffProfileUpdateSerializer`
- `StaffAuthorityRoleSerializer`
- `StaffAuthorityDepartmentSerializer`
- `StaffAuthorityAccessLevelSerializer`
- `StaffAuthorityNavigationSerializer` (`slugs` list)
- `StaffDeactivateSerializer`

---

## 7. View Rewiring

### `StaffViewSet`

Per-action permission map (in addition to
`[IsAuthenticated, CanViewStaffManagementModule, IsStaffMember, IsSameHotel]`):

| Action | Capability class |
|--------|------------------|
| `list`, `retrieve` (default) | `CanReadStaff` |
| `create` | `CanCreateStaff` + `assert_access_level_allowed` + `assert_role_department_ceiling` (+ rollback on ceiling violation) |
| `update`, `partial_update` | `CanUpdateStaffProfile` (serializer swap; authority fields inaccessible) |
| `destroy` | `CanDeleteStaff` + `assert_not_self_authority` + `assert_same_hotel` |
| `deactivate` (`POST`) | `CanDeactivateStaff` + `assert_not_self_authority` + `assert_same_hotel` |
| `authority` (`GET`) | `CanViewStaffAuthority` |
| `assign_role` (`PATCH`) | `CanAssignStaffRole` + full authority guard stack |
| `assign_department` (`PATCH`) | `CanAssignStaffDepartment` + full authority guard stack |
| `assign_access_level` (`PATCH`) | `CanAssignStaffAccessLevel` + `assert_access_level_allowed` |
| `assign_navigation` (`PATCH`) | `CanAssignStaffNavigation` + `assert_nav_subset` |

The helper `_apply_authority_guards` centralises the
not-self → same-hotel → field-specific guard sequence.

### Non-viewset endpoints

| Endpoint | Gate |
|----------|------|
| `StaffMetadataView` | `CanViewStaffManagementModule` |
| `UserListAPIView` | `CanReadStaffUsers` + hotel-scoped queryset via `profile__registration_code__hotel_slug` |
| `UsersByHotelRegistrationCodeAPIView` | `CanReadStaffUsers` |
| `PendingRegistrationsAPIView` | `CanReadPendingRegistrations` |
| `CreateStaffFromUserAPIView` | `CanCreateStaff` + anti-escalation |
| `GenerateRegistrationPackageAPIView` | `CanReadRegistrationPackages` (GET) / `CanCreateRegistrationPackages` (POST); superuser-no-profile safe |
| `EmailRegistrationPackageAPIView` | `CanEmailRegistrationPackages` |
| `PrintRegistrationPackageAPIView` | `CanPrintRegistrationPackages` |
| `DepartmentViewSet` | read: `CanReadStaffDepartments`; write: `CanManageStaffDepartments` |
| `RoleViewSet` | read: `CanReadStaffRoles`; write: `CanManageStaffRoles` |
| `StaffNavigationPermissionsView` | GET → `CanViewStaffAuthority`; PATCH → `CanAssignStaffAccessLevel` + `CanAssignStaffNavigation` + full authority guards |

---

## 8. Regressions Fixed

- **Superuser without `staff_profile` 500 on registration-package
  GET/POST** — `GenerateRegistrationPackageAPIView` now uses
  `getattr(user, 'staff_profile', None)` and catches
  `(Staff.DoesNotExist, AttributeError)`. Covered by
  `test_superuser_registration_package_without_staff_profile`.

- **Guard key drift** — `_apply_authority_guards` was reading
  `requester_effective.get('capabilities', ...)` but
  `resolve_effective_access` returns the capability list under
  `allowed_capabilities`. All four occurrences in `staff/views.py`
  were corrected. Covered by
  `test_assign_access_level_strict_less_than` and
  `test_assign_role_allowed_for_role_ssa`.

---

## 9. Tests

### New file: `hotel/tests/test_rbac_staff_management.py`

Four test classes, 44 tests total:

1. **`StaffManagementPolicyRegistryTest`** (5 tests)
   - `validate_preset_maps() == []`
   - `validate_module_policy() == []`
   - `staff_management` module is registered with correct
     `view_capability` / `read_capability`
   - Every action key maps to a canonical capability
   - **No `staff_management.*` capability in any tier preset**

2. **`StaffManagementPolicyPersonaTest`** (7 tests)
   - `regular_staff` → invisible
   - Tier-only `staff_admin` → invisible, zero actions
   - Tier-only `super_staff_admin` → invisible, zero actions
   - Role `staff_admin` → BASIC (create / update_profile /
     registration_package.create) but **not** delete / authority /
     supervise
   - Role `super_staff_admin` → FULL (authority.* + delete) but
     **not** supervise
   - Role `hotel_manager` → MANAGER (supervise + delete)
   - Role `operations_admin` → MANAGER (supervise)

3. **`StaffManagementEndpointEnforcementTest`** (29 tests)
   - Staff list read/write split
   - Generic PATCH cannot mutate `hotel`, `access_level`, `role`,
     `department`
   - Authority view read gate
   - `assign_role` denied without capability (role_sa), allowed with
     capability + ceiling-clean target (role_ssa)
   - `assign_access_level` strict-less-than enforced
     (role_ssa cannot assign equal; `hotel_manager` can via supervise)
   - Cannot assign authority to self
   - `assign_navigation` nav-subset enforced; supervise bypasses
   - Delete denied / allowed by capability; cannot delete self
   - `deactivate` rejects self; denied without capability
     (tier-only persona)
   - Department / role read vs manage split
   - Registration package read/create/tier-only-denied
   - **Superuser-without-staff-profile safety**
   - Pending registrations gate
   - User list hotel-scoped (no cross-hotel leak)
   - Create-staff escalation denied / lower-level allowed

4. **`AntiEscalationHelpersTest`** (3 tests) — unit-level for
   `assert_access_level_allowed`, `assert_nav_subset`,
   `assert_role_department_ceiling`.

### Regression Matrix

Command run:

```powershell
$env:PYTHONIOENCODING='UTF-8'
python manage.py test `
    hotel.tests.test_rbac_staff_management `
    hotel.tests.test_rbac_maintenance `
    hotel.tests.test_rbac_housekeeping `
    hotel.tests.test_rbac_rooms `
    hotel.tests.test_rbac_bookings `
    --keepdb --verbosity=1
```

Result:

```
Ran 229 tests in 93.465s

OK
```

**Zero failures, zero errors.** All prior RBAC phase regressions
(6A bookings, 6B rooms, 6C housekeeping, 6D maintenance) continue to
pass alongside the new 6E staff_management suite.

### System Check

```
python manage.py check
System check identified no issues (0 silenced).
```

---

## 10. Contract Compliance

| Rule | Status |
|------|--------|
| Capabilities are the only source of authority | ✅ Every mutation gated on a `HasCapability` subclass — no `IsSuperStaffAdminOrAbove`, no `CanManageStaff`, no role-string authorization remains in the Staff Management path. |
| No tier-based staff-management authority | ✅ `TIER_DEFAULT_CAPABILITIES` carries zero `staff_management.*` capabilities; asserted by `test_no_staff_management_capability_in_any_tier_preset`. |
| No nav-based mutation authority | ✅ `CanViewStaffManagementModule` (nav) gates visibility only; mutation requires an action capability. |
| No role-string authorization | ✅ `permissions.py` reads from resolved capabilities only. |
| Mandatory hotel scoping | ✅ `IsSameHotel` on ViewSet, `assert_same_hotel` on authority @actions, `UserListAPIView` hotel-filtered, `RegisterStaffSerializer` pulls hotel from context. |
| No self-mutation of authority fields | ✅ `assert_not_self_authority` guards every authority action, delete, and deactivate. |
| No cross-hotel identity/authority assignment | ✅ `RegisterStaffSerializer` rejects body `hotel`; `create` assigns `hotel` from URL kwarg; `assign_role`/`assign_department` reject cross-hotel targets via `IsSameHotel`. |
| No decorative capabilities | ✅ `test_no_decorative_action_keys`. |
| Tests required before GO | ✅ 44 new + 185 existing = 229 regression tests, all pass. |
| Frontend unchanged | ✅ No files under `src/` / `hotelmate/` were touched. |

---

## 11. Known Non-Goals

Out of scope for Phase 6E.1 (explicitly per the audit):

- **`authority.supervise` activation**: The capability is minted and
  wired into the bypass paths. No production role is granted it yet
  beyond `operations_admin` / `hotel_manager`. No change.
- **Face data management**: Owned by the Attendance module.
- **`/me` self-profile endpoint**: Read-only surface, already
  capability-agnostic (returns the caller's effective-access payload).

---

## 12. Risk Assessment

- **Deployment risk — LOW.** Additive capability catalog entries;
  existing preset maps for tiers are unchanged. New authority
  endpoints are behind capabilities that no existing user has unless
  they already hold one of the four relevant roles
  (`staff_admin`, `super_staff_admin`, `operations_admin`,
  `hotel_manager`).
- **Migration risk — NONE.** No model/schema changes in this phase.
- **Frontend regression — NONE.** No frontend contract change; the
  `rbac.staff_management` dict is additive to
  `resolve_module_policy()` output.
- **Data risk — NONE.** No data mutations introduced by this phase.

---

## 13. Post-Deploy Checklist

1. After deploy, seed the two new canonical roles
   (`staff_admin`, `super_staff_admin`) for existing hotels via the
   standard `seed_canonical_roles` management command (no code change
   required here — the catalog update is all that's needed for the
   seeder to pick them up on next run).
2. Verify `/api/staff/hotel/<slug>/me/` returns the new
   `rbac.staff_management` dict for a staff member with one of the
   new roles.
3. Smoke test: log in as a `super_staff_admin` role holder and
   confirm the `PATCH /assign-role/`, `/assign-department/`,
   `/assign-access-level/`, `/assign-navigation/` endpoints all
   return `200` for same-hotel targets with ceiling-clean roles.

---

## 14. Verdict

**GO.**

All contract rules are enforced and asserted by automated tests.
The full RBAC regression suite (bookings / rooms / housekeeping /
maintenance / staff_management) passes at 229/229 with the new
implementation. Django system check is clean. Frontend is untouched.

Implementation is ready for merge and deploy.
