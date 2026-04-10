# Canonical RBAC Implementation Plan

**Date:** 2026-04-10  
**Status:** Implementation planning — no code changes yet  
**Prerequisite:** [RBAC Permissions Audit](rbac_permissions_audit_2026_04_10.md)

---

## 1. Canonical Concepts Mapped to Current Code

### 1A. Canonical Tier → `Staff.access_level` + `User.is_superuser`

| Canonical Tier | Current Source | Resolution Logic |
|---|---|---|
| `super_user` | `User.is_superuser == True` | Django User field. Bypasses all staff-level checks. |
| `super_staff_admin` | `Staff.access_level == 'super_staff_admin'` | Highest hotel-level authority. |
| `staff_admin` | `Staff.access_level == 'staff_admin'` | Mid-level hotel admin. |
| `regular_staff` | `Staff.access_level == 'regular_staff'` | Default. Operational access only. |
| `guest` | No Django User. Token-based via `GuestBookingToken` / `BookingManagementToken`. | Entirely separate auth path. |

`Staff.access_level` is the canonical tier field. `ACCESS_LEVEL_CHOICES` already defines the exact 3 staff tiers. `User.is_superuser` provides the `super_user` tier above all staff tiers. No new fields needed.

### 1B. Canonical Job Role → `Staff.role` (FK to `Role` model)

| Concept | Current Source | Status |
|---|---|---|
| Job role identity | `Staff.role` → `Role.slug` | Exists. Per-hotel catalog. Free-form name/slug. |
| Job role → feature mapping | **Does not exist** | No `Role.allowed_navigation_items` or equivalent. |
| Hardcoded role slugs in permission logic | `'manager'`, `'admin'`, `'housekeeping'`, `'receptionist'`, `'porter'` | Scattered across 12 locations. |

`Role` is the right model for job role identity. It exists, is hotel-scoped, and already carries a slug. What is **missing** is a `Role → NavigationItem` M2M to define default features per job role. Currently, feature assignment is only per-Staff (manual).

### 1C. Canonical Feature/Module Key → `NavigationItem.slug`

| Concept | Current Source | Status |
|---|---|---|
| Feature module identifier | `NavigationItem.slug` | Exists. Per-hotel, unique within hotel. |
| Feature enforcement at view level | `HasNavPermission(slug)` | **Defined but never wired into any view.** Dead code. |
| Feature visibility for frontend | `resolve_staff_navigation(user)` → `allowed_navs[]` | Works. Returns slug list on login and `/me`. |

`NavigationItem.slug` is the canonical feature key. The visibility pipeline exists (`resolve_staff_navigation`). The enforcement pipeline (`HasNavPermission`) exists as code but has **zero usages**. The slug catalog has a mismatch between the Hotel post-save signal (13 slugs) and the seed command (17 slugs).

### 1D. Canonical Override → `Staff.allowed_navigation_items` (M2M)

| Concept | Current Source | Status |
|---|---|---|
| Per-user feature override | `Staff.allowed_navigation_items` M2M → `NavigationItem` | Exists. Currently the **only** source of feature access for non-superusers. |

Today this M2M is the **primary** system — not an override. In the canonical model, it becomes the **override layer** on top of tier defaults + job role defaults.

### 1E. Existing Elements Too Inconsistent for Canonical Use

| Element | File | Problem |
|---|---|---|
| `IsSuperUser` (staff) | `staff/permissions_superuser.py` | Misleading name — allows `staff_admin` too, not just superusers. |
| `IsSuperUser` (provisioning) | `hotel/provisioning_views.py` | Local class, checks only Django `is_superuser`. Same name, different behavior. |
| `HotelSubdomainBackend` | `hotel/auth_backends.py` | Not in `AUTHENTICATION_BACKENDS`. Dead code. |
| `HasNavPermission` | `staff/permissions.py` | Never used in any view. Dead enforcement code. |
| `create_nav_permission` | `staff/permissions.py` | Never called. Dead code. |
| `requires_nav_permission` | `staff/permissions.py` | Never used as decorator. Dead code. |
| `role.slug` hardcoded checks | 12 locations across 5 files | `['manager', 'admin']`, `'housekeeping'`, `'receptionist'`, `'porter'` — scattered, not in a permission class. |
| Nav slug catalog | Hotel signal vs seed command | 13 slugs vs 17 slugs — different sets, no canonical list. |

