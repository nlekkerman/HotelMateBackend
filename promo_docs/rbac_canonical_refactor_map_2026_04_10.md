# Canonical RBAC Refactor Map — Full Systematic Plan

**Date:** 2026-04-10  
**Status:** FINAL REFACTOR MAP — IN EXECUTION  
**Prerequisites:** [RBAC Audit](rbac_permissions_audit_2026_04_10.md) · [Implementation Plan](rbac_canonical_implementation_plan_2026_04_10.md)

---

## 0. FINAL ENFORCEMENT RULES (NON-NEGOTIABLE)

These rules override any other section in this document. No exceptions.

### Rule 1: Module visibility and action authority MUST be strictly separated
- `HasNavPermission` controls ONLY access to module/route
- It MUST NOT grant mutation authority

### Rule 2: EVERY mutation endpoint MUST have explicit action-level permission
- NO mutation logic may rely on nav visibility
- NO mutation logic may rely on frontend hiding buttons
- NO mutation logic may rely on tier checks inline

### Rule 3: Action permissions MUST be implemented as dedicated permission classes

**MANDATORY permission classes:**
- `CanManageRoster` — gates roster/attendance CUD operations
- `CanManageStaff` — gates staff creation/deletion/nav assignment
- `CanManageRooms` — gates room CUD operations (create, update, bulk operations)
- `CanManageBookings` — gates booking CUD operations (create, unseat, delete)
- `CanConfigureHotel` — gates hotel settings, precheckin/survey config, public page builder

Each class MUST:
- Derive authority from canonical `resolve_tier()`
- NOT rely on inline `access_level` checks
- NOT rely on duplicated logic

### Rule 4: Tier defaults MUST be minimal
- `regular_staff` MUST NOT see management modules
- `staff_admin` MUST NOT receive full module access
- `super_staff_admin` is the ONLY full-access hotel tier

### Rule 5: Role MUST define operational capability
- `Role.default_navigation_items` is REQUIRED
- Roles MUST be the primary source of module access for `regular_staff`
- Tier MUST act as a ceiling, not a blanket grant

### Rule 6: Override system MUST be additive only
- `Staff.allowed_navigation_items` MUST NOT remove access
- Override MUST NOT be used as primary permission system

### Rule 7: NO legacy permission logic may remain active after refactor

This includes:
- Inline `request.user.is_superuser` checks
- Inline `staff.access_level` checks
- Duplicate permission classes
- Legacy permission decorators
- Module access enforced only in frontend

ALL must be replaced by canonical system.

### Rule 8: No parallel systems allowed
- Old and new permission logic MUST NOT coexist
- If temporary coexistence is required for migration, it MUST be explicitly marked and removed after

### Rule 9: Backend is the source of truth
- Frontend MUST NOT be trusted for permission enforcement
- Backend MUST enforce ALL access rules

### Rule 10: If any endpoint allows mutation without explicit permission class → it is a bug
NO EXCEPTIONS.

---

## 1. Final Canonical Refactor Map

### 1A. Files to Change

| File | Change Type | Summary |
|------|------------|---------|
| `staff/permissions.py` | **MAJOR REWRITE** | Add `resolve_tier()`, evolve `resolve_staff_navigation()` → `resolve_effective_access()`, update `HasNavPermission`, remove `create_nav_permission`, remove `requires_nav_permission` |
| `staff/permissions_superuser.py` | **DELETE FILE** | `IsSuperUser` renamed → `IsAdminTier`, moved to `staff/permissions.py` |
| `staff/models.py` | **ADD FIELD** | Add `Role.default_navigation_items` M2M to `NavigationItem` |
| `hotel/permissions.py` | **MINOR** | Add `IsHotelStaffWithNav(slug)` composite or keep `IsHotelStaff` and layer `HasNavPermission` separately |
| `hotel/provisioning_views.py` | **MINOR** | Remove local `IsSuperUser` class, import `IsDjangoSuperUser` from `staff/permissions.py` |
| `hotel/base_views.py` | **MINOR** | Update import from `staff/permissions_superuser.py::IsSuperUser` → `staff/permissions.py::IsAdminTier` |
| `hotel/staff_views.py` | **MAJOR** | Add `HasNavPermission` to ~35 views. Split mutation views with `IsSuperStaffAdminForHotel`. Fix `[IsAuthenticated]`-only views. |
| `hotel/auth_backends.py` | **DELETE FILE** | `HotelSubdomainBackend` is dead code |
| `hotel/models.py` | **EDIT** | Update post-save signal to produce canonical slug list |
| `common/mixins.py` | **MINOR** | Optionally evolve `HotelScopedViewSetMixin` to accept a `nav_slug` class attribute |
| `staff/views.py` | **MAJOR** | Replace 19+ inline `is_superuser` / `access_level` checks with `resolve_tier()` or permission classes. Add `HasNavPermission('staff_management')` to management views. |
| `staff/serializers.py` | **MINOR** | Update `resolve_staff_navigation()` call to `resolve_effective_access()` |
| `staff/me_views.py` | **MINOR** | Update `resolve_staff_navigation()` call to `resolve_effective_access()` |
| `staff/management/commands/seed_navigation_items.py` | **REWRITE** | Align to canonical slug list |
| `stock_tracker/views.py` | **MODERATE** | Add `HasNavPermission('stock_tracker')` to 15 views. Replace inline `is_superuser` checks (5 locations). |
| `stock_tracker/comparison_views.py` | **MODERATE** | Add `HasNavPermission('stock_tracker')` to 6 views |
| `stock_tracker/report_views.py` | **MINOR** | Add `HasNavPermission('stock_tracker')` to 2 views |
| `housekeeping/views.py` | **MODERATE** | Add `HasNavPermission('housekeeping')` to 3 views. Replace inline `access_level` checks. |
| `housekeeping/policy.py` | **MINOR** | Replace `is_manager()` with `resolve_tier()` call. Remove `department.slug` from `is_housekeeping()`. |
| `maintenance/views.py` | **MINOR** | Add `HasNavPermission('maintenance')` to 3 views |
| `rooms/views.py` | **MODERATE** | Add `HasNavPermission('rooms')` to staff views. Fix `[IsAuthenticated]`-only views (`RoomViewSet`, `RoomTypeViewSet`, `RoomByHotelAndNumberView`, `room_details`). Replace inline `is_superuser` in `bulk_checkout_rooms_by_id`. |
| `bookings/views.py` | **MODERATE** | Fix `BookingViewSet`, `RestaurantViewSet`, `AvailableTablesView` — add `IsStaffMember`, `IsSameHotel`, `HasNavPermission`. Fix `UnseatBookingAPIView`, `DeleteBookingAPIView`. |
| `attendance/views.py` | **MODERATE** | Add `HasNavPermission('attendance')` to mixin-based views and `DailyPlanEntryViewSet` |
| `attendance/views_analytics.py` | **MINOR** | Fix `AnalyticsViewSet` — add `IsStaffMember`, `IsSameHotel`, `HasNavPermission('attendance')` |
| `attendance/face_views.py` | **MINOR** | Fix `FaceRecognitionViewSet` — add `IsStaffMember`, `IsSameHotel` |
| `staff_chat/views.py` | **MINOR** | Add `HasNavPermission('chat')` to chat views |
| `staff_chat/views_messages.py` | **MINOR** | Centralize `role.slug in ['manager', 'admin']` to `is_chat_manager(staff)` |
| `staff_chat/views_attachments.py` | **MINOR** | Centralize `role.slug in ['manager', 'admin']` to `is_chat_manager(staff)` |
| `staff_chat/permissions.py` | **MINOR** | Centralize role.slug check in `CanManageConversation` and `CanDeleteMessage` to use shared `is_chat_manager()` |
| `chat/views.py` | **MINOR** | Centralize role.slug check to `is_chat_manager()`. Add `HasNavPermission('chat')` to staff-facing endpoints. |
| `room_services/views.py` | **MINOR** | Add `HasNavPermission('room_services')` to staff views |
| `hotel_info/views.py` | **MINOR** | Add `HasNavPermission('hotel_info')` to staff views |
| `home/views.py` | **MODERATE** | Add `HasNavPermission('home')`. Fix `[IsAuthenticated]`-only views: `PostViewSet`, `CommentViewSet`, `CommentReplyViewSet`. |
| `guests/views.py` | **MINOR** | Fix `GuestViewSet` — add `IsStaffMember`, `IsSameHotel`, `HasNavPermission('rooms')` |
| `entertainment/views.py` | **MINOR** | Add `HasNavPermission('entertainment')` to dashboard views. Fix `[IsAuthenticated]`-only views. |
| `notifications/views.py` | **MINOR** | Fix `SaveFcmTokenView` — add `IsStaffMember` |
| `voice_recognition/views_voice.py` | **MINOR** | Fix `VoiceRecognitionViewSet` — add `IsStaffMember`, `IsSameHotel` |
| `common/views.py` | **NO CHANGE** | `ThemePreferenceViewSet` is user-scoped (not hotel-scoped), `[IsAuthenticated]` is correct |

### 1B. Symbols/Classes/Functions to ADD

| Symbol | Location | Purpose |
|--------|----------|---------|
| `resolve_tier(user)` | `staff/permissions.py` | Single canonical tier resolver → returns `'super_user'` / `'super_staff_admin'` / `'staff_admin'` / `'regular_staff'` / `None` |
| `resolve_effective_access(user)` | `staff/permissions.py` | Replaces `resolve_staff_navigation()`. Adds tier defaults + role defaults + override computation. Returns `{tier, hotel_slug, role_slug, effective_navs, navigation_items, is_superuser, access_level}` |
| `TIER_DEFAULT_NAVS` | `staff/permissions.py` | Code constant mapping tier → default nav slugs |
| `CANONICAL_NAV_SLUGS` | `staff/permissions.py` | Single source of truth for all valid nav slugs |
| `IsDjangoSuperUser` | `staff/permissions.py` | True platform-level superuser check (`user.is_superuser` only). Replaces local `IsSuperUser` in `hotel/provisioning_views.py`. |
| `IsAdminTier` | `staff/permissions.py` | Allows `super_user` + `super_staff_admin` + `staff_admin`. Replaces `staff/permissions_superuser.py::IsSuperUser`. |
| `IsSuperStaffAdminOrAbove` | `staff/permissions.py` | Allows `super_user` + `super_staff_admin` only. For mutation gates that `staff_admin` must NOT pass. Uses `resolve_tier()`. |
| `is_chat_manager(staff)` | `staff_chat/permissions.py` | Centralized `role.slug in ['manager', 'admin']` check. Replaces 7 scattered role slug checks in chat code. |
| `Role.default_navigation_items` | `staff/models.py` | M2M field to `NavigationItem`. Defines job-role default features. |
| `populate_role_nav_defaults` | `staff/management/commands/populate_role_nav_defaults.py` | Management command to seed `Role.default_navigation_items` for existing roles |
| `migrate_nav_to_defaults` | `staff/management/commands/migrate_nav_to_defaults.py` | Management command to convert `Staff.allowed_navigation_items` from primary → override |

