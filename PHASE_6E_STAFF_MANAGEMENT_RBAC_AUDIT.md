# Phase 6E — Staff Management RBAC Deep Audit

**Scope**: Read-only audit of the Staff Management module.
**Source of truth**: Actual code under `staff/`, `hotel/`, `staff_urls.py`
only. Docstrings, comments, and docs were cross-checked against code and
flagged when they drift.
**No code was modified. No tests were run.**

---

## 1. Module Footprint

### 1.1 Files participating in Staff Management

Authoritative code surface:

- [staff/urls.py](staff/urls.py) — routes
- [staff/views.py](staff/views.py) — all ViewSets and APIViews
- [staff/me_views.py](staff/me_views.py) — self-profile `/me`
- [staff/serializers.py](staff/serializers.py) — write shapes
- [staff/models.py](staff/models.py) — `Staff`, `Department`, `Role`,
  `NavigationItem`, `RegistrationCode`, `UserProfile`
- [staff/permissions.py](staff/permissions.py) — `HasNavPermission`,
  `CanManageStaff`, `IsSuperStaffAdminOrAbove`, `IsDjangoSuperUser`,
  tier resolver
- [staff/capability_catalog.py](staff/capability_catalog.py) — no
  `staff_management.*` capabilities exist yet (see §7)
- [staff/module_policy.py](staff/module_policy.py) — no
  `staff_management` module key registered
- [staff/role_catalog.py](staff/role_catalog.py) — canonical role slugs
- [staff/nav_catalog.py](staff/nav_catalog.py) — `staff_management` nav
  slug is canonical
- [staff/signals.py](staff/signals.py) — creates auth `Token` on every
  `User` create (side effect relevant to registration flow)
- [staff_urls.py](staff_urls.py) — mounts `/api/staff/hotel/<slug>/me/`
  via `StaffMeView`
- [hotel/staff_views.py](hotel/staff_views.py) — **NOT part of staff
  management**; it handles hotel-content CRUD (rooms, sections, etc.).
  No `Staff` / `Role` / `Department` / `RegistrationCode` mutation lives
  there. Listed here only to record that it was inspected and ruled out.

### 1.2 Files ruled out

- `attendance/face_views.py` — face-data management is under the
  Attendance module, not Staff Management. `has_registered_face` is a
  read-only boolean on `Staff`. No staff-management endpoint mutates
  face data. (Excluded from §7 proposal.)

### 1.3 Functional grouping of routes (mounted under `/api/staff/`)

| Group | Endpoints |
|-------|-----------|
| Auth | `POST login/`, `POST register/`, `POST password-reset/`, `POST password-reset-confirm/` |
| Registration packages | `GET\|POST registration-package/`, `POST registration-package/<pk>/email/`, `GET registration-package/<pk>/print/` |
| Staff directory (global) | `GET users/`, `GET users/by-hotel-codes/` |
| Staff directory (hotel) | `StaffViewSet` on `<hotel_slug>/` + `/me/`, `/by_department/`, `/by_hotel/`, `/attendance-summary/` |
| Staff creation (hotel) | `POST <hotel_slug>/create-staff/`, `POST <hotel_slug>/` (`StaffViewSet.create`) |
| Staff update / delete | `PUT\|PATCH\|DELETE <hotel_slug>/<pk>/` (`StaffViewSet`) |
| Pending registrations | `GET <hotel_slug>/pending-registrations/` |
| Department CUD | `DepartmentViewSet` (hotel-scoped + global) |
| Role CUD | `RoleViewSet` (hotel-scoped + global) |
| Navigation item CUD | `NavigationItemViewSet` (platform-global) |
| Nav + access-level assignment | `GET\|PATCH <staff_id>/permissions/` (`StaffNavigationPermissionsView`) |
| Metadata (dropdowns) | `GET <hotel_slug>/metadata/` |
| Self | `GET <hotel_slug>/me/` (`StaffMeView`), `StaffViewSet.me` action |
| FCM token | `POST save-fcm-token/` |

### 1.4 Capability override surface

None exists. There is no DB field for per-staff capability overrides;
capabilities are resolved at request time from
`tier ∪ role_preset ∪ department_preset` in
`staff/capability_catalog.py::resolve_capabilities`. Any
capability-override authority therefore must be designed from scratch
before it can be gated.

---

## 2. Endpoint Inventory

Columns:
**Mut. authority** = endpoint can change `access_level` / `role` /
`department` / `allowed_navigation_items` / `hotel` / `is_active` / a
user-creation side effect.

