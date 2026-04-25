# HotelMates Full Backend RBAC Audit

> Code-derived canonical-truth inventory.
> Every claim cites a concrete `path/to/file.py::Symbol` or `file:Lstart-Lend`.
> No code or tests modified during this audit. Docs/comments were NOT used as truth.

---

## 1. Global RBAC Architecture

### 1.1 Canonical capability registry

Source: [staff/capability_catalog.py](staff/capability_catalog.py)

- `CANONICAL_CAPABILITIES` (L406–L497) — Frozen set of every action permission slug enforced by the backend. Naming convention `domain.resource.action` (e.g. `booking.record.update`, `housekeeping.task.assign`).
- `TIER_DEFAULT_CAPABILITIES` (L755–L764) — `super_staff_admin` → supervisor authority + booking supervise; `staff_admin` → supervisor authority; `regular_staff` → empty.
- `ROLE_PRESET_CAPABILITIES` (L779–L1037) — Keyed by canonical role slug (e.g. `hotel_manager` → full manage bundle for bookings/rooms/housekeeping/maintenance/staff_management).
- `DEPARTMENT_PRESET_CAPABILITIES` (L1051–L1087) — Keyed by canonical department slug (e.g. `front_office` → booking operate + room read; `housekeeping` → room operate + housekeeping operate).
- `resolve_capabilities(tier, role_slug, department_slug, is_superuser)` (L799–L838) — Pure deterministic union; superuser short-circuits to ALL canonical caps; unknown tier/role/dept contribute nothing; result filtered against `CANONICAL_CAPABILITIES` (fail-closed on drift).
- `validate_preset_maps()` (L841–L860) — Returns `[]` when preset maps are self-consistent.

### 1.2 Module/action policy registry

Source: [staff/module_policy.py](staff/module_policy.py)

- `MODULE_POLICY` (L74–L222) — Dict mapping module slug → `{view_capability, read_capability, actions: {action_key → capability_slug}}`. Five modules registered:
  - `bookings` (L74–L97) — 12 action keys
  - `rooms` (L98–L119) — 13 action keys
  - `housekeeping` (L120–L135) — 10 action keys
  - `maintenance` (L136–L157) — 12 action keys
  - `staff_management` (L158–L222) — 24 action keys
- `resolve_module_policy(allowed_capabilities)` (L229–L267) — Builds `user.rbac` shape:

```python
{
  "<module>": {
    "visible": bool,            # view_capability ∈ allowed_capabilities
    "read":    bool,            # read_capability ∈ allowed_capabilities
    "actions": { "<action_key>": bool }  # capability ∈ allowed_capabilities
  }
}
```

Fail-closed: empty input → all `False`; unknown caps drift to `False` (L258–L259).

- `validate_module_policy()` (L270–L290) — Returns `[]` when every capability referenced by the registry is canonical.

### 1.3 Canonical role / department / nav registries

- Roles: [staff/role_catalog.py](staff/role_catalog.py) — `CANONICAL_ROLES` (L26–L110), `CANONICAL_ROLE_SLUGS` (L112–L114), `ROLE_DEPARTMENT_SLUG` (L116–L118), `LEGACY_ROLE_REMAP` (L150–L155), `resolve_legacy_manager_target` (L163–L168).
- Departments: [staff/department_catalog.py](staff/department_catalog.py) — `CANONICAL_DEPARTMENTS` (L17–L75, 8 depts), `CANONICAL_DEPARTMENT_SLUGS` (L82–L84), `DEPARTMENT_SLUG_ALIASES` (L94–L97).
- Navigation: [staff/nav_catalog.py](staff/nav_catalog.py) — `CANONICAL_NAV_SLUGS` (L12–L15, 12 slugs), `CANONICAL_NAV_ITEMS` (L17–L79). Assertion (L82–L84) enforces parity.

### 1.4 Backend enforcement plumbing

Source: [staff/permissions.py](staff/permissions.py)

- `resolve_tier(user)` (L61–L80) — Single source of truth for tier. `is_superuser=True` → `'super_user'`; else `staff.access_level`; else `None`.
- `TIER_HIERARCHY` (L58) = `('super_user', 'super_staff_admin', 'staff_admin', 'regular_staff')`.
- `_tier_at_least(tier, minimum)` (L83–L90).
- `resolve_effective_access(user)` (L97–L228) — **Canonical authority resolver**. Returns:
  ```python
  {
    'is_staff', 'is_superuser', 'hotel_slug',
    'access_level', 'tier',
    'department_slug', 'role_slug',
    'allowed_navs', 'navigation_items',
    'allowed_capabilities', 'rbac',
  }
  ```
  Three branches: unauthenticated (L99–L111), Django superuser → all caps + all hotel navs (L114–L148), staff member → tier∪role∪override navs (L191–L211) + `resolve_capabilities` (L215–L220) + `resolve_module_policy` (L221).
- `TIER_DEFAULT_NAVS` (L36–L48) — `super_staff_admin` = all 12; `staff_admin` = 9 (no staff_management/admin_settings/room_services); `regular_staff` = `{home, chat}`.

#### Permission classes

- `HasCapability(required_capability)` (L726–L775) — Capability gate. Safe-method bypass toggleable (`safe_methods_bypass=False` for read gates). Django superuser passes. Reads `allowed_capabilities` from resolver. Fail-closed on unknown capability (L749–L751).
- `has_capability(user, capability)` (L778–L795) — Imperative helper.
- `staff_with_capability(hotel, capability)` (L798–L841) — ORM companion. Returns active staff in hotel matching tier/role/dept presets.
- Module action classes (file enforces them):
  - Bookings (L806–L853): `CanViewBookings`, `CanReadBookings`, `CanUpdateBooking`, `CanCancelBooking`, `CanAssignBookingRoom`, `CanCheckInBooking`, `CanCheckOutBooking`, `CanCommunicateWithBookingGuest`, `CanSuperviseBooking`, `CanManageBookingConfig`.
  - Rooms (L877–L947): `CanViewRooms`, `CanReadRoomInventory`, `CanCreateRoomInventory`, `CanUpdateRoomInventory`, `CanDeleteRoomInventory`, `CanReadRoomTypes`, `CanManageRoomTypes`, `CanReadRoomMedia`, `CanManageRoomMedia`, `CanReadRoomStatus`, `CanTransitionRoomStatus`, `CanInspectRoom`, `CanFlagRoomMaintenance`, `CanClearRoomMaintenance`, `CanSetRoomOutOfOrder`, `CanBulkCheckoutRooms`, `CanDestructiveCheckoutRooms`.
  - Housekeeping (L976–L1051): `CanViewHousekeepingModule`, `CanReadHousekeepingDashboard`, `CanReadHousekeepingTasks`, `CanCreate/Update/Delete/Assign/Execute/CancelHousekeepingTask`, `CanTransition/FrontDesk/OverrideHousekeepingRoomStatus`, `CanReadHousekeepingStatusHistory`.
  - Maintenance (L1080–L1159): `CanViewMaintenanceModule`, `CanRead/Create/Accept/Resolve/Update/Reassign/Reopen/Close/DeleteMaintenanceRequest`, `CanCreate/ModerateMaintenanceComment`, `CanUpload/DeleteMaintenancePhoto`.
  - Staff management (L1191–L1280): 22 classes covering staff CRUD, authority, departments, roles, registration packages.
- Tier-only legacy gates:
  - `IsDjangoSuperUser` (L254–L263), `IsAdminTier` (L266–L274), `IsSuperStaffAdminOrAbove` (L277–L285).
  - Action-bundle tier gates: `CanManageRoster`, `CanManageStaff`, `CanManageRoomBookings`, `CanManageRestaurantBookings`, `CanConfigureHotel`, `CanManageHousekeeping`, `CanManageMaintenance`, `CanManageRoomServices`, `CanManageStaffChat` (L309–L410).
- Nav visibility classes:
  - `HasNavPermission(required_slug)` (L237–L251) — module visibility only.
  - Slug-bound subclasses (L413+): `HasRoomsNav`, `HasRoomBookingsNav`, `HasRestaurantBookingsNav`, `HasHotelInfoNav`, `HasAdminSettingsNav`, `HasAttendanceNav`, `HasStaffManagementNav`, `HasHousekeepingNav`, `HasRoomServicesNav`, `HasChatNav`, `HasHomeNav`, `HasMaintenanceNav`.
- Anti-escalation helpers (Phase 6E.1, [staff/permissions.py](staff/permissions.py) L1283–L1434): `assert_not_self_authority`, `assert_same_hotel`, `assert_access_level_allowed`, `assert_nav_subset`, `assert_role_department_ceiling`. Order: not-self → same-hotel → access-level → nav-subset → role-dept-ceiling.

#### Domain policy modules

- [housekeeping/policy.py](housekeeping/policy.py) — `can_change_room_status` (L63–L105) precedence: `housekeeping.room_status.override` → `.transition` → `.front_desk`; `can_assign_task` (L108–L122); `can_view_dashboard` (L125–L137).

### 1.5 Guest / public access plumbing (separate axis)

- [common/guest_access.py](common/guest_access.py) — `hash_token` (L80–L88). GuestBookingToken (GBT) primary, BookingManagementToken (BMT) fallback.
- Guest endpoints DO NOT call `resolve_effective_access` and DO NOT consult `allowed_capabilities`. Token scope = single booking (vs staff scope = hotel).

### 1.6 Three orthogonal axes (the canonical separation)

| Axis | Field | Built by | Consumed by | Authority? |
|---|---|---|---|---|
| Navigation visibility | `allowed_navs`, `navigation_items` | `resolve_effective_access` L191–L214 | `HasNavPermission`, frontend sidebar | **No** — display only |
| Backend action authorization | `allowed_capabilities`, `rbac` | `resolve_capabilities` + `resolve_module_policy` (L215–L221) | `HasCapability` subclasses (`CanX`), `has_capability()` in views/services | **Yes** — sole source of truth |
| Guest/public access | (token) | `common/guest_access.py`, custom DRF auth classes | `GuestBookingToken`, `BookingManagementToken`, `GuestChatSession` permission classes | Token-scoped; not RBAC |

