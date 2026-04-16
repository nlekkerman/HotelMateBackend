# RBAC & Permission Architecture Audit

**Date**: 2026-04-12  
**Scope**: Full backend permission system — sources, resolution, extensibility, gaps

---

## 1. Permission Sources Found

### A. Canonical Permission Module — `staff/permissions.py`

**Single source of truth for:**

| Concern | Implementation |
|---------|----------------|
| Tier resolution | `resolve_tier(user)` → `super_user`, `super_staff_admin`, `staff_admin`, `regular_staff`, `None` |
| Effective nav access | `resolve_effective_access(user)` → union of tier + role + staff overrides |
| Module visibility gates | `HasNavPermission(slug)` + 11 static subclasses |
| Action-level gates | 7 `CanManage*` classes (Roster, Staff, Rooms, RoomBookings, RestaurantBookings, ConfigureHotel, Housekeeping) |
| Tier gates | `IsDjangoSuperUser`, `IsAdminTier`, `IsSuperStaffAdminOrAbove` |
| Tier hierarchy | `TIER_HIERARCHY = ('super_user', 'super_staff_admin', 'staff_admin', 'regular_staff')` |
| Tier default navs | `TIER_DEFAULT_NAVS` dict per tier |

### B. Nav Catalog — `staff/nav_catalog.py`

14 canonical slugs in `CANONICAL_NAV_SLUGS` frozenset + full `CANONICAL_NAV_ITEMS` definitions.

### C. Data Models — `staff/models.py`

| Model | Permission Role |
|-------|-----------------|
| `NavigationItem` | Per-hotel nav slugs (hotel, slug, is_active) |
| `Role` | `default_navigation_items` M2M → NavigationItem |
| `Staff` | `access_level` (tier), `role` FK, `allowed_navigation_items` M2M (override) |

### D. Secondary Permission Files

| File | Classes | Issues |
|------|---------|--------|
| `hotel/permissions.py` | `IsHotelStaff`, `IsSuperStaffAdminForHotel` | `IsSuperStaffAdminForHotel` hardcodes `access_level != 'super_staff_admin'` directly, does NOT call `resolve_tier()`, does NOT grant access to Django superusers |
| `staff_chat/permissions.py` | `IsStaffMember`, `IsSameHotel`, `IsConversationParticipant`, `IsMessageSender`, `is_chat_manager()` | `is_chat_manager()` hardcodes `role.slug in ('manager', 'admin')` |
| `housekeeping/policy.py` | `is_manager()`, `is_housekeeping()`, `can_change_room_status()` | `is_manager()` hardcodes `access_level in ['staff_admin', 'super_staff_admin']` + direct `is_superuser` check; `is_housekeeping()` hardcodes `role.slug == 'housekeeping'` and `department.slug == 'housekeeping'` |

### E. Inline Permission Checks (Non-Centralized)

**staff/views.py** — 12+ inline `access_level ==` or `access_level in (...)` checks throughout view methods (lines 189, 326, 735, 847, 1004, 1058, 1074, 1251, 1355, 1546, 1623, 1725).

**stock_tracker/views.py** — 14+ inline `access_level` / `is_superuser` checks.