| # | URL | Method | View / action | Serializer | Service / helper | Permission classes | Inline checks | Mut. authority |
|---|-----|--------|---------------|------------|------------------|--------------------|---------------|----------------|
| 1 | `login/` | POST | `CustomAuthToken` | `StaffLoginInput/Output` | `resolve_effective_access` | `AllowAny` | password check | no (reads only) |
| 2 | `register/` | POST | `StaffRegisterAPIView` | — | `RegistrationCode`, `UserProfile` | `AllowAny` | validates code + `qr_token`; blocks reused code; creates `User` + `UserProfile` | **YES — creates `User`, consumes token, marks code used** |
| 3 | `registration-package/` | POST | `GenerateRegistrationPackageAPIView.post` | `RegistrationCodeSerializer` | `RegistrationCode.create_package` | `IsAuthenticated, HasStaffManagementNav` | inline: `staff.hotel.slug == hotel_slug`; `access_level in {staff_admin, super_staff_admin}` | **YES — mints registration tokens** |
| 4 | `registration-package/` | GET | `GenerateRegistrationPackageAPIView.get` | `RegistrationCodeSerializer` | — | `IsAuthenticated, HasStaffManagementNav` | superuser bypass, else `access_level in {staff_admin, super_staff_admin}` | no |
| 5 | `registration-package/<pk>/email/` | POST | `EmailRegistrationPackageAPIView` | `EmailRegistrationPackageSerializer` | `ensure_package_qr_ready`, `send_mail` | `IsAuthenticated, HasStaffManagementNav` | `_resolve_package` enforces same-hotel + `access_level in {staff_admin, super_staff_admin}`; blocks used packages | **YES — externalises token to arbitrary recipient** |
| 6 | `registration-package/<pk>/print/` | GET | `PrintRegistrationPackageAPIView` | — | `ensure_package_qr_ready`, `serialize_package` | `IsAuthenticated, HasStaffManagementNav` | same as above; **allowed even for used packages** | borderline (leaks token — see §6) |
| 7 | `save-fcm-token/` | POST | `SaveFCMTokenView` | — | — | `IsAuthenticated` | self-lookup `Staff.objects.get(user=request.user)` | no (self field only) |
| 8 | `password-reset/` | POST | `PasswordResetRequestView` | — | `send_mail` | `AllowAny` | — | no |
| 9 | `password-reset-confirm/` | POST | `PasswordResetConfirmView` | — | `default_token_generator` | `AllowAny` | token check | changes password only |
| 10 | `users/` | GET | `UserListAPIView` | `UserSerializer` | — | `IsAuthenticated, HasStaffManagementNav` | — | no, but **cross-hotel: returns `User.objects.all()`** |
| 11 | `users/by-hotel-codes/` | GET | `UsersByHotelRegistrationCodeAPIView` | `UserSerializer` | — | `IsAuthenticated, HasStaffManagementNav` | scoped by requester's `staff.hotel` | no |
| 12 | `departments/` | GET/POST/PATCH/DELETE (global + hotel) | `DepartmentViewSet` | `DepartmentSerializer` | — | List/Retr.: `IsAuthenticated, HasNavPermission('staff_management')`; CUD: `+ CanManageStaff` | `check_write_permission` requires `staff_admin+` same hotel | **YES — department CUD** |
| 13 | `roles/` | GET/POST/PATCH/DELETE (global + hotel) | `RoleViewSet` | `RoleSerializer` | — | List/Retr.: same; CUD: `+ CanManageStaff` | `check_write_permission` requires `staff_admin+` same hotel | **YES — role CUD (+ Role.default_navigation_items authority)** |
| 14 | `navigation-items/` | GET | `NavigationItemViewSet` | `NavigationItemSerializer` | — | `IsAuthenticated` | — | no (read) |
| 15 | `navigation-items/` | POST/PATCH/DELETE | `NavigationItemViewSet` | `NavigationItemSerializer` | — | `IsAuthenticated, IsDjangoSuperUser` | — | platform-level only |
| 16 | `<staff_id>/permissions/` | GET | `StaffNavigationPermissionsView` | — | `resolve_effective_access` | `IsAuthenticated, HasStaffManagementNav, IsSuperStaffAdminOrAbove` | same-hotel scoping inside `_check_authorization` | no |
| 17 | `<staff_id>/permissions/` | PATCH | `StaffNavigationPermissionsView` | — | nav-set replacement + `trigger_navigation_permission_update` | same | validates slugs scoped to target hotel; self-lockout check for nav ONLY | **YES — sets `access_level` and `allowed_navigation_items`** |
| 18 | `<hotel_slug>/metadata/` | GET | `StaffMetadataView` | — | — | `IsAuthenticated, HasStaffManagementNav` | — | no |
| 19 | `<hotel_slug>/pending-registrations/` | GET | `PendingRegistrationsAPIView` | — | — | `IsAuthenticated, HasStaffManagementNav` | superuser bypass; else requester must be `staff_admin+` of same hotel (via `_tier_at_least`) | no |
| 20 | `<hotel_slug>/create-staff/` | POST | `CreateStaffFromUserAPIView` | — | — | `IsAuthenticated, HasStaffManagementNav` | `ALLOWED_CREATIONS` matrix (tier-based); target-user must have used a reg code for this hotel; sets `is_staff=True`; deletes reg code | **YES — creates `Staff`, assigns `access_level`, `department`, `role`, `is_active`** |
| 21 | `<hotel_slug>/departments/` | CUD | `DepartmentViewSet` (hotel router) | `DepartmentSerializer` | — | as #12 | as #12 | **YES** |
| 22 | `<hotel_slug>/roles/` | CUD | `RoleViewSet` (hotel router) | `RoleSerializer` | — | as #13 | as #13 | **YES** |
| 23 | `<hotel_slug>/` | GET (list) | `StaffViewSet.list` | `StaffSerializer` | — | `IsAuthenticated, HasNavPermission('staff_management'), IsStaffMember, IsSameHotel` | hotel-slug filter on queryset | no |
| 24 | `<hotel_slug>/<pk>/` | GET | `StaffViewSet.retrieve` | `StaffSerializer` | — | same | hotel-slug filter | no |
| 25 | `<hotel_slug>/` | POST | `StaffViewSet.create` | `RegisterStaffSerializer` | — | `+ CanManageStaff` | requester must be staff of same hotel; `access_level=='super_staff_admin'` requires `super_staff_admin` tier; forces `is_superuser=False` | **YES — creates `Staff` with arbitrary `access_level`, `department`, `role`, `is_active`** |
| 26 | `<hotel_slug>/<pk>/` | PUT/PATCH | `StaffViewSet.update` / `.partial_update` | `StaffSerializer` | — | `+ CanManageStaff` | **inline: `instance.user != request.user` → 403**; i.e. self-only edits | **YES — writable fields include `access_level`, `department`, `role`, `hotel`, `is_active`** (see §5) |
| 27 | `<hotel_slug>/<pk>/` | DELETE | `StaffViewSet.destroy` | — | `trigger_staff_profile_update` | `+ CanManageStaff` | — | **YES — hard-deletes staff row (no deactivate endpoint)** |
| 28 | `<hotel_slug>/me/` (action) | GET | `StaffViewSet.me` | `StaffSerializer` | — | base | self lookup | no |
| 29 | `<hotel_slug>/me/` (route) | GET | `StaffMeView` | `StaffSerializer + resolve_effective_access` | — | `IsAuthenticated` | self lookup | no |
| 30 | `<hotel_slug>/by_department/` | GET | action | `StaffSerializer` | — | base | dept scoped by hotel | no |
| 31 | `<hotel_slug>/by_hotel/` | GET | action | `StaffSerializer` | — | base | — | no |
| 32 | `<hotel_slug>/attendance-summary/` | GET | action | `StaffAttendanceSummarySerializer` | `optimize_attendance_queryset` | base | — | no |

Total mutating-authority endpoints: **#2, #3, #5, #6, #12, #13, #17, #20, #21, #22, #25, #26, #27**. Every one is analysed in §4–§5.

---

## 3. Real Action Map

Every action below was confirmed from live code. Actions that do not map
to a real endpoint are explicitly marked **NOT PRESENT**.