### 1C. Symbols/Classes/Functions to RENAME

| Old | New | Location | Reason |
|-----|-----|----------|--------|
| `staff/permissions_superuser.py::IsSuperUser` | `IsAdminTier` | Moved to `staff/permissions.py` | Name is misleading — allows `staff_admin` too. New name reflects actual tier check. |
| `hotel/provisioning_views.py::IsSuperUser` (local) | `IsDjangoSuperUser` | Moved to `staff/permissions.py` | Distinguish from `IsAdminTier`. Clear that this is Django-level superuser only. |
| `resolve_staff_navigation()` | `resolve_effective_access()` | `staff/permissions.py` | New function replaces old one with tier+role+override computation. Old name removed after all call sites migrated. |

### 1D. Symbols/Classes/Functions to REMOVE

| Symbol | Location | Reason |
|--------|----------|--------|
| `create_nav_permission()` | `staff/permissions.py` | Dead code. Zero usages. Unnecessary factory. |
| `requires_nav_permission()` | `staff/permissions.py` | Dead code. Zero usages. `HasNavPermission` serves this purpose. |
| `HotelSubdomainBackend` | `hotel/auth_backends.py` | Dead code. Not in `AUTHENTICATION_BACKENDS`. Entire file deleted. |
| `IsSuperUser` class | `staff/permissions_superuser.py` | Replaced by `IsAdminTier` in `staff/permissions.py`. Entire file deleted. |
| `IsSuperUser` local class | `hotel/provisioning_views.py` | Replaced by `IsDjangoSuperUser` import from `staff/permissions.py`. |
| `resolve_staff_navigation()` | `staff/permissions.py` | Replaced by `resolve_effective_access()`. Removed after all call sites updated. |

### 1E. Models/Migrations Required

| Change | Model | Migration Type |
|--------|-------|---------------|
| Add `default_navigation_items` M2M to `NavigationItem` | `Role` | Schema migration (add field) |
| No structural change | `Staff` | None — `allowed_navigation_items` M2M stays, repurposed semantically |
| No structural change | `NavigationItem` | None — slug list reconciled via data migration |
| Reconcile nav slug data | `NavigationItem` | Data migration — normalize existing records to canonical slugs |
| Populate role defaults | `Role → NavigationItem` | Data migration via management command |
| Convert staff M2M from primary to override | `Staff → NavigationItem` | Data migration via management command |

### 1F. Views/ViewSets/FBVs That Must Be Updated

**Priority 1 — Fix `[IsAuthenticated]`-only views handling staff/hotel data (24 views):**