---

## 2. Canonical Backend Access Contract

### 2A. Canonical Tier Resolver

One function, one location, one truth:

```
resolve_tier(user) → Tier
```

**Decision logic:**

```
IF user has no Django account:
    → GUEST (token-scoped, separate path)

IF user.is_superuser:
    → SUPER_USER

IF user has staff_profile:
    → staff_profile.access_level (one of: super_staff_admin, staff_admin, regular_staff)

ELSE:
    → DENY (authenticated Django user with no staff profile and not superuser)
```

**Where this exists today:** Partially in `resolve_staff_navigation()`, partially in every permission class independently. No single `resolve_tier()` function exists.

**What must change:** Extract tier resolution into a single canonical function. All permission classes and helpers call this instead of doing their own `is_superuser` / `access_level` checks.

### 2B. Canonical Job Role Source

**Source:** `Staff.role` → `Role` model.

**Current Role model suitability:**
- Has `hotel` FK (hotel-scoped) ✓
- Has `slug` (stable identifier) ✓
- Has `department` FK (organizational context) ✓
- Has `unique_together = [['hotel', 'slug']]` (no duplicates per hotel) ✓
- **Missing:** No M2M to `NavigationItem` for default feature mapping ✗

**Department as permission-relevant:**
Currently `Department.slug == 'housekeeping'` is checked in `housekeeping/policy.py` alongside `Role.slug == 'housekeeping'`. Department is used as a **fallback** for the same check that role handles. In the canonical model, department is **descriptive/organizational only**. Permission-relevant operational identity comes from `Role.slug` exclusively. The housekeeping policy's `department.slug` check is a workaround for inconsistent role assignment.

**What must change:** Add `Role.default_navigation_items` M2M to `NavigationItem`. This is the **tier_defaults + job_role_defaults** mapping that does not exist today:
- Tier defaults: a set of nav items every staff member at a given `access_level` gets.
- Job role defaults: additional nav items specific to the `Role`.

### 2C. Canonical Feature/Module Source

**Source:** `NavigationItem.slug`.

**Canonical slug catalog must be unified.** Currently two competing sources:
- Hotel post-save signal: `home`, `rooms`, `bookings`, `chat`, `stock_tracker`, `housekeeping`, `attendance`, `staff_management`, `room_services`, `maintenance`, `entertainment`, `hotel_info`, `admin_settings`
- Seed command: `home`, `chat`, `reception`, `rooms`, `guests`, `roster`, `staff`, `restaurants`, `bookings`, `maintenance`, `hotel_info`, `good_to_know`, `stock_tracker`, `games`, `settings`, `room_service`, `breakfast`

These must be reconciled into ONE canonical slug list before any enforcement can be reliable.

### 2D. Canonical Override Source

**Source:** `Staff.allowed_navigation_items` M2M — but repurposed.

**Current behavior:** This M2M is the **only** way non-superuser staff get nav items. It is the primary system.

**Canonical behavior:** This M2M becomes an **additive override** on top of computed defaults. The primary system becomes `tier_defaults + role.default_navigation_items`. The M2M stores only **exceptions** (additions beyond defaults, or flags for removals if needed).

**Override semantics — two options:**

1. **Additive only:** `Staff.allowed_navigation_items` adds items beyond tier+role defaults. No way to remove defaults per-user.
2. **Additive + subtractive:** Separate field or flag to also deny specific defaults per-user.

The additive-only approach is simpler and matches current M2M structure. Removals would be extremely rare exceptions and could be handled by assigning a different role.

---

## 3. Canonical Access Decision Flow

For every authenticated staff request:

```
Step 1 — RESOLVE ACTOR TYPE
    Is request from a guest token?  → Guest access path (separate, unchanged)
    Is request from a Django user?  → Continue to Step 2
    Neither?                        → DENY

Step 2 — RESOLVE HOTEL SCOPE
    Derive hotel from: request.user.staff_profile.hotel (ONLY canonical source)
    If URL contains hotel_slug: cross-check against profile hotel → mismatch = DENY
    Never trust hotel from query params, request body, or headers for authorization

Step 3 — RESOLVE TIER
    Call resolve_tier(user):
        is_superuser         → SUPER_USER
        access_level match   → SUPER_STAFF_ADMIN | STAFF_ADMIN | REGULAR_STAFF
        no staff profile     → DENY

Step 4 — RESOLVE JOB ROLE
    staff.role → Role instance (nullable)
    role.slug  → stable identifier for job role defaults
    If role is None → only tier defaults apply (no job-role features)

Step 5 — COMPUTE EFFECTIVE FEATURE KEYS
    tier_features     = get_tier_default_navs(tier)
    role_features     = role.default_navigation_items.slugs() if role else []
    override_features = staff.allowed_navigation_items.slugs()
    
    effective_features = tier_features ∪ role_features ∪ override_features
    
    (SUPER_USER: gets ALL active nav items for hotel — unchanged from current behavior)

Step 6 — ENFORCE ACCESS
    For module/nav visibility: return effective_features in login/me response
    For view-level access:     permission class checks required_slug ∈ effective_features
    For action-level access:   permission class checks tier ≥ required_tier
```

### Guest Access Flow (unchanged)

```
Step 1 — Extract token from query param, header, or body
Step 2 — Resolve via resolve_guest_access() → GuestAccessContext
Step 3 — Check token scopes against required scopes
Step 4 — Check hotel scope against URL hotel_slug
Step 5 — Allow/Deny
```

---

## 4. Backend Ownership Boundaries

### 4A. Who Computes Effective Feature Keys?

**Owner:** One canonical resolver function (evolution of `resolve_staff_navigation`).

```
resolve_effective_access(user) → {
    tier: str,
    hotel_slug: str,
    role_slug: str | None,
    effective_navs: [str],        # computed: tier + role + override
    navigation_items: [dict],     # full serialized NavigationItem objects
    is_superuser: bool,
    access_level: str,
}
```

This function is called:
- On login (response payload)
- On `/me` (response payload)
- By `HasNavPermission` (enforcement)

**NOT called:** On every request via middleware. Only called when permission check needs it or when client requests fresh data.

### 4B. Who Returns Nav/Module Visibility to Frontend?

**Owner:** `resolve_effective_access()` called from:
- `StaffLoginView.post()` — in login response
- `StaffMeView.get()` — in /me response
- `StaffNavigationPermissionsView` — admin managing another staff's overrides

Frontend receives `effective_navs` (slug list) and `navigation_items` (full objects) and renders UI accordingly.

### 4C. Who Enforces Module Access at View Level?

**Owner:** `HasNavPermission(required_slug)` DRF permission class.

Every staff-facing view that belongs to a module declares which nav slug it requires:

```python
permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('stock_tracker')]
```

`HasNavPermission.has_permission()` calls `resolve_effective_access()` and checks `required_slug in effective_navs`.

### 4D. Who Enforces Action-Level Access?

**Owner:** Tier-checking permission classes for admin-only actions.

| Action Type | Enforcement |
|---|---|
| Module visibility / read access | `HasNavPermission(slug)` |
| Admin-only mutations (CUD on settings, staff, nav) | `IsSuperStaffAdminForHotel` or tier check |
| Object-level ownership checks | `IsConversationParticipant`, `IsMessageSender`, etc. |
| Inline business rules | `housekeeping/policy.py` functions (role-based transition rules) |

Tier-based action checks happen in permission classes, **not** inline in view bodies.

### 4E. Where Does Hotel Scoping Happen?

**Owner:** `IsSameHotel` permission class + `HotelScopedQuerysetMixin`/`HotelScopedViewSetMixin`.

| Layer | Responsibility |
|---|---|
| `IsSameHotel.has_permission()` | Ensures URL `hotel_slug` matches `staff_profile.hotel.slug`. Rejects cross-hotel requests. |
| `HotelScopedQuerysetMixin.get_queryset()` | Filters queryset to `staff_profile.hotel`. Server-side tenant isolation. |
| `HotelScopedViewSetMixin` | Combines both: permission check + queryset scoping. Default `permission_classes` includes `IsSameHotel`. |

**Canonical rule:** Hotel is ALWAYS derived from `request.user.staff_profile.hotel` for authorization. URL `hotel_slug` is validated against it. Query params, request body, and headers are NEVER used to determine authorization scope.

