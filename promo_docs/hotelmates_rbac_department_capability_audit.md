# HotelMates Backend Audit — RBAC → Department + Capability Architecture

> **Scope:** Read-only architectural audit of the Django backend in preparation for a hybrid
> **Tier + Department + Role + Capability + Hotel-scope** model.
> **Status:** No code changes in this task. All findings are grounded in current source files.

---

## 1. Executive summary

The backend today is a **tier-first, nav-slug-mediated** authorization system with a partial role/department layer:

- **Tier** (`Staff.access_level`) is the primary enforcement axis: `super_user` (Django superuser) > `super_staff_admin` > `staff_admin` > `regular_staff`. It is resolved centrally in [staff/permissions.py](staff/permissions.py) via `resolve_tier(user)`.
- **Role** exists as a `Role` model with `name`, `slug`, optional `hotel`, optional `department`, and an M2M to `NavigationItem` (`default_navigation_items`). Roles carry **no action permissions** today — only nav defaults.
- **Department** already exists as a first-class model and is FK'd from both `Staff` and `Role`, but it is **not yet used in any authorization decision**.
- **Navigation items** act as a **hybrid UI-visibility + backend module gate** via `HasNavPermission(slug)`. Nav slugs are effectively pseudo-capabilities for "can see / use this module", but not for fine-grained action authority.
- **Action authority** is enforced by a second tier-based class family (`CanManageRooms`, `CanManageHousekeeping`, `CanManageStaff`, `CanManageStaffChat`, …). These classes check tier, not role, not capability.
- **Hotel scoping** is enforced in multiple layers: `IsSameHotel`, `HotelScopedQuerysetMixin`, and ad-hoc `.filter(hotel=staff.hotel)` calls in views.

**Mixture:** Tier-based + nav-slug-based + hotel-scoped. **Not** role-name-matching, **not** capability-based.

**Distance from target model:**

- ✅ Tier, Department, Role, Hotel scope — all present as models.
- ✅ Central resolvers (`resolve_tier`, `resolve_effective_access`) — clean seam to extend.
- ❌ No `Capability` model. Action authority is derived from tier only.
- ❌ Role is decorative for authorization (nav-only M2M, no permissions M2M).
- ❌ Department is a dangling FK — never consulted in any permission class.
- ⚠️ Nav slugs are doing double duty as UI labels **and** backend authorization keys.

**Top architectural risks blocking the target model:**

1. **Role does not carry authority.** Any move to role/department-driven authority needs a new source of truth. Today `Role.name` is a free-text display label in most serialized responses.
2. **Nav slug overload.** If capabilities are introduced, the relationship between nav slug and capability slug must be defined explicitly to avoid a third parallel system.
3. **Tier `access_level` is a string enum on `Staff`, not a FK.** Evolving the tier concept (e.g., adding tier-scoped capabilities) requires either keeping the enum or migrating to a `Tier` model.
4. **Duplicated hotel scoping patterns** (permission class / mixin / manual filter). Not a target-model blocker, but multiplies surface area to audit on every change.
5. **No seeded, canonical role presets.** Roles are created ad-hoc via provisioning and admin. A capability migration requires a canonical starter catalog.

Overall verdict up-front: **the target model can be introduced incrementally** without a rewrite. The central resolvers are the right extension seams.

---

## 2. Current staff authorization model

### 2.1 `Staff` model — [staff/models.py](staff/models.py)

Relevant fields (class `Staff`, approx. L119–L280):

| Field | Type | Purpose |
|---|---|---|
| `user` | `OneToOneField(User, related_name='staff_profile')` | Auth identity linkage. |
| `hotel` | `ForeignKey('hotel.Hotel')` **required** | Tenant scope. |
| `department` | `ForeignKey(Department, null=True, blank=True)` | Org grouping. **Not read by any permission class.** |
| `role` | `ForeignKey(Role, null=True, blank=True)` | Job title / nav preset. |
| `access_level` | `CharField(choices=ACCESS_LEVEL_CHOICES, default='regular_staff')` | **Tier string** — primary auth axis. |
| `allowed_navigation_items` | `ManyToManyField(NavigationItem)` | Per-staff nav override (additive). |
| `is_active`, `duty_status`, `is_on_duty`, `has_registered_face`, `fcm_token`, `profile_image`, `first_name`, `last_name`, `email`, `phone_number` | — | Non-auth metadata. |

`ACCESS_LEVEL_CHOICES`:

```python
ACCESS_LEVEL_CHOICES = [
    ('staff_admin', 'Staff Admin'),
    ('super_staff_admin', 'Super Staff Admin'),
    ('regular_staff', 'Regular Staff'),
]
```

Note: `'super_user'` is **not** a stored value on `Staff`. It is synthesized at resolve-time from `user.is_superuser`.

### 2.2 `Role` model — [staff/models.py](staff/models.py)

Fields (class `Role`, approx. L84–L115):

| Field | Type | Notes |
|---|---|---|
| `hotel` | `ForeignKey('hotel.Hotel', null=True, blank=True)` | Hotel-specific or global. |
| `department` | `ForeignKey(Department, null=True, blank=True)` | Optional org grouping. |
| `name` | `CharField(max_length=100)` | Human label (e.g., `"Waiter"`, `"porter"`, `"Manager"`). |
| `slug` | `SlugField(max_length=100)` | Normalized machine id — **already present**. |
| `description` | `TextField(blank=True, null=True)` | — |
| `default_navigation_items` | `ManyToManyField(NavigationItem, related_name='default_for_roles')` | The only authorization-relevant field on `Role` today. |