| File | View | Current | Target |
|------|------|---------|--------|
| `home/views.py` | `PostViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('home')]` |
| `home/views.py` | `CommentViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('home')]` |
| `home/views.py` | `CommentReplyViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('home')]` |
| `guests/views.py` | `GuestViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]` |
| `rooms/views.py` | `RoomViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]` |
| `rooms/views.py` | `RoomTypeViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]` |
| `rooms/views.py` | `RoomByHotelAndNumberView` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]` |
| `rooms/views.py` | `room_details` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]` |
| `bookings/views.py` | `BookingViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]` |
| `bookings/views.py` | `RestaurantViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]` |
| `bookings/views.py` | `AvailableTablesView` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]` |
| `bookings/views.py` | `UnseatBookingAPIView` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]` |
| `bookings/views.py` | `DeleteBookingAPIView` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]` |
| `attendance/views_analytics.py` | `AnalyticsViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('attendance')]` |
| `attendance/face_views.py` | `FaceRecognitionViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` |
| `staff_chat/views.py` | `StaffListViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('chat')]` |
| `staff_chat/views.py` | `StaffConversationViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('chat')]` |
| `entertainment/views.py` | `MemoryGameAchievementViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('entertainment')]` |
| `entertainment/views.py` | `DashboardViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('entertainment')]` |
| `voice_recognition/views_voice.py` | `VoiceRecognitionViewSet` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` |
| `voice_recognition/views_voice.py` | TTS view | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` |
| `hotel/staff_views.py` | `PresetViewSet` | `[IsAuthenticated]` | `[IsAuthenticated]` (global presets — no change needed) |
| `hotel/staff_views.py` | `HotelSettingsView` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('admin_settings')]` |
| `hotel/staff_views.py` | `SendPrecheckinLinkView` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]` |
| `notifications/views.py` | `SaveFcmTokenView` | `[IsAuthenticated]` | `[IsAuthenticated, IsStaffMember]` (no hotel slug in URL for token save) |

**Priority 2 — Add `HasNavPermission` to views already using `IsHotelStaff` (26 views):**

All `stock_tracker/views.py` views (15), `stock_tracker/comparison_views.py` (6), `maintenance/views.py` (3), `hotel/overstay_views.py` (3) — add `HasNavPermission('<slug>')` alongside existing `IsHotelStaff`.

**Priority 3 — Add `HasNavPermission` to views already using `[IsAuthenticated, IsStaffMember, IsSameHotel]` (~30 views):**

All `hotel/staff_views.py` booking management views, `housekeeping/views.py` views, `rooms/views.py` staff views, `attendance/views.py` views — add `HasNavPermission('<slug>')`.

**Priority 4 — Add action-level tier enforcement to mutation views:**

Views that need `IsSuperStaffAdminOrAbove` for CUD operations on top of `HasNavPermission` for module access:
- `staff/views.py` — `NavigationItemViewSet` perform_create/update/destroy
- `staff/views.py` — `StaffViewSet` create (staff creation)
- `staff/views.py` — `StaffNavigationPermissionsView` (nav assignment)
- `staff/views.py` — `DepartmentViewSet`, `RoleViewSet` CUD actions
- `hotel/staff_views.py` — public page builder views (already use `IsSuperStaffAdminForHotel`)
- `hotel/staff_views.py` — `HotelPrecheckinConfigView`, `HotelSurveyConfigView` (already use `IsSuperStaffAdminForHotel`)
- `stock_tracker/views.py` — `PeriodDeleteAPIView`, `PeriodReopenAPIView`
- `stock_tracker/report_views.py` — `StockValueReportView`, `SalesReportView` (already use `IsSuperStaffAdminForHotel`)

### 1G. Dead Logic to Delete After Rollout

| Item | File | Reason |
|------|------|--------|
| `create_nav_permission()` function | `staff/permissions.py` | Dead factory. Zero call sites. |
| `requires_nav_permission()` decorator | `staff/permissions.py` | Dead decorator. Zero usages. |
| Entire `HotelSubdomainBackend` class | `hotel/auth_backends.py` | Not in `AUTHENTICATION_BACKENDS`. Delete entire file. |
| Entire `IsSuperUser` class | `staff/permissions_superuser.py` | Replaced by `IsAdminTier`. Delete entire file. |
| Local `IsSuperUser` class | `hotel/provisioning_views.py` | Replaced by `IsDjangoSuperUser` import. |
| `resolve_staff_navigation()` | `staff/permissions.py` | Replaced by `resolve_effective_access()`. |
| `department.slug == 'housekeeping'` check | `housekeeping/policy.py` | Replaced by role-only check after data cleanup. |
| All inline `request.user.is_superuser` checks in view bodies | 19 locations across 4 files | Replaced by `resolve_tier()` calls or class-level permission. |
| All inline `staff.access_level in (...)` checks | 14 locations across 4 files | Replaced by `resolve_tier()` calls or class-level permission. |

---

## 2. Old-to-New Replacement Matrix

### 2A. Permission Class Replacements

| OLD | FILE | NEW | FILE |
|-----|------|-----|------|
| `staff/permissions_superuser.py::IsSuperUser` | `staff/permissions_superuser.py` | `IsAdminTier` | `staff/permissions.py` |
| `hotel/provisioning_views.py::IsSuperUser` (local) | `hotel/provisioning_views.py` | `IsDjangoSuperUser` | `staff/permissions.py` |
| No module enforcement (views have no `HasNavPermission`) | everywhere | `HasNavPermission('<slug>')` | `staff/permissions.py` |
| No mutation enforcement separate from visibility | everywhere | `IsSuperStaffAdminOrAbove` for CUD | `staff/permissions.py` |

### 2B. Resolver Replacements

| OLD | FILE | NEW | FILE |
|-----|------|-----|------|
| `resolve_staff_navigation(user)` | `staff/permissions.py` | `resolve_effective_access(user)` | `staff/permissions.py` |
| Calls to `resolve_staff_navigation()` in login | `staff/views.py` L139 | `resolve_effective_access()` | `staff/permissions.py` |
| Calls to `resolve_staff_navigation()` in staff update | `staff/views.py` L1501, L1585 | `resolve_effective_access()` | `staff/permissions.py` |
| Calls to `resolve_staff_navigation()` in serializer | `staff/serializers.py` L338 | `resolve_effective_access()` | `staff/permissions.py` |
| Calls to `resolve_staff_navigation()` in /me | `staff/me_views.py` L38, L47 | `resolve_effective_access()` | `staff/permissions.py` |
| No `resolve_tier()` exists | — | `resolve_tier(user)` | `staff/permissions.py` |

### 2C. Inline Authorization Check Replacements

**`request.user.is_superuser` — 19 view-body locations → `resolve_tier()` or class-level permission:**

| File | Location | Current | Replacement |
|------|----------|---------|-------------|
| `staff/views.py` | `StaffViewSet.create()` L331 | `user.is_superuser = False` | Keep as-is (security hardening, not auth check) |
| `staff/views.py` | `RegistrationCodeRetriever.get()` L796 | `if request.user.is_superuser:` pass hotel filter | `if resolve_tier(request.user) == 'super_user':` |
| `staff/views.py` | `CreateStaffFromUserAPIView.post()` L976 | `if user.is_superuser:` allow any access level | `if resolve_tier(user) == 'super_user':` |
| `staff/views.py` | `CreateStaffFromUserAPIView.post()` L1045 | `if user.is_superuser:` creation bypass | `if resolve_tier(user) == 'super_user':` |
| `staff/views.py` | `DepartmentViewSet.get_queryset()` L1227 | `if user.is_superuser: return all` | `if resolve_tier(user) == 'super_user':` |
| `staff/views.py` | `DepartmentViewSet.check_write_permission()` L1242 | `if user.is_superuser: return` | `if resolve_tier(user) == 'super_user':` |
| `staff/views.py` | `RoleViewSet.get_queryset()` L1327 | `if user.is_superuser:` | `if resolve_tier(user) == 'super_user':` |
| `staff/views.py` | `RoleViewSet.check_write_permission()` L1342 | `if user.is_superuser: return` | `if resolve_tier(user) == 'super_user':` |
| `staff/views.py` | `NavigationItemViewSet.perform_create/update/destroy()` L1449-1465 | `if not self.request.user.is_superuser` → 403 | `if resolve_tier(self.request.user) != 'super_user':` → 403 |
| `staff/views.py` | `StaffNavigationPermissionsView._check_authorization()` L1595 | `if requester_user.is_superuser: return True` | `if resolve_tier(requester_user) == 'super_user':` |
| `staff/views.py` | `RegistrationPackageView.get()` L1689 | `if request.user.is_superuser:` | `if resolve_tier(request.user) == 'super_user':` |
| `stock_tracker/views.py` | `PeriodReopenAPIView.post()` L721 | `if user.is_superuser: can_reopen = True` | `if resolve_tier(user) in ('super_user', 'super_staff_admin'):` |
| `rooms/views.py` | `bulk_checkout_rooms_by_id()` L185 | `if destructive and not request.user.is_superuser` | `if destructive and resolve_tier(request.user) not in ('super_user', 'super_staff_admin'):` |
| `housekeeping/views.py` | `RoomTasksAvailableView.post()` L336 | `not (is_manager(staff) or request.user.is_superuser)` | `resolve_tier(request.user) not in ('super_user', 'super_staff_admin', 'staff_admin')` |
| `housekeeping/admin.py` | Admin delete action L249 | `return request.user.is_superuser` | Keep as-is (Django Admin, not API) |

**`staff.access_level in (...)` — 14 locations → `resolve_tier()` or class-level permission:**

| File | Location | Current | Replacement |
|------|----------|---------|-------------|
| `staff/views.py` | `StaffViewSet.create()` L307 | `requesting_staff.access_level != "super_staff_admin"` | `resolve_tier(request.user) not in ('super_user', 'super_staff_admin')` |
| `staff/views.py` | `RegistrationCodeCreateView.post()` L719 | `staff.access_level not in ['staff_admin', 'super_staff_admin']` | `resolve_tier(request.user) not in ('super_user', 'super_staff_admin', 'staff_admin')` |
| `staff/views.py` | `RegistrationCodeRetriever.get()` L831 | `staff.access_level not in ('staff_admin', 'super_staff_admin')` | `resolve_tier(request.user) not in ('super_user', 'super_staff_admin', 'staff_admin')` |
| `staff/views.py` | Pending registrations L988 | `requesting_staff.access_level == 'regular_staff'` → 403 | `resolve_tier(request.user) == 'regular_staff'` → 403 |
| `staff/views.py` | `CreateStaffFromUserAPIView.post()` L1058 | `requesting_staff.access_level == 'regular_staff'` → 403 | `resolve_tier(request.user) == 'regular_staff'` → 403 |
| `staff/views.py` | Department/Role queryset L1231, L1331 | `staff.access_level in ('staff_admin', 'super_staff_admin')` | `resolve_tier(request.user) in ('super_user', 'super_staff_admin', 'staff_admin')` |
| `staff/views.py` | `StaffNavigationPermissionsView._check_authorization()` L1604 | `requester_staff.access_level != 'super_staff_admin'` | `resolve_tier(requester_user) not in ('super_user', 'super_staff_admin')` |
| `staff/views.py` | `RegistrationPackageView.get()` L1706 | `staff.access_level not in ('staff_admin', 'super_staff_admin')` | `resolve_tier(request.user) not in ('super_user', 'super_staff_admin', 'staff_admin')` |
| `stock_tracker/views.py` | `PeriodDeleteAPIView.delete()` L501 | `staff.access_level != 'super_staff_admin'` | `resolve_tier(request.user) not in ('super_user', 'super_staff_admin')` |
| `housekeeping/views.py` | `TasksDashboard` L80 | `staff.access_level in ['staff_admin', 'super_staff_admin']:` | `resolve_tier(request.user) in ('super_user', 'super_staff_admin', 'staff_admin')` |
| `housekeeping/policy.py` | `is_manager()` L30 | `staff.access_level in ['staff_admin', 'super_staff_admin']` | `resolve_tier(staff.user) in ('super_user', 'super_staff_admin', 'staff_admin')` |

**`role.slug in ['manager', 'admin']` — 7 locations → centralized `is_chat_manager()`:**

| File | Location | Current | Replacement |
|------|----------|---------|-------------|
| `staff_chat/permissions.py` | `CanManageConversation.has_object_permission()` L104 | `staff.role.slug in ['manager', 'admin']` | `is_chat_manager(staff)` |
| `staff_chat/permissions.py` | `CanDeleteMessage.has_object_permission()` L129 | `staff.role.slug in ['manager', 'admin']` | `is_chat_manager(staff)` |
| `staff_chat/views_messages.py` | `delete_message()` L482 | `staff.role.slug in ['manager', 'admin']` | `is_chat_manager(staff)` |
| `staff_chat/views_messages.py` | `delete_message()` L491 | `staff.role.slug in ['manager', 'admin']` | `is_chat_manager(staff)` |
| `staff_chat/views_attachments.py` | `delete_attachment()` L285 | `staff.role.slug in ['manager', 'admin']` | `is_chat_manager(staff)` |
| `chat/views.py` | Notification routing L817 | `staff.role.slug in ['manager', 'admin']` | Keep as-is (notification routing, not authorization) |

**`department.slug == 'housekeeping'` — 1 location → remove after data fix:**

| File | Location | Current | Replacement |
|------|----------|---------|-------------|
| `housekeeping/policy.py` | `is_housekeeping()` L49 | `staff.department.slug == 'housekeeping'` fallback | Remove. Ensure all housekeeping staff have `role.slug == 'housekeeping'`. |

### 2D. View Permission Class Upgrades

**`[IsHotelStaff]` → `[IsHotelStaff, HasNavPermission('<slug>')]`:**

| File | Views | Nav Slug |
|------|-------|----------|
| `stock_tracker/views.py` | `IngredientViewSet`, `CocktailRecipeViewSet`, `CocktailConsumptionViewSet`, `CocktailIngredientConsumptionViewSet`, `IngredientUsageView`, `StockCategoryViewSet`, `LocationViewSet`, `StockPeriodViewSet`, `StockSnapshotViewSet`, `StockItemViewSet`, `StockMovementViewSet`, `StocktakeViewSet`, `StocktakeLineViewSet`, `SaleViewSet`, `KPISummaryView` | `stock_tracker` |
| `stock_tracker/comparison_views.py` | `CompareCategoriesView`, `TopMoversView`, `CostAnalysisView`, `TrendAnalysisView`, `VarianceHeatmapView`, `PerformanceScorecardView` | `stock_tracker` |
| `maintenance/views.py` | `MaintenanceRequestViewSet`, `MaintenanceCommentViewSet`, `MaintenancePhotoViewSet` | `maintenance` |
| `hotel/overstay_views.py` | `OverstayAcknowledgeView`, `OverstayExtendView`, `OverstayStatusView` | `bookings` |

**`[IsAuthenticated, IsSuperStaffAdminForHotel]` → `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('<slug>'), IsSuperStaffAdminOrAbove]`:**

| File | Views | Nav Slug |
|------|-------|----------|
| `hotel/staff_views.py` | All public page builder views (12 viewsets + 4 APIViews) | `admin_settings` |
| `hotel/staff_views.py` | `HotelPrecheckinConfigView`, `HotelSurveyConfigView` | `admin_settings` |
| `stock_tracker/report_views.py` | `StockValueReportView`, `SalesReportView` | `stock_tracker` |

**`[IsAuthenticated, IsStaffMember, IsSameHotel]` → `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('<slug>')]`:**

| File | Views | Nav Slug |
|------|-------|----------|
| `hotel/staff_views.py` | `StaffRoomTypeViewSet`, `StaffRoomViewSet` | `rooms` |
| `hotel/staff_views.py` | `StaffAccessConfigViewSet` | `admin_settings` |
| `hotel/staff_views.py` | All booking management views (14 views) | `bookings` |
| `housekeeping/views.py` | `HousekeepingDashboardViewSet`, `HousekeepingTaskViewSet`, `RoomStatusViewSet` | `housekeeping` |
| `rooms/views.py` | `StaffRoomViewSet`, `bulk_create_room_types`, `bulk_create_rooms`, `update_room_floor`, `validate_room_migration`, `move_room_api`, `validate_existing_guest_move`, `move_guest_forward`, `move_guest_backward` | `rooms` |
| `attendance/views.py` | `DailyPlanEntryViewSet` | `attendance` |
| `attendance/views.py` (via mixin) | `ShiftLocationViewSet`, `DailyPlanViewSet`, `CopyRosterViewSet` | `attendance` |

---

## 3. Final Target Permission Model

### 3A. Actor Resolution

```
resolve_tier(user) → Tier | None

    IF NOT user.is_authenticated:
        → None (DENY)
    
    IF user.is_superuser:
        → 'super_user'
    
    TRY staff = user.staff_profile:
        → staff.access_level   (one of: 'super_staff_admin', 'staff_admin', 'regular_staff')
    
    EXCEPT Staff.DoesNotExist:
        → None (DENY — authenticated Django user with no staff profile)
```

**Tier hierarchy (descending authority):**

| Tier | Identity Source | Capabilities |
|------|----------------|-------------|
| `super_user` | `User.is_superuser == True` | Platform-level. Bypasses ALL module/tier gates. Sees all hotels. |
| `super_staff_admin` | `Staff.access_level == 'super_staff_admin'` | Full hotel authority. All modules visible. CUD on settings, staff, nav, config. |
| `staff_admin` | `Staff.access_level == 'staff_admin'` | Supervisor/department-lead. Broader module **visibility** (read/monitor). NO structural mutation authority. |
| `regular_staff` | `Staff.access_level == 'regular_staff'` | Operational only. Minimal default modules. Additional modules via job role or override. |
| `guest` | `GuestBookingToken` / `BookingManagementToken` | Separate auth path. No Django User. Token-scoped access only. |

### 3B. Hotel Scoping

**Canonical source:** `request.user.staff_profile.hotel`

**Validation rules:**
- URL `hotel_slug` is validated against `staff_profile.hotel.slug` by `IsSameHotel`
- If URL contains `hotel_identifier`, also validate against `staff_profile.hotel.subdomain` (as `IsHotelStaff` does now)
- `super_user` may access any hotel (exempted from hotel scoping in specific views)

**Old scoping paths that must NOT be authorization sources:**
- Query params (`?hotel=...`) — never used for auth, no change needed
- Request body hotel fields — never used for auth, no change needed
- `hotel_slug` from URL alone without `IsSameHotel` or `IsHotelStaff` — MUST add check where missing

**Scoping enforcement pattern:**

| Layer | Purpose | Enforcer |
|-------|---------|----------|
| Permission: hotel match | Reject requests for wrong hotel | `IsSameHotel.has_permission()` or `IsHotelStaff.has_permission()` |
| Queryset: tenant isolation | Filter DB results to correct hotel | `HotelScopedQuerysetMixin.get_queryset()` or manual `.filter(hotel=staff.hotel)` |
| Create: auto-assign hotel | Set hotel on new objects | `HotelScopedQuerysetMixin.perform_create()` or manual `serializer.save(hotel=...)` |

### 3C. Module Visibility/Access

**Computation formula:**

```python
def compute_effective_navs(tier, role, staff):
    if tier == 'super_user':
        return ALL_ACTIVE_NAV_SLUGS_FOR_HOTEL
    
    tier_navs     = TIER_DEFAULT_NAVS.get(tier, set())
    role_navs     = set(role.default_navigation_items.values_list('slug', flat=True)) if role else set()
    override_navs = set(staff.allowed_navigation_items.values_list('slug', flat=True))
    
    return tier_navs | role_navs | override_navs