### 4F. What Lives Where

| Responsibility | Location | NOT in |
|---|---|---|
| Tier resolution | `staff/permissions.py` → `resolve_tier()` | View bodies, serializers, helpers |
| Effective access computation | `staff/permissions.py` → `resolve_effective_access()` | View bodies |
| Module enforcement | `staff/permissions.py` → `HasNavPermission` | Inline `if` checks in views |
| Tier enforcement | `hotel/permissions.py` → `IsSuperStaffAdminForHotel` (or new tier class) | Inline `is_superuser` checks |
| Hotel scoping | `staff_chat/permissions.py` → `IsSameHotel` + `common/mixins.py` | Query params, request body |
| Nav/module visibility data | `resolve_effective_access()` called from login/me views | Scattered across serializers |
| Business rule checks (e.g. room status transitions) | `housekeeping/policy.py` (stay as-is) | Permission classes |
| Guest access | `common/guest_access.py` (unchanged) | Staff permission classes |

---

## 5. Blocking Conflicts in Current Backend

### Conflict 1: Two `IsSuperUser` classes with different semantics

| File | Logic | Used By |
|---|---|---|
| `staff/permissions_superuser.py` | `is_superuser` OR `access_level in ('super_staff_admin', 'staff_admin')` | `HotelViewSet`, `StaffViewSet` |
| `hotel/provisioning_views.py` | `is_superuser` only (Django) | `ProvisionHotelView` |

**Impact:** The name `IsSuperUser` means different things depending on import path. `staff/permissions_superuser.py::IsSuperUser` actually means "is any admin tier", which conflates tier levels. Must be renamed/split.

### Conflict 2: No tier-default or role-default feature mapping exists

Current `Staff.allowed_navigation_items` is the **only** mechanism for non-superuser feature access. There is no `Role.default_navigation_items` and no access-level → feature mapping. Without these, the canonical formula `effective = tier_defaults + role_defaults + override` cannot be computed.

**Impact:** Must add `Role.default_navigation_items` M2M and define a tier-defaults mechanism before the resolver can work.

### Conflict 3: NavigationItem slug catalog is inconsistent

Hotel post-save signal creates 13 slugs. Seed management command creates 17 slugs. The sets overlap but differ. No canonical source of truth for what slugs exist.

**Impact:** Views cannot reliably declare `HasNavPermission('some_slug')` if the slug set is unstable. Must unify into one canonical slug definition.

### Conflict 4: `HasNavPermission` is defined but never used

The entire nav-permission enforcement infrastructure (`HasNavPermission`, `create_nav_permission`, `requires_nav_permission`) exists as dead code. No view calls it. This means **no view currently enforces module-level access**. All staff-facing views only check authentication and hotel scoping, never feature authorization.

**Impact:** Wiring `HasNavPermission` into views is the core enforcement step. Must be done after the resolver is canonical.

### Conflict 5: `role.slug` hardcoded permission checks bypass canonical tier

12 locations check `role.slug in ['manager', 'admin']`, `role.slug == 'housekeeping'`, `role.slug == 'receptionist'`, `role.slug == 'porter'`. These are **action-level** checks that bypass the tier system — a staff member with `regular_staff` access_level but `role.slug == 'manager'` gets elevated chat permissions.

**Impact:** These checks are business-rule-level (not module-level). They can remain as domain-specific action guards inside their respective apps, but must be documented as separate from the canonical tier/feature system. They are NOT blocking — they serve a different purpose (action permission vs module permission).

### Conflict 6: Views with only `[IsAuthenticated]` that handle staff data

Multiple views (C14 `AddGuestToRoomView`, C15 `BookingViewSet`, `RestaurantViewSet`, C20 `RosterAnalyticsViewSet`, C21 `FaceManagementViewSet`, etc.) use only `[IsAuthenticated]` without `IsStaffMember`, `IsSameHotel`, or any hotel scoping.

**Impact:** These views cannot participate in the canonical access flow until they are updated to include at minimum `[IsAuthenticated, IsStaffMember, IsSameHotel]`. Must be fixed as part of rollout.

### Conflict 7: `department.slug` used as fallback for `role.slug` in housekeeping policy