| Action | Endpoint | Code path | Serializer fields involved | Mutation | Side effects | Tenant scoping | Current gate |
|--------|----------|-----------|----------------------------|----------|--------------|----------------|--------------|
| List staff | `GET /<hotel_slug>/` | `StaffViewSet.list` + `get_queryset` | `StaffSerializer` (read) | none | — | queryset filtered by `hotel__slug` | nav `staff_management` |
| Retrieve staff | `GET /<hotel_slug>/<pk>/` | `StaffViewSet.retrieve` | read | none | — | same | nav `staff_management` |
| Get self | `GET /<hotel_slug>/me/` | `StaffMeView` / `StaffViewSet.me` | read | none | — | self + hotel | `IsAuthenticated` |
| Login | `POST /login/` | `CustomAuthToken.post` | read payload | issues Token | logging, pusher none | — | `AllowAny` |
| Staff self-register (consume token) | `POST /register/` | `StaffRegisterAPIView.post` | — | creates `User`, `UserProfile`; marks `RegistrationCode.used_by` | `Token` auto-created; pusher `pending` event | hotel resolved from code | `AllowAny` |
| Approve registration → create Staff | `POST /<hotel_slug>/create-staff/` | `CreateStaffFromUserAPIView.post` | `access_level`, `department_id`, `role_id`, `first_name`, `last_name`, `email`, `is_active` | creates `Staff`, deletes `RegistrationCode`, sets `user.is_staff=True` | pusher `created`, `approved` | hotel required via URL; target user must have used a code for this hotel | nav + `ALLOWED_CREATIONS` matrix |
| Direct staff create (bypasses pending-registration flow) | `POST /<hotel_slug>/` | `StaffViewSet.create` | `RegisterStaffSerializer`: `user_id`, `access_level`, `department`, `role`, `hotel`, `is_active`, etc. | creates `Staff`; forces `is_staff=True`, `is_superuser=False` | pusher | hotel forced from URL; **department/role pk queryset is unscoped — relies on `Staff.clean()` cross-tenant guard** | nav + `CanManageStaff` (super_staff_admin+) |
| Update staff profile (self-only under current code) | `PUT\|PATCH /<hotel_slug>/<pk>/` | `StaffViewSet.update/partial_update` | `StaffSerializer` writable: `access_level`, `department`, `role`, `hotel`, `is_active`, `first_name`, `last_name`, `email`, `phone_number`, `duty_status`, `is_on_duty`, `profile_image`, `has_registered_face` | arbitrary field mutation | pusher | inline `instance.user == request.user`; queryset filtered by hotel | nav + `CanManageStaff` + inline self-only guard |
| Hard-delete staff | `DELETE /<hotel_slug>/<pk>/` | `StaffViewSet.destroy` | — | `Staff` row deleted | pusher | hotel queryset | nav + `CanManageStaff` |
| Deactivate staff | **NOT PRESENT** as a distinct endpoint. `is_active` is writable in `StaffSerializer` and exposed on `CreateStaffFromUserAPIView`. No soft-delete verb. |
| Assign role | via `POST /<hotel_slug>/create-staff/` (`role_id`) OR `StaffViewSet.update` (`role`) | — | `role` | writes `Staff.role` | pusher | via `Staff.clean()` cross-tenant guard | nav + `CanManageStaff` OR inline tier matrix |
| Assign department | same as role | — | `department` | writes `Staff.department` | pusher | `Staff.clean()` | same |
| Change access_level | via `POST create-staff/`, `StaffViewSet.update`, OR `PATCH <staff_id>/permissions/` | — | `access_level` | writes `Staff.access_level` | pusher | hotel queryset only for StaffViewSet; permissions view same-hotel scoped | nav + tier matrix; permissions view requires `IsSuperStaffAdminOrAbove` |
| Assign allowed navigation | `PATCH /<staff_id>/permissions/` | `StaffNavigationPermissionsView.patch` | `allowed_navs`, `access_level` | M2M replace + `access_level` set | pusher | nav slugs validated against target-hotel nav items | `IsSuperStaffAdminOrAbove` |
| Grant/revoke capability override | **NOT PRESENT** — no DB surface, no endpoint, no serializer field |
| Generate registration package | `POST /registration-package/` | `GenerateRegistrationPackageAPIView.post` | `hotel_slug`, optional `code`, `count ≤ 50` | creates `RegistrationCode` rows; uploads QR to Cloudinary | — | inline `staff.hotel.slug == hotel_slug` | nav + inline `access_level in {staff_admin, super_staff_admin}` |
| List registration packages | `GET /registration-package/` | `GenerateRegistrationPackageAPIView.get` | — | — | — | superuser passes `hotel_slug`; staff bound to own hotel | nav + tier matrix |
| Mark package used | **implicit only** — set by `/register/` flow when a user consumes the code. No manual endpoint. |
| Revoke / delete package | **NOT PRESENT** — code deletion happens automatically inside `CreateStaffFromUserAPIView` after approval. No revoke/expiry API. |
| Email registration package | `POST /registration-package/<pk>/email/` | `EmailRegistrationPackageAPIView` | `email`, `subject`, `message` | sends email containing code + QR url | Cloudinary QR generation | via `_resolve_package` same-hotel | nav + inline tier |
| Print registration package | `GET /registration-package/<pk>/print/` | `PrintRegistrationPackageAPIView` | — | — | — | same | same |
| Upload / update face data | **NOT PRESENT in staff app** — lives in `attendance.face_views.FaceManagementViewSet` |
| Resend invite | **NOT PRESENT** as a first-class action — effectively overlaps with #5 Email |
| Staff self-update profile (non-authority fields) | NOT a distinct endpoint. Self-update goes through `StaffViewSet.update`, which requires `CanManageStaff` — so ordinary staff cannot edit even their own name/phone/photo. No dedicated `PATCH /me/` mutator. |
| Metadata (dropdowns) | `GET /<hotel_slug>/metadata/` | `StaffMetadataView` | — | — | filter by `hotel__slug` | nav |
| Pending registrations | `GET /<hotel_slug>/pending-registrations/` | `PendingRegistrationsAPIView` | — | — | inline hotel match | nav + tier matrix |
| FCM save | `POST /save-fcm-token/` | — | — | writes `Staff.fcm_token` only | — | self | `IsAuthenticated` |

---

## 4. Current Permission Model

### 4.1 Per-endpoint