```

**Tier-default feature sets:**

```python
TIER_DEFAULT_NAVS = {
    'super_staff_admin': {
        'home', 'rooms', 'bookings', 'chat', 'stock_tracker', 'housekeeping',
        'attendance', 'staff_management', 'room_services', 'maintenance',
        'entertainment', 'hotel_info', 'admin_settings',
    },
    'staff_admin': {
        'home', 'rooms', 'bookings', 'chat', 'housekeeping',
        'attendance', 'maintenance', 'hotel_info',
    },
    'regular_staff': {
        'home', 'chat',
    },
}
```

**Key distinctions:**
- `super_staff_admin`: ALL modules including `admin_settings`, `staff_management`, `stock_tracker`, `room_services`, `entertainment`
- `staff_admin`: Broader visibility for monitoring — rooms, bookings, housekeeping, attendance, maintenance, hotel_info — but NOT `admin_settings`, `staff_management`, `stock_tracker`, `room_services`, `entertainment`
- `regular_staff`: Minimal — `home` + `chat`. Everything else via job role or override.

**Module access enforcement:**

```python
# On every staff-facing view:
permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('<slug>')]
```

`HasNavPermission` calls `resolve_effective_access()` → checks `required_slug in effective_navs`.

### 3D. Action Authority

Action authority is **separate from module visibility**. A staff member may have module visibility (can see the roster page) but NOT mutation authority (cannot create/edit/delete roster entries).

**Action authority tiers:**

| Action Category | Required Tier | Examples |
|----------------|---------------|----------|
| **Platform operations** | `super_user` only | Provision hotels, manage NavigationItem CUD, view cross-hotel data |
| **Structural hotel mutations** | `super_staff_admin` (or `super_user`) | Staff creation/deletion, nav assignment, precheckin/survey config, public page builder CUD, registration codes, stock period deletion, hotel settings CUD |
| **Supervisory read + limited write** | `staff_admin` (or above) | View staff list, view roster analytics, approve housekeeping tasks, generate registration codes, manage conversations |
| **Operational CRUD** | `regular_staff` + module access | Clock in/out, create maintenance requests, manage own room tasks, post chat messages |
| **Role-specific business rules** | `role.slug`-based (not tier) | Chat hard-delete (`manager`/`admin` role), housekeeping room status transitions (`housekeeping` role), notification routing (`porter`/`receptionist` role) |

**Enforcement pattern:**

```python
# Read/list view — module visibility only
class RosterListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('attendance')]

# Mutation view — module visibility + tier gate
class RosterCreateView(APIView):
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('attendance'), IsSuperStaffAdminOrAbove]

# Role-specific action — module visibility + business rule
class HardDeleteMessageView(APIView):
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('chat')]
    # Inside view: check is_chat_manager(staff) for hard delete
```

**Actions that belong ONLY to `super_staff_admin` (or `super_user`):**

| Action | File | Current Check |
|--------|------|---------------|
| Create staff with elevated access_level | `staff/views.py` | `access_level != "super_staff_admin"` |
| Manage navigation assignments | `staff/views.py` | `access_level != 'super_staff_admin'` |
| NavigationItem CUD | `staff/views.py` | `is_superuser` (platform-level only) |
| Delete stock periods | `stock_tracker/views.py` | `access_level != 'super_staff_admin'` |
| Reopen stock periods | `stock_tracker/views.py` | `is_superuser` |
| Configure precheckin/survey | `hotel/staff_views.py` | `IsSuperStaffAdminForHotel` |
| Public page builder CUD | `hotel/staff_views.py` | `IsSuperStaffAdminForHotel` |
| Stock reports (value, sales) | `stock_tracker/report_views.py` | `IsSuperStaffAdminForHotel` |

**Actions `staff_admin` CAN do (supervisor functions):**

| Action | File | Current Check |
|--------|------|---------------|
| View staff list / pending registrations | `staff/views.py` | `access_level != 'regular_staff'` |
| Generate registration codes | `staff/views.py` | `access_level in ('staff_admin', 'super_staff_admin')` |
| View registration packages | `staff/views.py` | `access_level in ('staff_admin', 'super_staff_admin')` |
| View roster analytics (read-only) | `attendance/views_analytics.py` | Currently `[IsAuthenticated]` only |
| Approve housekeeping tasks | `housekeeping/views.py` | `is_manager(staff)` |
| Manage departments (hotel-scoped, read + limited write) | `staff/views.py` | `access_level in ('staff_admin', 'super_staff_admin')` |
| Manage roles (hotel-scoped, read + limited write) | `staff/views.py` | `access_level in ('staff_admin', 'super_staff_admin')` |

**Domain-specific action checks that remain as business rules (NOT canonical tier):**

| Rule | File | Check | Stays As-Is? |
|------|------|-------|-------------|
| Chat conversation management | `staff_chat/permissions.py` | `role.slug in ['manager', 'admin']` | Yes — centralized to `is_chat_manager()` but stays role-based |
| Chat message hard delete | `staff_chat/permissions.py` | `role.slug in ['manager', 'admin']` | Yes — centralized to `is_chat_manager()` |
| Housekeeping role check | `housekeeping/policy.py` | `role.slug == 'housekeeping'` | Yes — remains role-based business rule |
| Housekeeping room transitions | `housekeeping/policy.py` | `can_change_room_status()` | Yes — remains business rule |
| Notification targeting | `notifications/` | `role__slug='porter'`, `role__slug='receptionist'` | Yes — routing logic, not authorization |

### 3E. Override Behavior

**Semantics:** Additive only.

`Staff.allowed_navigation_items` M2M adds nav slugs **on top of** tier defaults + role defaults.

```
effective_navs = tier_defaults ∪ role_defaults ∪ overrides
```

- There is NO subtractive override. You cannot remove a default via override.
- If a staff member should NOT have a tier-default module, the correct action is to change their tier or role — not to add a "deny" override.
- The M2M stores only **additions beyond computed defaults**. During migration, items already covered by defaults are removed from the M2M.

**Where overrides plug in:**

```python
def resolve_effective_access(user):
    tier = resolve_tier(user)
    staff = user.staff_profile
    role = staff.role
    
    tier_navs     = set(TIER_DEFAULT_NAVS.get(tier, []))
    role_navs     = set(role.default_navigation_items.values_list('slug', flat=True)) if role else set()
    override_navs = set(staff.allowed_navigation_items.filter(hotel=staff.hotel, is_active=True).values_list('slug', flat=True))
    
    effective_navs = tier_navs | role_navs | override_navs
    # ... build and return payload