`is_housekeeping(staff)` checks both `department.slug == 'housekeeping'` and `role.slug == 'housekeeping'`. This makes department a permission-relevant field, contradicting the canonical model where department is descriptive only.

**Impact:** Must be resolved by ensuring staff in housekeeping department have a role with `slug='housekeeping'`. Then the department check can be removed from permission logic.

### Conflict 8: `Staff.allowed_navigation_items` is currently primary, not override

Every non-superuser staff member's nav access comes **exclusively** from this M2M today. There are no defaults. Making this an "override" layer requires first creating the defaults layer (tier + role), then migrating existing M2M data.

**Impact:** Migration must preserve current behavior: existing M2M entries must be honored during transition. A migration step computes what would be defaults for each staff member vs what are genuine overrides.

---

## 6. Ordered Implementation Plan

### Phase 0 — Prerequisites (no behavior change)

**Step 0.1: Unify NavigationItem slug catalog**
- Define ONE canonical list of nav slugs
- Reconcile Hotel post-save signal and seed command to produce the same set
- Add migration to normalize existing NavigationItem records
- Deliverable: single source of truth for all nav slugs

**Step 0.2: Define tier-default feature sets**
- Create a configuration (can be code constant, not DB) mapping each tier to default nav slugs:
  ```python
  TIER_DEFAULT_NAVS = {
      'super_staff_admin': ['home', 'rooms', 'bookings', 'chat', 'stock_tracker', 'housekeeping',
                            'attendance', 'staff_management', 'room_services', 'maintenance',
                            'entertainment', 'hotel_info', 'admin_settings'],
      'staff_admin':       ['home', 'rooms', 'bookings', 'chat', 'stock_tracker', 'housekeeping',
                            'attendance', 'staff_management', 'room_services', 'maintenance',
                            'entertainment', 'hotel_info', 'admin_settings'],
      'regular_staff':     ['home', 'chat'],
  }
  ```
- `regular_staff` gets minimal defaults. Additional modules come from job role.
- `super_user` gets ALL active nav items (unchanged from current behavior).
- Deliverable: code constant in `staff/permissions.py`

> **CLARIFICATION NEEDED:** Confirm the exact tier-default sets. The above is a starting proposal. Should `staff_admin` be identical to `super_staff_admin`, or should certain admin modules (e.g. `admin_settings`, `staff_management`) be `super_staff_admin`-only?

**Step 0.3: Add `Role.default_navigation_items` M2M**
- Add `default_navigation_items = ManyToManyField(NavigationItem, blank=True)` to `Role` model
- Migration: add field (no data change)
- Admin interface for hotel admins to configure which nav items a role gets
- Deliverable: model field + migration

**Step 0.4: Populate role defaults for existing roles**
- For each hotel, map existing roles to sensible default nav items based on their slug
- This is a data migration or management command
- Deliverable: management command `populate_role_nav_defaults`

### Phase 1 — Build Canonical Resolver (no behavior change yet)

**Step 1.1: Create `resolve_tier(user)` function**
- Location: `staff/permissions.py`
- Returns: string tier (`'super_user'`, `'super_staff_admin'`, `'staff_admin'`, `'regular_staff'`) or `None`
- Replaces all inline `is_superuser` / `access_level` dispatch

**Step 1.2: Evolve `resolve_staff_navigation()` → `resolve_effective_access()`**
- Same location: `staff/permissions.py`
- New logic: tier_defaults ∪ role.default_navigation_items ∪ staff.allowed_navigation_items
- Returns same structure as today, plus `tier` and `role_slug`
- **Backward compatible:** `allowed_navs` and `navigation_items` keys stay the same
- Superuser path unchanged (all active nav items)

**Step 1.3: Update `HasNavPermission` to use `resolve_effective_access()`**
- Already calls `resolve_staff_navigation()` — just update to new resolver
- No views use it yet, so this is a safe internal change

**Step 1.4: Wire login and /me to use `resolve_effective_access()`**
- `StaffLoginView.post()` — swap call
- `StaffMeView.get()` — swap call
- `StaffLoginResponseSerializer.to_representation()` — swap call
- Frontend sees same response shape, but nav items now include tier+role defaults
- Deliverable: frontend starts getting default-driven nav items

### Phase 2 — Fix Permission Class Naming (no behavior change)