Visibility ⊥ Authority: a staff member can hold `bookings` nav without `booking.record.update`, and vice versa.

---

## 2. Complete App / Module Inventory

| App | Staff-facing? | Guest-facing? | Public? | Canonical RBAC covered? | Source files |
|---|---|---|---|---|---|
| attendance | ✓ | ✗ | ✗ | NO (nav + tier) | [attendance/urls.py](attendance/urls.py), [attendance/views.py](attendance/views.py), [attendance/face_views.py](attendance/face_views.py), [attendance/views_analytics.py](attendance/views_analytics.py) |
| bookings (restaurant) | ✓ | partial | ✓ (form) | NO (nav + tier) | [bookings/urls.py](bookings/urls.py), [bookings/staff_urls.py](bookings/staff_urls.py), [bookings/views.py](bookings/views.py) |
| chat (guest↔staff) | ✓ | ✓ | ✗ | NO (auth-only / inline role) | [chat/urls.py](chat/urls.py), [chat/staff_urls.py](chat/staff_urls.py), [chat/views.py](chat/views.py) |
| common | ✓ | ✗ | ✗ | NO (auth-only) | [common/urls.py](common/urls.py), [common/views.py](common/views.py) |
| entertainment | partial | ✓ | ✓ | NO (AllowAny / tier) | [entertainment/urls.py](entertainment/urls.py), [entertainment/views.py](entertainment/views.py) |
| guests | ✓ | ✗ | ✗ | NO (auth-only) | [guests/urls.py](guests/urls.py), [guests/views.py](guests/views.py) |
| home | ✓ | ✗ | ✗ | NO (nav-only) | [home/urls.py](home/urls.py), [home/views.py](home/views.py) |
| hotel (core / provisioning / public / settings) | ✓ | ✓ | ✓ | partial — bookings module + super_user gates | [hotel/urls.py](hotel/urls.py), [hotel/staff_views.py](hotel/staff_views.py), [hotel/public_views.py](hotel/public_views.py), [hotel/booking_views.py](hotel/booking_views.py), [hotel/payment_views.py](hotel/payment_views.py), [hotel/provisioning_views.py](hotel/provisioning_views.py), [hotel/base_views.py](hotel/base_views.py) |
| hotel_info | ✓ | ✗ | ✗ | NO (nav + tier) | [hotel_info/urls.py](hotel_info/urls.py), [hotel_info/views.py](hotel_info/views.py) |
| housekeeping | ✓ | ✗ | ✗ | **YES (canonical)** | [housekeeping/staff_urls.py](housekeeping/staff_urls.py), [housekeeping/views.py](housekeeping/views.py), [housekeeping/policy.py](housekeeping/policy.py) |
| maintenance | ✓ | ✗ | ✗ | **YES (canonical)** | [maintenance/urls.py](maintenance/urls.py), [maintenance/views.py](maintenance/views.py) |
| notifications | ✓ | ✓ | ✗ | NO (infrastructure) | [notifications/urls.py](notifications/urls.py), [notifications/views.py](notifications/views.py), [notifications/notification_manager.py](notifications/notification_manager.py) |
| room_bookings | ✓ | ✗ | ✗ | **YES (canonical)** | [room_bookings/staff_urls.py](room_bookings/staff_urls.py), [hotel/staff_views.py](hotel/staff_views.py) |
| room_services | partial | ✓ | ✗ | partial (routing caps only) | [room_services/urls.py](room_services/urls.py), [room_services/views.py](room_services/views.py) |
| rooms | ✓ | ✗ | ✗ | **YES (canonical)** | [rooms/staff_urls.py](rooms/staff_urls.py), [rooms/views.py](rooms/views.py) |
| staff | ✓ | ✗ | ✗ | **YES (canonical, staff_management)** | [staff/urls.py](staff/urls.py), [staff/views.py](staff/views.py), [staff/me_views.py](staff/me_views.py) |
| staff_chat | ✓ | ✗ | ✗ | partial (capability for moderation) | [staff_chat/urls.py](staff_chat/urls.py), [staff_chat/views_messages.py](staff_chat/views_messages.py), [staff_chat/views_attachments.py](staff_chat/views_attachments.py) |
| stock_tracker | ✓ | ✗ | ✗ | NO (nav + inline `is_superuser`) | [stock_tracker/urls.py](stock_tracker/urls.py), [stock_tracker/views.py](stock_tracker/views.py), [stock_tracker/report_views.py](stock_tracker/report_views.py), [stock_tracker/comparison_views.py](stock_tracker/comparison_views.py) |
| posts | unknown | – | – | UNKNOWN_NEEDS_INSPECTION | [posts/](posts/) |
| promo_docs | – | – | – | NO ENDPOINTS | [promo_docs/](promo_docs/) |
| voice_recognition | – | – | – | NO ENDPOINTS | [voice_recognition/](voice_recognition/) |
| tools | – | – | – | NO ENDPOINTS | [tools/](tools/) |

---

## 3. Complete Endpoint Inventory

> Status legend: `CANONICAL_RBAC`, `PUBLIC_ALLOWANY_EXPECTED`, `GUEST_TOKEN_EXPECTED`, `AUTH_ONLY_NEEDS_REVIEW`, `ROLE_OR_TIER_LEGACY`, `NAV_SECURITY_LEGACY`, `UNPROTECTED_GAP`, `UNKNOWN_NEEDS_INSPECTION`.

### 3.1 PUBLIC zone (`/api/public/`)

| URL | Method | View | App | Access | Permission classes | Module | Action | Status |
|---|---|---|---|---|---|---|---|---|
| `/presets/` | GET | `hotel/public_views.py::PublicPresetsView` | hotel | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotels/` | GET | `hotel/public_views.py::HotelPublicListView` | hotel | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotels/filters/` | GET | `hotel/public_views.py::HotelFilterOptionsView` | hotel | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotel/<slug>/page/` | GET | `hotel/public_views.py::HotelPublicPageView` | hotel | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotel/<slug>/availability/` | GET | `hotel/booking_views.py::HotelAvailabilityView` | hotel | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotel/<slug>/pricing/quote/` | POST | `hotel/booking_views.py::HotelPricingQuoteView` | hotel | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotel/<slug>/bookings/` | POST | `hotel/booking_views.py::HotelBookingCreateView` | hotel | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotel/<slug>/room-bookings/<id>/` | GET | `hotel/booking_views.py::PublicRoomBookingDetailView` | hotel | PUBLIC | `[GuestBookingToken]` | room_bookings | booking.record.read | GUEST_TOKEN_EXPECTED |
| `/hotel/<slug>/room-bookings/<id>/cancel/` | POST | `hotel/public_views.py::BookingStatusView` | hotel | PUBLIC | `[GuestBookingToken]` | room_bookings | booking.record.cancel | GUEST_TOKEN_EXPECTED |
| `/hotel/<slug>/room-bookings/<id>/payment/` | POST | `hotel/payment_views.py::CreatePaymentSessionView` | hotel | PUBLIC | `[GuestBookingToken]` | – | – | GUEST_TOKEN_EXPECTED |
| `/hotel/<slug>/room-bookings/<id>/payment/verify/` | POST | `hotel/payment_views.py::VerifyPaymentView` | hotel | PUBLIC | `[GuestBookingToken]` | – | – | GUEST_TOKEN_EXPECTED |
| `/hotel/room-bookings/stripe-webhook/` | POST | `hotel/payment_views.py::StripeWebhookView` | hotel | PUBLIC | `[AllowAny]` (Stripe sig) | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotels/<slug>/booking/status/<id>/` | GET | `hotel/public_views.py::BookingStatusView` | hotel | PUBLIC | `[BookingManagementToken]` | room_bookings | booking.record.read | GUEST_TOKEN_EXPECTED |
| `/booking/validate-token/` | POST | `hotel/public_views.py::ValidateBookingManagementTokenView` | hotel | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/booking/cancel/` | POST | `hotel/public_views.py::CancelBookingView` | hotel | PUBLIC | `[BookingManagementToken]` | room_bookings | booking.record.cancel | GUEST_TOKEN_EXPECTED |
| `/hotels/<slug>/cancellation-policy/` | GET | `hotel/public_views.py::HotelCancellationPolicyView` | hotel | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotel/<slug>/precheckin/` | POST | `hotel/public_views.py::ValidatePrecheckinTokenView` | hotel | PUBLIC | `[AllowAny]` (token) | – | – | GUEST_TOKEN_EXPECTED |
| `/hotel/<slug>/precheckin/submit/` | POST | `hotel/public_views.py::SubmitPrecheckinDataView` | hotel | PUBLIC | `[AllowAny]` (token) | – | – | GUEST_TOKEN_EXPECTED |
| `/hotel/<slug>/survey/` | POST | `hotel/public_views.py::ValidateSurveyTokenView` | hotel | PUBLIC | `[AllowAny]` (token) | – | – | GUEST_TOKEN_EXPECTED |
| `/hotel/<slug>/survey/submit/` | POST | `hotel/public_views.py::SubmitSurveyDataView` | hotel | PUBLIC | `[AllowAny]` (token) | – | – | GUEST_TOKEN_EXPECTED |

### 3.2 GUEST zone (`/api/guest/`)