```

---

## 4. Detailed Implementation Order

### Execution Block 1 — Foundation (NO behavior change)

**Step 1.1: Create `resolve_tier(user)` function**
- File: `staff/permissions.py`
- Dependencies: None
- Behavior change: None (new function, not called yet)
- Verification: Unit test `resolve_tier()` with superuser, all access levels, no staff profile

**Step 1.2: Define `CANONICAL_NAV_SLUGS` and `TIER_DEFAULT_NAVS` constants**
- File: `staff/permissions.py`
- Dependencies: None
- Behavior change: None (constants defined, not used yet)

**Step 1.3: Add `Role.default_navigation_items` M2M field**
- File: `staff/models.py`
- Dependencies: None
- Behavior change: None (empty M2M, not referenced in any query yet)
- Migration: `python manage.py makemigrations staff`

**Step 1.4: Create `IsDjangoSuperUser` permission class**
- File: `staff/permissions.py`
- Dependencies: None
- Behavior change: None (new class, not imported yet)

**Step 1.5: Create `IsAdminTier` permission class**
- File: `staff/permissions.py`
- Dependencies: Step 1.1 (`resolve_tier`)
- Behavior change: None (new class, not imported yet)

**Step 1.6: Create `IsSuperStaffAdminOrAbove` permission class**
- File: `staff/permissions.py`
- Dependencies: Step 1.1 (`resolve_tier`)
- Behavior change: None (new class, not imported yet)

**Step 1.7: Create `is_chat_manager(staff)` helper**
- File: `staff_chat/permissions.py`
- Dependencies: None
- Behavior change: None (helper not called yet)

### Execution Block 2 — Canonical Resolver (NO behavior change)

**Step 2.1: Create `resolve_effective_access(user)` function**
- File: `staff/permissions.py`
- Dependencies: Steps 1.1, 1.2, 1.3
- Logic: `tier_defaults ∪ role_defaults ∪ override` computation
- **Critical:** Must return SAME payload shape as `resolve_staff_navigation()` for backward compatibility
- Behavior change: None (new function, not called yet)
- Verification: Unit test confirming `resolve_effective_access()` returns same result as `resolve_staff_navigation()` for existing data (where role defaults are empty, effective_navs = override M2M only)

**Step 2.2: Update `HasNavPermission` to use `resolve_effective_access()`**
- File: `staff/permissions.py`
- Dependencies: Step 2.1
- Behavior change: None (`HasNavPermission` has zero view usages — updating its internals changes nothing)

### Execution Block 3 — Unify Nav Slug Catalog (data normalization, minimal behavior change)

**Step 3.1: Define canonical slug list**

Reconciled list (merging signal + seed, removing duplicates):

| Slug | Source | Status |
|------|--------|--------|
| `home` | Both | Keep |
| `rooms` | Both | Keep |
| `bookings` | Both | Keep |
| `chat` | Both | Keep |
| `stock_tracker` | Both | Keep |
| `housekeeping` | Signal only | Keep |
| `attendance` | Signal only | Keep (`roster` from seed is same concept) |
| `staff_management` | Signal only | Keep (`staff` from seed is same concept) |
| `room_services` | Signal only | Keep (`room_service` from seed is same concept) |
| `maintenance` | Both | Keep |
| `entertainment` | Signal only | Keep (`games` from seed is same concept) |
| `hotel_info` | Both | Keep |
| `admin_settings` | Signal only | Keep (`settings` from seed is same concept) |
| `reception` | Seed only | **DROP** — functionality covered by `rooms` + `bookings` |
| `guests` | Seed only | **DROP** — maps to `rooms` nav slug |
| `restaurants` | Seed only | **DROP** — maps to `bookings` nav slug |
| `good_to_know` | Seed only | **DROP** — maps to `hotel_info` |
| `breakfast` | Seed only | **DROP** — maps to `room_services` |
| `roster` | Seed only | **DROP** — maps to `attendance` |
| `staff` | Seed only | **DROP** — maps to `staff_management` |
| `games` | Seed only | **DROP** — maps to `entertainment` |
| `settings` | Seed only | **DROP** — maps to `admin_settings` |
| `room_service` | Seed only | **DROP** — maps to `room_services` |

**Canonical 13 slugs:** `home`, `rooms`, `bookings`, `chat`, `stock_tracker`, `housekeeping`, `attendance`, `staff_management`, `room_services`, `maintenance`, `entertainment`, `hotel_info`, `admin_settings`

**Step 3.2: Update Hotel post-save signal**
- File: `hotel/models.py`
- Ensure signal produces exactly the canonical 13 slugs
- Current signal already produces these 13 — verify and lock down

**Step 3.3: Rewrite seed command to match canonical list**
- File: `staff/management/commands/seed_navigation_items.py`
- Replace 17-slug list with canonical 13-slug list
- Use `update_or_create` for idempotency

**Step 3.4: Data migration — normalize existing NavigationItem records**
- Management command: `normalize_nav_slugs`
- For each hotel: ensure exactly 13 canonical slugs exist
- Merge orphaned seed-only slugs into canonical equivalents in `Staff.allowed_navigation_items` M2M:
  - Staff with `roster` → add `attendance` if not present, remove `roster`
  - Staff with `staff` → add `staff_management` if not present, remove `staff`
  - Staff with `games` → add `entertainment` if not present, remove `games`
  - etc.
- Deactivate orphaned NavigationItem records (don't delete — might break FK references)

### Execution Block 4 — Wire Canonical Resolver (behavior change: nav items may change)

**Step 4.1: Replace `resolve_staff_navigation()` calls with `resolve_effective_access()`**
- `staff/views.py` L139 (login)
- `staff/views.py` L1501, L1585 (staff update)
- `staff/serializers.py` L338 (staff creation)
- `staff/me_views.py` L38, L47 (/me)
- Dependencies: Steps 2.1, 3.4 (resolver + slugs must be canonical)
- **Behavior change:** If `Role.default_navigation_items` is populated, staff may see MORE modules than before (tier defaults + role defaults kick in). If not populated yet, behavior is identical (defaults are empty sets, effective = override M2M only).

**Step 4.2: Populate `Role.default_navigation_items` for existing roles**
- Management command: `populate_role_nav_defaults`
- Map well-known role slugs to recommended nav items:
  - `housekeeping` → `home`, `chat`, `housekeeping`, `rooms`
  - `receptionist` → `home`, `chat`, `rooms`, `bookings`
  - `porter` → `home`, `chat`, `rooms`
  - `manager` → `home`, `chat`, `rooms`, `bookings`, `housekeeping`, `attendance`, `maintenance`, `stock_tracker`
  - `admin` → same as `manager` + `staff_management`, `admin_settings`
  - Other/unknown roles → `home`, `chat` (minimal)
- Dependencies: Step 1.3 (M2M field exists)
- **Behavior change:** Staff with roles will start getting role-default modules IN ADDITION to their current M2M overrides. This is intentionally additive — no one loses access.

**Step 4.3: Migrate `Staff.allowed_navigation_items` from primary to override**
- Management command: `migrate_nav_to_defaults`
- For each staff member:
  1. Compute `tier_defaults ∪ role_defaults` from their current `access_level` and `role`
  2. Compare against current `allowed_navigation_items` M2M
  3. Items in M2M already covered by defaults → remove from M2M (now redundant)
  4. Items in M2M NOT in defaults → keep (genuine overrides)
- **Behavior change:** None — `resolve_effective_access()` still returns same effective set (defaults ∪ override)
- Verification: For every staff member, compare `resolve_effective_access()` output before and after migration

### Execution Block 5 — Rename Permission Classes (behavior-preserving refactor)

**Step 5.1: Create `IsAdminTier` in `staff/permissions.py` with same logic as old `IsSuperUser`**
- Already done in Block 1 (Step 1.5)

**Step 5.2: Update `hotel/base_views.py` import**
- Old: `from staff.permissions_superuser import IsSuperUser`
- New: `from staff.permissions import IsAdminTier`
- Update `HotelViewSet.permission_classes = [IsAdminTier]`
- Behavior: Identical

**Step 5.3: Update `staff/views.py` import (if used)**
- Check for any imports of `IsSuperUser` from `staff/permissions_superuser`
- Replace with `IsAdminTier` from `staff/permissions`

**Step 5.4: Replace local `IsSuperUser` in `hotel/provisioning_views.py`**
- Remove local class definition
- Add: `from staff.permissions import IsDjangoSuperUser`
- Update `ProvisionHotelView.permission_classes = [IsDjangoSuperUser]`
- Behavior: Identical

**Step 5.5: Delete `staff/permissions_superuser.py`**
- Dependencies: Steps 5.2, 5.3 (all imports updated)
- Verification: `grep -r "permissions_superuser" .` returns zero results

### Execution Block 6 — Wire `HasNavPermission` to Views (MAIN ENFORCEMENT ROLLOUT)

**This is the core behavioral change: views now enforce module-level access.**

**Order: lowest-risk apps first, highest-risk apps last.**

**Step 6.1: `stock_tracker` (21 views, well-isolated)**
- Add `HasNavPermission('stock_tracker')` to all 21 views
- Pattern: `[IsHotelStaff, HasNavPermission('stock_tracker')]`
- For report views: keep `IsSuperStaffAdminForHotel` → change to `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('stock_tracker'), IsSuperStaffAdminOrAbove]`
- Risk: LOW — all views already hotel-scoped via `IsHotelStaff`

**Step 6.2: `maintenance` (3 views)**
- Add `HasNavPermission('maintenance')` to 3 views
- Pattern: `[IsHotelStaff, HasNavPermission('maintenance')]`
- Risk: LOW

**Step 6.3: `housekeeping` (3 views)**
- Add `HasNavPermission('housekeeping')` to 3 views
- Pattern: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('housekeeping')]`
- Risk: LOW

**Step 6.4: `attendance` (4+ views)**
- Add `HasNavPermission('attendance')` to `DailyPlanEntryViewSet`, `ShiftLocationViewSet`, `DailyPlanViewSet`, `CopyRosterViewSet`, `AnalyticsViewSet`
- Fix `AnalyticsViewSet` and `FaceRecognitionViewSet` to add `IsStaffMember` + `IsSameHotel`
- Risk: MEDIUM — mixin-based views need careful testing

**Step 6.5: `rooms` (10+ views)**
- Add `HasNavPermission('rooms')` to `StaffRoomViewSet`, FBVs
- Fix `RoomViewSet`, `RoomTypeViewSet`, `RoomByHotelAndNumberView`, `room_details` — add full stack
- Risk: MEDIUM — some views currently unscoped

**Step 6.6: `bookings` (5+ views)**
- Fix `BookingViewSet`, `RestaurantViewSet`, `AvailableTablesView`, `UnseatBookingAPIView`, `DeleteBookingAPIView` — add full stack with `HasNavPermission('bookings')`
- Risk: MEDIUM — currently unscoped views

**Step 6.7: `hotel/staff_views.py` booking management (14+ views)**
- Add `HasNavPermission('bookings')` to booking views
- Add `HasNavPermission('rooms')` to room views
- Add `HasNavPermission('admin_settings')` to config views
- Risk: MEDIUM — large file, many views

**Step 6.8: `staff_chat` + `chat` (4+ views)**
- Add `HasNavPermission('chat')` to `StaffListViewSet`, `StaffConversationViewSet`, staff-facing chat views
- Risk: LOW

**Step 6.9: `home` (3 views)**
- Fix `PostViewSet`, `CommentViewSet`, `CommentReplyViewSet` — add `IsStaffMember`, `IsSameHotel`, `HasNavPermission('home')`
- Risk: MEDIUM — currently fully open

**Step 6.10: `hotel_info`, `room_services`, `entertainment` (varies)**
- Add `HasNavPermission` to each app's staff views
- Risk: LOW

**Step 6.11: `guests` (1 view)**
- Fix `GuestViewSet` — add `IsStaffMember`, `IsSameHotel`, `HasNavPermission('rooms')`
- Risk: MEDIUM

**Step 6.12: `staff` management views**
- Add `HasNavPermission('staff_management')` to `StaffViewSet`, `DepartmentViewSet`, `RoleViewSet`, `NavigationItemViewSet`, registration views, etc.
- Risk: HIGH — these views have the most inline auth logic

### Execution Block 7 — Replace Inline Authorization Checks

**Step 7.1: Replace inline `is_superuser` checks in `staff/views.py`**
- 12 locations per the matrix in Section 2C
- Replace with `resolve_tier(request.user)` comparisons
- Dependencies: Step 1.1

**Step 7.2: Replace inline `access_level` checks in `staff/views.py`**
- 10 locations per the matrix in Section 2C
- Replace with `resolve_tier(request.user)` comparisons
- Dependencies: Step 1.1

**Step 7.3: Replace inline checks in `stock_tracker/views.py`**
- 6 locations (5 `is_superuser` + 1 `access_level`)
- Dependencies: Step 1.1

**Step 7.4: Replace inline checks in `housekeeping/views.py` and `housekeeping/policy.py`**
- 4 locations
- `is_manager()` → use `resolve_tier()`
- `is_housekeeping()` → remove `department.slug` fallback
- Dependencies: Step 1.1, data fix ensuring housekeeping staff have correct role

**Step 7.5: Replace inline check in `rooms/views.py`**
- 1 location (`bulk_checkout_rooms_by_id`)
- Dependencies: Step 1.1

**Step 7.6: Centralize `role.slug` chat checks**
- 5 authorization locations → `is_chat_manager(staff)` calls
- Keep 1 notification routing location (`chat/views.py` L817) as-is
- Dependencies: Step 1.7

### Execution Block 8 — Delete Dead Code

**Step 8.1:** Delete `staff/permissions.py::create_nav_permission()` function
**Step 8.2:** Delete `staff/permissions.py::requires_nav_permission()` function  
**Step 8.3:** Delete `hotel/auth_backends.py` (entire file)
**Step 8.4:** Delete `staff/permissions_superuser.py` (already done in Block 5)
**Step 8.5:** Remove `resolve_staff_navigation()` after confirming zero remaining call sites