**Step 2.1: Rename `staff/permissions_superuser.py::IsSuperUser` → `IsAdminTier`**
- Update all 2 import sites: `hotel/base_views.py`, `staff/views.py`
- Name now reflects actual behavior: allows `super_staff_admin` and `staff_admin` (and superuser)

**Step 2.2: Move `hotel/provisioning_views.py::IsSuperUser` to `staff/permissions.py` as `IsDjangoSuperUser`**
- Rename to `IsDjangoSuperUser`
- Update `ProvisionHotelView` import
- Clear separation: `IsDjangoSuperUser` (true platform superuser), `IsAdminTier` (hotel admin), `IsSuperStaffAdminForHotel` (top hotel admin)

### Phase 3 — Enforce Module Access on Views (gradual rollout)

**Step 3.1: Map each view module to its canonical nav slug**

| App / View Group | Nav Slug |
|---|---|
| `stock_tracker/*` | `stock_tracker` |
| `housekeeping/*` | `housekeeping` |
| `attendance/*` | `attendance` |
| `maintenance/*` | `maintenance` |
| `rooms/*` (staff) | `rooms` |
| `room_services/*` (staff) | `room_services` |
| `bookings/*` (staff) | `bookings` |
| `staff_chat/*` | `chat` |
| `chat/*` (staff endpoints) | `chat` |
| `hotel_info/*` | `hotel_info` |
| `entertainment/*` (dashboard) | `entertainment` |
| `home/*` | `home` |
| `guests/*` | `rooms` (or new slug if separate) |
| `staff/*` (staff management views) | `staff_management` |
| `hotel/staff_views.py` (public page builder) | `admin_settings` |
| `hotel/staff_views.py` (booking mgmt) | `bookings` |

> **CLARIFICATION NEEDED:** Should `guests/views.py` and `home/views.py` get their own nav slugs, or map to existing ones?

**Step 3.2: Add `HasNavPermission` to each module's views**
- Roll out one app at a time, starting with the most isolated
- Suggested order:
  1. `stock_tracker` (all views already use `IsHotelStaff`, well-isolated)
  2. `maintenance` (all views use `IsHotelStaff`, small surface)
  3. `housekeeping` (uses `IsStaffMember + IsSameHotel`, has policy layer)
  4. `attendance` (uses mixin-based permissions, larger surface)
  5. `room_services` (staff views)
  6. `rooms` (staff views)
  7. `staff_chat`
  8. `chat` (staff endpoints)
  9. `hotel_info`
  10. `bookings` (staff endpoints)
  11. `hotel/staff_views.py` groups (booking mgmt, public page builder, settings)
  12. `staff` management views
  13. `entertainment` dashboard
  14. `home`, `guests`

For each app:
```python
# Before
permission_classes = [IsHotelStaff]

# After
permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('stock_tracker')]
```

**Step 3.3: Fix views with only `[IsAuthenticated]` that handle staff data**

Priority fixes (no hotel scoping today):
1. `bookings/views.py` → `BookingViewSet` — add `IsStaffMember`, `IsSameHotel`, hotel queryset filter
2. `bookings/views.py` → `RestaurantViewSet` — add `IsStaffMember`, `IsSameHotel`, hotel queryset filter
3. `rooms/views.py` → `AddGuestToRoomView` — add `IsStaffMember`, `IsSameHotel`
4. `rooms/views.py` → `RoomByHotelAndNumberView` — add `IsStaffMember`, `IsSameHotel`
5. `attendance/views_analytics.py` → `RosterAnalyticsViewSet` — add `IsStaffMember`, `IsSameHotel`
6. `attendance/face_views.py` → all views — add `IsStaffMember`, `IsSameHotel`
7. `bookings/views.py` → `UnseatBookingAPIView`, `DeleteBookingAPIView` — add `IsStaffMember`, `IsSameHotel`

### Phase 4 — Clean Up Scattered Authorization (gradual)

**Step 4.1: Replace inline `is_superuser` checks with tier-aware permission classes**
- 21+ locations currently check `request.user.is_superuser` inline
- Replace with `resolve_tier(request.user)` or appropriate permission class on the view
- Priority: `stock_tracker/views.py` (5 checks), `staff/views.py` (6 checks)