| URL | Method | View | App | Access | Permission classes | Module | Action | Status |
|---|---|---|---|---|---|---|---|---|
| `/context/` | GET | `hotel/guest_portal_views.py::GuestContextView` | hotel | GUEST | `[GuestBookingToken]` | – | – | GUEST_TOKEN_EXPECTED |
| `/hotels/<slug>/` (+ `/site/home/`, `/site/rooms/`) | GET | `guest_urls.py::guest_home`, `::guest_rooms` | hotel | GUEST | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotels/<slug>/availability/` | GET | `guest_urls.py::check_availability` | hotel | GUEST | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotels/<slug>/pricing/quote/` | POST | `guest_urls.py::get_pricing_quote` | hotel | GUEST | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotels/<slug>/bookings/` | POST | `guest_urls.py::create_booking` | hotel | GUEST | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotels/<slug>/room-services/orders/` | GET, POST | `room_services/views.py::OrderViewSet` | room_services | GUEST | `[AllowAny]` (token in header) | – | – | GUEST_TOKEN_EXPECTED |
| `/hotels/<slug>/room/<num>/menu/` | GET | `room_services/views.py::RoomServiceItemViewSet` | room_services | GUEST | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/hotel/<slug>/chat/context` | GET | `hotel/canonical_guest_chat_views.py::GuestChatContextView` | chat | GUEST | `[GuestToken or GuestChatSession]` | – | – | GUEST_TOKEN_EXPECTED |
| `/hotel/<slug>/chat/messages` | POST | `hotel/canonical_guest_chat_views.py::GuestChatSendMessageView` | chat | GUEST | `[GuestChatSession]` | – | – | GUEST_TOKEN_EXPECTED |
| `/hotel/<slug>/chat/pusher/auth` | POST | `hotel/canonical_guest_chat_views.py::GuestChatPusherAuthView` | chat | GUEST | `[GuestChatSession]` | – | – | GUEST_TOKEN_EXPECTED |
| `/hotel/<slug>/chat/conversations/<id>/mark_read/` | POST | `hotel/canonical_guest_chat_views.py::GuestChatMarkReadView` | chat | GUEST | `[GuestChatSession]` | – | – | GUEST_TOKEN_EXPECTED |

### 3.3 STAFF zone — auth & profile

| URL | Method | View | Access | Permission classes | Module | Action | Status |
|---|---|---|---|---|---|---|---|
| `/api/staff/login/` | POST | `staff/views.py::CustomAuthToken` | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/api/staff/register/` | POST | `staff/views.py::StaffRegisterAPIView` | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/api/staff/password-reset/` | POST | `staff/views.py::PasswordResetRequestView` | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/api/staff/password-reset-confirm/` | POST | `staff/views.py::PasswordResetConfirmView` | PUBLIC | `[AllowAny]` | – | – | PUBLIC_ALLOWANY_EXPECTED |
| `/api/staff/hotel/<slug>/me/` | GET | `staff/me_views.py::StaffMeView` | STAFF | `[IsAuthenticated]` | – | – | AUTH_ONLY_NEEDS_REVIEW |

### 3.4 STAFF zone — staff_management (canonical, Phase 6E.1)

All endpoints chain `IsAuthenticated + IsStaffMember + IsSameHotel + CanViewStaffManagementModule + <action>` unless noted. Source: [staff/views.py](staff/views.py), [staff/urls.py](staff/urls.py).

| URL | Method | View | Action gate | Action key | Status |
|---|---|---|---|---|---|
| `/api/staff/<slug>/` | GET | `StaffViewSet.list` | `CanReadStaff` | `staff_management.staff.read` | CANONICAL_RBAC |
| `/api/staff/<slug>/` | POST | `StaffViewSet.create` | `CanCreateStaff` | `staff_management.staff.create` | CANONICAL_RBAC |
| `/api/staff/<slug>/<pk>/` | GET | `StaffViewSet.retrieve` | `CanReadStaff` | `staff_management.staff.read` | CANONICAL_RBAC |
| `/api/staff/<slug>/<pk>/` | PUT, PATCH | `StaffViewSet.update` | `CanUpdateStaffProfile` (anti-escalation helpers) | `staff_management.staff.update_profile` | CANONICAL_RBAC |
| `/api/staff/<slug>/<pk>/` | DELETE | `StaffViewSet.destroy` | `CanDeleteStaff` | `staff_management.staff.delete` | CANONICAL_RBAC |
| `/api/staff/<slug>/departments/…` | GET / POST / PATCH / DELETE | `DepartmentViewSet` | `CanReadStaffDepartments` / `CanManageStaffDepartments` | `staff_management.department.{read,manage}` | CANONICAL_RBAC |
| `/api/staff/<slug>/roles/…` | GET / POST / PATCH / DELETE | `RoleViewSet` | `CanReadStaffRoles` / `CanManageStaffRoles` | `staff_management.role.{read,manage}` | CANONICAL_RBAC |
| `/api/staff/<slug>/pending-registrations/` | GET | `PendingRegistrationsAPIView` | `CanReadPendingRegistrations` | `staff_management.pending_registration.read` | CANONICAL_RBAC |
| `/api/staff/registration-package/` | POST | `GenerateRegistrationPackageAPIView` | `CanCreateRegistrationPackages` | `staff_management.registration_package.create` | CANONICAL_RBAC |
| Authority sub-endpoints (role/dept/access_level/nav assign) | POST/PATCH | `StaffViewSet` actions | `CanAssignStaff{Role,Department,AccessLevel,Navigation}`, `CanSuperviseStaffAuthority` | `staff_management.authority.*` | CANONICAL_RBAC |

### 3.5 STAFF zone — room_bookings (canonical, Phase 6A)

All endpoints chain `IsAuthenticated + IsStaffMember + IsSameHotel + CanViewBookings + CanReadBookings + <action>`. Source: [hotel/staff_views.py](hotel/staff_views.py), [room_bookings/staff_urls.py](room_bookings/staff_urls.py).

| URL | Method | View | Action gate | Action key | Status |
|---|---|---|---|---|---|
| `/api/staff/hotel/<slug>/room-bookings/` | GET | `StaffBookingsListView` | `CanReadBookings` | `booking.record.read` | CANONICAL_RBAC |
| `…/room-bookings/<id>/` | GET | `StaffBookingDetailView` | `CanReadBookings` | `booking.record.read` | CANONICAL_RBAC |
| `…/room-bookings/<id>/confirm/` | POST | `StaffBookingConfirmView` | `CanUpdateBooking` | `booking.record.update` | CANONICAL_RBAC |
| `…/room-bookings/<id>/cancel/` | POST | `StaffBookingCancelView` | `CanCancelBooking` | `booking.record.cancel` | CANONICAL_RBAC |
| `…/room-bookings/<id>/safe-assign-room/` | POST | `SafeAssignRoomView` | `CanAssignBookingRoom` | `booking.room.assign` | CANONICAL_RBAC |
| `…/room-bookings/<id>/check-in/` | POST | `BookingCheckInView` | `CanCheckInBooking` | `booking.stay.checkin` | CANONICAL_RBAC |
| `…/room-bookings/<id>/check-out/` | POST | `BookingCheckOutView` | `CanCheckOutBooking` | `booking.stay.checkout` | CANONICAL_RBAC |
| `…/room-bookings/<id>/approve/` | POST | `StaffBookingAcceptView` | `CanSuperviseBooking` | `booking.override.supervise` | CANONICAL_RBAC |
| `…/room-bookings/<id>/decline/` | POST | `StaffBookingDeclineView` | `CanSuperviseBooking` | `booking.override.supervise` | CANONICAL_RBAC |
| `…/room-bookings/<id>/send-precheckin-link/` | POST | `SendPrecheckinLinkView` | `CanCommunicateWithBookingGuest` | `booking.guest.communicate` | CANONICAL_RBAC |
| `…/room-bookings/<id>/extend-overstay/` | POST | `OverstayExtendView` | `CanCheckOutBooking` (semantic mismatch — see 6A audit BREAK-O1) | `booking.stay.extend` | CANONICAL_RBAC (wrong cap) |
| `…/room-bookings/<id>/acknowledge-overstay/` | POST | `OverstayAcknowledgeView` | `CanSuperviseBooking` | `booking.override.supervise` | CANONICAL_RBAC |
| `…/room-bookings/<id>/mark-seen/` | POST | `StaffBookingMarkSeenView` | `CanUpdateBooking` (over-gated; metadata only) | `booking.record.update` | CANONICAL_RBAC (over-gated) |

### 3.6 STAFF zone — rooms (canonical, Phase 6B.1)

Source: [rooms/views.py](rooms/views.py), [rooms/staff_urls.py](rooms/staff_urls.py). All chain `IsAuthenticated + IsStaffMember + IsSameHotel + CanViewRooms`.

| URL | Method | View | Action gate | Action key | Status |
|---|---|---|---|---|---|
| `…/room-management/` | GET | `StaffRoomViewSet.list` | `CanReadRoomInventory` | `room.inventory.read` | CANONICAL_RBAC |
| `…/room-management/` | POST | `StaffRoomViewSet.create` | `CanCreateRoomInventory` | `room.inventory.create` | CANONICAL_RBAC |
| `…/room-management/<pk>/` | PATCH/PUT | `StaffRoomViewSet.update` | split-payload routing → `CanUpdateRoomInventory` / `CanTransitionRoomStatus` / `CanFlagRoomMaintenance` / `CanClearRoomMaintenance` / `CanSetRoomOutOfOrder` | `room.inventory.update` / `room.status.transition` / `room.maintenance.flag` / `room.maintenance.clear` / `room.out_of_order.set` | CANONICAL_RBAC |
| `…/room-management/<pk>/` | DELETE | `StaffRoomViewSet.destroy` | `CanDeleteRoomInventory` | `room.inventory.delete` | CANONICAL_RBAC |
| `…/room-types/…` | GET / CUD | `StaffRoomTypeViewSet` ([hotel/staff_views.py](hotel/staff_views.py)) | `CanReadRoomTypes` / `CanManageRoomTypes` | `room.type.{read,manage}` | CANONICAL_RBAC |
| `…/rooms/checkout/` | POST | `checkout_rooms` (FBV) | `CanBulkCheckoutRooms` | `room.checkout.bulk` | CANONICAL_RBAC |
| `…/rooms/<num>/inspect/` | POST | `inspect_room` (FBV) | `CanInspectRoom` | `room.inspect` | CANONICAL_RBAC |
| Room media endpoints | GET/CUD | `RoomMediaViewSet` | `CanReadRoomMedia` / `CanManageRoomMedia` | `room.media.{read,manage}` | CANONICAL_RBAC |

### 3.7 STAFF zone — housekeeping (canonical, Phase 6C)

Source: [housekeeping/views.py](housekeeping/views.py), [housekeeping/staff_urls.py](housekeeping/staff_urls.py).