Meta:

```python
unique_together = [['hotel', 'name'], ['hotel', 'slug']]
```

### 2.3 Department concept — [staff/models.py](staff/models.py)

`Department` model exists (approx. L66–L81) with `hotel`, `name`, `slug`, `description`, unique `(hotel, name)` and `(hotel, slug)`. **It carries no permissions, nav items, or capabilities.** It is FK'd from `Staff.department` and `Role.department` but never consulted in permission classes. A helper `Staff.get_by_department(department)` exists at approx. L257 for querying.

### 2.4 Tier / access-level field

Stored as a **string CharField** on `Staff` (`access_level`). No `Tier` model exists. Canonical tier ordering is a Python tuple in [staff/permissions.py](staff/permissions.py):

```python
TIER_HIERARCHY = ('super_user', 'super_staff_admin', 'staff_admin', 'regular_staff')
```

### 2.5 Navigation item / permissions M2Ms

Two M2Ms to `NavigationItem`:

- `Role.default_navigation_items` — role-level defaults.
- `Staff.allowed_navigation_items` — per-staff overrides (additive).

No Django `Permission`/`Group` M2M is used for authorization. Django groups/permissions appear unused by the custom permission layer.

### 2.6 Django auth permissions/groups

Not used for staff authorization. `user.is_superuser` is used, but `user.groups` / `user.user_permissions` are **not** referenced in [staff/permissions.py](staff/permissions.py).

### 2.7 Are role names used directly in logic?

**No direct enforcement via role name strings in production permission classes.** All current authority checks route through `resolve_tier(user)` and tier hierarchy, or through nav-slug membership. Role name strings appear only in serialization / display / fixture code (see §4 for full inventory).

---

## 3. Current permission resolution flow

### 3.1 Authenticated user → staff identity

1. DRF `TokenAuthentication` (or equivalent) populates `request.user`.
2. `user.staff_profile` is the `OneToOneField` reverse accessor set on `Staff.user` with `related_name='staff_profile'`.
3. Convenience helpers:
   - `resolve_tier(user)` in [staff/permissions.py](staff/permissions.py) (approx. L56–L76).
   - `IsStaffMember` in [staff_chat/permissions.py](staff_chat/permissions.py) — checks `hasattr(user, 'staff_profile')`.

### 3.2 Hotel scoping