| # | Capability gate | Nav gate | Tier gate | Role-string gate | SU shortcut | Object-level | Missing checks |
|---|-----------------|----------|-----------|------------------|-------------|--------------|----------------|
| 1 login | — | — | — | — | — | — | expected |
| 2 register | — | — | — | — | — | code + qr_token match | no throttling; trusts code+token alone |
| 3 reg-pkg create | — | `staff_management` | inline `staff_admin+` | — | superuser bypass via `_resolve_package`? **No** — POST path checks `staff.hotel.slug` only; **Django superusers without a staff_profile get 500** (`request.user.staff_profile` raises) | — | **no capability**; tier-only authority |
| 4 reg-pkg list | — | `staff_management` | inline `staff_admin+` | — | explicit `if user.is_superuser` | — | **no capability** |
| 5 reg-pkg email | — | `staff_management` | inline `staff_admin+` | — | `_resolve_package` superuser bypass | hotel-slug match | **no capability**; unvalidated recipient (only DRF `EmailField`); no rate-limit |
| 6 reg-pkg print | — | `staff_management` | inline `staff_admin+` | — | same | same | **prints even used packages — token re-exposure** |
| 10 users list | — | `staff_management` | — | — | — | **NONE — returns `User.objects.all()`** | **cross-hotel leak** |
| 12 dept CUD | — | `staff_management` | `CanManageStaff` = `super_staff_admin+` (class) **AND** `check_write_permission` = `staff_admin+` (inline) | — | `is_superuser` | inline hotel match | inline check is weaker than class — contradiction, see §12 |
| 13 role CUD | — | `staff_management` | same contradictory pair | — | same | same | same |
| 14/15 nav items | — | — | — | — | `IsDjangoSuperUser` (CUD) | — | OK |
| 16/17 staff permissions | — | `staff_management` | `IsSuperStaffAdminOrAbove` | — | tier resolver returns `super_user` | hotel match inside `_check_authorization` | **no capability**; no self-escalation guard on `access_level`; self-lockout guard covers nav only |
| 19 pending-regs | — | `staff_management` | inline `staff_admin+` | — | `is_superuser` bypass | hotel match | **no capability** |
| 20 create-staff | — | `staff_management` | inline `ALLOWED_CREATIONS` tier matrix | — | `is_superuser` bypass | target user's registration-code hotel scope | **no capability**; matrix uses `staff.access_level` string (role-string-like but is tier-level) |
| 25 StaffViewSet.create | — | `staff_management` | `CanManageStaff` = `super_staff_admin+` | — | superuser via tier resolver | `Staff.clean()` cross-tenant | **no capability**; user_id pick from global User table |
| 26 StaffViewSet.update | — | `staff_management` | `CanManageStaff` | — | same | **inline self-only (`instance.user == request.user`)** | **authority fields writable on self** (access_level/hotel/role/dept/is_active) |
| 27 StaffViewSet.destroy | — | `staff_management` | `CanManageStaff` | — | same | hotel-slug filter only | hard-delete, no capability |
| 17 (PATCH perms) `access_level` write | — | as above | as above | — | as above | — | **no self-downgrade/self-escalate block on access_level**; a super_staff_admin can promote a peer to super_staff_admin without a supervisor capability |

### 4.2 Global flags

- **Tier leaks**: Every mutating endpoint relies on `_tier_at_least(...)`
  (explicit or via `CanManageStaff`). Tier is currently the only
  authority gate for staff mutation. Violates "Tier must not grant
  module action authority".
- **Nav leaks**: No endpoint uses nav as the *sole* gate, but `users/`,
  `users/by-hotel-codes/`, `metadata/` have **nav-only** protection
  (read-only — acceptable) with the exception of `users/` which leaks
  all users across hotels.
- **Role leaks**: None — `role.slug` is not used for authorization in
  staff management (good).
- **Superuser bypasses**: Seven sites:
  `GenerateRegistrationPackageAPIView.get`,
  `_RegistrationPackageDeliveryMixin._resolve_package`,
  `PendingRegistrationsAPIView.get`,
  `CreateStaffFromUserAPIView.post`,
  `StaffNavigationPermissionsView._check_authorization`,
  `resolve_effective_access`, `resolve_tier`. All consistent.
  One *partial* bypass gap: `GenerateRegistrationPackageAPIView.post`
  does **not** implement a superuser shortcut — a Django superuser
  without a `staff_profile` will hit `request.user.staff_profile`
  AttributeError (500) rather than a clean 403.
- **Cross-hotel risks**: `UserListAPIView.get_queryset` returns
  `User.objects.all()` (any authenticated staff w/ nav sees every user
  in the platform). `StaffViewSet.create` accepts `user_id` and
  `department`/`role` PKs from arbitrary hotels (only saved by
  `Staff.clean()` constraint).
- **Self-mutation of authority**:
  - `StaffViewSet.update/partial_update` requires
    `instance.user == request.user` and tier `super_staff_admin+`. A
    super_staff_admin can therefore PATCH their own `access_level`,
    `hotel`, `role`, `department`, `is_active`, etc. with no guard.
  - `StaffNavigationPermissionsView.patch` allows super_staff_admin to
    target self; nav self-lockout guard exists for
    `{staff_management, admin_settings}` but **no guard on
    `access_level`**.
- **Equal/higher authority creation**: `CreateStaffFromUserAPIView`
  allows `super_staff_admin` → `super_staff_admin`
  (`ALLOWED_CREATIONS['super_staff_admin'] = {…, 'super_staff_admin'}`).
  The docstring of the same view says
  *"super_staff_admin: can create regular_staff and staff_admin"* —
  **code drifts from docstring**.

---

## 5. Authority Surface Analysis