| URL | Method | View | Action gate | Action key | Status |
|---|---|---|---|---|---|
| `…/housekeeping/dashboard/` | GET | `HousekeepingDashboardViewSet.list` | `CanReadHousekeepingDashboard` | `housekeeping.dashboard.read` | CANONICAL_RBAC (note: `housekeeping/views.py:80` still uses `access_level in [...]` for dashboard scope toggling — see Section 6) |
| `…/housekeeping/tasks/` | GET | `HousekeepingTaskViewSet.list` | `CanReadHousekeepingTasks` | `housekeeping.task.read` | CANONICAL_RBAC |
| `…/housekeeping/tasks/` | POST | `HousekeepingTaskViewSet.create` | `CanCreateHousekeepingTask` | `housekeeping.task.create` | CANONICAL_RBAC |
| `…/housekeeping/tasks/<pk>/` | PATCH/PUT | `HousekeepingTaskViewSet.update` | split-payload `_required_task_update_caps` → `CanUpdateHousekeepingTask` / `CanAssignHousekeepingTask` / `CanExecuteHousekeepingTask` / `CanCancelHousekeepingTask` | `housekeeping.task.{update,assign,execute,cancel}` | CANONICAL_RBAC |
| `…/housekeeping/tasks/<pk>/` | DELETE | `HousekeepingTaskViewSet.destroy` | `CanDeleteHousekeepingTask` | `housekeeping.task.delete` | CANONICAL_RBAC |
| `…/housekeeping/rooms/<id>/status/` | POST | `RoomStatusViewSet.update_status` | `housekeeping/policy.py::can_change_room_status` (capability precedence) | `housekeeping.room_status.{transition,front_desk,override}` | CANONICAL_RBAC |
| `…/housekeeping/rooms/<id>/status-history/` | GET | `RoomStatusViewSet.status_history` | `CanReadHousekeepingStatusHistory` | `housekeeping.room_status.history.read` | CANONICAL_RBAC |

### 3.8 STAFF zone — maintenance (canonical, Phase 6D.1)

Source: [maintenance/views.py](maintenance/views.py), [maintenance/urls.py](maintenance/urls.py).

| URL | Method | View | Action gate | Action key | Status |
|---|---|---|---|---|---|
| `…/maintenance/requests/` | GET | `MaintenanceRequestViewSet.list` | `CanReadMaintenanceRequests` | `maintenance.request.read` | CANONICAL_RBAC |
| `…/maintenance/requests/` | POST | `…create` | `CanCreateMaintenanceRequest` | `maintenance.request.create` | CANONICAL_RBAC |
| `…/maintenance/requests/<pk>/` | PATCH/PUT | `…update` | `CanUpdateMaintenanceRequest` (action fields blocked from generic update) | `maintenance.request.update` | CANONICAL_RBAC |
| `…/maintenance/requests/<pk>/` | DELETE | `…destroy` | `CanDeleteMaintenanceRequest` | `maintenance.request.delete` | CANONICAL_RBAC |
| `…/requests/<pk>/{accept,resolve,reassign,reopen,close}/` | POST | `MaintenanceRequestViewSet.@action` | `CanAcceptMaintenanceRequest` etc. | `maintenance.request.{accept,resolve,reassign,reopen,close}` | CANONICAL_RBAC |
| `…/maintenance/comments/` | POST/DELETE | `MaintenanceCommentViewSet` | `CanCreateMaintenanceComment` / `CanModerateMaintenanceComment` | `maintenance.comment.{create,moderate}` | CANONICAL_RBAC |
| `…/maintenance/photos/` | POST/DELETE | `MaintenancePhotoViewSet` | `CanUploadMaintenancePhoto` / `CanDeleteMaintenancePhoto` | `maintenance.photo.{upload,delete}` | CANONICAL_RBAC |

### 3.9 STAFF zone — restaurant bookings (legacy)

Source: [bookings/views.py](bookings/views.py), [bookings/staff_urls.py](bookings/staff_urls.py).

| URL | Method | View | Permission classes | Status |
|---|---|---|---|---|
| `…/service-bookings/bookings/` | GET, POST | `BookingViewSet` | `[IsAuthenticated, HasRestaurantBookingsNav, IsStaffMember, IsSameHotel]` | NAV_SECURITY_LEGACY |
| `…/service-bookings/assign/<slug>/` | POST | `AssignGuestToTableAPIView` | `[…+ CanManageRestaurantBookings]` | NAV_SECURITY_LEGACY |
| `…/service-bookings/unseat/<slug>/` | POST | `UnseatBookingAPIView` | `[…+ CanManageRestaurantBookings]` | NAV_SECURITY_LEGACY |
| `…/service-bookings/delete/<slug>/<id>/` | DELETE | `DeleteBookingAPIView` | `[…+ CanManageRestaurantBookings]` | NAV_SECURITY_LEGACY |
| Public guest dinner booking, restaurant viewset reads | mixed | `bookings/views.py` AllowAny viewsets | – | PUBLIC_ALLOWANY_EXPECTED |

### 3.10 STAFF zone — attendance (legacy)

Source: [attendance/views.py](attendance/views.py), [attendance/face_views.py](attendance/face_views.py), [attendance/urls.py](attendance/urls.py).

| URL | Method | View | Permission classes | Status |
|---|---|---|---|---|
| `…/attendance/roster-periods/` | GET, POST | `RosterPeriodViewSet` | `[IsAuthenticated, HasAttendanceNav, IsStaffMember, IsSameHotel, CanManageRoster]` | NAV_SECURITY_LEGACY |
| `…/attendance/shifts/` | GET, POST | `StaffRosterViewSet` | as above | NAV_SECURITY_LEGACY |
| `…/attendance/clock-logs/` | GET, POST | `ClockLogViewSet` | `[IsAuthenticated, HasAttendanceNav, IsStaffMember, IsSameHotel]` | NAV_SECURITY_LEGACY |
| `…/attendance/face-management/face-clock-in/` | POST | `FaceManagementViewSet.face_clock_in` | `[IsAuthenticated, HasAttendanceNav]` | NAV_SECURITY_LEGACY |
| Analytics endpoints (`views_analytics.py`, `analytics_roster.py`) | GET | various | `[IsAuthenticated, HasAttendanceNav, IsStaffMember, IsSameHotel]` | NAV_SECURITY_LEGACY |

### 3.11 STAFF zone — chat (legacy)

Source: [chat/views.py](chat/views.py), [chat/staff_urls.py](chat/staff_urls.py).

| URL | Method | View | Permission classes | Status |
|---|---|---|---|---|
| `…/chat/conversations/` | GET | `get_active_conversations` | `[IsAuthenticated]` (inline hotel-scope) | AUTH_ONLY_NEEDS_REVIEW |
| `…/chat/conversations/<id>/messages/` | GET | `get_conversation_messages` | `[IsAuthenticated]` | AUTH_ONLY_NEEDS_REVIEW |
| `…/chat/conversations/<id>/messages/send/` | POST | `send_conversation_message` | `[IsAuthenticated]` | AUTH_ONLY_NEEDS_REVIEW |
| `…/chat/messages/<id>/delete/` | DELETE | `delete_message` | `[IsAuthenticated]` + inline `has_capability('chat.message.moderate')` | CANONICAL_RBAC (inline) |
| Guest-side dual mode: `mark_conversation_read`, `update_message`, `upload_message_attachment`, `delete_attachment`, `save_fcm_token` | various | `chat/views.py` | `[AllowAny]` + token check | GUEST_TOKEN_EXPECTED |

### 3.12 STAFF zone — staff_chat

Source: [staff_chat/views.py](staff_chat/views.py), [staff_chat/views_messages.py](staff_chat/views_messages.py), [staff_chat/views_attachments.py](staff_chat/views_attachments.py), [staff_chat/permissions.py](staff_chat/permissions.py).

| URL | Method | View | Permission classes | Status |
|---|---|---|---|---|
| `…/staff_chat/conversations/` | GET, POST | `StaffConversationViewSet` | `[IsAuthenticated, HasChatNav, IsStaffMember, IsSameHotel]` | NAV_SECURITY_LEGACY |
| `…/staff_chat/conversations/<id>/messages/` | GET, POST | `views_messages` FBVs | `[IsAuthenticated, HasChatNav, IsStaffMember, IsSameHotel]` | NAV_SECURITY_LEGACY |
| `…/staff_chat/messages/<id>/delete/` | DELETE | `delete_message` | `[…]` + inline `has_capability('staff_chat.conversation.moderate')` | CANONICAL_RBAC (inline, capability) |

### 3.13 STAFF zone — home (legacy)

Source: [home/views.py](home/views.py), [home/urls.py](home/urls.py).

| URL | Method | View | Permission classes | Status |
|---|---|---|---|---|
| `…/home/posts/` | GET, POST | `PostViewSet` | `[IsAuthenticated, HasHomeNav, IsStaffMember, IsSameHotel]` | NAV_SECURITY_LEGACY |
| `…/home/posts/<id>/comments/` | GET, POST | `CommentViewSet` | as above | NAV_SECURITY_LEGACY |
| `…/home/posts/<id>/comments/<cid>/replies/` | GET, POST | `CommentReplyViewSet` | as above | NAV_SECURITY_LEGACY |

### 3.14 STAFF zone — hotel settings / config (legacy/tier)

Source: [hotel/staff_views.py](hotel/staff_views.py), [hotel/permissions.py](hotel/permissions.py).

| URL | Method | View | Permission classes | Status |
|---|---|---|---|---|
| `…/settings/` | GET, PATCH | `HotelSettingsView` | `[…HasAdminSettingsNav, CanConfigureHotel]` | NAV_SECURITY_LEGACY |
| `…/access-config/` | GET, PATCH | `StaffAccessConfigViewSet` | `[…HasAdminSettingsNav, IsSuperStaffAdminOrAbove]` | ROLE_OR_TIER_LEGACY |
| `…/public-page-builder/` | GET | `PublicPageBuilderView` | `[…HasAdminSettingsNav, IsSuperStaffAdminOrAbove]` | ROLE_OR_TIER_LEGACY |
| `…/precheckin-config/` | GET, PATCH | `HotelPrecheckinConfigView` | `[…CanViewBookings, CanReadBookings, CanManageBookingConfig]` | CANONICAL_RBAC (booking module) |
| `…/survey-config/` | GET, PATCH | `HotelSurveyConfigView` | `[…CanManageBookingConfig]` | CANONICAL_RBAC (booking module) |
| `…/cancellation-policies/…` | GET/CUD | `hotel/cancellation_policies/views.py` | `[…HasAdminSettingsNav, CanConfigureHotel]` | NAV_SECURITY_LEGACY |
| `…/rate-plans/…` | GET/CUD | `hotel/rate_plans/views.py` | `[…HasAdminSettingsNav, CanConfigureHotel]` | NAV_SECURITY_LEGACY |
| Public-page builder sections / hero / gallery / list / cards / news / content blocks viewsets | CUD | `hotel/staff_views.py` | `[HasHotelInfoNav + IsSuperStaffAdminForHotel]` | ROLE_OR_TIER_LEGACY |