**Step 4.2: Replace inline `access_level` checks with tier resolver**
- 9+ locations check `staff.access_level in [...]`
- Replace with `resolve_tier()` calls or move to permission class
- Priority: `staff/views.py` (4 checks), `housekeeping/views.py` (2 checks)

**Step 4.3: Centralize `role.slug` action checks**
- Keep `housekeeping/policy.py` functions as business-rule layer (they serve a different purpose than module access)
- Centralize chat `['manager', 'admin']` checks — currently in `staff_chat/permissions.py` (2 classes) + `staff_chat/views_messages.py` (2 places) + `staff_chat/views_attachments.py` (1 place) + `chat/views.py` (1 place)
- Move to a single helper: `is_chat_manager(staff)` → `role.slug in ['manager', 'admin']`

**Step 4.4: Remove `department.slug` from permission logic**
- `housekeeping/policy.py::is_housekeeping()` checks `department.slug == 'housekeeping'` as fallback
- Ensure all housekeeping staff have `role.slug == 'housekeeping'` assigned
- Then remove the `department.slug` check

### Phase 5 — Remove Dead Code

**Step 5.1:** Remove `hotel/auth_backends.py` (`HotelSubdomainBackend`) — not in `AUTHENTICATION_BACKENDS`, never active.

**Step 5.2:** Remove `create_nav_permission()` and `requires_nav_permission()` from `staff/permissions.py` — never used. Keep `HasNavPermission` (will be wired).

**Step 5.3:** Remove old `resolve_staff_navigation()` once all call sites use `resolve_effective_access()`.

### Phase 6 — Migration Strategy for Existing Data

**Step 6.1: Compute override delta for existing staff**
- For each staff member: compute what `tier_defaults ∪ role.default_navigation_items` would give them
- Compare against their current `allowed_navigation_items` M2M
- Items in current M2M that are NOT in computed defaults → genuine overrides (keep in M2M)
- Items in current M2M that ARE in computed defaults → remove from M2M (now covered by defaults)
- Deliverable: management command `migrate_nav_to_defaults`

**Step 6.2: Run migration**
- Populate `Role.default_navigation_items` (Step 0.4)
- Run `migrate_nav_to_defaults` for each hotel
- Verify: all staff members' `resolve_effective_access()` returns same `allowed_navs` as before
- If mismatch → investigate and fix before proceeding

**Step 6.3: Update admin UI**
- `StaffNavigationPermissionsView` now manages **overrides only**
- Show computed defaults (read-only) + override M2M (editable)
- Frontend must distinguish between default access and override access

---

## 7. Clarification Questions

**Q1: Tier-default feature sets**
Should `staff_admin` and `super_staff_admin` have identical default feature sets, or should certain modules (e.g. `admin_settings`, `staff_management`) be restricted to `super_staff_admin` only? The current codebase uses `IsSuperStaffAdminForHotel` for public page builder and precheckin/survey config, but `IsSuperUser` (which includes `staff_admin`) for `HotelViewSet` and `StaffViewSet`.

**Q2: Guest-related staff views**
Should `guests/views.py::GuestViewSet` map to the `rooms` nav slug, get its own slug (e.g. `guests`), or be treated as part of a broader `reception` module? The post-save signal does not create a `guests` nav item, but the seed command doesn't either. The guest list is typically a reception/front-desk function.

**Q3: Override semantics**
Should `Staff.allowed_navigation_items` be **additive only** (adds features beyond tier+role defaults), or should there also be a way to **remove** default features for specific staff? Additive-only is simpler and the M2M structure supports it directly.

**Q4: `home/views.py` posts/comments**
Are `PostViewSet`, `CommentViewSet`, `CommentReplyViewSet` staff-only features tied to a module, or are they general functionality available to all authenticated staff regardless of tier/role? This determines whether they need `HasNavPermission('home')` or just `IsStaffMember + IsSameHotel`.

**Q5: Notification routing by role slug**
`notifications/notification_manager.py` uses `role__slug='porter'` (3 places) and `role__slug='receptionist'` (2 places) to target notifications to specific staff. This is a notification-routing concern, not a permission concern. Confirm these should remain as-is (they are read-only queries, not authorization gates).

---

*End of implementation plan. Awaiting clarification answers before proceeding to code.*