| Field / relationship | Writable from API? | Endpoint(s) | Serializer | Current gate | Hotel-scoped? | Self-mutation possible? | Create equal/higher? | Cross-hotel assign? |
|----------------------|--------------------|-------------|------------|--------------|----------------|-------------------------|----------------------|---------------------|
| `Staff.access_level` | **YES** | #25 create; #26 update (self-only); #17 perms PATCH; #20 create-staff | `RegisterStaffSerializer`, `StaffSerializer.access_level`, raw body in `CreateStaffFromUserAPIView` and `StaffNavigationPermissionsView` | tier (`CanManageStaff` / `IsSuperStaffAdminOrAbove` / `ALLOWED_CREATIONS`) | queryset-hotel only for #26; per-target-hotel for others | **YES via #26 and #17** | **YES** — super_staff_admin can create/promote another super_staff_admin | only within requester's hotel for #17/#20; #26 can flip `hotel` FK (see below) |
| `Staff.role` | YES | #25, #26, #20 | `role` PK (unscoped queryset) | tier | only via `Staff.clean()` cross-tenant guard (raises `ValidationError`) | via #26 yes | n/a | blocked by `Staff.clean()` hotel check |
| `Staff.department` | YES | #25, #26, #20 | same | tier | via `Staff.clean()` | yes | n/a | blocked by `Staff.clean()` |
| `Staff.allowed_navigation_items` | YES | #17 only | raw `allowed_navs` list | `IsSuperStaffAdminOrAbove` | nav items queried with `hotel=target_staff.hotel` → safe | yes (self can target self; nav self-lockout guard only for `{staff_management, admin_settings}`) | n/a | no |
| `Staff.hotel` | **YES (dangerous)** | #26 (self-only) | `StaffSerializer.hotel = PrimaryKeyRelatedField(queryset=Hotel.objects.all())` | `CanManageStaff` | **NO scoping on PK** | **YES** — a super_staff_admin could transfer themselves to another hotel | — | **YES — authority transfer across tenants** |
| `Staff.is_active` | YES | #26, #20 | `StaffSerializer.is_active` | `CanManageStaff` | hotel queryset (for #26) | self — yes (super_staff_admin can deactivate self) | — | — |
| `User.is_staff` | YES (forced `True`) | #25, #20 | server-side assign | inside view | — | — | — | — |
| `User.is_superuser` | NO via API (explicitly forced `False` in #25 and #20). Only Django admin / CLI can set it. | — | — | — | — | — | — | — |
| `Role.default_navigation_items` (indirect authority — shapes nav defaults) | YES | `RoleViewSet` CUD (#13/#22) | `RoleSerializer` does **not** expose it directly, but the M2M can be written via Django admin; no API write path. | CanManageStaff + `check_write_permission` | hotel | — | — | — |
| Role / Department rename (slug regen via `slugify(name)`) | YES | #12/#13/#21/#22 | name → slug | same | hotel | — | — | — |
| `RegistrationCode` mint | YES | #3 | raw body | nav + inline tier | hotel from body, checked against requester | — | **effectively yes** (see §6) | **no** — requester hotel must match |
| `RegistrationCode.used_by` | YES (indirectly) | #2 `/register/` | raw body | `AllowAny` | hotel derived from code | — | — | — |
| `RegistrationCode` delete | YES (auto) | #20 | — | tier matrix | — | — | — | — |
| Face data (`has_registered_face`) | field technically in `StaffSerializer.fields`, **not** in `read_only_fields` → writable via #26 | — | should be read-only at API edge | none | — | self yes | — | — |

Summary — the **writable authority surface that Phase 6E must close** is:
1. `Staff.access_level`
2. `Staff.role`
3. `Staff.department`
4. `Staff.allowed_navigation_items`
5. `Staff.hotel`
6. `Staff.is_active`
7. `RegistrationCode` generation, email, print
8. `RegistrationCode` delete (implicit via approval)
9. `Role.default_navigation_items` (indirect)
10. `has_registered_face` accidental writability

---

## 6. Registration / QR / Token Flow Audit

### 6.1 Package creation (#3)

- **Who can create?** Any staff with `access_level in {staff_admin, super_staff_admin}` AND matching `staff.hotel.slug`. Tier-only gate; no capability. Not accessible to Django superuser without staff profile (500-risk).
- **Another hotel?** Blocked — inline `staff.hotel.slug != hotel_slug` → 403.
- **Assigns role / department / access_level?** **No** — the package itself carries no authority. Authority is assigned later in #20 (`create-staff`).
- **Token reuse?** The code itself is single-use (`used_by` unique OneToOne; `/register/` checks `used_by is None`). But the generated QR/code is **not expirable** — there is no `expires_at` on `RegistrationCode` and no revoke endpoint. A printed/emailed package remains valid until consumed.
- **Hotel scope on consumption?** `/register/` resolves the hotel from `reg_code.hotel_slug` only. `CreateStaffFromUserAPIView` later enforces "user must have used a code for this hotel". So a code minted for hotel A cannot be approved for hotel B.

### 6.2 Package email (#5)

- Tier-gated (same hotel, `staff_admin+`). **Recipient is unvalidated** — any email address is accepted. No rate-limit, no allow-list, no audit log row (only a logger INFO). A staff_admin can exfiltrate a usable token to an arbitrary external email.

### 6.3 Package print (#6)

- Returns the **full code + QR URL** — even for **used packages** (the view explicitly documents "print is allowed for audit"). Re-exposing used tokens is acceptable from a reuse standpoint (they can't be re-consumed), but re-exposure of *unused* packages is unlogged.

### 6.4 Self-registration (#2)

- `AllowAny`. Flow:
  1. Validate `registration_code`; must have `used_by is None`.
  2. If `reg_code.qr_token` is set, match the submitted `qr_token`. (Backward-compatible: codes without tokens skip QR check.)
  3. Create `User`; `UserProfile.registration_code = reg_code`; `reg_code.used_by = user`.
  4. Emit pusher `pending` event.
- **Authority of new staff**: **NONE** — `Staff` is not created at this step. The `User` exists but cannot authenticate into any hotel feature because `resolve_effective_access` returns the empty base payload when no `staff_profile` exists. Good.
- **Risks**:
  - Legacy codes without `qr_token` (created pre-Phase-X migration) bypass the QR check.
  - No throttling — token brute-force mitigated only by `token_urlsafe(32)` entropy; acceptable but should be made explicit.
  - `Token.objects.create` runs automatically on `User` post-save (see `staff/signals.py`). A freshly-registered user therefore has an API token **before** staff approval. With no `Staff` record their permission payload is empty — but they can still call any `AllowAny` endpoint including `/register/` repeatedly and any endpoint keyed off authenticated-without-staff assumptions (e.g. `/save-fcm-token/` fails cleanly with 404, but the pattern is footgun-y).

### 6.5 Package approval → staff creation (#20)

- Tier-matrix (`ALLOWED_CREATIONS`) controls which `access_level` a requester can mint.
  - `staff_admin` → `{regular_staff}`.
  - `super_staff_admin` → `{regular_staff, staff_admin, super_staff_admin}` — **peer-escalation allowed**; see §4.
  - `is_superuser` → any.
- Target user must have consumed a `RegistrationCode` for the current hotel (enforced inline).
- Sets `user.is_staff=True`, `user.is_superuser=False`, deletes the used `RegistrationCode`.
- No gate on **capability overrides** because there is no override surface yet.
- No gate on **navigation defaults** — they are derived from the role preset (`Role.default_navigation_items`).

### 6.6 Verdict — privileged staff minting without capability approval

**YES — possible today**. A `super_staff_admin` holder can mint another
`super_staff_admin` via `#20` or mint a peer via `#17` without needing a
`staff_management.authority.supervise` capability (which does not
exist). Any `staff_admin` can mint arbitrary unused registration codes
(#3) and email / print them to arbitrary recipients (#5, #6). The code
itself cannot self-escalate (no auto-privilege), but the end-to-end
pipeline `mint code → hand to candidate → approve as super_staff_admin`
is gated only by tier.

---

## 7. Capability Proposal

Every capability below is grounded in a real endpoint from §2.

**Module**

- `staff_management.module.view` — module visibility (replaces
  `HasNavPermission('staff_management')`).

**Read surfaces**

- `staff_management.staff.read` — list / retrieve Staff, `/me`, metadata,
  `/by_department`, `/by_hotel`.
- `staff_management.user.read` — list `User` objects (#10, #11).
  Dangerous cross-hotel surface — separate capability so it can be
  granted only to platform-admins.
- `staff_management.authority.view` — `GET
  /<staff_id>/permissions/` (#16).
- `staff_management.pending_registration.read` — #19.

**Staff lifecycle**

- `staff_management.staff.create` — #20 + #25 (create paths).
- `staff_management.staff.update_profile` — non-authority fields of #26
  (`first_name`, `last_name`, `email`, `phone_number`, `duty_status`,
  `profile_image`). Requires the serializer-drift fix in §10.
- `staff_management.staff.deactivate` — flipping `is_active`.
  Introduce as its own capability + dedicated endpoint.
- `staff_management.staff.delete` — #27.

**Authority mutation (NEW capabilities)**

- `staff_management.authority.role.assign`
- `staff_management.authority.department.assign`
- `staff_management.authority.access_level.assign`
- `staff_management.authority.nav.assign`
- `staff_management.authority.supervise` — meta-capability required to
  assign any authority a requester does not themselves hold (see §8).
- `staff_management.authority.capability_override.assign` — **reserved**
  for the future per-staff override surface; do not register until a DB
  field exists.

**Catalog surfaces (role + department)**

- `staff_management.role.read` / `.manage`
- `staff_management.department.read` / `.manage`

**Registration packages**

- `staff_management.registration_package.read` — #4.
- `staff_management.registration_package.create` — #3.
- `staff_management.registration_package.email` — #5.
- `staff_management.registration_package.print` — #6.
- `staff_management.registration_package.revoke` — **requires new
  endpoint** (not modelled today). Do not register until the endpoint
  exists, per the Phase rules.

**Platform-level (already covered by existing primitives)**

- `NavigationItem` CUD stays on `IsDjangoSuperUser`. Do **not** create a
  `staff_management.nav.manage` capability — this is a platform-wide
  catalog, not a staff-management concern.

**Deliberately NOT proposed**

- `staff_management.face_data.manage` — face endpoints live in
  Attendance and are out of scope.
- `staff_management.staff.invite.resend` — no resend action exists;
  `#5 email` covers the surface.

---

## 8. Anti-Escalation Rules

Recommended constraints, capability-based where possible:

1. **Self-mutation of authority is always forbidden.** Endpoints
   mutating `access_level`, `allowed_navigation_items`, `role`,
   `department`, `hotel`, or `is_active` must reject requests where
   `target.user_id == request.user.id`, including for Django
   superusers (superusers may still mutate via Django admin / CLI).
2. **Same-hotel constraint.** Every authority mutation must assert
   `target_staff.hotel_id == requester.staff_profile.hotel_id`.
   Superuser bypass only for platform admins (`is_superuser=True`).
3. **No equal-or-higher access level without supervise capability.** A
   requester without
   `staff_management.authority.supervise` may only assign
   `access_level < requester.access_level` (strict less-than). Today a
   super_staff_admin creating another super_staff_admin should require
   this capability.
4. **No nav assignment beyond requester's own nav set.** Unless the
   requester holds `staff_management.authority.supervise`, the set of
   slugs assigned via `#17` must be a subset of the requester's
   currently-allowed navs.
5. **No role assignment beyond requester's own capability bundle.**
   Unless the requester holds
   `staff_management.authority.supervise`, the union of capabilities
   granted by `(role.preset ∪ department.preset)` must already be held
   by the requester. (Prevents a super_staff_admin without a
   housekeeping role from handing out a housekeeping-manager role
   preset to bypass their own department.)
6. **No cross-hotel reassignment.** `Staff.hotel` must be immutable
   from the API; transfers must happen via Django admin or a
   dedicated `staff_management.authority.transfer_hotel` endpoint
   guarded by `IsDjangoSuperUser`.
7. **Registration-package mint does not grant authority.** Packages
   must remain authority-free; authority is assigned only at #20.
8. **Registration package ceiling.** A `staff_admin` can mint
   packages but may only approve `regular_staff`; only
   `super_staff_admin` (with supervise capability) may approve higher.
9. **Package email targets.** Recipient domain should be logged and
   rate-limited; consider requiring
   `staff_management.registration_package.email` as a distinct
   capability.

---

## 9. Enforcement Mapping

| Capability | Endpoint | View / action | Serializer fields | Enforcement point |
|-----------|----------|---------------|-------------------|-------------------|
| `staff_management.module.view` | every module endpoint | class-level permission | — | `HasCapability` on view `permission_classes` |
| `staff_management.staff.read` | #23, #24, #28, #29, #30, #31, #32, #18 | `StaffViewSet` safe methods, `StaffMeView`, `StaffMetadataView` | — | view permission |
| `staff_management.user.read` | #10, #11 | `UserListAPIView`, `UsersByHotelRegistrationCodeAPIView` | — | view permission + queryset hotel filter |
| `staff_management.authority.view` | #16 | `StaffNavigationPermissionsView.get` | — | view permission |
| `staff_management.pending_registration.read` | #19 | `PendingRegistrationsAPIView` | — | view permission + hotel match |
| `staff_management.staff.create` | #25, #20 | `StaffViewSet.create`, `CreateStaffFromUserAPIView.post` | `access_level`, `department`, `role`, `is_active`, `user_id` | inside view + serializer `validate_*` (anti-escalation) |
| `staff_management.staff.update_profile` | new `PATCH /<hotel_slug>/me/profile/` OR payload-split on #26 | `StaffViewSet.partial_update` | `first_name`, `last_name`, `email`, `phone_number`, `duty_status`, `profile_image` | split serializer; capability on action |
| `staff_management.staff.deactivate` | new `POST /<hotel_slug>/<pk>/deactivate/` | `StaffViewSet` action | `is_active=false` | view permission |
| `staff_management.staff.delete` | #27 | `StaffViewSet.destroy` | — | view permission |
| `staff_management.authority.role.assign` | payload-split #26 or dedicated action | serializer path | `role` | serializer `validate_role` refuses without cap |
| `staff_management.authority.department.assign` | same | — | `department` | same |
| `staff_management.authority.access_level.assign` | #17 PATCH + dedicated action | — | `access_level` | capability + anti-escalation rule #3 |
| `staff_management.authority.nav.assign` | #17 PATCH | — | `allowed_navs` | capability + anti-escalation rule #4 |
| `staff_management.authority.supervise` | enforcement helper | — | — | used by rules #3–#5 |
| `staff_management.role.read` | #13 list/retrieve | `RoleViewSet` safe methods | — | view permission |
| `staff_management.role.manage` | #13, #22 CUD | `RoleViewSet` write methods | name, description, department, default_navigation_items | view permission |
| `staff_management.department.read` | #12 list/retrieve | same | — | view permission |
| `staff_management.department.manage` | #12, #21 CUD | — | — | view permission |
| `staff_management.registration_package.read` | #4 | `GenerateRegistrationPackageAPIView.get` | — | view permission |
| `staff_management.registration_package.create` | #3 | `.post` | `hotel_slug`, `code`, `count` | view permission + hotel equality |
| `staff_management.registration_package.email` | #5 | `EmailRegistrationPackageAPIView` | `email`, `subject`, `message` | view permission |
| `staff_management.registration_package.print` | #6 | `PrintRegistrationPackageAPIView` | — | view permission |

---

## 10. Serializer Drift / PATCH Risk

### `StaffSerializer` — #26

`read_only_fields` lists only:
`user, allowed_navs, hotel_name, hotel_slug, profile_image_url,
department_detail, role_detail, has_fcm_token, is_staff_member,
role_slug, current_status`.

Writable today via generic PATCH:
- `access_level` — **authority**
- `role` — **authority**
- `department` — **authority**
- `hotel` (`PrimaryKeyRelatedField(queryset=Hotel.objects.all())`) —
  **authority + cross-tenant**
- `is_active` — **authority**
- `has_registered_face` — face-data flag, should not be editable via
  staff management
- `duty_status`, `is_on_duty` — operational; belongs to attendance
- `profile_image`, `first_name`, `last_name`, `email`, `phone_number` —
  profile-only; safe

### `RegisterStaffSerializer` — #25

Accepts: `user_id`, `hotel` (PK, unscoped), `department`, `role`,
`access_level`, `first_name`, `last_name`, `email`, `phone_number`,
`is_active`, `duty_status`, `is_on_duty`, `profile_image`.

Risks:
- `hotel` is a PK from `Hotel.objects.all()` — the view forces it via
  `serializer.save(hotel=hotel)` so the URL slug wins, but the field is
  still exposed in the validated data; a drift-prone surface.
- `department` and `role` querysets are unscoped; `Staff.clean()` is the
  only barrier against cross-tenant pairs.
- `user_id` is a raw `IntegerField`; any `User` id accepted.

### `RegistrationCodeSerializer`

Exposes `qr_token` and `qr_code_url`. Both are read-only in the sense
that `read_only_fields` lists them, but the serializer itself is used
for the package LIST response. `qr_token` is effectively the QR secret
— returning it at list-time to any `staff_admin+` is intentional but
means any staff_admin can hand a token over to any candidate, not just
via the #5 / #6 flows.

### Recommendation

Prefer **option B: payload-aware permission split**, mirroring the
Rooms / Housekeeping / Maintenance pattern:

- Keep `StaffSerializer` as the read shape.
- Introduce a `StaffProfileUpdateSerializer` with only
  `{first_name, last_name, email, phone_number, profile_image,
  duty_status}` — wired to
  `staff_management.staff.update_profile`.
- Introduce `StaffAuthorityUpdateSerializer` (separate endpoints or
  separate actions) for `role`, `department`, `access_level`,
  `allowed_navs`, `is_active`, each gated by its dedicated capability
  and the §8 anti-escalation rules.
- Make `hotel` read-only at the API edge everywhere.
- Never accept `hotel` from the request body — always take it from the
  URL kwarg.

---

## 11. Cross-Hotel / Tenant Isolation Risks

| # | Surface | Lookup | Risk | Expected safe behaviour | Recommendation | Info leak? |
|---|---------|--------|------|-------------------------|----------------|------------|
| A | `UserListAPIView.get_queryset` | `User.objects.all()` | **Cross-hotel `User` enumeration** by any staff_management nav holder. | Filter by users tied to requester's hotel (via `UserProfile.registration_code`). | Scope queryset; require `staff_management.user.read`. | returns full username/email list |
| B | `StaffViewSet.create` → `RegisterStaffSerializer` `user_id` | `User.objects.get(id=user_id)` | Pick any `User` id from global table and bind to local hotel. Currently partially mitigated by `Staff.objects.filter(user=user).exists()` but a user without an existing staff row is claimable. | Require target user to have an unused `RegistrationCode` scoped to this hotel (as #20 does). | Add the same `RegistrationCode.objects.filter(hotel_slug=..., used_by=user)` check to #25. | existence leak (`User not found`) |
| C | `StaffSerializer.hotel` writable | `Hotel.objects.all()` | Authority transfer across tenants by self-PATCH. | Field read-only; transfer via dedicated superuser endpoint. | Read-only the field. | — |
| D | `RegisterStaffSerializer.hotel` | same | Stored body includes foreign-hotel PK even though view overrides. | Accept only URL slug. | Remove the field or restrict queryset. | — |
| E | `StaffViewSet.update` queryset | scoped by hotel_slug — **safe** | — | — | — | — |
| F | Department / Role PK queryset | `Department.objects.all()` / `Role.objects.all()` in `StaffSerializer` and `RegisterStaffSerializer` | Assign a role/department from another hotel. Currently blocked by `Staff.clean()` (`ValidationError`). | Scope queryset to `hotel=URL hotel`. | Scope. Remove reliance on `Staff.clean()` alone. | — |
| G | `StaffMetadataView` | `hotel__slug` filter when slug present; else `.all()` | When called without a hotel slug (route requires one, so unreachable today) would leak. | Make slug required at URL (already the case). | Keep asserting. | — |
| H | `RegistrationCode` listing (#4) | `hotel_slug` from requester's profile (safe); superuser passes slug via query param (safe) | — | — | — | — |
| I | `NavigationItem` admin (#14/#15) | platform-global | `IsDjangoSuperUser` | — | — | — |
| J | `StaffNavigationPermissionsView` hotel scoping | `requester.hotel == target.hotel` | safe | — | — | — |
| K | `Role.default_navigation_items` queryset (Django admin M2M, no API CUD) | platform-global | A superuser could attach a NavigationItem from hotel A to a Role in hotel B via admin. | Validate hotel equality in `Role.clean()`. | Add constraint. | — |
| L | `GenerateRegistrationPackageAPIView.post` superuser without staff_profile | `request.user.staff_profile` | `AttributeError → 500`. Info leak minor. | Superuser bypass branch. | Add bypass. | 500 |

---

## 12. Dead Code / Duplicate Surface

- **Two `/me` surfaces**: `StaffMeView` (canonical, under
  `/api/staff/hotel/<slug>/me/`) **and** `StaffViewSet.me` action
  (under `/api/staff/<slug>/me/`). Both active. Recommend retiring the
  ViewSet action.
- **Two gates for Department / Role CUD**: `CanManageStaff` requires
  `super_staff_admin+`, inline `check_write_permission` requires
  `staff_admin+`. Under current code the stricter class wins, so the
  inline staff_admin clause is **dead**. Pick one.
- **Global `DepartmentViewSet` / `RoleViewSet` mount** (no hotel slug)
  coexists with the hotel-scoped mount. The global mount falls back to
  `request.user.staff_profile.hotel`, i.e. effectively does the same
  thing for non-superusers. Risk of divergence; consider removing the
  global mount.
- **`StaffAttendanceSummarySerializer`** lives in the staff module but
  is pure Attendance surface. Out of scope.
- **`UsersByHotelRegistrationCodeAPIView` + `UserListAPIView`** overlap.
  Keep the hotel-scoped one; retire the global one (see §11 A).
- **Docstring drift**: `CreateStaffFromUserAPIView.ALLOWED_CREATIONS`
  contradicts its own docstring (see §4.2).
- **No dead permission classes** found in `staff/permissions.py`.
- **Printable reg-pkg for used codes** — not dead, but should be an
  audit-only read that does not re-emit the token.
- **`has_registered_face`** exposed writable via `StaffSerializer` but
  owned by Attendance. Should be read-only here.

---

## 13. Gap Analysis

Blockers (must close before or during Phase 6E implementation):

1. **No `staff_management.*` capabilities exist** in
   `staff/capability_catalog.py`. Every mutation is tier-gated.
2. **No `staff_management` entry in `module_policy.py`** — frontend
   `rbac.staff_management` is unpopulated today.
3. **`Staff.hotel` writable via self-PATCH** — cross-tenant authority
   transfer vector.
4. **`Staff.access_level` writable via self-PATCH** under
   `StaffViewSet.update`.
5. **`StaffNavigationPermissionsView.patch` lacks self-`access_level`
   guard** (self-lockout guard covers nav only).
6. **`ALLOWED_CREATIONS['super_staff_admin']` includes
   `super_staff_admin`** — peer-escalation allowed without a supervise
   capability.
7. **`UserListAPIView` returns every `User` platform-wide** — cross-
   hotel leak.
8. **`GenerateRegistrationPackageAPIView.post` 500s for a Django
   superuser without `staff_profile`**.
9. **`RegisterStaffSerializer.hotel` / `department` / `role` /
   `user_id`** accept unscoped PKs; only `Staff.clean()` protects.
10. **`StaffViewSet` CUD is pure tier authority** — violates the
    "Tier must not grant module action authority" rule.
11. **Registration packages have no expiry, no revoke endpoint**, and
    `#5 email` accepts any recipient without audit.
12. **`#6 print` re-exposes tokens of used packages** without logging.
13. **Docstring drift** in `CreateStaffFromUserAPIView`.
14. **Two `/me` surfaces** (duplicate).
15. **Dead inline `check_write_permission(staff_admin+)`** under
    `CanManageStaff(super_staff_admin+)` in Department / Role
    ViewSets.
16. **`Staff.access_level` default (`regular_staff`)** — safe default,
    but `#20` accepts any value when requester tier allows; no
    serializer-level clamp if requester is staff_admin.
17. **`has_registered_face` writable** via generic PATCH.
18. **No capability override surface** — §7
    `staff_management.authority.capability_override.assign` is a
    future capability, do not ship decoratively.
19. **No tests** exist under `staff/` for authority mutation paths
    (`staff/tests.py` exists but was not inspected; there is no test
    file specifically targeting `StaffNavigationPermissionsView.patch`,
    `ALLOWED_CREATIONS`, `StaffViewSet.update` self-only guard, or
    registration-package email exfiltration).

---

## 14. Final Verdict

```md
READY for RBAC implementation? NO
```

### Blocking issues (in order)

1. `staff_management` capabilities + module policy entry do not exist.
2. Writable `Staff.hotel`, `Staff.access_level`, `Staff.is_active`, and
   `Staff.allowed_navigation_items` via generic PATCH / self-PATCH
   (§5, §10).
3. Peer-escalation via `ALLOWED_CREATIONS` and
   `StaffNavigationPermissionsView.patch` (§4, §5, §8).
4. `UserListAPIView` cross-hotel leak (§11 A).
5. Tier-only authority for every mutation endpoint (§4.2).
6. Registration-package revoke / expiry absent; email recipient
   unaudited (§6).
7. Duplicate `/me` and duplicate write-gate contradictions (§12).
8. Unscoped PK querysets in `RegisterStaffSerializer` and
   `StaffSerializer` (§11 B/D/F).
9. Missing self-mutation guards across every authority-mutation
   endpoint (§5, §8).

### Recommended capability list (atomic)

```
staff_management.module.view
staff_management.staff.read
staff_management.user.read
staff_management.staff.create
staff_management.staff.update_profile
staff_management.staff.deactivate
staff_management.staff.delete
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
staff_management.pending_registration.read
staff_management.registration_package.read
staff_management.registration_package.create
staff_management.registration_package.email
staff_management.registration_package.print
```

Deferred (require new endpoints / surfaces — do **not** register yet):

```
staff_management.registration_package.revoke
staff_management.authority.capability_override.assign
staff_management.authority.transfer_hotel
```

### Recommended anti-escalation rules

(See §8 for the full text.)

1. No self-mutation of authority fields.
2. Same-hotel constraint on every authority mutation.
3. No assignment of `access_level >= requester.access_level` without
   `staff_management.authority.supervise`.
4. No nav assignment beyond requester's own navs without
   `.authority.supervise`.
5. No role/department assignment whose preset capabilities exceed the
   requester's own capability bundle without `.authority.supervise`.
6. `Staff.hotel` immutable via API.
7. Registration packages never grant authority.
8. Approval of `access_level > regular_staff` requires
   `super_staff_admin` + supervise capability.
9. Rate-limit and audit `registration-package/<pk>/email/`.

### Recommended implementation order

1. Register capabilities (§7) + `staff_management` entry in
   `module_policy.py`.
2. Harden serializers (§10): make `hotel`, `access_level`,
   `has_registered_face`, `is_active`, `allowed_navigation_items`
   read-only in `StaffSerializer`; scope `department` / `role` /
   `user_id` querysets to the URL hotel.
3. Split authority endpoints from profile endpoints (payload-aware
   split).
4. Replace every tier check in staff views with `HasCapability`
   (keep tier as a preset source only, via
   `capability_catalog.TIER_DEFAULT_CAPABILITIES`).
5. Implement §8 anti-escalation rules inside view `perform_*` methods
   AND serializer `validate_*` hooks (defence in depth).
6. Fix `UserListAPIView` cross-hotel leak.
7. Fix superuser-without-staff 500 in
   `GenerateRegistrationPackageAPIView.post`.
8. Remove duplicate `/me` action and the dead
   `check_write_permission` clause.
9. Add a `staff_management.registration_package.revoke` endpoint
   (and register the capability).
10. Rate-limit + audit-log `registration-package/<pk>/email/`.
11. Correct `CreateStaffFromUserAPIView.ALLOWED_CREATIONS` +
    docstring to enforce `super_staff_admin` NOT creating another
    `super_staff_admin` without the supervise capability.
12. Write tests covering every anti-escalation rule above.