### 3.15 STAFF zone — hotel_info

Source: [hotel_info/views.py](hotel_info/views.py).

| URL | Method | View | Permission classes | Status |
|---|---|---|---|---|
| `…/hotel_info/hotelinfo/` | GET | `HotelInfoViewSet` (read) | `[IsAuthenticatedOrReadOnly]` | AUTH_ONLY_NEEDS_REVIEW |
| `…/hotel_info/hotelinfo/` | POST/PATCH | `HotelInfoViewSet` (write) | `[…HasHotelInfoNav, IsStaffMember, IsSameHotel, CanConfigureHotel]` | NAV_SECURITY_LEGACY |
| `…/hotel_info/categories/` | GET, POST | `HotelInfoCategoryViewSet` | `[IsAuthenticatedOrReadOnly]` | AUTH_ONLY_NEEDS_REVIEW |
| `…/hotel_info/qr/<category>/` | GET | `CategoryQRView`, `download_all_qrs` | `[IsAuthenticated]` | AUTH_ONLY_NEEDS_REVIEW |

### 3.16 STAFF zone — common, guests, room_services, stock_tracker, entertainment, notifications

| URL | Method | View | App | Permission classes | Status |
|---|---|---|---|---|---|
| `…/common/theme/` | GET, PATCH | `common/views.py::ThemePreferenceViewSet` | common | `[IsAuthenticatedOrReadOnly]` | AUTH_ONLY_NEEDS_REVIEW |
| `…/guests/` | GET, POST, PATCH, DELETE | `guests/views.py::GuestViewSet` | guests | `[IsAuthenticated]` (no `IsStaffMember`/`IsSameHotel`) | UNPROTECTED_GAP |
| `…/room-services/items/` | GET / CUD | `room_services/views.py::RoomServiceItemViewSet` | room_services | `[AllowAny]` for read; CUD `[…CanManageRoomServices]` | NAV_SECURITY_LEGACY (CUD) / GUEST_TOKEN_EXPECTED (orders) |
| `…/room-services/orders/` (staff-side) | GET, PATCH | `OrderViewSet` (staff actions) | room_services | hybrid; staff actions `[IsAuthenticated, CanManageRoomServices]` | NAV_SECURITY_LEGACY |
| `…/stock-tracker/<all viewsets>` | GET / CUD | [stock_tracker/views.py](stock_tracker/views.py) | stock_tracker | `[IsAuthenticated, HasStockTrackerNav, IsStaffMember, IsSameHotel]` (no `Can*`) | NAV_SECURITY_LEGACY |
| `…/stock-tracker/periods/<id>/reopen/` | POST | `PeriodReopenAPIView` ([stock_tracker/views.py:1762](stock_tracker/views.py)) | stock_tracker | inline `if user.is_superuser: can_reopen = True` | UNPROTECTED_GAP / ROLE_OR_TIER_LEGACY |
| `…/stock-tracker/reports/…` | GET | `report_views.py`, `comparison_views.py` | stock_tracker | `[IsAuthenticated]` mostly | AUTH_ONLY_NEEDS_REVIEW |
| `…/entertainment/games/…` | GET / play | `entertainment/views.py` (game session) | entertainment | `[AllowAny]` | PUBLIC_ALLOWANY_EXPECTED |
| `…/entertainment/dashboard/`, `…/tournaments/`, `…/quiz/<CUD>` | various | `entertainment/views.py` (staff) | entertainment | `[IsAuthenticated]` | AUTH_ONLY_NEEDS_REVIEW |
| `/api/notifications/pusher/auth/` | POST | `notifications/views.py::PusherAuthView` | notifications | `[AllowAny]` (custom token validation) | UNPROTECTED_GAP (by design — infra) |
| `/api/notifications/save-fcm-token/` | POST | `SaveFcmTokenView` | notifications | `[IsAuthenticated]` | AUTH_ONLY_NEEDS_REVIEW |

### 3.17 ADMIN zone (`/api/hotel/`) — platform/superuser

Source: [hotel/provisioning_views.py](hotel/provisioning_views.py), [hotel/base_views.py](hotel/base_views.py).

| URL | Method | View | Permission classes | Status |
|---|---|---|---|---|
| `/api/hotel/hotels/provision/` | POST | `ProvisionHotelView` | `[IsDjangoSuperUser]` | ROLE_OR_TIER_LEGACY (intentional platform op) |
| `/api/hotel/hotels/` | GET, POST | `HotelViewSet` | `[IsDjangoSuperUser]` | ROLE_OR_TIER_LEGACY |
| `/api/hotel/hotels/<pk>/` | GET, PATCH, DELETE | `HotelViewSet` | `[IsDjangoSuperUser]` | ROLE_OR_TIER_LEGACY |

> Many additional FBVs/viewsets exist within each app's `urls.py`; rows above are exhaustive for canonical-covered modules and representative for legacy modules. Items not visited individually here remain `UNKNOWN_NEEDS_INSPECTION` until a per-app sweep — see Section 9 Phase A for the prioritized order.

---

## 4. Canonical RBAC Covered Modules

### 4.1 `bookings` (room booking domain)

| Field | Value |
|---|---|
| Module key | `bookings` ([staff/module_policy.py:74-97](staff/module_policy.py)) |
| Actions (12) | `update`, `cancel`, `assign_room`, `checkin`, `checkout`, `communicate`, `override_conflicts`, `force_checkin`, `force_checkout`, `resolve_overstay`, `modify_locked`, `extend`, `manage_rules` |
| Backend policy source | [staff/permissions.py](staff/permissions.py) `Can{View,Read,Update,Cancel,AssignRoom,CheckIn,CheckOut,CommunicateWithGuest,Supervise,ManageConfig}Booking{,s}` |
| Endpoint coverage | 13 staff endpoints under `/api/staff/hotel/<slug>/room-bookings/…` (Section 3.5); 6 guest/public endpoints under `/api/public/…` use GBT/BMT |
| Notes | Phase 6A (see [/memories/repo/rbac_phase6a_audit.md](/memories/repo/rbac_phase6a_audit.md)). Two open semantic mismatches: `OverstayExtendView` gated on `booking.stay.extend` (operate) — should be `booking.override.*`; `StaffBookingMarkSeenView` over-gated on `record.update`. `booking.config.manage` now wired by `HotelPrecheckinConfigView`/`HotelSurveyConfigView`; rate-plans / cancellation-policies still tier-gated (see Section 5). |

### 4.2 `rooms`

| Field | Value |
|---|---|
| Module key | `rooms` ([staff/module_policy.py:98-119](staff/module_policy.py)) |
| Actions (13) | `inventory_create/update/delete`, `type_manage`, `media_manage`, `out_of_order_set`, `checkout_destructive`, `status_transition`, `maintenance_flag`, `inspect`, `maintenance_clear`, `checkout_bulk` |
| Backend policy source | [staff/permissions.py](staff/permissions.py) L877–L947 (`CanReadRoomInventory` … `CanDestructiveCheckoutRooms`) |
| Endpoint coverage | All `/room-management/`, `/room-types/`, `/rooms/checkout/`, `/rooms/<num>/inspect/`, room media (Section 3.6) |
| Notes | Split-payload PATCH routing on `StaffRoomViewSet.update` — different fields require different capabilities. |

### 4.3 `housekeeping`

| Field | Value |
|---|---|
| Module key | `housekeeping` ([staff/module_policy.py:120-135](staff/module_policy.py)) |
| Actions (10) | `dashboard_read`, `task_create/update/delete/assign/execute/cancel`, `status_transition/front_desk/override`, `status_history_read` |
| Backend policy source | [staff/permissions.py](staff/permissions.py) L976–L1051; runtime: [housekeeping/policy.py](housekeeping/policy.py) `can_change_room_status` |
| Endpoint coverage | All endpoints under `/api/staff/hotel/<slug>/housekeeping/…` (Section 3.7) |
| Notes | Split-payload routing via `_required_task_update_caps`. `housekeeping/views.py:80` still consults `staff.access_level in [...]` for dashboard scope toggling — see Section 6 (MEDIUM). |

### 4.4 `maintenance`

| Field | Value |
|---|---|
| Module key | `maintenance` ([staff/module_policy.py:136-157](staff/module_policy.py)) |
| Actions (12) | `request_create/accept/resolve/update/reassign/reopen/close/delete`, `comment_create/moderate`, `photo_upload/delete` |
| Backend policy source | [staff/permissions.py](staff/permissions.py) L1080–L1159 |
| Endpoint coverage | All `/api/staff/hotel/<slug>/maintenance/…` (Section 3.8) |
| Notes | Phase 6D.1. Action fields (`status`, `accepted_by`) are blocked from generic update path — only `@action` endpoints can mutate them. |

### 4.5 `staff_management`

| Field | Value |
|---|---|
| Module key | `staff_management` ([staff/module_policy.py:158-222](staff/module_policy.py)) |
| Actions (24) | staff CRUD + authority assignments + dept/role manage + registration packages |
| Backend policy source | [staff/permissions.py](staff/permissions.py) L1191–L1280; anti-escalation helpers L1283–L1434 |
| Endpoint coverage | All endpoints under `/api/staff/<slug>/…` (Section 3.4) |
| Notes | Phase 6E.1. Anti-escalation chain enforced on every authority mutation. **However**: 9 inline `is_superuser` queryset bypasses still live in [staff/views.py](staff/views.py) — see Section 6. |