Dependencies: All call sites updated in Blocks 4–7.

### Execution Block 9 — Verification & Hardening

**Step 9.1:** Run full test suite
**Step 9.2:** For every staff member in test dataset: compare `resolve_effective_access()` output against expected
**Step 9.3:** API smoke test: hit every endpoint with `regular_staff`, `staff_admin`, `super_staff_admin`, `super_user` — verify correct 200/403
**Step 9.4:** Verify no imports of deleted modules remain: `grep -r "permissions_superuser\|auth_backends\|create_nav_permission\|requires_nav_permission\|resolve_staff_navigation" .`

---

## 5. App-by-App Impact Plan

### 5.1 `staff`

**Canonical logic after refactor:**
- `staff/permissions.py` is the single canonical home for: `resolve_tier()`, `resolve_effective_access()`, `HasNavPermission`, `IsDjangoSuperUser`, `IsAdminTier`, `IsSuperStaffAdminOrAbove`, `TIER_DEFAULT_NAVS`, `CANONICAL_NAV_SLUGS`
- `staff/views.py` management views use `HasNavPermission('staff_management')` + inline `resolve_tier()` for action-level checks
- `StaffViewSet` (staff CRUD): `[IsAdminTier, HasNavPermission('staff_management')]` with inline tier escalation guard for `super_staff_admin` creation
- `NavigationItemViewSet`: `[IsDjangoSuperUser]` (platform-only CUD)
- `DepartmentViewSet`, `RoleViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('staff_management')]` with `resolve_tier()` for write gate
- Login/me/staff-update views: call `resolve_effective_access()` instead of `resolve_staff_navigation()`

**Old logic currently present:**
- 12 inline `is_superuser` checks in view bodies
- 10 inline `access_level` checks in view bodies
- Import of `IsSuperUser` from `staff/permissions_superuser.py`
- `resolve_staff_navigation()` calls in 4 locations
- Dead code: `create_nav_permission()`, `requires_nav_permission()`

**What must be replaced:**
- All 22 inline checks → `resolve_tier()` calls
- `IsSuperUser` import → `IsAdminTier`
- `resolve_staff_navigation()` calls → `resolve_effective_access()`
- Dead code deleted

**Business-rule logic that may remain:** None specific to staff app.

**Migration risk:** HIGH — most inline auth logic lives here. Most critical to get right.

---

### 5.2 `hotel`

**Canonical logic after refactor:**
- `hotel/permissions.py` keeps `IsHotelStaff` and `IsSuperStaffAdminForHotel` (both still useful)
- `hotel/staff_views.py` booking management: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]`
- `hotel/staff_views.py` room management: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]`
- `hotel/staff_views.py` public page builder: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('admin_settings'), IsSuperStaffAdminOrAbove]`
- `hotel/staff_views.py` config views: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('admin_settings'), IsSuperStaffAdminOrAbove]`
- `hotel/staff_views.py` `HotelSettingsView`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('admin_settings')]`
- `hotel/base_views.py` `HotelViewSet`: `[IsAdminTier]` (renamed from `IsSuperUser`)
- `hotel/provisioning_views.py` `ProvisionHotelView`: `[IsDjangoSuperUser]` (imported from `staff/permissions.py`)
- `hotel/overstay_views.py`: `[IsHotelStaff, HasNavPermission('bookings')]`
- `hotel/auth_backends.py` deleted

**Old logic currently present:**
- Local `IsSuperUser` in `hotel/provisioning_views.py`
- Import of `IsSuperUser` from `staff/permissions_superuser.py` in `hotel/base_views.py`
- `HotelSubdomainBackend` dead code
- ~35 views missing `HasNavPermission`
- `HotelSettingsView` and `SendPrecheckinLinkView` with only `[IsAuthenticated]`

**What must be replaced:**
- Local `IsSuperUser` → `IsDjangoSuperUser` import
- `IsSuperUser` import → `IsAdminTier`
- Add `HasNavPermission` to all 35+ views
- Fix `[IsAuthenticated]`-only views
- Delete `hotel/auth_backends.py`

**Business-rule logic that may remain:** None.

**Migration risk:** HIGH — `hotel/staff_views.py` is a very large file with 35+ views.

---

### 5.3 `rooms`

**Canonical logic after refactor:**
- `StaffRoomViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]`
- `RoomViewSet`, `RoomTypeViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]`
- `RoomByHotelAndNumberView`, `room_details`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]`
- FBVs (`bulk_create_room_types`, `bulk_create_rooms`, `update_room_floor`, `validate_room_migration`, `move_room_api`, `validate_existing_guest_move`, `move_guest_forward`, `move_guest_backward`): `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]`
- `bulk_checkout_rooms_by_id`: destructive mode gated by `resolve_tier()` instead of inline `is_superuser`

**Old logic:** `RoomViewSet`, `RoomTypeViewSet`, `RoomByHotelAndNumberView`, `room_details` have only `[IsAuthenticated]`. One inline `is_superuser` check.

**Migration risk:** MEDIUM — 4 views gain new permission requirements.

---

### 5.4 `bookings`

**Canonical logic after refactor:**
- `BookingViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]` + hotel queryset filter
- `RestaurantViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]` + hotel queryset filter
- `AvailableTablesView`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]`
- `UnseatBookingAPIView`, `DeleteBookingAPIView`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('bookings')]`

**Old logic:** All views currently `[IsAuthenticated]` only. No hotel scoping in queryset.

**Migration risk:** MEDIUM — views gain scoping for the first time. Must ensure hotel FK exists on models.

---

### 5.5 `attendance`

**Canonical logic after refactor:**
- `ShiftLocationViewSet`, `DailyPlanViewSet`, `CopyRosterViewSet` (via mixin): `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('attendance')]`
- `DailyPlanEntryViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('attendance')]`
- `AnalyticsViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('attendance')]` (currently `[IsAuthenticated]` only)
- `FaceRecognitionViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel]` (face recognition is not a nav module)

**Old logic:** Mixin-based views already have `IsStaffMember, IsSameHotel`. `AnalyticsViewSet` and `FaceRecognitionViewSet` have only `[IsAuthenticated]`.

**Migration risk:** MEDIUM — analytics currently unscoped.

---

### 5.6 `housekeeping`

**Canonical logic after refactor:**
- `HousekeepingDashboardViewSet`, `HousekeepingTaskViewSet`, `RoomStatusViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('housekeeping')]`
- `housekeeping/policy.py::is_manager()` → uses `resolve_tier()` instead of inline `access_level` check
- `housekeeping/policy.py::is_housekeeping()` → uses `role.slug` only, removes `department.slug` fallback
- `can_change_room_status()` and `can_view_dashboard()` → remain as business-rule functions

**Old logic:** Inline `access_level` checks in views and policy. `department.slug` fallback.

**Business-rule logic that remains:** `housekeeping/policy.py` functions for room status transitions — these are domain rules, not module access.

**Migration risk:** LOW — views already have `IsStaffMember, IsSameHotel`.

---

### 5.7 `maintenance`

**Canonical logic after refactor:**
- All 3 views: `[IsHotelStaff, HasNavPermission('maintenance')]`

**Old logic:** `[IsHotelStaff]` only.

**Migration risk:** LOW — well-isolated, simple views.

---

### 5.8 `stock_tracker`

**Canonical logic after refactor:**
- All 21 views: `[IsHotelStaff, HasNavPermission('stock_tracker')]`
- Report views: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('stock_tracker'), IsSuperStaffAdminOrAbove]`
- `PeriodDeleteAPIView`: `resolve_tier()` for `super_staff_admin` check (replaces inline `access_level` check)
- `PeriodReopenAPIView`: `resolve_tier()` for tier check (replaces inline `is_superuser` check)
- 5 inline `is_superuser` checks → `resolve_tier()` calls

**Old logic:** `[IsHotelStaff]` + inline `is_superuser`/`access_level` checks in 6 locations.

**Migration risk:** LOW — all views already hotel-scoped.

---

### 5.9 `staff_chat`

**Canonical logic after refactor:**
- `StaffListViewSet`, `StaffConversationViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('chat')]`
- `CanManageConversation`, `CanDeleteMessage`: use `is_chat_manager(staff)` instead of inline role.slug check
- `views_messages.py`, `views_attachments.py`: use `is_chat_manager(staff)` for role-based checks

**Old logic:** `[IsAuthenticated]` only on main views. Inline `role.slug in ['manager', 'admin']` in 5 locations.

**Business-rule logic that remains:** `is_chat_manager()` — role-based action check for chat management powers.

**Migration risk:** LOW — chat views are relatively isolated.

---

### 5.10 `chat`

**Canonical logic after refactor:**
- Staff-facing endpoints: add `HasNavPermission('chat')` where applicable
- Guest-facing endpoints: unchanged (separate token-based auth)
- Notification routing `role.slug in ['manager', 'admin']` at L817: keep as-is (routing, not auth)

**Migration risk:** LOW.

---

### 5.11 `room_services`

**Canonical logic after refactor:**
- Staff views: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('room_services')]`
- Guest views: unchanged (token-based)

**Migration risk:** LOW.

---

### 5.12 `hotel_info`