**entertainment/views.py** — Uses `request.user.is_staff` (Django's generic boolean) instead of access_level or resolve_tier.

---

## 2. Effective Access Resolution Formula

### Canonical Formula (`resolve_effective_access` in `staff/permissions.py`)

```
effective_navs = tier_defaults ∪ role_defaults ∪ staff_overrides
```

**Step-by-step:**

1. **Resolve tier** via `resolve_tier(user)`:
   - `user.is_superuser` → `'super_user'`
   - else `staff.access_level` → one of `('super_staff_admin', 'staff_admin', 'regular_staff')`
   - no staff profile → `None`

2. **If `super_user`**: effective = ALL active `NavigationItem` rows for the hotel. Done.

3. **Otherwise, union**:
   - `tier_navs` = `TIER_DEFAULT_NAVS[tier]` (hardcoded set per tier)
   - `role_navs` = `staff.role.default_navigation_items` filtered by `hotel + is_active`
   - `override_navs` = `staff.allowed_navigation_items` filtered by `hotel + is_active`

4. **Filter**: only items where `slug ∈ effective_slugs AND is_active=True` in the hotel's `NavigationItem` table

### What fields are read, in order:

| Order | Source | Field(s) | Effect |
|-------|--------|----------|--------|
| 1 | `User` | `is_superuser` | Full access bypass |
| 2 | `Staff` | `access_level` | Selects tier default set |
| 3 | `Role` | `default_navigation_items` | Additive union |
| 4 | `Staff` | `allowed_navigation_items` | Additive union |
| 5 | `NavigationItem` | `is_active` | Suppressive filter |

### Conflict resolution:

- **Additive only** — there is NO subtraction/removal mechanism
- A nav granted by tier OR role OR staff override is included
- If a `NavigationItem.is_active = False`, it is suppressed regardless of who granted it
- There is no "deny" or "exclude" concept

### Frontend consumption:

- `resolve_effective_access()` is called by the `staff-permissions` endpoint
- Returns `allowed_navs` (list of slug strings) + `navigation_items` (serialized objects)
- Frontend uses this to render sidebar/navigation
- Frontend does NOT independently compute permissions

---

## 3. Current Role/Tier Extensibility Assessment

### Can a new role be created without adding hardcoded checks in Python views?

**PARTIALLY.** Nav visibility works cleanly — new roles inherit tier defaults and can define their own `default_navigation_items`. But:

- **staff_chat**: `is_chat_manager()` and 4 inline checks hardcode `role.slug in ('manager', 'admin')`. A new "head_of_ops" role with management authority will NOT be recognized.
- **housekeeping/policy.py**: `is_housekeeping()` hardcodes `role.slug == 'housekeeping'`. New housekeeping-adjacent roles are excluded.
- **Action permissions**: All `CanManage*` classes gate on **tier only** (access_level), not role. So a new role can't independently gain action permissions — it must be assigned the right tier.

### Can a new role define its own default nav access?

**YES.** `Role.default_navigation_items` M2M works correctly. The `resolve_effective_access()` union picks these up automatically.

### Can a new role automatically inherit tier behavior?

**YES for nav visibility** — tier defaults are unioned. **NO for action authority** — action classes check tier (access_level) only, and a role cannot elevate or override its tier.

### Places where logic is tied to specific role names or tier names:

| Location | Hardcoded Value | Impact |
|----------|-----------------|--------|
| `staff_chat/permissions.py:12` | `role.slug in ('manager', 'admin')` | New management roles excluded |
| `staff_chat/views_messages.py:482,491` | `role.slug in ['manager', 'admin']` | Delete/hard-delete blocked for new roles |
| `staff_chat/views_attachments.py:285` | `role.slug in ['manager', 'admin']` | Attachment deletion blocked |
| `housekeeping/policy.py:54` | `role.slug == 'housekeeping'` | New housekeeping roles excluded |
| `housekeeping/policy.py:30` | `access_level in ['staff_admin', 'super_staff_admin']` | Duplicates centralized logic |
| `hotel/permissions.py:63` | `access_level != 'super_staff_admin'` | Bypasses resolve_tier, excludes Django superusers |
| `entertainment/views.py:657,680` | `request.user.is_staff` | Uses Django's generic is_staff, not HotelMate tiers |

### Places where permission checks depend on admin/staff booleans instead of capabilities:

| Location | Boolean Check | Should Be |
|----------|---------------|-----------|
| `entertainment/views.py:657,680` | `request.user.is_staff` | `resolve_tier()` or `CanManage*` |
| `staff/serializers.py:352-355` | `is_superuser` conflated with `access_level` | These are orthogonal concepts |
| Multiple in `staff/views.py` | `user.is_superuser` (12+ locations) | Should use `IsDjangoSuperUser` or `resolve_tier()` at class level |

---

## 4. Domain Permission Matrix

| Domain | Nav Slug | View Permission | Manage Permission | Enforcement | View/Manage Split |
|--------|----------|-----------------|-------------------|-------------|-------------------|
| **Home** | `home` | `HasHomeNav + IsStaffMember + IsSameHotel` | Same as view (any staff can post) | Class-level | ❌ No — all staff with nav can CUD posts |
| **Chat (Guest↔Staff)** | `chat` | `HasNavPermission('chat')` inline | Same as view | Inline in FBVs | ❌ No manage gate |
| **Chat (Staff↔Staff)** | `chat` | `HasChatNav + IsStaffMember + IsSameHotel` | Hardcoded `role.slug in ['manager','admin']` for delete | Class + inline | ⚠️ Partial — delete is hardcoded |
| **Rooms** | `rooms` | `HasRoomsNav + IsStaffMember + IsSameHotel` | `CanManageRooms` (super_staff_admin+) | Class-level | ✅ Yes |
| **Room Bookings** | `room_bookings` | `HasRoomBookingsNav + IsStaffMember + IsSameHotel` | `CanManageRoomBookings` (staff_admin+) | Class-level | ✅ Yes |
| **Restaurant Bookings** | `restaurant_bookings` | `HasRestaurantBookingsNav + IsStaffMember + IsSameHotel` | `CanManageRestaurantBookings` (staff_admin+) | Class-level | ✅ Yes |
| **Room Services** | `room_services` | `HasNavPermission('room_services') + IsStaffMember + IsSameHotel` | No explicit manage gate | Class-level | ❌ No manage distinction |
| **Housekeeping** | `housekeeping` | `HasHousekeepingNav + IsStaffMember + IsSameHotel` | `CanManageHousekeeping` (staff_admin+) + `housekeeping/policy.py` inline | Class + inline | ⚠️ Partial — policy.py has hardcoded checks |
| **Attendance** | `attendance` | `HasNavPermission('attendance') + IsStaffMember + IsSameHotel` | `CanManageRoster` (super_staff_admin+) | Class-level | ✅ Yes |
| **Staff Management** | `staff_management` | `HasNavPermission('staff_management') + IsStaffMember + IsSameHotel` | `CanManageStaff` (super_staff_admin+) | Class + inline | ⚠️ Partial — many inline checks in staff/views.py |
| **Hotel Info** | `hotel_info` | `HasHotelInfoNav` | `IsSuperStaffAdminForHotel` | Class-level | ✅ Yes (but IsSuperStaffAdminForHotel lacks superuser bypass) |
| **Admin Settings** | `admin_settings` | `HasAdminSettingsNav + IsStaffMember + IsSameHotel` | `CanConfigureHotel` (super_staff_admin+) | Class-level | ✅ Yes |
| **Stock Tracker** | `stock_tracker` | `IsHotelStaff` (no nav check!) | Inline `access_level != 'super_staff_admin'` | `IsHotelStaff` + inline | ❌ No nav gate; manage is inline |
| **Maintenance** | `maintenance` | `IsHotelStaff` (no nav check!) | No manage gate | `IsHotelStaff` only | ❌ No nav gate; no manage distinction |
| **Entertainment** | `entertainment` | `AllowAny` (guest-facing) | `request.user.is_staff` inline | AllowAny + inline | ❌ Uses Django is_staff, not RBAC |

### Modules NOT using the canonical nav permission system:

| Module | Current Permission | Missing |
|--------|-------------------|---------|
| `stock_tracker` | `IsHotelStaff` | `HasNavPermission('stock_tracker')` |
| `maintenance` | `IsHotelStaff` | `HasNavPermission('maintenance')` |
| `hotel_info/views.py` | `IsAuthenticatedOrReadOnly` / `IsAuthenticated` | `HasHotelInfoNav` on staff endpoints |
| `entertainment` staff actions | `request.user.is_staff` | `HasNavPermission('entertainment')` + proper action gate |

---

## 5. View vs Manage Separation Audit

### Where correctly implemented (HasNavPermission for VIEW + CanManage* for MUTATE):

| Domain | View Gate | Manage Gate | Status |
|--------|-----------|-------------|--------|
| Rooms | `HasRoomsNav` | `CanManageRooms` | ✅ |
| Room Bookings | `HasRoomBookingsNav` | `CanManageRoomBookings` | ✅ |
| Restaurant Bookings | `HasRestaurantBookingsNav` | `CanManageRestaurantBookings` | ✅ |
| Attendance | `HasAttendanceNav` | `CanManageRoster` | ✅ |
| Housekeeping | `HasHousekeepingNav` | `CanManageHousekeeping` | ✅ |
| Admin Settings | `HasAdminSettingsNav` | `CanConfigureHotel` | ✅ |
| Staff Management | `HasStaffManagementNav` | `CanManageStaff` | ✅ (at class level; inline checks also exist) |

### Where missing or incomplete:

| Domain | View Gate | Manage Gate | Gap |
|--------|-----------|-------------|-----|
| Home (Posts) | `HasHomeNav` | **NONE** | Any staff with nav can CUD posts/comments. May be intentional for social feed. |
| Chat (Guest) | `HasChatNav` inline | **NONE** | Any authenticated staff can send messages. May be intentional. |
| Chat (Staff) | `HasChatNav` | **Hardcoded role.slug** | Delete-others uses `role.slug in ['manager','admin']` instead of CanManage* |
| Room Services | `HasRoomServicesNav` | **NONE** | No mutation-specific gate for staff actions (order status updates) |
| Stock Tracker | **IsHotelStaff** (no nav) | **Inline access_level** | No nav permission, no CanManage class |
| Maintenance | **IsHotelStaff** (no nav) | **NONE** | No nav permission, no manage gate |
| Entertainment | **AllowAny** | **is_staff inline** | No RBAC at all |
| Hotel Info | **IsAuthenticated** | **NONE** | Staff-only create endpoint has no manage gate |

### CanManage* classes that DO NOT YET EXIST but are needed:

| Proposed Class | Would Gate | Minimum Tier |
|----------------|-----------|--------------|
| `CanManageStockTracker` | Stock CUD, period delete, reopen | `super_staff_admin` |
| `CanManageMaintenance` | Ticket status changes, assignment | `staff_admin` |
| `CanManageEntertainment` | Tournament start/end, admin actions | `staff_admin` |
| `CanManageRoomServices` | Order status updates (staff-side) | `staff_admin` |
| `CanManageStaffChat` | Delete others' messages/attachments | `staff_admin` (replaces role.slug checks) |

---

## 6. Hardcoded / Non-Extensible Logic Found

### CRITICAL — Role slug hardcoding (will break when new roles are added):

| File | Line(s) | Code | Impact |
|------|---------|------|--------|
| `staff_chat/permissions.py` | 12 | `staff.role.slug in ('manager', 'admin')` | New management roles can't manage chat |
| `staff_chat/views_messages.py` | 482, 491 | `staff.role.slug in ['manager', 'admin']` | Delete/hard-delete blocked |
| `staff_chat/views_attachments.py` | 285 | `staff.role.slug in ['manager', 'admin']` | Attachment delete blocked |
| `housekeeping/policy.py` | 54 | `staff.role.slug == 'housekeeping'` | New housekeeping roles excluded |
| `housekeeping/policy.py` | 49 | `staff.department.slug == 'housekeeping'` | Department slug hardcoded |

### HIGH — Inline access_level checks (bypass centralized permission classes):

| File | Count | Pattern |
|------|-------|---------|
| `staff/views.py` | 12+ | `access_level == 'super_staff_admin'`, `access_level in (...)`, `access_level == 'regular_staff'` |
| `stock_tracker/views.py` | 14+ | `access_level != 'super_staff_admin'`, `is_superuser` direct |
| `housekeeping/policy.py` | 1 | `access_level in ['staff_admin', 'super_staff_admin']` |
| `hotel/permissions.py` | 1 | `access_level != 'super_staff_admin'` (IsSuperStaffAdminForHotel) |

### MEDIUM — is_superuser inconsistencies:

| File | Issue |
|------|-------|
| `hotel/permissions.py` | `IsSuperStaffAdminForHotel` does NOT grant access to Django superusers — inconsistent with `resolve_tier()` where superuser is highest |
| `staff/views.py` | 12+ direct `user.is_superuser` checks instead of using `IsDjangoSuperUser` or `resolve_tier()` |
| `staff/serializers.py` | Conflates `is_superuser` with `access_level == 'super_staff_admin'` — these are orthogonal |
| `stock_tracker/views.py` | Multiple direct `is_superuser` bypasses |
| `entertainment/views.py` | Uses `request.user.is_staff` (Django generic) instead of RBAC |

### LOW — Missing nav permission gates:

| Module | Uses | Should Use |
|--------|------|------------|
| `stock_tracker` | `IsHotelStaff` | `HasNavPermission('stock_tracker')` + `IsStaffMember` + `IsSameHotel` |
| `maintenance` | `IsHotelStaff` | `HasNavPermission('maintenance')` + `IsStaffMember` + `IsSameHotel` |
| `hotel_info` (staff) | `IsAuthenticated` | `HasHotelInfoNav` + `IsStaffMember` + `IsSameHotel` |
| `entertainment` (admin) | `AllowAny` / `is_staff` | `HasNavPermission('entertainment')` for staff actions |

---

## 7. Backend vs Frontend Ownership

### A. What should remain backend-owned:

| Concern | Owner | Mechanism |
|---------|-------|-----------|
| Tier resolution | Backend | `resolve_tier()` |
| Effective nav computation | Backend | `resolve_effective_access()` |
| Module visibility enforcement | Backend | `HasNavPermission` on every staff endpoint |
| Action/mutation authorization | Backend | `CanManage*` classes on every write endpoint |
| Hotel tenant isolation | Backend | `IsStaffMember + IsSameHotel` |
| Superuser bypass | Backend | Inside `resolve_tier()` and permission classes |

### B. What should be frontend-consumed only:

| Concern | Source | Frontend Role |
|---------|--------|---------------|
| Sidebar/nav rendering | `allowed_navs` from backend | Show/hide navigation items |
| Action button visibility | Could derive from tier/role sent by backend | Show/hide CUD buttons (UX hint only) |
| Role/tier display labels | Backend data | Display purposes |

**Frontend MUST NOT independently compute permissions.** Backend is the enforcement layer.

### C. Current system classification:

The current system is a **mixed hybrid**:

| Layer | Type |
|-------|------|
| Nav visibility | **Tier-based + Role-based** (additive union) |
| Action authority | **Tier-based only** (CanManage* all gate on access_level via tier hierarchy) |
| Per-user overrides | **Nav-only** (allowed_navigation_items is additive, no action override) |
| Some endpoints | **Hardcoded role-name checks** (staff_chat, housekeeping) |
| Some endpoints | **Boolean checks** (is_superuser, is_staff) |

**Truth statement**: This is a **tier-primary, role-supplemented, nav-centric** permission system with **inconsistent enforcement** at the action layer and **hardcoded role-name logic** in 3 modules.

---

## 8. Final Verdict

### A. Is the current permission model good enough to support new roles cleanly?

**PARTIALLY.**

### B. What exact missing pieces prevent clean extensibility?

| # | Gap | Severity | Impact |
|---|-----|----------|--------|
| 1 | **Role slug hardcoding** in staff_chat (4 locations) and housekeeping/policy.py (2 locations) | **CRITICAL** | New management/housekeeping roles will be silently denied |
| 2 | **No action-level permission classes** for stock_tracker, maintenance, entertainment, room_services, staff_chat | **HIGH** | Mutations in these modules are either ungated or use inline access_level checks |
| 3 | **3 modules skip nav permission gates** entirely (stock_tracker, maintenance, hotel_info staff endpoints) | **HIGH** | Nav visibility system is bypassed — removing nav access won't block these modules |
| 4 | **IsSuperStaffAdminForHotel** doesn't honor superuser bypass | **MEDIUM** | Django superusers without Staff profile are blocked on hotel_info CMS mutations |
| 5 | **12+ inline access_level checks in staff/views.py** | **MEDIUM** | Tier hierarchy not enforced uniformly; changes to tier logic require editing multiple files |
| 6 | **14+ inline checks in stock_tracker/views.py** | **MEDIUM** | Same as above |
| 7 | **is_superuser/is_staff conflation** in serializers and entertainment | **LOW** | Django's is_staff is meaningless in HotelMate RBAC; conflation with access_level causes confusion |
| 8 | **No capability/domain permission model** — roles can define navs but not action capabilities | **MEDIUM** | A "front_desk_lead" role cannot be granted manage permissions without changing their tier |

### C. Minimum Correct Next Step

**Do NOT rewrite the permission system.** The core architecture (`resolve_tier` → `resolve_effective_access` → `HasNavPermission` + `CanManage*`) is sound.

**Fix in priority order:**

#### Wave 1 — Eliminate role-slug hardcoding (CRITICAL, ~2 hours)

1. Replace `is_chat_manager()` in `staff_chat/permissions.py` with a tier-based check:
   ```python
   def is_chat_manager(staff):
       return _tier_at_least(resolve_tier(staff.user), 'staff_admin')
   ```
2. Update the 4 inline `role.slug in ['manager','admin']` checks in `staff_chat/views_messages.py` and `staff_chat/views_attachments.py` to call `is_chat_manager(staff)`.
3. Replace `is_housekeeping()` role.slug check in `housekeeping/policy.py` — use department.slug only (department is structural; role is assignable and shouldn't be hardcoded).

#### Wave 2 — Add missing CanManage* classes + nav gates (~4 hours)

1. Create `CanManageStockTracker`, `CanManageMaintenance`, `CanManageEntertainment`, `CanManageRoomServices`, `CanManageStaffChat` in `staff/permissions.py`.
2. Add corresponding `Has*Nav` static classes if missing.
3. Apply to `stock_tracker/views.py`, `maintenance/views.py`, `entertainment/views.py`, `room_services/views.py` (staff actions), `staff_chat/views_messages.py`, `staff_chat/views_attachments.py`.
4. Remove inline `access_level` checks that the new classes replace.

#### Wave 3 — Fix IsSuperStaffAdminForHotel + inline cleanups (~3 hours)

1. Fix `hotel/permissions.py` `IsSuperStaffAdminForHotel` to honor `user.is_superuser`:
   ```python
   if request.user.is_superuser:
       return True
   ```
2. Refactor inline access_level checks in `staff/views.py` to use tier-based helper or permission class where possible. Some business-specific guards (e.g., "only super_staff_admin can create super_staff_admin") are legitimate and may remain inline but should call `_tier_at_least()` instead of string comparison.
3. Replace `entertainment/views.py` `is_staff` checks with proper RBAC.

#### Future consideration — Role-level capabilities (NOT urgent)

The current system gates actions by **tier only**. If a future requirement needs "role X can manage bookings but role Y cannot, both at staff_admin tier", the system would need a capability M2M on Role (similar to `default_navigation_items` but for actions). This is **not needed now** — tier-based action gating is sufficient for the current role structure.

---

## Appendix: Complete View Permission Map

### Canonical RBAC Pattern (correctly applied):

```
permission_classes = [IsAuthenticated, Has*Nav, IsStaffMember, IsSameHotel]  # view
get_permissions():  [IsAuthenticated, Has*Nav, IsStaffMember, IsSameHotel, CanManage*]  # CUD
```

### Modules following canonical pattern:

- ✅ rooms/views.py (all ViewSets + FBVs)
- ✅ bookings/views.py (staff ViewSets)
- ✅ attendance/views.py, views_analytics.py, face_views.py
- ✅ housekeeping/views.py (class-level; policy.py has inline issues)
- ✅ hotel/staff_views.py (room types, rooms, bookings, CMS builder, access config)
- ✅ hotel/overstay_views.py
- ✅ hotel/base_views.py (HotelViewSet)
- ✅ staff/views.py (class-level on ViewSets; inline issues in FBVs)
- ✅ home/views.py (nav gate; no manage gate — likely intentional)
- ✅ guests/views.py

### Modules NOT following canonical pattern:

- ❌ stock_tracker/views.py — `IsHotelStaff` only, no nav gate, inline manage checks
- ❌ maintenance/views.py — `IsHotelStaff` only, no nav gate, no manage checks
- ❌ entertainment/views.py — `AllowAny` + `is_staff` inline
- ❌ hotel_info/views.py — `IsAuthenticatedOrReadOnly`, no nav gate for staff endpoints
- ⚠️ staff_chat/views_messages.py, views_attachments.py — `IsStaffMember + IsSameHotel` but no nav gate, hardcoded role.slug for manage
- ⚠️ chat/views.py — Inline `HasNavPermission` checks instead of class-level on some FBVs

### Guest-facing / Public (correctly AllowAny):

- hotel/booking_views.py, payment_views.py, public_views.py
- hotel/canonical_guest_chat_views.py, guest_portal_views.py
- bookings/views.py (GuestDinnerBooking, AvailableTables, BlueprintObjectType)
- room_services/views.py (menus, guest orders)
- entertainment/views.py (games, quizzes — all guest-facing)
- chat/views.py (guest message endpoints with token validation)
- common/views.py (theme)