> The 5 modules above are the entire canonical-coverage surface today. Every other endpoint relies on nav, tier, role/dept slug, or `IsAuthenticated`-only.

---

## 5. Non-Covered / Partially Covered Modules

| App / Module | Current protection | Missing canonical module? | Missing actions? | Risk | Required decision |
|---|---|---|---|---|---|
| hotel — provisioning ([hotel/provisioning_views.py::ProvisionHotelView](hotel/provisioning_views.py)) | `IsDjangoSuperUser` only | YES — no `hotel.provision` module | provision/decommission hotel | **CRITICAL** | Confirm `IsDjangoSuperUser` canonical for platform ops, OR introduce `platform.hotel.{provision,decommission}` |
| hotel — public page builder (`HotelPublicPageViewSet`, `PublicSectionViewSet`, `HeroSectionViewSet`, `GalleryContainerViewSet`, `GalleryImageViewSet`, `ListContainerViewSet`, `CardViewSet`, `NewsItemViewSet`, `ContentBlockViewSet`, `RoomsSectionViewSet` — [hotel/staff_views.py](hotel/staff_views.py)) | `HasHotelInfoNav + IsSuperStaffAdminForHotel` | YES — no `hotel_info.public_page` | section/hero/gallery/list/cards CUD, reorder, media | **HIGH** (public marketing surface) | Register `hotel_info.public_page.*` (read/operate/manage) OR confirm tier-gate |
| hotel — settings ([hotel/staff_views.py::HotelSettingsView](hotel/staff_views.py)) | `HasAdminSettingsNav + CanConfigureHotel` (tier-only) | partial — no granular `hotel.settings.*` | basic_info / theme / contact / classification | **MED** | Decide: keep tier-only OR split into `hotel.settings.{update_basic_info,update_theme,update_contact}` |
| hotel — access-config ([hotel/staff_views.py::StaffAccessConfigViewSet](hotel/staff_views.py)) | `HasAdminSettingsNav + IsSuperStaffAdminOrAbove` | YES — no `hotel.access_config` | checkout time, approval cutoff | **HIGH** (drives booking approval/overstay) | Create `hotel.access_config.{read,update}` OR confirm tier-only |
| hotel — rate-plans ([hotel/rate_plans/views.py](hotel/rate_plans/views.py)) | `HasAdminSettingsNav + CanConfigureHotel` | YES — `booking.config.manage` not yet wired here | rate plan CUD | **MED** | Wire `CanManageBookingConfig` (already a canonical capability) |
| hotel — cancellation-policies ([hotel/cancellation_policies/views.py](hotel/cancellation_policies/views.py)) | `HasAdminSettingsNav + CanConfigureHotel` | YES — same as rate-plans | policy CUD | **MED** | Wire `CanManageBookingConfig` |
| hotel — booking-rules / blocked-dates | tier or unverified | partial | block CUD | **MED** | Verify; likely `booking.config.manage` |
| hotel_info — QR generation ([hotel_info/views.py::CategoryQRView](hotel_info/views.py), `download_all_qrs`) | `IsAuthenticated` only | YES — no `hotel_info.qr` | generate, download | **LOW** | Add `IsStaffMember + IsSameHotel + HasHotelInfoNav` minimum, OR `hotel_info.qr.generate` |
| hotel_info — info entries | `IsAuthenticatedOrReadOnly` (write requires nav+tier) | YES — no `hotel_info.entry` | entry CUD | **MED** | Register `hotel_info.entry.{read,manage}` |
| stock_tracker — every endpoint | `IsAuthenticated, HasStockTrackerNav, IsStaffMember, IsSameHotel` (no `Can*`) | YES — no `stock_tracker` module registered | inventory CUD, recipes, consumption, stocktake, sales, period close/reopen, KPI/reports | **HIGH** (financial / liquor / cost data) | Register `stock_tracker.*` module with read/operate/supervise/manage buckets |
| stock_tracker — `PeriodReopenAPIView` ([stock_tracker/views.py:1762](stock_tracker/views.py)) | inline `if user.is_superuser: can_reopen = True` | YES — `stock_tracker.period.reopen` | reopen closed accounting period | **HIGH** | Replace inline with `HasCapability('stock_tracker.period.reopen')` |
| bookings (restaurant) — all viewsets | `HasRestaurantBookingsNav + CanManageRestaurantBookings` (tier-only) | YES — no `restaurant.booking` module | record CRUD, table assign, unseat, blueprint manage | **MED** | Register `restaurant.booking.*` with read/operate/manage OR confirm tier-only |
| chat (guest↔staff) — staff-side | `IsAuthenticated` + inline hotel-scope; deletion uses `has_capability('chat.message.moderate')` | partial — `chat.message.moderate` and `chat.guest.respond` exist as capabilities but no module/action policy | view/respond/moderate as a module surface | **MED** | Register `chat` module with `{conversation.read, message.send, message.moderate, message.delete}` |
| staff_chat — conversation/messages | `HasChatNav + IsStaffMember + IsSameHotel`; moderation uses `has_capability('staff_chat.conversation.moderate')` | partial — capability exists; no module key | conversation CUD, message moderation | **MED** | Register `staff_chat` module |
| home — posts/comments/replies | `HasHomeNav + IsStaffMember + IsSameHotel` only | YES — no `home` module | post CUD, comment moderation | **MED** | Register `home.{post.{create,update,delete}, comment.moderate}` |
| guests — `GuestViewSet` ([guests/views.py](guests/views.py)) | `IsAuthenticated` only — **no `IsStaffMember`/`IsSameHotel`** | YES | guest CUD, checkout | **HIGH** (PII; cross-hotel risk) | Add hotel-scope guards; create `guest.{read,update,delete}` (likely under `room` module) |
| room_services — staff side | hybrid; staff CUD via `CanManageRoomServices` (tier) | partial — fulfillment routing uses canonical caps (`room_service.order.fulfill_porter` / `.fulfill_kitchen`) | menu CUD, order status update, refund | **MED** | Register `room_service` module with menu/order buckets |
| entertainment | `AllowAny` (game sessions) + `IsAuthenticated` (staff dashboard / quiz CUD) | YES | dashboard read, tournament/quiz CUD, achievement moderation | **LOW** | Optional: register `entertainment.*`; otherwise keep tier |
| attendance — all endpoints | `HasAttendanceNav + IsStaffMember + IsSameHotel + CanManageRoster` (tier-only) | YES — no `attendance` module in `MODULE_POLICY` | clock-in/out, roster CRUD, face management, analytics | **MED** | Register `attendance.{clock.{read,perform}, roster.{read,manage}, face.manage, analytics.read}` |
| common — theme | `IsAuthenticatedOrReadOnly` | YES | theme CUD | **LOW** | Fold into `hotel.settings.theme` OR register `hotel_info.theme.{read,manage}` |
| notifications — `PusherAuthView`, `SaveFcmTokenView` | `[AllowAny]` / `[IsAuthenticated]` | NO (infra) | – | **LOW** | Keep |
| posts (app) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Per-app sweep needed |
| promo_docs / tools / voice_recognition | no `urls.py` exposed | – | – | N/A | None |

---

## 6. Legacy Authority Usage

> Excludes legitimate auth-infrastructure callers (`hotel/auth_backends.py`, `staff/admin.py`, `resolve_tier`, `resolve_effective_access` — all keep `is_superuser`).

| File | Function/Class | Legacy check | What it controls | Risk | Suggested canonical replacement |
|---|---|---|---|---|---|
| [staff/views.py:131](staff/views.py) | `StaffViewSet.get_queryset` | `if user.is_superuser:` | superuser sees all staff across hotels | **HIGH** (cross-tenant leak) | `resolve_tier(user) == 'super_user'` |
| [staff/views.py:281,299,324](staff/views.py) | `DepartmentViewSet.perform_*`, `RoleViewSet.perform_*` | `if err and not request.user.is_superuser:` | bypass hotel-scoped validation | **MED** | `resolve_tier == 'super_user'` |
| [staff/views.py:426](staff/views.py) | `NavigationItemViewSet.perform_create/update/destroy` | `if not user.is_superuser: 403` | platform-only nav item CUD | **CRITICAL** | Use `IsDjangoSuperUser` permission class instead of inline |
| [staff/views.py:1088](staff/views.py) | `CreateStaffFromUserAPIView.post` | `if not user.is_superuser:` (hotel slug check) | superuser can create staff for any hotel | **HIGH** | `resolve_tier == 'super_user'` |
| [staff/views.py:1155, 1337, 1421, 1505, 1619, 1633, 1644, 1735, 1749, 1763, 2097](staff/views.py) | various (`get_queryset`, `check_write_permission`, `RegistrationPackageView`, `StaffNavigationPermissionsView`) | inline `is_superuser` | cross-hotel queryset access, write bypass, package issuance | **HIGH/MED** | `resolve_tier == 'super_user'` |
| [stock_tracker/views.py:1762](stock_tracker/views.py) | `PeriodReopenAPIView.post` | `if user.is_superuser: can_reopen = True` | reopen closed accounting periods | **HIGH** | `HasCapability('stock_tracker.period.reopen')` |
| [stock_tracker/views.py:1837](stock_tracker/views.py) | unknown | `if not request.user.is_superuser:` | TBD | **MED** | `resolve_tier == 'super_user'` |
| [stock_tracker/stock_serializers.py:365,392](stock_tracker/stock_serializers.py) | serializer validation | `if request.user.is_superuser:` | bypass stock validation | **MED** | Prefer business-rule fix; if escape hatch needed → `resolve_tier == 'super_user'` |
| [hotel/permissions.py:54](hotel/permissions.py) | `IsSuperStaffAdminForHotel.has_permission` | `if request.user.is_superuser:` | tier bypass | **HIGH** (cross-hotel implicit) | `resolve_tier(user) in ('super_user', 'super_staff_admin')` |
| [housekeeping/views.py:80](housekeeping/views.py) | `TasksDashboard.get` | `if staff.access_level in ['staff_admin','super_staff_admin']:` | dashboard scope (hotel-wide vs self-assigned) | **MED** | `'housekeeping.task.assign' in allowed_capabilities` |
| [staff/serializers.py:365](staff/serializers.py) | serializer | `if not is_superuser and access_level == 'super_staff_admin':` | block escalation | **MED** | Already covered by anti-escalation helpers (Phase 6E.1); replace with `assert_access_level_allowed` |
| [staff/permissions.py:653](staff/permissions.py) | `HasCapability.__init__` | legacy `role_slugs` parameter (deprecated) | – | **LOW** | Mark deprecated; remove when no callers remain |