**Canonical logic after refactor:**
- Staff views: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('hotel_info')]`

**Migration risk:** LOW.

---

### 5.13 `home`

**Canonical logic after refactor:**
- `PostViewSet`, `CommentViewSet`, `CommentReplyViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('home')]`

**Old logic:** `[IsAuthenticated]` only.

**Migration risk:** MEDIUM — views gain hotel scoping for first time. Must verify models have hotel FK.

---

### 5.14 `guests`

**Canonical logic after refactor:**
- `GuestViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('rooms')]` (maps to rooms module)

**Old logic:** `[IsAuthenticated]` only.

**Migration risk:** MEDIUM — gains hotel scoping for first time.

---

### 5.15 `notifications`

**Canonical logic after refactor:**
- `SaveFcmTokenView`: `[IsAuthenticated, IsStaffMember]`
- `role__slug='porter'` / `role__slug='receptionist'` routing: unchanged (notification routing, not authorization)

**Business-rule logic that remains:** All role-based notification targeting stays as-is.

**Migration risk:** LOW.

---

### 5.16 `entertainment`

**Canonical logic after refactor:**
- `MemoryGameAchievementViewSet`, `DashboardViewSet`: `[IsAuthenticated, IsStaffMember, IsSameHotel, HasNavPermission('entertainment')]`

**Old logic:** `[IsAuthenticated]` only.

**Migration risk:** MEDIUM — gains scoping.

---

### 5.17 `voice_recognition`

**Canonical logic after refactor:**
- `VoiceRecognitionViewSet`, TTS view: `[IsAuthenticated, IsStaffMember, IsSameHotel]`
- No nav slug needed — utility function, not a module

**Migration risk:** LOW.

---

### 5.18 `common`

**Canonical logic after refactor:**
- `ThemePreferenceViewSet`: `[IsAuthenticated]` — user-scoped, no change needed
- `HotelScopedViewSetMixin`: stays as-is, optionally add `nav_slug` class attribute support
- `HotelScopedQuerysetMixin`: stays as-is

**Migration risk:** LOW.

---

## 6. Model and Data Migration Plan

### Migration 1: Add `Role.default_navigation_items` M2M

**When:** Execution Block 1 (Step 1.3)  
**Type:** Schema migration (add field)  
**Reversible:** Yes (drop M2M table)

```python
# staff/models.py — Role model
default_navigation_items = models.ManyToManyField(
    NavigationItem,
    blank=True,
    related_name='default_for_roles',
    help_text="Default navigation items for staff with this role"
)
```

```bash
python manage.py makemigrations staff --name add_role_default_nav_items
python manage.py migrate
```

**Impact:** None. Empty M2M. No existing behavior changes.

---

### Migration 2: Normalize NavigationItem slugs

**When:** Execution Block 3 (Step 3.4)  
**Type:** Data migration via management command  
**Reversible:** Yes (keep old NavigationItem records deactivated, not deleted)

**Command: `normalize_nav_slugs`**

```
For each hotel:
    1. Ensure all 13 canonical slugs exist (create missing ones)
    2. Map seed-only slugs to canonical equivalents:
       roster      → attendance
       staff       → staff_management
       games       → entertainment
       settings    → admin_settings
       room_service → room_services
       reception   → (no direct map — staff with this get rooms + bookings)
       guests      → rooms
       restaurants → bookings
       good_to_know → hotel_info
       breakfast   → room_services
    3. For each staff member with orphaned slug in allowed_navigation_items:
       - Add canonical equivalent to M2M
       - Remove orphaned slug from M2M
    4. Set is_active=False on orphaned NavigationItem records (don't delete)
```

**Verification:**
- Before: record `Staff.allowed_navigation_items` for every staff member
- After: verify each staff member's effective slugs are equivalent (mapped slugs replaced, no loss)

---

### Migration 3: Populate `Role.default_navigation_items`

**When:** Execution Block 4 (Step 4.2)  
**Type:** Data migration via management command  
**Reversible:** Yes (clear M2M)

**Command: `populate_role_nav_defaults`**

```
For each hotel:
    For each role in hotel:
        Match role.slug to recommended defaults:
        
        housekeeping:  home, chat, housekeeping, rooms
        receptionist:  home, chat, rooms, bookings
        porter:        home, chat, rooms
        manager:       home, chat, rooms, bookings, housekeeping, attendance, maintenance, stock_tracker
        admin:         home, chat, rooms, bookings, housekeeping, attendance, maintenance, stock_tracker, staff_management, admin_settings
        waiter:        home, chat, room_services
        bartender:     home, chat, stock_tracker
        chef:          home, chat, room_services, stock_tracker
        (other):       home, chat
        
        Set role.default_navigation_items to corresponding NavigationItem records for this hotel
```

**Impact:** No immediate behavior change if `resolve_effective_access()` is not yet wired. Once wired (Step 4.1), staff will see role defaults + tier defaults + overrides.

---

### Migration 4: Convert `Staff.allowed_navigation_items` from primary to override

**When:** Execution Block 4 (Step 4.3)  
**Type:** Data migration via management command  
**Reversible:** Yes (restore from backup snapshot)

**Command: `migrate_nav_to_defaults`**

```
For each staff member:
    1. Snapshot current allowed_navigation_items slugs → save to log file
    
    2. Compute expected defaults:
       tier_navs = TIER_DEFAULT_NAVS[staff.access_level]
       role_navs = staff.role.default_navigation_items.slugs() if staff.role else []
       computed_defaults = tier_navs ∪ role_navs
    
    3. Current M2M slugs:
       current_navs = staff.allowed_navigation_items.slugs()
    
    4. Genuine overrides = current_navs - computed_defaults
       Redundant entries = current_navs ∩ computed_defaults
    
    5. Remove redundant entries from M2M
       Keep genuine overrides in M2M
    
    6. Verify: resolve_effective_access(staff.user).effective_navs == original current_navs
       If mismatch → LOG WARNING, do not proceed for this staff member
```

**Verification matrix:**

| Staff | Before M2M | Computed Defaults | After M2M (overrides only) | Effective (defaults ∪ override) | Match? |
|-------|-----------|-------------------|---------------------------|--------------------------------|--------|
| Staff A | home, chat, rooms | home, chat (tier) + rooms (role) | (empty) | home, chat, rooms | ✓ |
| Staff B | home, chat, rooms, stock_tracker | home, chat (tier) + rooms (role) | stock_tracker | home, chat, rooms, stock_tracker | ✓ |

---

### Migration 5: Update Hotel post-save signal (if needed)

**When:** Execution Block 3 (Step 3.2)  
**Type:** Code change (no data migration)

Current signal already produces the canonical 13 slugs. Verify and ensure `is_active` flags match desired defaults.

---

### Migration 6: Rewrite seed command

**When:** Execution Block 3 (Step 3.3)  
**Type:** Code change (no data migration)

Replace 17-slug list with canonical 13-slug list. Use `update_or_create` for idempotency.

---

## 7. Final Permission Class / Helper Surface

### 7A. `resolve_tier(user)` — NEW

| Attribute | Value |
|-----------|-------|
| **Location** | `staff/permissions.py` |
| **Owns** | Single source of truth for "what tier is this user" |
| **No longer owns** | N/A (new) |
| **Replaces** | All inline `user.is_superuser` dispatch + `staff.access_level` dispatch across 33+ locations |
| **Returns** | `'super_user'` / `'super_staff_admin'` / `'staff_admin'` / `'regular_staff'` / `None` |

### 7B. `resolve_effective_access(user)` — NEW (replaces `resolve_staff_navigation`)

| Attribute | Value |
|-----------|-------|
| **Location** | `staff/permissions.py` |
| **Owns** | Computing effective feature keys: `tier_defaults ∪ role_defaults ∪ overrides`. Building canonical nav payload for login/me/permission checks. |
| **No longer owns** | N/A (new) |
| **Replaces** | `resolve_staff_navigation(user)` — same payload shape, new computation logic |
| **Called by** | Login view, /me view, staff update views, staff creation serializer, `HasNavPermission` |

### 7C. `HasNavPermission(required_slug)` — EXISTING, REWIRED

| Attribute | Value |
|-----------|-------|
| **Location** | `staff/permissions.py` |
| **Owns** | View-level module access enforcement. Checks `required_slug ∈ effective_navs`. |
| **No longer owns** | N/A |
| **Replaces** | The absence of module-level enforcement on 80+ views |
| **Usage** | `permission_classes = [..., HasNavPermission('stock_tracker')]` |

### 7D. `IsDjangoSuperUser` — NEW

| Attribute | Value |
|-----------|-------|
| **Location** | `staff/permissions.py` |
| **Owns** | Platform-level superuser gate. `user.is_superuser` only. |
| **No longer owns** | N/A |
| **Replaces** | Local `IsSuperUser` in `hotel/provisioning_views.py` |
| **Used by** | `ProvisionHotelView` |

### 7E. `IsAdminTier` — NEW (replaces `staff/permissions_superuser.py::IsSuperUser`)

| Attribute | Value |
|-----------|-------|
| **Location** | `staff/permissions.py` |
| **Owns** | "Is this user at least `staff_admin` tier?" Gate for any-admin access. |
| **No longer owns** | N/A |
| **Replaces** | `staff/permissions_superuser.py::IsSuperUser` (misleading name, same logic) |
| **Used by** | `HotelViewSet` (hotel CRUD by any admin) |

### 7F. `IsSuperStaffAdminOrAbove` — NEW

| Attribute | Value |
|-----------|-------|
| **Location** | `staff/permissions.py` |
| **Owns** | Mutation authority gate. Only `super_user` + `super_staff_admin` pass. `staff_admin` does NOT pass. |
| **No longer owns** | N/A |
| **Replaces** | Where `IsSuperStaffAdminForHotel` is used for mutation-only gates |
| **Used by** | Views where structural mutations require top hotel admin authority |

### 7G. `IsSuperStaffAdminForHotel` — EXISTING, KEPT

| Attribute | Value |
|-----------|-------|
| **Location** | `hotel/permissions.py` |
| **Owns** | `super_staff_admin` + hotel match from URL. Combines tier check with hotel scoping. |
| **No longer owns** | N/A |
| **Replaces** | Nothing new — stays for views that need both hotel match + super admin tier in one class |
| **Used by** | Public page builder views, config views, report views |

### 7H. `IsHotelStaff` — EXISTING, KEPT

| Attribute | Value |
|-----------|-------|
| **Location** | `hotel/permissions.py` |
| **Owns** | User is authenticated staff belonging to URL hotel (by slug or subdomain). |
| **No longer owns** | N/A |
| **Used by** | `stock_tracker`, `maintenance`, `hotel/overstay_views.py` |

### 7I. `IsStaffMember` — EXISTING, KEPT

| Attribute | Value |
|-----------|-------|
| **Location** | `staff_chat/permissions.py` |
| **Owns** | User has a `staff_profile`. Basic staff identity check. |
| **No longer owns** | N/A |
| **Used by** | Nearly every hotel-scoped view (as first in permission stack) |

### 7J. `IsSameHotel` — EXISTING, KEPT

| Attribute | Value |
|-----------|-------|
| **Location** | `staff_chat/permissions.py` |
| **Owns** | URL `hotel_slug` matches `staff_profile.hotel.slug`. Request-level hotel scoping. |
| **No longer owns** | N/A |
| **Used by** | Nearly every hotel-scoped view (paired with `IsStaffMember`) |

### 7K. `IsConversationParticipant`, `IsMessageSender` — EXISTING, KEPT

| Attribute | Value |
|-----------|-------|
| **Location** | `staff_chat/permissions.py` |
| **Owns** | Object-level ownership checks for chat messages/conversations |
| **Used by** | Chat object endpoints |

### 7L. `CanManageConversation`, `CanDeleteMessage` — EXISTING, UPDATED

| Attribute | Value |
|-----------|-------|
| **Location** | `staff_chat/permissions.py` |
| **Owns** | Role-based action checks for chat management |
| **Change** | Replace inline `role.slug in [...]` with `is_chat_manager(staff)` call |

### 7M. `is_chat_manager(staff)` — NEW helper

| Attribute | Value |
|-----------|-------|
| **Location** | `staff_chat/permissions.py` |
| **Owns** | Centralized "is this staff member a chat manager" check: `role.slug in ['manager', 'admin']` |
| **Replaces** | 5 scattered inline `role.slug in ['manager', 'admin']` checks across chat files |

### 7N. `TIER_DEFAULT_NAVS` — NEW constant

| Attribute | Value |
|-----------|-------|
| **Location** | `staff/permissions.py` |
| **Owns** | Mapping from tier → default nav slug set |

### 7O. `CANONICAL_NAV_SLUGS` — NEW constant

| Attribute | Value |
|-----------|-------|
| **Location** | `staff/permissions.py` |
| **Owns** | Single source of truth for valid nav slugs |

### 7P. `housekeeping/policy.py` functions — EXISTING, UPDATED

| Function | Change |
|----------|--------|
| `is_manager(staff)` | Use `resolve_tier(staff.user)` instead of inline `access_level` check |
| `is_housekeeping(staff)` | Remove `department.slug` fallback, use `role.slug` only |
| `can_change_room_status()` | No change — remains business-rule function |
| `can_view_dashboard()` | No change — remains business-rule function |

---

## 8. Legacy Cleanup Plan

### 8A. Dead Code to Delete

| Item | File | When | Verification |
|------|------|------|-------------|
| `create_nav_permission()` | `staff/permissions.py` | Block 8 | `grep -r "create_nav_permission" .` → 0 results |
| `requires_nav_permission()` | `staff/permissions.py` | Block 8 | `grep -r "requires_nav_permission" .` → 0 results |
| `HotelSubdomainBackend` class + entire file | `hotel/auth_backends.py` | Block 8 | `grep -r "HotelSubdomainBackend\|auth_backends" .` → 0 results (except settings if referenced) |
| `IsSuperUser` class + entire file | `staff/permissions_superuser.py` | Block 5 | `grep -r "permissions_superuser" .` → 0 results |
| Local `IsSuperUser` class | `hotel/provisioning_views.py` | Block 5 | Class definition removed, import replaces it |
| `resolve_staff_navigation()` | `staff/permissions.py` | Block 8 | `grep -r "resolve_staff_navigation" .` → 0 results |

### 8B. Inline Authorization Paths Made Redundant

| Category | Count | Files | Replaced By |
|----------|-------|-------|------------|
| Inline `request.user.is_superuser` in view bodies | 19 | `staff/views.py`, `stock_tracker/views.py`, `rooms/views.py`, `housekeeping/views.py` | `resolve_tier()` calls |
| Inline `staff.access_level in (...)` in view bodies | 14 | `staff/views.py`, `stock_tracker/views.py`, `housekeeping/views.py`, `housekeeping/policy.py` | `resolve_tier()` calls |
| Inline `role.slug in ['manager', 'admin']` | 5 auth | `staff_chat/permissions.py`, `staff_chat/views_messages.py`, `staff_chat/views_attachments.py` | `is_chat_manager()` |
| `department.slug == 'housekeeping'` | 1 | `housekeeping/policy.py` | Removed (role-only check) |

### 8C. Old Permission Class Names Removed

| Old Name | Old Location | Replaced By | New Location |
|----------|-------------|------------|-------------|
| `IsSuperUser` | `staff/permissions_superuser.py` | `IsAdminTier` | `staff/permissions.py` |
| `IsSuperUser` (local) | `hotel/provisioning_views.py` | `IsDjangoSuperUser` | `staff/permissions.py` |

### 8D. Old Resolver Removed

| Old | Old Location | Replaced By | New Location |
|-----|-------------|------------|-------------|
| `resolve_staff_navigation()` | `staff/permissions.py` | `resolve_effective_access()` | `staff/permissions.py` |

---

## 9. Risks and Verification Checklist

### 9A. Most Dangerous Areas

| Risk Area | Severity | Why |
|-----------|----------|-----|
| **`staff/views.py` inline auth replacement** | CRITICAL | 22 inline auth checks. One wrong tier comparison = privilege escalation or lockout. |
| **Views gaining `HasNavPermission` for the first time** | HIGH | 80+ views that currently have NO module enforcement. Staff who lack the nav slug will get 403 where they previously got 200. |
| **`Staff.allowed_navigation_items` M2M migration** | HIGH | If tier/role defaults don't fully cover what a staff member had before, they lose access to modules. |
| **`bookings/views.py` gaining hotel scoping** | HIGH | `BookingViewSet` and `RestaurantViewSet` currently have no hotel filter. Adding one could hide data if models lack proper hotel FK. |
| **`home/views.py` gaining hotel scoping** | MEDIUM | Posts/comments currently visible to all authenticated users. Adding hotel scoping changes visibility. |
| **`IsSuperStaffAdminOrAbove` vs `IsSuperStaffAdminForHotel`** | MEDIUM | Must not mix up: `IsSuperStaffAdminOrAbove` checks tier only. `IsSuperStaffAdminForHotel` also checks hotel match. Using wrong one = cross-hotel access or unnecessary denial. |

### 9B. What Could Break

| Scenario | Impact | Prevention |
|----------|--------|-----------|
| Staff member's computed defaults don't cover their current M2M | **Access loss** — staff can't reach modules they could before | Migration command verifies effective access before and after for every staff member |
| Nav slug not in `CANONICAL_NAV_SLUGS` used in `HasNavPermission` | **Silent 403** — permission check fails because slug doesn't exist | Use constant reference, not string literals. Lint check. |
| `role.default_navigation_items` not populated for a role | **Reduced access** — role adds nothing to effective set | Fallback: regular_staff with no role gets `home`, `chat` from tier defaults. Management command populates all known roles. |
| `BookingViewSet` queries break after adding hotel filter | **Missing data** — bookings not linked to hotel correctly | Check that Booking model has hotel FK before adding filter. If not, scoping must be via related field (e.g., `room__hotel`). |
| Super_user bypass removed accidentally | **Platform admin locked out** | `resolve_tier()` always returns `super_user` first. `HasNavPermission` checks superuser bypass. All permission classes check superuser. |

### 9C. What Must Be Tested After Each Phase

| Phase | Test |
|-------|------|
| Block 1 (Foundation) | Unit test `resolve_tier()` with all 5 actor types. Unit test permission classes with mock requests. |
| Block 2 (Resolver) | Unit test `resolve_effective_access()` returns same result as old `resolve_staff_navigation()` when role defaults are empty. |
| Block 3 (Nav slugs) | Verify every hotel has exactly 13 canonical NavigationItem records. Verify staff M2M references only canonical slugs. |
| Block 4 (Wire resolver) | Login response includes correct nav items. /me response matches. Staff who had `n` modules still have `n` modules. |
| Block 5 (Rename) | `grep` confirms no remaining imports of old names. All views using renamed classes still return 200 for authorized users. |
| Block 6 (HasNavPermission rollout) | For each app: API test that `regular_staff` without the nav slug gets 403. `super_staff_admin` gets 200. Staff with nav slug gets 200. |
| Block 7 (Inline replacement) | Regression test every view with inline auth: same users get same access as before. Escalation prevention still works. |
| Block 8 (Cleanup) | `grep` confirms zero references to deleted symbols. Full test suite passes. |
| Block 9 (Final) | Full 4-tier smoke test: hit every endpoint with `regular_staff`, `staff_admin`, `super_staff_admin`, `super_user`. |

### 9D. Comparisons Before Deleting Old Logic

| Before Deleting | Compare |
|----------------|---------|
| `resolve_staff_navigation()` | For every staff member in test data: `resolve_effective_access().effective_navs == resolve_staff_navigation().allowed_navs` after migration |
| `IsSuperUser` from `permissions_superuser.py` | `IsAdminTier` grants identical access to same users (test with `is_superuser`, `super_staff_admin`, `staff_admin`, `regular_staff`) |
| Local `IsSuperUser` in provisioning | `IsDjangoSuperUser` grants identical access |
| Inline `is_superuser` checks | Test view before/after: same user gets same response |
| Inline `access_level` checks | Test view before/after: same user gets same response |

### 9E. Intentional Visibility Changes vs Parity

| Change | Intentional or Parity? |
|--------|----------------------|
| `regular_staff` without nav slug gets 403 on module views | **INTENTIONAL** — this is the whole point of the refactor. Currently no module enforcement exists. |
| `staff_admin` gets read access to attendance/roster but cannot CUD | **INTENTIONAL** — confirmed by business rule #4. |
| Staff members get MORE modules via tier/role defaults | **INTENTIONAL** — defaults are additive. Previously, access required manual M2M assignment for every staff member. |
| `BookingViewSet` / `RestaurantViewSet` gain hotel scoping | **INTENTIONAL** — these views were security gaps (no hotel filter). |
| `PostViewSet`, `CommentViewSet` gain hotel scoping | **INTENTIONAL** — previously visible to all authenticated users. |
| `staff_admin` cannot access `admin_settings`, `staff_management`, `stock_tracker` | **INTENTIONAL** — per tier-default definition. `super_staff_admin`-only modules. Can be overridden per-user if needed. |
| Role defaults give houekeeping staff automatic `housekeeping` module access | **INTENTIONAL** — replaces manual M2M assignment. |
| After M2M migration, `Staff.allowed_navigation_items` is mostly empty | **EXPECTED** — items moved to defaults. Effective access unchanged. |

---

## 10. Clarification Questions

**Q1: `bookings/views.py` model scoping**
`BookingViewSet` and `RestaurantViewSet` currently have no hotel filter. Does the `Booking` model have a direct `hotel` FK, or must hotel be derived through a related field (e.g., `room__hotel`, `restaurant__hotel`)? This determines how to add the queryset filter. Need to verify before implementing Block 6 Step 6.6.

**Q2: `home/views.py` model scoping**
Do `Post`, `Comment`, `CommentReply` models have a `hotel` FK? If not, how should hotel scoping be applied? Through `author__staff_profile__hotel`? Need to verify before implementing Block 6 Step 6.9.

**Q3: `entertainment/views.py` model scoping**
Do the game/entertainment models have a `hotel` FK? Need to verify which views are hotel-scoped vs user-scoped before adding `IsSameHotel`.

**Q4: `staff_admin` department/role write access**
Currently `DepartmentViewSet.check_write_permission()` and `RoleViewSet.check_write_permission()` allow both `staff_admin` and `super_staff_admin` to write. Per confirmed business rule #4, should department/role CUD be restricted to `super_staff_admin` only? Or is this a supervisor function that `staff_admin` can do?

**Q5: `IsHotelStaff` vs `IsStaffMember + IsSameHotel` unification**
`IsHotelStaff` (hotel/permissions.py) and `IsStaffMember + IsSameHotel` (staff_chat/permissions.py) serve overlapping purposes. Should we keep both or unify? `IsHotelStaff` does a `Staff.objects.get()` query. `IsStaffMember` uses `hasattr(request.user, 'staff_profile')`. Do we want to standardize on one pattern and deprecate the other?

---

*End of canonical refactor map. Ready for execution upon clarification answers.*