- **Permission-layer:** `IsSameHotel` in [staff_chat/permissions.py](staff_chat/permissions.py) resolves `view.kwargs['hotel_slug']` and compares to `request.user.staff_profile.hotel.slug`. Has `has_object_permission` for `Conversation` / `Message` / `Attachment`.
- **Mixin-layer:** `HotelScopedQuerysetMixin` in [common/mixins.py](common/mixins.py) (approx. L15–L37) sources hotel from `staff_profile.hotel`, filters queryset, and sets `hotel` on create.
- **Ad-hoc:** Many views (e.g., [rooms/views.py](rooms/views.py#L84-L94), [attendance/face_views.py](attendance/face_views.py#L192)) call `.filter(hotel=staff.hotel)` directly.
- **Hotel-specific:** `IsSuperStaffAdminForHotel` in [hotel/permissions.py](hotel/permissions.py) (approx. L38–L67) combines tier and hotel slug check.

### 3.3 Tier resolution

Single canonical function:

```python
# staff/permissions.py, approx L56
def resolve_tier(user) -> str | None:
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if user.is_superuser:
        return 'super_user'
    try:
        staff = user.staff_profile
        return staff.access_level
    except (AttributeError, Staff.DoesNotExist):
        return None
```

Comparison helper: `_tier_at_least(tier, minimum)` compares via position in `TIER_HIERARCHY`.

### 3.4 Navigation access resolution

Single canonical function — `resolve_effective_access(user)` in [staff/permissions.py](staff/permissions.py) (approx. L94–L170):

```
effective_slugs = TIER_DEFAULT_NAVS[tier]
               ∪ role.default_navigation_items.slugs
               ∪ staff.allowed_navigation_items.slugs
```

For `super_user` the effective set is **all active** `NavigationItem`s of the staff's hotel.

Returns a dict:

```python
{
  'is_staff', 'is_superuser', 'hotel_slug',
  'access_level', 'tier',
  'allowed_navs': [...slug strings...],
  'navigation_items': [...serialized NavigationItem dicts...]
}
```

Callers:
- [staff/views.py](staff/views.py) login endpoint (approx. L145–L148, L163, L173, L185).
- [staff/views.py](staff/views.py) staff update endpoint (approx. L1503–L1600).
- [staff/serializers.py](staff/serializers.py) `to_representation()` (approx. L330–L339).
- [staff/me_views.py](staff/me_views.py) `/me` endpoint (approx. L37–L47).

### 3.5 API permission class enforcement

Two enforcement layers applied in combination on each view:

1. **Module visibility** — `HasNavPermission(slug)` or its static subclasses (`HasRoomsNav`, `HasChatNav`, …).
2. **Action authority** — `CanManage*` classes enforce mutation-level tier gates (pass-through for safe methods).

Canonical example — [rooms/views.py](rooms/views.py#L44):

```python
permission_classes = [IsAuthenticated, HasRoomsNav, IsStaffMember, IsSameHotel]
# With CanManageRooms added for mutation endpoints.
```

### 3.6 Serializer / queryset / view-level restrictions

- **Serializer:** `StaffSerializer` attaches `resolve_effective_access` output in `to_representation`.
- **Queryset:** `HotelScopedQuerysetMixin` or manual filter (see 3.2).
- **View:** `permission_classes` list, or `get_permissions()` for dynamic gating (common pattern: mutate vs read).

### 3.7 FBVs, APIViews, ViewSets, mixins, decorators, helpers involved

- **ViewSets / APIViews:** compose permission classes in `permission_classes` (static) or `get_permissions()` (dynamic).
- **FBVs:** inline call `HasNavPermission('slug').has_permission(request, None)` plus a `CanManage*` check; multiple examples in [chat/views.py](chat/views.py).
- **Mixin:** `HotelScopedQuerysetMixin` ([common/mixins.py](common/mixins.py)).
- **Decorators:** none custom — DRF decorators only.
- **Helpers:** `resolve_tier`, `_tier_at_least`, `resolve_effective_access` (all in [staff/permissions.py](staff/permissions.py)); `is_chat_manager(staff)` in [staff_chat/permissions.py](staff_chat/permissions.py) (approx. L7–L14).

---

## 4. Current role usage audit

### 4.1 Where `Role` / `staff.role` is referenced

Role is referenced in **models, admin, serializers, views, notifications, and tests**. The following table lists every touchpoint found where `role.name` or `role.slug` is read. No location is using role for authorization decisions.

| File | Approx line | Usage | Purpose |
|---|---|---|---|
| [chat/models.py](chat/models.py) | 129 | `self.staff_role_name = self.staff.role.name` | Snapshots role name onto `ChatMessage`. |
| [chat/views.py](chat/views.py) | 588 | `'role': staff.role.name if staff.role else 'Staff'` | Response payload (display). |
| [chat/serializers.py](chat/serializers.py) | 170 | `obj.staff.role.name if obj.staff.role else 'Staff'` | Message sender role label. |
| [notifications/notification_manager.py](notifications/notification_manager.py) | 383 | `'role': staff.role.name if staff.role else None` | Realtime payload. |
| [notifications/test_porter_notifications.py](notifications/test_porter_notifications.py) | 32–33, 357–358 | `Role.objects.create(name="Porter", slug="porter")` | Test fixtures. |
| [staff/admin.py](staff/admin.py) | 169 | `return obj.role.name if obj.role else "-"` | Django admin column. |
| [staff/serializers.py](staff/serializers.py) | 264 | `return obj.role.slug if obj.role else None` | Uses **slug**, not name. |
| [staff/views.py](staff/views.py) | 163, 185 | `'role': staff.role.name if staff.role else None` | Login / debug response. |
| [staff/pusher_utils.py](staff/pusher_utils.py) | 69 | `'role': staff.role.name if staff.role else None` | Pusher broadcast payload. |
| [staff_chat/serializers_staff.py](staff_chat/serializers_staff.py) | 49, 104 | `obj.role.name if obj.role else None` | Staff list display. |
| [staff_chat/serializers_conversations.py](staff_chat/serializers_conversations.py) | 116 | `other.role.name if other.role else None` | Conversation partner display. |
| [staff_chat/serializers.py](staff_chat/serializers.py) | 79 | `'name': obj.role.name` | Message role detail. |

### 4.2 Display vs filtering vs enforcement

- **Display / serialization:** all occurrences above.
- **Filtering:** None found. No queryset filters by role name/slug for authorization purposes.
- **Enforcement:** **None.** No permission class checks role name or slug.

### 4.3 Casing / normalization risk

Current data (per user) contains mixed-casing values: `"Manager"`, `"porter"`, `"Waiter"`. Since no code compares role name strings for authorization, this is **not a current security risk**, but it is a **data-quality risk** that matters as soon as any logic starts relying on role identity.

`Role.slug` already exists and could act as the normalized machine id, but it is **not always populated consistently** (no enforced generator in the model). No occurrence of `role.name.lower()` was found in permission / business logic.

### 4.4 Hotel-specific vs global roles

`Role.hotel` is nullable. Design permits both per-hotel and cross-hotel (null-hotel) roles. Uniqueness is `(hotel, name)` / `(hotel, slug)`; with `hotel=None` these act as global uniques.

In practice, almost all `Role` rows are hotel-scoped via the provisioning flow. No cross-hotel role sharing logic was found.

### 4.5 Shared roles

`Role` is FK'd from `Staff.role`, so multiple staff can share one role row (many-to-one). No uniqueness constraint preventing that.

### 4.6 Do roles carry permissions today?

**No.** The only authorization-relevant attachment on `Role` is `default_navigation_items` (nav slugs — module visibility). `Role` has no M2M to permission strings, no capability list, and no action flags. From an authority perspective, `Role` is currently a **nav preset + display label**.

### 4.7 Role-name string matching in enforcement

**Not found.** Grep for `role.name ==`, `role.name in [`, `role.slug ==` across production code returns no authorization check. The earlier `role.slug in ['manager', 'admin']` pattern in staff chat was previously removed and is now `CanManageStaffChat` (tier-based). See [staff/permissions.py](staff/permissions.py) approx. L439–L451.

---

## 5. Current navigation-based authorization audit

### 5.1 Models involved

- `NavigationItem` — [staff/models.py](staff/models.py) approx L12–L59. Fields: `hotel` (FK, required), `name`, `slug`, `path`, `description`, `display_order`, `is_active`, `created_at`, `updated_at`. Unique `(hotel, slug)`.
- `Role.default_navigation_items` M2M — role-level defaults.
- `Staff.allowed_navigation_items` M2M — per-staff overrides.

### 5.2 Canonical slug catalog

[staff/nav_catalog.py](staff/nav_catalog.py):

```python
CANONICAL_NAV_SLUGS = frozenset({
    'home', 'rooms', 'room_bookings', 'restaurant_bookings', 'chat',
    'housekeeping', 'attendance', 'staff_management',
    'room_services', 'maintenance', 'hotel_info', 'admin_settings',
})
```

Seeded per hotel by [staff/management/commands/seed_navigation_items.py](staff/management/commands/seed_navigation_items.py). Legacy slugs (`'entertainment'`, `'stock_tracker'`, `'reception'`, earlier `'bookings'`) are deactivated via `is_active=False`.

### 5.3 Effective nav resolution

See §3.4 — `resolve_effective_access(user)` is the single source. Result includes `allowed_navs` (list of slugs) and `navigation_items` (serialized items). Additional filter: only `NavigationItem.objects.filter(hotel=staff.hotel, is_active=True)` are considered — so deactivated slugs cannot leak even if an M2M row exists.

### 5.4 Are nav items acting as authorization keys?

**Yes — as a module gate.** `HasNavPermission(slug)` ([staff/permissions.py](staff/permissions.py) approx. L178–L210) is mounted on every staff-facing ViewSet / APIView to enforce "can this tier+role see/use this module?".

It does **not** grant mutation rights. Mutations additionally require a `CanManage*` tier check. Comment in the class explicitly enforces this contract:

> "This class enforces module VISIBILITY only — it does NOT grant mutation authority. Every mutation endpoint MUST additionally use an action-level permission class (CanManage*, IsSuperStaffAdminOrAbove, etc.)."

### 5.5 Endpoints / permission classes depending on nav slugs

All 14 static subclasses in [staff/permissions.py](staff/permissions.py) approx. L347–L401:

- `HasHomeNav`, `HasChatNav`, `HasRoomsNav`, `HasRoomBookingsNav`, `HasRestaurantBookingsNav`, `HasHousekeepingNav`, `HasMaintenanceNav`, `HasAttendanceNav`, `HasStaffManagementNav`, `HasRoomServicesNav`, `HasHotelInfoNav`, `HasAdminSettingsNav`.

Used across at least: [rooms/views.py](rooms/views.py), [bookings/views.py](bookings/views.py), [housekeeping/views.py](housekeeping/views.py), [attendance/views.py](attendance/views.py), [room_services/views.py](room_services/views.py), [staff_chat/views.py](staff_chat/views.py), [chat/views.py](chat/views.py), [home/views.py](home/views.py), [hotel/staff_views.py](hotel/staff_views.py).

### 5.6 Frontend contract on nav slugs

Serializers return both `allowed_navs` (slug list) and `navigation_items` (full objects). Frontend almost certainly renders UI from these. Because the **same slug set is the backend gate**, slug changes are a dual-risk contract: a silent rename breaks both UI and backend enforcement simultaneously.

### 5.7 Overloaded role of navigation

**Yes, navigation is overloaded.** A single slug string drives:

1. Sidebar visibility on the frontend (UI).
2. Backend module access check (`HasNavPermission`).
3. Role-to-modules mapping (`Role.default_navigation_items`).
4. Per-staff override grants (`Staff.allowed_navigation_items`).

**Risk:** If a new module needs to be granted to only some staff at a role tier that normally cannot see it, the only handle today is per-staff override. There is no clean capability concept like `bookings.edit_restaurant_booking` independent of the sidebar. This constrains product flexibility and conflates UX with authorization.

---

## 6. Hotel scoping audit

### 6.1 Custom permission classes

- [staff_chat/permissions.py](staff_chat/permissions.py) — `IsSameHotel` (hotel_slug from `view.kwargs`), `IsStaffMember`, `is_chat_manager(staff)` helper.
- [hotel/permissions.py](hotel/permissions.py) — `IsSuperStaffAdminForHotel` combines tier + hotel.
- [staff/permissions.py](staff/permissions.py) — tier gates; hotel scoping is expected to be layered on by the view.

### 6.2 Queryset filtering

- **Mixin:** `HotelScopedQuerysetMixin` in [common/mixins.py](common/mixins.py) (approx. L15–L37) — sources hotel from `staff_profile.hotel`, filters `get_queryset()` and stamps `hotel` on create.
- **Manual filter:** many views, e.g. [rooms/views.py](rooms/views.py) `get_queryset` (approx. L84–L94), [attendance/face_views.py](attendance/face_views.py#L192). The pattern is consistent in spirit but redundant in form.

### 6.3 Serializer validation

No dedicated "hotel is mine" serializer validation layer was found. Hotel assignment is generally controlled at view level (`perform_create`) and at the queryset level. Serializers serialize `hotel` but do not re-validate ownership.

### 6.4 URL-scoped hotel slug logic

Used explicitly by `IsSameHotel` and `IsSuperStaffAdminForHotel` via `view.kwargs.get('hotel_slug')` / `'hotel_identifier'`. Many URL patterns embed `<slug:hotel_slug>` (staff-scoped URLs in [staff_urls.py](staff_urls.py) and per-app `staff_urls.py`).

### 6.5 Helper methods that confirm same hotel

- `IsSameHotel.has_permission` — URL-slug-vs-staff-hotel compare.
- `IsSameHotel.has_object_permission` — traverses `obj.hotel` or `obj.conversation.hotel`.
- `HotelScopedQuerysetMixin.get_hotel()` — raises `PermissionDenied` if no staff profile.

### 6.6 Known weak spots

- **Legacy chat URLs:** prior audits ([GUEST_STAFF_CHAT_REALTIME_AUDIT.md](GUEST_STAFF_CHAT_REALTIME_AUDIT.md), [FULL_BACKEND_DISCOVERY.md](FULL_BACKEND_DISCOVERY.md)) note that `/api/chat/<slug>/` used the same FBVs as `/api/staff/hotel/<slug>/chat/` without equivalent wrapper enforcement. The RBAC Wave 2 pass added inline hotel scoping to 6 chat FBVs (see repo memory `/memories/repo/rbac_wave1_status.md`), but contract-level duplication of URL surface remains a risk worth re-verifying.
- **Ad-hoc `.filter(hotel=staff.hotel)` without permission class:** easy to forget on new endpoints. Searchable pattern `AllowAny` + staff models should be reviewed case-by-case (guest-facing endpoints explicitly left `AllowAny`).
- **No serializer-layer cross-hotel guard:** a malicious payload setting `hotel_id` to another hotel could slip through if a view doesn't re-stamp hotel on create. `HotelScopedQuerysetMixin.perform_create` mitigates, but not every writable view uses it.

---

## 7. Department readiness audit

### 7.1 Existing assets

- `Department` model exists ([staff/models.py](staff/models.py) approx. L66–L81). Fields: `hotel`, `name`, `slug`, `description`; unique `(hotel, name)` and `(hotel, slug)`.
- `Staff.department` FK exists.
- `Role.department` FK exists.
- `Staff.get_by_department(department)` helper exists (approx. L257).
- `DepartmentSerializer` exists in [staff/serializers.py](staff/serializers.py) (approx. L40–L62).

### 7.2 Assets missing

- No canonical department catalog (no `CANONICAL_DEPARTMENT_SLUGS`, no seed command analogous to `seed_navigation_items.py`).
- No permission class references `Department`.
- No effective-access resolver reads `department`.
- No serializer returns a department slug/id in the top-level user auth payload (`resolve_effective_access` does not surface department).
- No frontend contract for department-scoped access.

### 7.3 Team / section / unit concepts

Searched for `team`, `section`, `unit`, `category`, `group` on Staff and Role: **none used for org grouping**. Only `Role.description` and `Department` are relevant.

### 7.4 Role families or nav clusters mappable to departments

Nav slugs cluster naturally to departments:

| Nav slugs | Target department |
|---|---|
| `rooms`, `housekeeping`, `maintenance` | `housekeeping` / `maintenance` / `rooms_ops` |
| `restaurant_bookings`, `room_services` | `food_beverage` |
| `room_bookings`, `hotel_info` | `front_office` |
| `chat`, `home` | cross-department / all |
| `attendance`, `staff_management`, `admin_settings` | `administration` / `management` |

This is an **implicit clustering only** — no code ties nav slugs to departments today.

### 7.5 Where should `department` live?

Already on both `Staff` and `Role`. This is sensible:

- **Role-level department** = default/canonical organizational home for that job title.
- **Staff-level department** = actual assignment for that individual (overrides role default).

Recommended: **keep both**, resolve staff's effective department as `staff.department or staff.role.department or None` inside a helper.

### 7.6 What data could be migrated

Current `Role` rows (`"Manager"`, `"porter"`, `"Waiter"`) can be mapped by hand into a canonical starter department set. This is **small-volume, one-time data migration** territory — manageable via a management command or data migration.

### 7.7 What logic becomes cleaner with departments

- Roster/schedule filtering ("show all housekeeping on-duty").
- Staff-chat "@department" broadcasts.
- Department-scoped dashboards without relying on nav slugs.
- "Department lead" tier (staff_admin restricted to their department).

---

## 8. Capability readiness audit

### 8.1 Existing capability-like surfaces

- **Nav slugs** (`CANONICAL_NAV_SLUGS`) — act as pseudo-capabilities for "can see/use module X".
- **`CanManage*` classes** (e.g., `CanManageRooms`, `CanManageBookings`, `CanManageHousekeepingStaff`) — each is effectively "capability X" but currently computed from tier only.
- **Effective access dict** — `allowed_navs` is the closest thing to a capability list exposed to the frontend.
- **Helper `is_chat_manager(staff)`** — encapsulates one implicit capability ("can moderate staff chat").

### 8.2 What cannot be reused safely

- **Raw `access_level` string comparisons** (e.g., [hotel/permissions.py](hotel/permissions.py#L67) `if staff.access_level != 'super_staff_admin'`) — should not be extended, should be refactored to `resolve_tier` + `_tier_at_least`.
- **Role name strings** in serialized payloads — not a capability source.
- **Django permissions/groups** — not currently wired; reintroducing them would be a third parallel system.

### 8.3 Can nav slugs serve as a temporary migration bridge?

Yes — with discipline:

- Short-term: treat each nav slug as a coarse-grained capability (`nav:rooms`, `nav:bookings`, …).
- Introduce fine-grained capabilities (`bookings.edit_restaurant_booking`) in a new `Capability` model, and make each `CanManage*` class check **both** (tier + explicit capability) during migration.
- Freeze the nav-slug contract (don't add new slugs) while capabilities take over mutation authority.

### 8.4 Cleanest canonical source of capabilities

Given the codebase, the cleanest approach is:

- Define `capabilities.py` (parallel to [staff/nav_catalog.py](staff/nav_catalog.py)) with a frozenset of canonical capability slugs.
- Add `Capability` model with FK `hotel` (nullable for global) and `slug` (unique) — mirror `NavigationItem`'s shape.
- Add M2Ms: `Role.capabilities`, `Staff.extra_capabilities`.
- Extend `resolve_effective_access(user)` to compute and return `effective_capabilities`.
- Rewire `CanManage*` classes to check tier **or** capability membership, configurable.

---

## 9. Dangerous coupling and anti-patterns

| ID | Issue | Location | Why it's dangerous |
|---|---|---|---|
| D1 | Raw `access_level` string comparison | [hotel/permissions.py](hotel/permissions.py) approx. L67: `if staff.access_level != 'super_staff_admin'` | Bypasses `TIER_HIERARCHY` — a future tier (e.g., `'platform_admin'`) won't grant access even if semantically above. Should call `resolve_tier` + `_tier_at_least`. |
| D2 | Nav slug overload | [staff/permissions.py](staff/permissions.py) `HasNavPermission`, `resolve_effective_access` | Same identifier governs UI sidebar, role defaults, per-staff overrides, and backend module gate. Any rename is a quadruple-contract break. |
| D3 | `Role.name` mixed casing exposed to frontend | [chat/views.py](chat/views.py#L588), [staff_chat/serializers_conversations.py](staff_chat/serializers_conversations.py#L116), [notifications/notification_manager.py](notifications/notification_manager.py#L383) | Values like `"Manager"` vs `"porter"` ship to UI. If any frontend gating checks `role.name`, case + spacing is unsafe. |
| D4 | Duplicated hotel scoping patterns | `HotelScopedQuerysetMixin` in [common/mixins.py](common/mixins.py) vs manual `.filter(hotel=staff.hotel)` in [rooms/views.py](rooms/views.py), [attendance/face_views.py](attendance/face_views.py) | Three patterns (mixin, permission class `IsSameHotel`, manual filter). New endpoints can pick any combination — audit surface multiplies. |
| D5 | `Role` has no permissions M2M | [staff/models.py](staff/models.py) L84–L115 | Any "give porters the right to X" request has nowhere to live except `allowed_navigation_items`, which isn't capability-grained. |
| D6 | Department is a dangling FK | [staff/models.py](staff/models.py) L66–L81 | Present on `Staff` and `Role`, but read by no permission class. Creates a silent illusion of org structure. |
| D7 | `access_level` is a string enum, not FK | [staff/models.py](staff/models.py) | Adding tier-scoped metadata (display label, allowed caps) requires parallel dicts in Python rather than DB rows. |
| D8 | No canonical role presets / seed command | No `seed_roles.py`; only [staff/management/commands/seed_navigation_items.py](staff/management/commands/seed_navigation_items.py) | Role data entered hotel-by-hotel leads to naming drift (`"porter"` vs `"Porter"`). |
| D9 | Possible stale legacy chat URL surface | [chat/urls.py](chat/urls.py) vs [chat/staff_urls.py](chat/staff_urls.py) (per project architecture memory, chat/urls.py 100% duplicates chat/staff_urls.py) | Redundant URL surfaces risk inconsistent enforcement contracts even after inline scoping is added. |
| D10 | Frontend may compensate for role-name ambiguity | Not seen in backend, but payloads ship both `role.name` and `tier`/`allowed_navs` | If frontend uses `role.name` for gating, **frontend is the de-facto auth source for that feature**. Backend can't know. |

---

## 10. Gap analysis: current state vs target model

| Target layer | Exists | Partial | Missing | Reusable as-is | Should deprecate |
|---|---|---|---|---|---|
| **Tier** (seniority) | ✅ `Staff.access_level`, `TIER_HIERARCHY`, `resolve_tier` | `access_level` is a string, not FK | A proper `Tier` model (optional improvement) | `resolve_tier`, `_tier_at_least`, `TIER_HIERARCHY` | Raw string comparisons outside `resolve_tier` |
| **Department** (operational domain) | ✅ `Department` model, FKs on `Staff` and `Role`, `DepartmentSerializer` | — | Canonical slug catalog, seed command, effective-access surfacing, any permission logic | `Department` model, FKs, serializer | — |
| **Role** (job title / preset) | ✅ `Role` model with `name`, `slug`, optional `hotel`, optional `department` | `slug` not always consistently normalized | Canonical role presets, slug normalization enforcement, capabilities M2M | `Role` model shape, `default_navigation_items` M2M (for bridge period) | Using `role.name` anywhere that isn't display |
| **Capability** (real enforcement key) | ❌ | Nav slugs act as coarse pseudo-capabilities via `HasNavPermission` | `Capability` model, canonical catalog, M2Ms to `Role` and `Staff`, effective-capability resolver | `HasNavPermission` as a compat shim while migrating | Tier-only `CanManage*` decisions once caps exist |
| **Hotel scope** (isolation) | ✅ `Staff.hotel`, `IsSameHotel`, `HotelScopedQuerysetMixin`, `IsSuperStaffAdminForHotel` | Three patterns coexist (mixin / perm class / manual filter) | A single canonical mixin+perm combo the team commits to | All three — they're compatible | Gradually remove manual `.filter(hotel=…)` in favor of mixin |

---

## 11. Migration proposal — phased and low-risk

### Phase A — stabilization

- Normalize existing `Role` rows: regenerate `Role.slug` from `slugify(name)` and lowercase `name` or adopt a canonical title-case policy. Add a pre-save signal to enforce slug derivation.
- Audit every serializer that emits `role.name`; ensure frontend is not doing name-string gating. Document the contract: **only `tier`, `access_level`, and `allowed_navs` are trusted for gating**.
- Replace `if staff.access_level != 'super_staff_admin'` in [hotel/permissions.py](hotel/permissions.py#L67) with `resolve_tier` + `_tier_at_least`.
- Confirm Wave 2 inline hotel scoping on legacy chat URLs is complete; drop any genuinely unused URL surface (see D9 and project architecture memory).

**Can remain:** all existing enforcement, nav slugs, `CanManage*` classes.
**Biggest risk:** frontend drift on `role.name` — catch before Phase C.
**Order:** do before introducing any new model.

### Phase B — canonical departments

- Add `CANONICAL_DEPARTMENT_SLUGS` catalog (`front_office`, `housekeeping`, `food_beverage`, `maintenance`, `guest_relations`, `management`, `administration`).
- Add a `seed_departments.py` management command analogous to `seed_navigation_items.py`.
- Backfill `Role.department` for existing roles via a data migration (manual mapping table).
- Extend `resolve_effective_access` return payload with `department_slug` (derived from `staff.department or staff.role.department`).
- Update `StaffSerializer` to expose department to the frontend.

**Can remain:** no permission class needs to read `department` yet.
**Biggest risk:** backfill mapping for existing production `Role` rows; keep this as a reviewable data migration, not auto-inferred.
**Order:** second. Decouples from capability work.

### Phase C — capability layer

- Introduce `Capability` model (hotel nullable; slug unique per scope). Parallel to `NavigationItem` in shape.
- Add `CAPABILITY_SLUGS` canonical catalog covering every action-level tier gate currently enforced by `CanManage*`.
- Add M2Ms: `Role.capabilities`, `Staff.extra_capabilities`.
- Extend `resolve_effective_access` with `effective_capabilities = tier_default_caps ∪ role.capabilities ∪ staff.extra_capabilities`.
- Seed tier-default capabilities (e.g., `super_staff_admin` gets all; `staff_admin` gets a subset; `regular_staff` minimal).
- Keep nav slugs as a parallel "module visibility" surface — do **not** collapse them into capabilities.

**Can remain:** `CanManage*` classes untouched in Phase C. They still pass on tier alone.
**Biggest risk:** defining the canonical capability list — over-granularize and the table explodes; under-granularize and you rebuild nav slugs.
**Order:** third. Requires departments to be stable for "department-scoped capability" concepts later.

### Phase D — permission enforcement cleanup

- Rewire each `CanManage*` class to check `capability` membership **in addition to** tier (fallback OR during migration, then capability-primary once coverage is proven).
- Consolidate hotel scoping on `HotelScopedQuerysetMixin` + `IsSameHotel` (drop manual `.filter(hotel=…)` in favor of mixin where practical).
- Remove the `hotel/permissions.py` `IsSuperStaffAdminForHotel` string comparison (Phase A) and replace with `IsSuperStaffAdminOrAbove` + `IsSameHotel`.

**Can remain:** `HasNavPermission` stays — module visibility is a distinct concern.
**Biggest risk:** silently removing a tier fallback before capability coverage is complete.
**Order:** fourth. Requires Phase C catalog to be stable.

### Phase E — frontend contract alignment

- Extend `/me` and login payloads to include:
  - `tier`
  - `department_slug`
  - `role_slug` (not `role.name`)
  - `allowed_navs` (unchanged)
  - `allowed_capabilities` (new)
- Frontend gates UI on capabilities where fine-grained, nav slugs where coarse.
- Deprecate any `role.name` string consumption on the frontend.

**Can remain:** backward-compatible payload fields shipped alongside new ones for a release or two.
**Biggest risk:** frontend implicitly consuming a removed field — keep old fields during a deprecation window.
**Order:** last.

---

## 12. Concrete recommendations for data model design

Grounded in current `Staff`, `Role`, `Department`, `NavigationItem`:

### `Department`

Already good. Add a canonical slug catalog + seed command. Consider a `display_order` field for UI consistency with `NavigationItem`. Keep `hotel` FK nullable if cross-hotel departments may exist (recommended: per-hotel rows even for canonical slugs, mirroring NavItem pattern).

### `Role`

- Keep FK to `Department` (nullable) — role's canonical home department.
- Enforce `slug` normalization via a pre-save signal (`slugify(name)`) so `"porter"`, `"Porter"`, `"PORTER"` all collapse.
- Add `is_preset` boolean to distinguish canonical starter roles from hotel-custom ones.
- Add M2M `capabilities` (new — see below).
- Keep `default_navigation_items` M2M — it is the module-visibility preset, not a capability.

### Role slug normalization

Pre-save signal or overridden `save()`:

```
Role.slug = slugify(Role.name) if not Role.slug else Role.slug
```

Plus a `clean()` to enforce `slug == slugify(name)` for preset roles.

### Capability source of truth

- New `Capability` model: `slug` (unique, canonical), `name` (display), `description`, optional `category` (e.g., `bookings`, `rooms`, `staff`).
- Canonical list in `staff/capability_catalog.py` parallel to `staff/nav_catalog.py`.
- Seed command `seed_capabilities.py`.
- Hotel-scoping: likely **global** (not per-hotel) — capabilities are product primitives, not tenant data.

### Role ↔ Department

- Keep `Role.department` FK (nullable). Role's default / canonical home.
- Allow role to span departments only when explicitly null.

### Staff ↔ Role

- Keep `Staff.role` FK (nullable) as today.
- Do not require role for authorization to work — tier alone must still be sufficient for baseline.

### Staff ↔ Capabilities

- M2M `Staff.extra_capabilities` for per-staff additive grants (analog to `allowed_navigation_items`).
- Do not introduce `Staff.denied_capabilities` — the additive-only model is simpler and matches the current nav model.

### Department on `Staff` vs `Role`

- **Keep both.** `Staff.department` = actual assignment (operational truth). `Role.department` = canonical home.
- Effective department: `staff.department or (staff.role.department if staff.role else None)`.

### Hotel-specific vs global definitions

- `Capability` = global (product-level).
- `Department` = per-hotel rows, but with a canonical slug set (same pattern as `NavigationItem`).
- `Role` = per-hotel (`hotel` FK) to allow customization, optionally marked `is_preset` when matching canonical presets.
- `NavigationItem` = per-hotel (unchanged).

---

## 13. Files to inspect

Already inspected or referenced in this audit. Extend if needed during implementation phases.

### Staff / auth core
- [staff/models.py](staff/models.py) — `Staff`, `Role`, `Department`, `NavigationItem`.
- [staff/permissions.py](staff/permissions.py) — `resolve_tier`, `resolve_effective_access`, `HasNavPermission`, tier gates, `CanManage*` classes, static nav subclasses.
- [staff/serializers.py](staff/serializers.py) — `DepartmentSerializer`, `StaffSerializer.to_representation` integration with effective access.
- [staff/views.py](staff/views.py) — login, `/staff/update/...`.
- [staff/me_views.py](staff/me_views.py) — `/me`.
- [staff/nav_catalog.py](staff/nav_catalog.py) — canonical nav slugs.
- [staff/management/commands/seed_navigation_items.py](staff/management/commands/seed_navigation_items.py) — nav seeding + legacy deactivation.
- [staff/admin.py](staff/admin.py) — admin display of role.
- [staff/pusher_utils.py](staff/pusher_utils.py) — role name in broadcasts.

### Common
- [common/mixins.py](common/mixins.py) — `HotelScopedQuerysetMixin`.

### Hotel
- [hotel/permissions.py](hotel/permissions.py) — `IsSuperStaffAdminForHotel` (contains D1).
- [hotel/provisioning.py](hotel/provisioning.py) — provisioning flow that creates first `Staff` + `Role` + `Department`.
- [hotel/staff_views.py](hotel/staff_views.py) — preset endpoints.

### Staff chat
- [staff_chat/permissions.py](staff_chat/permissions.py) — `IsStaffMember`, `IsSameHotel`, `is_chat_manager`.
- [staff_chat/serializers_staff.py](staff_chat/serializers_staff.py), [staff_chat/serializers_conversations.py](staff_chat/serializers_conversations.py), [staff_chat/serializers.py](staff_chat/serializers.py) — role.name exposure.

### Chat
- [chat/models.py](chat/models.py) — `staff_role_name` snapshot field.
- [chat/views.py](chat/views.py), [chat/serializers.py](chat/serializers.py) — role.name exposure.
- [chat/urls.py](chat/urls.py) / [chat/staff_urls.py](chat/staff_urls.py) — legacy URL duplication.

### Notifications
- [notifications/notification_manager.py](notifications/notification_manager.py) — role.name in payloads.

### Representative app views (permission patterns)
- [rooms/views.py](rooms/views.py)
- [bookings/views.py](bookings/views.py)
- [housekeeping/views.py](housekeeping/views.py)
- [attendance/views.py](attendance/views.py), [attendance/face_views.py](attendance/face_views.py)
- [room_services/views.py](room_services/views.py)
- [home/views.py](home/views.py)

### Prior audits / context
- [RBAC_PERMISSION_AUDIT.md](RBAC_PERMISSION_AUDIT.md)
- [FULL_BACKEND_DISCOVERY.md](FULL_BACKEND_DISCOVERY.md)
- [GUEST_STAFF_CHAT_REALTIME_AUDIT.md](GUEST_STAFF_CHAT_REALTIME_AUDIT.md)

---

## 14. Final verdict

- **Can the target model be introduced incrementally?** Yes. The central resolvers (`resolve_tier`, `resolve_effective_access`) are the correct extension seams. `Department` already exists. Adding `Capability` is an additive change with a safe fallback (tier-based `CanManage*` remains valid until capability coverage is proven).
- **Is the current backend close enough to migrate without a major rewrite?** Yes. No permission class does raw role-name matching. Hotel scoping, tier resolution, and nav-based module gating are already canonical. The biggest risk is **frontend role-name dependence**, which is out-of-scope here but must be surveyed before Phase C.
- **Single most important backend decision to make next, before any frontend work:**
  **Define the canonical `Capability` slug catalog and decide whether `NavigationItem` slugs are a temporary bridge or a permanent parallel "module visibility" surface.** Everything else — department seeding, role slug normalization, `CanManage*` rewiring — follows from that decision. Delaying it forces every subsequent phase into a guess about the final contract.