### Routing-only (NOT authority — keep)

| File | Symbol | Pattern | Reason to keep |
|---|---|---|---|
| [notifications/notification_manager.py:2134,2137](notifications/notification_manager.py) | `_notify_*` | `staff_qs.filter(role__slug=…)` / `department__slug=…` | Channel addressing for Pusher; authorization is via `staff_with_capability` elsewhere |
| [notifications/pusher_utils.py:84,35](notifications/pusher_utils.py) | `notify_staff_by_role` / `_by_department` | role/dept slug routing | Channel name contract |
| [staff/models.py:308,315](staff/models.py) | `Staff.objects_by_role`, `objects_by_department` | filter helpers | Convenience query helpers |
| [attendance/views.py:617,1043,1521,1566,1756,1799,1855](attendance/views.py), [attendance/analytics.py](attendance/analytics.py), [attendance/analytics_roster.py](attendance/analytics_roster.py) | various | `qs.filter(department__slug=…)` from query params | Read-only analytics filtering |

---

## 7. User Payload Contract

Sources: [staff/me_views.py::StaffMeView.get](staff/me_views.py) (L21–L52); [staff/views.py::CustomAuthToken.post](staff/views.py) (L155–L280); [staff/serializers.py::StaffLoginOutputSerializer.to_representation](staff/serializers.py) (L481–L500); [staff/permissions.py::resolve_effective_access](staff/permissions.py) (L97–L228).

Both `/me` and `/login` always merge `resolve_effective_access(user)` into the response (login serializer enforces it at L489–L495 even if caller omits it).

| Field | Emitted? | Source | Used for | Frontend trust for action control? |
|---|---|---|---|---|
| `rbac` | **YES** | [staff/module_policy.py::resolve_module_policy](staff/module_policy.py#L229-L267) called from [permissions.py:221](staff/permissions.py) | Per-module `{visible, read, actions}` boolean dict | **YES — sole action authority** (mirrors backend `HasCapability`) |
| `allowed_capabilities` | **YES** | [permissions.py:215-220](staff/permissions.py) → `resolve_capabilities(...)` | Capability slug list | **YES — authority** (raw form of `rbac`) |
| `is_superuser` | **YES** | [permissions.py:105](staff/permissions.py) | Platform bypass | **YES — bypass authority** |
| `tier` | **YES** | [permissions.py:178](staff/permissions.py) → `resolve_tier(user)` | tier-bucketed legacy gates | **Mixed** — input to capability resolution; some legacy backend gates still tier-based |
| `effective_navs` | **NO** | – (legacy name; superseded) | – | – |
| `allowed_navs` | **YES** | [permissions.py:212](staff/permissions.py) | Sidebar visibility | **NO — display only** |
| `navigation_items` | **YES** | [permissions.py:213-214](staff/permissions.py) (`NavigationItemSerializer(...)`) | Sidebar render | **NO — display only** |
| `access_level` | **YES** | [permissions.py:180](staff/permissions.py) | Display + tier identifier | **NO — display only** (authority via tier/caps) |
| `role` / `role_slug` | **YES** / **YES** | [permissions.py:183](staff/permissions.py); login adds `role.name` ([views.py:213](staff/views.py)) | Display label; preset-resolution input | **NO — input, never authority** |
| `department` / `department_slug` | **YES** / **YES** | [permissions.py:179](staff/permissions.py); login adds `department.name` ([views.py:214](staff/views.py)) | Display label; preset-resolution input | **NO — input, never authority** |
| `is_staff` | **YES** | [permissions.py:104](staff/permissions.py) | Has Staff row | **NO — informational** |
| `hotel_slug` | **YES** | [permissions.py:175](staff/permissions.py) | Scoping key | **NO — metadata** |
| `is_staff_admin` | **NO** | – | – | – |
| `is_super_staff_admin` | **NO** | – | – | – |
| Login-only: `staff_id`, `username`, `token`, `hotel_id`, `hotel_name`, `hotel`, `profile_image_url` | **YES** | [staff/views.py:199-217](staff/views.py) | Session bootstrap | **NO — session metadata** |
| Login-only: `isAdmin` (legacy compat) | **YES** | [staff/views.py:218](staff/views.py) | Mirrors `is_superuser` | **NO — alias** |

**Invariant (verified in code):** Backend enforcement reads ONLY `allowed_capabilities` (or `is_superuser`) for action gating. Phase 5b removed all `role.slug == ...` and `role__slug=...` enforcement filters from chat / staff_chat / housekeeping / notifications. Remaining role/department slug lookups exist solely in (a) display serializers, (b) notification routing, (c) attendance analytics filters — NONE are authority.

---

## 8. Canonical Module/Action Proposal Map (PROPOSED — not truth)

| Area | Proposed module | Proposed actions | Existing endpoints needing it | Notes |
|---|---|---|---|---|
| Hotel public page builder **PROPOSED** | `hotel_info.public_page` | `view`, `read`, `section.create`, `section.update`, `section.delete`, `section.reorder`, `media.upload`, `media.delete`, `manage` | `HotelPublicPageViewSet`, `PublicSectionViewSet`, `HeroSectionViewSet`, `GalleryContainerViewSet`, `GalleryImageViewSet`, `ListContainerViewSet`, `CardViewSet`, `NewsItemViewSet`, `ContentBlockViewSet`, `RoomsSectionViewSet` ([hotel/staff_views.py](hotel/staff_views.py)) | Currently `IsSuperStaffAdminForHotel` |
| Hotel settings **PROPOSED** | `hotel.settings` | `read`, `update_basic_info`, `update_theme`, `update_contact`, `update_classification` | `HotelSettingsView` ([hotel/staff_views.py](hotel/staff_views.py)) | Or keep tier-only `CanConfigureHotel` |
| Hotel access config **PROPOSED** | `hotel.access_config` | `read`, `update` | `StaffAccessConfigViewSet` ([hotel/staff_views.py](hotel/staff_views.py)) | Drives approval/overstay timing |
| Hotel info QR **PROPOSED** | `hotel_info.qr` | `generate`, `download` | `CategoryQRView`, `download_all_qrs` ([hotel_info/views.py](hotel_info/views.py)) | Low risk |
| Hotel info entries **PROPOSED** | `hotel_info.entry` | `read`, `create`, `update`, `delete` | `HotelInfoViewSet`, `HotelInfoCategoryViewSet` ([hotel_info/views.py](hotel_info/views.py)) | – |
| Stock tracker **PROPOSED** (mandatory) | `stock_tracker` | `module.view`, `inventory.{read,create,update,delete}`, `recipe.{read,create,update,delete}`, `consumption.{read,create,update,delete}`, `stocktake.{read,create,submit,complete}`, `sale.{read,create,update,delete}`, `period.{read,create,close,reopen}`, `report.{stock_value,sales,comparison,kpi}.read` | every viewset in [stock_tracker/views.py](stock_tracker/views.py), [report_views.py](stock_tracker/report_views.py), [comparison_views.py](stock_tracker/comparison_views.py); **`period.reopen` replaces inline `is_superuser` at [stock_tracker/views.py:1762](stock_tracker/views.py)** | Buckets: read/operate/supervise/manage |
| Restaurant bookings **PROPOSED** | `restaurant.booking` | `module.view`, `record.{read,create,update,delete}`, `table.assign`, `table.unseat`, `blueprint.manage` | `BookingViewSet`, `AssignGuestToTableAPIView`, `UnseatBookingAPIView`, `DeleteBookingAPIView`, blueprint viewsets ([bookings/views.py](bookings/views.py)) | Distinct namespace from `booking.*` (room domain) |
| Chat (guest↔staff) **PROPOSED** | `chat` | `module.view`, `conversation.read`, `message.send`, `message.moderate`, `message.delete`, `attachment.upload`, `attachment.delete`, `guest.respond` | `chat/views.py` staff FBVs; `chat.message.moderate` and `chat.guest.respond` already exist as capabilities — wrap them in `MODULE_POLICY['chat']` | Currently `IsAuthenticated` |
| Staff chat **PROPOSED** | `staff_chat` | `module.view`, `conversation.read`, `conversation.create`, `message.send`, `message.moderate`, `attachment.delete` | `staff_chat/views*.py`; `staff_chat.conversation.moderate` already exists | – |
| Home (staff bulletin) **PROPOSED** | `home` | `module.view`, `post.read`, `post.create`, `post.update`, `post.delete`, `comment.create`, `comment.moderate` | `home/views.py` viewsets | – |
| Guest record management **PROPOSED** | `guest` (or fold into `rooms`) | `read`, `update`, `delete`, `checkout` | `guests/views.py::GuestViewSet` | **CRITICAL TODAY**: missing `IsStaffMember`/`IsSameHotel` |
| Room services (staff) **PROPOSED** | `room_service` | `module.view`, `menu.{read,create,update,delete}`, `order.{read,update_status}`, `order.fulfill_kitchen`, `order.fulfill_porter` (latter two already canonical capabilities) | `room_services/views.py` staff actions | – |
| Entertainment **PROPOSED** | `entertainment` | `module.view`, `dashboard.read`, `tournament.{create,update,end}`, `quiz.{create,update,delete}`, `achievement.moderate`, `leaderboard.read` | `entertainment/views.py` staff endpoints | Low priority |
| Attendance **PROPOSED** | `attendance` | `module.view`, `clock.{read,perform}`, `clock.override`, `roster.{read,create,update,assign,publish}`, `face.{enroll,manage}`, `analytics.read` | `attendance/views.py`, `face_views.py`, `views_analytics.py`, `analytics_roster.py` | Currently `HasAttendanceNav + CanManageRoster` (tier) |
| Booking config (rate-plans, cancellation policies) **PROPOSED — partial wiring** | use existing `booking.config.manage` | wire to existing capability (no new actions) | [hotel/rate_plans/views.py](hotel/rate_plans/views.py), [hotel/cancellation_policies/views.py](hotel/cancellation_policies/views.py) | Cap exists; just needs `CanManageBookingConfig` on these views |
| Platform hotel ops **PROPOSED** | `platform.hotel` | `provision`, `decommission`, `list`, `update` | `ProvisionHotelView`, `HotelViewSet` ([hotel/provisioning_views.py](hotel/provisioning_views.py), [hotel/base_views.py](hotel/base_views.py)) | Or keep `IsDjangoSuperUser` — confirm canonical for platform layer |
| Common theme **PROPOSED** | fold into `hotel.settings.theme` or `hotel_info.theme` | – | `common/views.py::ThemePreferenceViewSet` | – |

---

## 9. Priority Fix Plan

### Phase A — Security-critical backend gaps (must-fix)

Endpoints where unauthorized staff or cross-tenant actors can act today.

| Item | Location | Why critical |
|---|---|---|
| A1 | [guests/views.py::GuestViewSet](guests/views.py) | `IsAuthenticated` only — any logged-in staff (even regular_staff at another hotel via PK manipulation) can read/update/delete guest PII. Add `IsStaffMember + IsSameHotel`, then wire canonical `guest.*` or fold under `rooms`. |
| A2 | [stock_tracker/views.py:1762](stock_tracker/views.py) — `PeriodReopenAPIView` | inline `is_superuser` reopen of closed accounting periods. Replace with `HasCapability('stock_tracker.period.reopen')`. |
| A3 | [hotel/permissions.py:54](hotel/permissions.py) — `IsSuperStaffAdminForHotel` | `is_superuser` short-circuit allows cross-hotel super_staff_admin bypass; affects public-page builder. Switch to `resolve_tier`. |
| A4 | [staff/views.py:131,1155,1337,1421,1505,1619,1633,1644,1735,1749,1763,2097](staff/views.py) | 12+ inline `is_superuser` queryset/write bypasses on Staff/Department/Role/RegistrationPackage. Switch all to `resolve_tier(user) == 'super_user'`. |
| A5 | [stock_tracker/views.py:1837](stock_tracker/views.py), [stock_tracker/stock_serializers.py:365,392](stock_tracker/stock_serializers.py) | inline `is_superuser` validation bypass on stock operations. Replace or eliminate. |
| A6 | [stock_tracker/views.py](stock_tracker/views.py) — entire app | NAV-only enforcement for financial/inventory data; any nav holder can mutate stock. Register `stock_tracker` module + wire `Can*` classes per Section 8. |
| A7 | [hotel_info/views.py::HotelInfoCategoryViewSet](hotel_info/views.py) | `IsAuthenticatedOrReadOnly` — any auth user can write. Add `HasHotelInfoNav + IsStaffMember + IsSameHotel + CanConfigureHotel` (or canonical `hotel_info.entry.manage`). |
| A8 | [chat/views.py](chat/views.py) staff FBVs | `IsAuthenticated` only with inline hotel-scope; missing module/action coverage. Add `IsStaffMember + IsSameHotel + HasChatNav` and register `chat` module. |
| A9 | [home/views.py](home/views.py) — verify `IsStaffMember` is present | per /memories/repo/rbac_wave1_status.md it was added; confirm in code post-rebase. |

### Phase B — Frontend contract blockers

Areas where the frontend cannot safely gate UI because the backend does not emit `rbac.<module>` truth.

| Module | Reason | Action |
|---|---|---|
| B1 — `attendance` | NAV_SECURITY_LEGACY; no `rbac.attendance.actions.*` | Register `MODULE_POLICY['attendance']`; map endpoints to `Can*` classes |
| B2 — `restaurant.booking` | tier-only; frontend buttons gated by tier today | Register module; wire viewsets |
| B3 — `chat` / `staff_chat` | capabilities exist (`chat.message.moderate`, `staff_chat.conversation.moderate`, `chat.guest.respond`) but not exposed in `MODULE_POLICY` | Register both modules; expose actions in `rbac` payload |
| B4 — `home` | NAV_SECURITY_LEGACY | Register `home` module |
| B5 — `room_service` | partial — fulfillment caps exist | Register `room_service` module covering menu + order |
| B6 — `hotel_info.public_page` / `hotel.settings` | tier-only | Decide granularity; register at chosen level |
| B7 — `stock_tracker` | covered in Phase A6 | – |

### Phase C — Cleanup / legacy removal

Once Phase A+B land:

| Item | Action |
|---|---|
| C1 | Delete deprecated `role_slugs=` parameter on `HasCapability.__init__` ([staff/permissions.py:653](staff/permissions.py)) |
| C2 | Replace `staff/serializers.py:365` `is_superuser` access-level guard with `assert_access_level_allowed` (already canonical) |
| C3 | Replace `housekeeping/views.py:80` `access_level in [...]` with `'housekeeping.task.assign' in allowed_capabilities` |
| C4 | Audit and delete dead view: `BookingAssignmentView` ([hotel/staff_views.py](hotel/staff_views.py), unrouted; would enforce wrong cap) |
| C5 | Fix `OverstayExtendView` cap mismatch (`booking.stay.extend` operate vs override-bucket semantics) |
| C6 | Fix `StaffBookingMarkSeenView` over-gating (`booking.record.update`) — make read-bucket or new action |
| C7 | Add `restaurant.*` namespace check to forbid `booking.*` slug leakage into `bookings/` app (currently isolated; preventive) |
| C8 | Remove `LEGACY_ROLE_REMAP` once all data migrated (pending Phase 5c data) |
| C9 | Decide whether platform ops (`provision`, `HotelViewSet`) deserve a `platform.*` module or stay on `IsDjangoSuperUser` permanently |

---

## 10. Final 100% Coverage Checklist

Goal: HotelMates has one canonical RBAC truth across the full backend project.

### 10.1 Backend enforcement

- [ ] Every staff-facing endpoint has either: `HasCapability(...)`-derived class, OR documented exception (auth-only / public / guest-token)
- [ ] Every module owning mutations is registered in `MODULE_POLICY`
- [x] `bookings`, `rooms`, `housekeeping`, `maintenance`, `staff_management` registered
- [ ] `attendance`, `restaurant.booking`, `chat`, `staff_chat`, `home`, `room_service`, `stock_tracker`, `hotel.settings`, `hotel_info.public_page`, `hotel_info.entry` registered
- [ ] No inline `if user.is_superuser` outside `resolve_tier`, `resolve_effective_access`, `IsDjangoSuperUser`, `auth_backends`, `admin.py`
- [ ] No `role.slug == 'X'` / `role__slug=` / `access_level in [...]` in enforcement paths (routing/analytics OK)
- [ ] No `Has*Nav` class as the SOLE permission for a write/mutation endpoint
- [ ] `validate_module_policy()` returns `[]`
- [ ] `validate_preset_maps()` returns `[]`

### 10.2 User payload emission

- [x] `/me` and `/login` always merge `resolve_effective_access`
- [x] `rbac` emitted with `{visible, read, actions}` per module
- [x] `allowed_capabilities` emitted
- [x] `allowed_navs` and `navigation_items` emitted (display only)
- [x] `tier`, `role_slug`, `department_slug`, `is_superuser` emitted
- [ ] All registered modules appear in every staff `rbac` payload (today only the 5 covered modules appear)

### 10.3 Frontend action gating contract

- [ ] Every action button reads `user.rbac.<module>.actions.<action_key>` — no role/tier/nav reads
- [ ] No reliance on `effective_navs` / `allowed_navs` for action authority
- [ ] No reliance on `user.role`, `user.role_slug`, `user.access_level` for action authority

### 10.4 Route / page gating

- [ ] Page route guards consult `user.rbac.<module>.visible` (or `allowed_navs` for display)
- [ ] No tier strings in route guards

### 10.5 Nav visibility separation

- [x] Nav visibility computed independently of capabilities ([staff/permissions.py:191-211](staff/permissions.py))
- [ ] Frontend renders nav from `allowed_navs` / `navigation_items` only; never as authority

### 10.6 Tests / validation coverage

- [ ] Test for every covered module: regular_staff DENIED, role-preset GRANTED, super_user GRANTED
- [ ] Test that unknown capability strings fail closed
- [ ] Test that anti-escalation helpers block self-elevation, cross-hotel, ceiling violations
- [ ] CI guard: `validate_module_policy()` and `validate_preset_maps()` must return `[]`
- [ ] CI guard: grep for forbidden patterns (`role__slug=`, inline `is_superuser` in views) — fail build on hits in non-allowlisted files

### 10.7 Documentation

- [ ] One canonical reference doc lists modules + actions + capability slugs (this file is the audit; a kept-current contract doc should follow once Phase A+B land)

---

## Sources of truth (cited throughout)

- [staff/capability_catalog.py](staff/capability_catalog.py) — capabilities, presets, `resolve_capabilities`, `validate_preset_maps`
- [staff/module_policy.py](staff/module_policy.py) — `MODULE_POLICY`, `resolve_module_policy`, `validate_module_policy`
- [staff/permissions.py](staff/permissions.py) — `resolve_tier`, `resolve_effective_access`, `HasCapability`, `has_capability`, `staff_with_capability`, all `Can*` classes, all `Has*Nav` classes, anti-escalation helpers
- [staff/role_catalog.py](staff/role_catalog.py) — canonical roles
- [staff/department_catalog.py](staff/department_catalog.py) — canonical departments
- [staff/nav_catalog.py](staff/nav_catalog.py) — canonical navs
- [staff/me_views.py](staff/me_views.py), [staff/views.py](staff/views.py), [staff/serializers.py](staff/serializers.py) — payload emission
- [housekeeping/policy.py](housekeeping/policy.py) — runtime housekeeping policy
- [common/guest_access.py](common/guest_access.py) — guest token plumbing
- All app `urls.py` / `staff_urls.py` / `views.py` referenced inline above
