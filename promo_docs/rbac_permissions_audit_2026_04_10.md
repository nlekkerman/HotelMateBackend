# RBAC / Permissions System Audit

**Date:** 2026-04-10  
**Scope:** Existing code only — no recommendations, no redesign proposals  
**Method:** Full codebase grep + file-level inspection

---

## A. Roles and Auth Sources

### A1. User Model

Django's built-in `django.contrib.auth.models.User`. No `AUTH_USER_MODEL` override in `HotelMateBackend/settings.py`. Built-in fields used: `is_superuser`, `is_staff`, `is_active`.

Django Groups and `django.contrib.auth.models.Permission` are **not used anywhere** in the codebase.

### A2. Staff Model — `staff/models.py` → class `Staff`

| Field | Type | Values / Notes |
|---|---|---|
| `user` | `OneToOneField(User, related_name='staff_profile')` | Nullable |
| `hotel` | `ForeignKey('hotel.Hotel')` | Tenant scope |
| `department` | `ForeignKey(Department)` | Nullable, SET_NULL |
| `role` | `ForeignKey(Role)` | Nullable, SET_NULL |
| `access_level` | `CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES)` | `'super_staff_admin'`, `'staff_admin'`, `'regular_staff'` (default) |
| `is_active` | `BooleanField(default=True)` | Active toggle |
| `duty_status` | `CharField(choices=DUTY_STATUS_CHOICES)` | `'off_duty'`, `'on_duty'`, `'on_break'` |
| `allowed_navigation_items` | `ManyToManyField(NavigationItem)` | Feature-level permission gate |

`access_level` is the **primary RBAC field**: 3 tiers — `super_staff_admin` > `staff_admin` > `regular_staff`.

### A3. Role Model — `staff/models.py` → class `Role`

| Field | Type | Notes |
|---|---|---|
| `hotel` | `ForeignKey('hotel.Hotel')` | Per-hotel catalog |
| `department` | `ForeignKey(Department)` | Nullable |
| `name` | `CharField(max_length=100)` | Free-form, e.g. "Receptionist" |
| `slug` | `SlugField(max_length=100)` | Some slugs have hardcoded meaning: `'manager'`, `'admin'`, `'housekeeping'` |

This is a **free-form per-hotel catalog**, not a fixed enum. Certain `slug` values are checked in permission logic (see section E).

### A4. Department Model — `staff/models.py` → class `Department`

| Field | Type | Notes |
|---|---|---|
| `hotel` | `ForeignKey('hotel.Hotel')` | Per-hotel |
| `name` | `CharField(max_length=100)` | |
| `slug` | `SlugField(max_length=100)` | `'housekeeping'` slug has special meaning in `housekeeping/policy.py` |

### A5. NavigationItem Model — `staff/models.py` → class `NavigationItem`

| Field | Type | Notes |
|---|---|---|
| `hotel` | `ForeignKey('hotel.Hotel')` | Per-hotel |
| `name` | `CharField(max_length=100)` | e.g. "Home", "Chat", "Stock Tracker" |
| `slug` | `SlugField(max_length=100)` | Used as permission gate via `HasNavPermission` |
| `path` | `CharField(max_length=255)` | Frontend route |
| `is_active` | `BooleanField(default=True)` | |

Staff are assigned navigation items via `Staff.allowed_navigation_items` M2M. This is the **feature-level permission** system.

### A6. UserProfile Model — `staff/models.py` → class `UserProfile`

| Field | Type |
|---|---|
| `user` | `OneToOneField(User, related_name='profile')` |
| `registration_code` | `OneToOneField(RegistrationCode)` |

No role/permission fields — registration tracking only.

### A7. Guest Model — `guests/models.py` → class `Guest`

| Field | Type | Values |
|---|---|---|
| `guest_type` | `CharField(choices=GUEST_TYPE_CHOICES)` | `'PRIMARY'`, `'COMPANION'`, `'WALKIN'` |
| `primary_guest` | `ForeignKey('self')` | For companion guests |

Guests are **not** Django users. No auth linkage.

### A8. Guest Token Models

**`GuestBookingToken`** — `hotel/models.py`:
- `scopes`: JSONField — e.g. `['STATUS_READ', 'CHAT', 'ROOM_SERVICE']`
- `purpose`: CharField choices — `'STATUS'`, `'PRECHECKIN'`, `'CHAT'`, `'ROOM_SERVICE'`, `'FULL_ACCESS'`

**`BookingManagementToken`** — `hotel/models.py`:
- Time-limited workflow token for email links
- `actions_performed`: JSONField

### A9. BookingGuest Model — `hotel/models.py` → class `BookingGuest`

| Field | Type | Values |
|---|---|---|
| `role` | `CharField(choices=ROLE_CHOICES)` | `'PRIMARY'`, `'COMPANION'` |

Booking party role, not an RBAC role.

### A10. Identity Architecture Summary

```
Django User (is_superuser, is_staff) ─┐
                                      │ OneToOne (staff_profile)
                                      ▼
                              Staff (access_level) ──► Role (slug) ──► Department (slug)
                                │                         │
                                │ M2M                     │ hardcoded slugs: 'manager', 'admin', 'housekeeping'
                                ▼
                         NavigationItem (slug)  ◄── feature gate

Guest identity: GuestBookingToken.scopes[] + BookingManagementToken (no Django User)
```

---

## B. Permission Classes Inventory

### B1. `staff/permissions.py`

| Symbol | Type | Logic |
|---|---|---|
| `resolve_staff_navigation(user)` | Helper function | Returns dict: `is_staff`, `is_superuser`, `hotel_slug`, `access_level`, `allowed_navs[]`, `navigation_items[]`. Superusers get ALL nav items; regular staff get M2M-assigned items. |
| `HasNavPermission(required_slug)` | `BasePermission` | `has_permission`: superuser bypass → calls `resolve_staff_navigation()` → checks `required_slug in allowed_navs`. Parameterized with a nav slug. |
| `requires_nav_permission(slug)` | Decorator | Same logic as `HasNavPermission` for function-based views. **Defined but no usages found in views.** |
| `create_nav_permission(slug)` | Factory function | Returns `HasNavPermission` subclass with slug baked in. |

### B2. `staff/permissions_superuser.py`

| Symbol | Type | Logic |
|---|---|---|
| `IsSuperUser` | `BasePermission` | `has_permission`: `is_superuser` = True **OR** `staff.access_level in ('super_staff_admin', 'staff_admin')`. Despite its name, this grants access to **both admin tiers**, not just superusers. |

### B3. `hotel/permissions.py`

| Symbol | Type | Logic |
|---|---|---|
| `IsHotelStaff` | `BasePermission` | `has_permission`: authenticated + `Staff.objects.get(user=request.user)` + hotel slug/subdomain matches URL's `hotel_slug` or `hotel_identifier`. |
| `IsSuperStaffAdminForHotel` | `BasePermission` | `has_permission`: authenticated + `staff.access_level == 'super_staff_admin'` + `staff.hotel.slug == hotel_slug`. |

### B4. `staff_chat/permissions.py`

| Symbol | Type | Logic |
|---|---|---|
| `IsStaffMember` | `BasePermission` | `has_permission`: authenticated + `hasattr(request.user, 'staff_profile')`. |
| `IsConversationParticipant` | `BasePermission` | `has_object_permission`: `obj.participants.filter(id=staff.id).exists()`. |
| `IsMessageSender` | `BasePermission` | `has_object_permission`: `obj.sender.id == staff.id`. |
| `IsSameHotel` | `BasePermission` | `has_permission`: `staff.hotel.slug == URL hotel_slug`. `has_object_permission`: `obj.hotel.id == staff.hotel.id`. |
| `CanManageConversation` | `BasePermission` | `has_object_permission`: creator OR `role.slug in ['manager', 'admin']`. |
| `CanDeleteMessage` | `BasePermission` | `has_object_permission`: hard delete requires `role.slug in ['manager', 'admin']` or own message. Soft delete: own messages only. |

### B5. `hotel/provisioning_views.py` — inline class

| Symbol | Type | Logic |
|---|---|---|
| `IsSuperUser` (local) | `BasePermission` | `has_permission`: `IsAuthenticated` + `is_superuser` (Django-level only). |

Note: different from `staff/permissions_superuser.py::IsSuperUser` — this one checks only Django `is_superuser`, not `access_level`.

### B6. `housekeeping/policy.py` — policy functions (not DRF classes)

| Symbol | Type | Logic |
|---|---|---|
| `is_manager(staff)` | Function | `user.is_superuser` OR `access_level in ['staff_admin', 'super_staff_admin']` |
| `is_housekeeping(staff)` | Function | `department.slug == 'housekeeping'` OR `role.slug == 'housekeeping'` |
| `can_change_room_status(staff, room, ...)` | Function | Hotel match + role-based status transition matrix |
| `can_view_dashboard(staff)` | Function | `is_manager(staff) or is_housekeeping(staff)` |

### B7. `common/mixins.py` — mixin-based permissions

| Symbol | Type | Default `permission_classes` |
|---|---|---|
| `HotelScopedQuerysetMixin` | Mixin | None (inherits). Derives hotel from `request.user.staff_profile.hotel` only. |
| `HotelScopedViewSetMixin` | Mixin | `[IsAuthenticated, IsStaffMember, IsSameHotel]`. Derives hotel from URL + cross-checks profile. |
| `AttendanceHotelScopedMixin` | Mixin | Inherits from `HotelScopedViewSetMixin`. Adds auto staff assignment. |

### B8. Guest Authentication (non-DRF, custom)

| Module | Mechanism |
|---|---|
| `common/guest_access.py` | `resolve_guest_access(token_str, hotel_slug, required_scopes, require_in_house)` — SHA-256 hash lookup against `GuestBookingToken` + `BookingManagementToken` fallback. Returns `GuestAccessContext` with scopes. |
| `common/guest_auth.py` | `TokenAuthenticationMixin` — extracts token from `?token=` or `Authorization: GuestToken <token>`. `ChatSessionAuthenticationMixin` — extracts from `X-Guest-Chat-Session` header. |
| `common/guest_chat_grant.py` | HMAC-signed, time-limited grant for post-bootstrap chat auth. Claims: `booking_id`, `hotel_slug`, `room_id`, `scope="guest_chat"`. Max age: 4 hours. |

### B9. Global DRF Defaults — `HotelMateBackend/settings.py`

```python
DEFAULT_AUTHENTICATION_CLASSES: [TokenAuthentication, SessionAuthentication]
DEFAULT_PERMISSION_CLASSES: [IsAuthenticated]
```

Views without explicit `permission_classes` fall back to `[IsAuthenticated]`.

---

## C. Endpoint Protection Table

### C1. `staff/views.py`

| View Class | permission_classes | Hotel Scoping |
|---|---|---|
| `CustomAuthToken` | `[AllowAny]` | N/A (login) |
| `StaffRegisterAPIView` | `[AllowAny]` | N/A (registration) |
| `PasswordResetRequestView` | `[AllowAny]` | N/A |
| `PasswordResetConfirmView` | `[AllowAny]` | N/A |
| `StaffMetadataView` | `[IsAuthenticated]` | `hotel__slug=hotel_slug` from URL |
| `UserListAPIView` | `[IsAuthenticated]` | **NO hotel filter** |
| `StaffViewSet` | `[IsSuperUser]` | `get_queryset` filters by staff hotel |
| `GenerateRegistrationPackageAPIView` | `[IsAuthenticated]` | Internal hotel scoping |
| `UsersByHotelRegistrationCodeAPIView` | `[IsAuthenticated]` | Via registration code |
| `PendingRegistrationsAPIView` | `[IsAuthenticated]` | Hotel scoping in view body |
| `CreateStaffFromUserAPIView` | `[IsAuthenticated]` | Hotel scoping in view body |
| `DepartmentViewSet` | `[IsAuthenticated]` (all actions) | `hotel__slug=hotel_slug`; write checks inline |
| `RoleViewSet` | `[IsAuthenticated]` (all actions) | `hotel__slug=hotel_slug`; write checks inline |
| `NavigationItemViewSet` | `[IsAuthenticated]` | `?hotel_slug=` query param (optional); CUD inline `is_superuser` check |
| `StaffNavigationPermissionsView` | `[IsAuthenticated]` | Inline `_check_authorization()` |
| `SaveFCMTokenView` | `[IsAuthenticated]` | Via staff_profile |
| `EmailRegistrationPackageAPIView` | `[IsAuthenticated]` | Via `_resolve_package` |
| `PrintRegistrationPackageAPIView` | `[IsAuthenticated]` | Via `_resolve_package` |

### C2. `staff/me_views.py`

| View Class | permission_classes | Hotel Scoping |
|---|---|---|
| `StaffMeView` | `[IsAuthenticated]` | Via staff_profile |

### C3. `hotel/staff_views.py`

| View Class | permission_classes | Hotel Scoping |
|---|---|---|
| `StaffRoomTypeViewSet` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `StaffRoomViewSet` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `StaffAccessConfigViewSet` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `PresetViewSet` | `[IsAuthenticated]` | Yes |
| `HotelPublicPageViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `PublicSectionViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `PublicElementViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `PublicElementItemViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `HeroSectionViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `GalleryContainerViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `GalleryImageViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `ListContainerViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `CardViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `NewsItemViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `ContentBlockViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `RoomsSectionViewSet` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `HotelSettingsView` | `[IsAuthenticated]` | Yes |
| `StaffBookingsListView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | `.filter(hotel=hotel)` |
| `StaffBookingConfirmView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | `.filter(hotel=hotel)` |
| `StaffBookingCancelView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | `.filter(hotel=hotel)` |
| `StaffBookingDetailView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `StaffBookingMarkSeenView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `StaffBookingAcceptView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `StaffBookingDeclineView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `PublicPageBuilderView` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `HotelStatusCheckView` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `PublicPageBootstrapView` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `SectionCreateView` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `BookingAssignmentView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `BookingPartyManagementView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `AvailableRoomsView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `SafeAssignRoomView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `UnassignRoomView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `MoveRoomView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `BookingCheckInView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `BookingCheckOutView` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Yes |
| `SendPrecheckinLinkView` | `[IsAuthenticated]` | Yes |
| `HotelPrecheckinConfigView` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `HotelSurveyConfigView` | `[IsAuthenticated, IsSuperStaffAdminForHotel]` | Yes |
| `SendSurveyLinkView` | `[IsAuthenticated, IsStaffMember]` | Yes |

### C4. `hotel/public_views.py` — ALL `[AllowAny]`

| View Class | authentication_classes |
|---|---|
| `HotelPublicListView` | default |
| `HotelFilterOptionsView` | default |
| `HotelPublicPageView` | default |
| `PublicPresetsView` | default |
| `ValidatePrecheckinTokenView` | default |
| `SubmitPrecheckinDataView` | default |
| `ValidateSurveyTokenView` | default |
| `SubmitSurveyDataView` | default |
| `HotelCancellationPolicyView` | default |
| `ValidateBookingManagementTokenView` | default |
| `CancelBookingView` | default |
| `BookingStatusView` | default |

### C5. `hotel/booking_views.py` — ALL `[AllowAny]`

`HotelAvailabilityView`, `HotelPricingQuoteView`, `HotelBookingCreateView`, `PublicRoomBookingDetailView`

### C6. `hotel/payment_views.py` — ALL `[AllowAny]`

`CreatePaymentSessionView`, `StripeWebhookView`, `VerifyPaymentView`

### C7. `hotel/canonical_guest_chat_views.py` — ALL `[AllowAny]`, `authentication_classes = []`

`GuestChatContextView`, `GuestChatSendMessageView`, `GuestChatMarkReadView`, `GuestChatPusherAuthView`

### C8. `hotel/guest_portal_views.py`

| View Class | permission_classes | authentication_classes |
|---|---|---|
| `GuestContextView` | `[AllowAny]` | `[]` (custom token in body) |

### C9. `hotel/base_views.py`

| View Class | permission_classes |
|---|---|
| `HotelViewSet` | `[IsSuperUser]` |
| `HotelBySlugView` | `[AllowAny]` |

### C10. `hotel/provisioning_views.py`

| View Class | permission_classes |
|---|---|
| `ProvisionHotelView` | `[IsSuperUser]` (local class: Django `is_superuser` only) |

### C11. `hotel/overstay_views.py`

`OverstayAcknowledgeView`, `OverstayExtendView`, `OverstayStatusView` — ALL `[IsHotelStaff]`

### C12. `hotel/views/rate_plans/views.py` (FBVs)

`rate_plans_list_create`, `rate_plan_detail`, `rate_plan_delete` — ALL `[IsAuthenticated, IsStaffMember]`

### C13. `hotel/views/cancellation_policies/views.py` (FBVs)

`cancellation_policies_list_create`, `cancellation_policy_detail`, `cancellation_policy_validate` — ALL `[IsAuthenticated, IsStaffMember]`

### C14. `rooms/views.py`

| View Class | permission_classes | Hotel Scoping |
|---|---|---|
| `RoomViewSet` | `[IsAuthenticated]` | `.filter(hotel=staff.hotel)` |
| `StaffRoomViewSet` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | `.filter(hotel=staff.hotel)` |
| `RoomTypeViewSet` | `[IsAuthenticated]` | `.filter(hotel=staff.hotel)` |
| `AddGuestToRoomView` | **NONE (default: IsAuthenticated)** | Hotel from URL slug |
| `RoomByHotelAndNumberView` | **NONE (default: IsAuthenticated)** | Hotel from URL slug |
| `checkout_rooms` (FBV) | `[IsAuthenticated]` | Hotel from URL slug |
| `start_cleaning` (FBV) | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Hotel from URL slug |
| `mark_cleaned` (FBV) | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Hotel from URL slug |
| `inspect_room` (FBV) | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Hotel from URL slug |
| `mark_maintenance` (FBV) | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Hotel from URL slug |
| `complete_maintenance` (FBV) | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Hotel from URL slug |
| `turnover_rooms` (FBV) | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Hotel from URL slug |
| `turnover_stats` (FBV) | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Hotel from URL slug |
| `checkout_needed` (FBV) | `[IsAuthenticated]` | Hotel from URL slug |
| `bulk_create_rooms` (FBV) | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Hotel from URL slug |
| `RoomImageViewSet` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | `.filter(room__hotel=staff.hotel)` |

### C15. `bookings/views.py`

| View Class | permission_classes | Hotel Scoping |
|---|---|---|
| `BookingViewSet` | **NONE (default: IsAuthenticated)** | **NO hotel filter** |
| `BookingCategoryViewSet` | **NONE (default: IsAuthenticated)** | Optional `?hotel_slug=` only |
| `GuestDinnerBookingView` | `[AllowAny]` | Hotel from URL slug |
| `RestaurantViewSet` | **NONE (default: IsAuthenticated)** | **NO hotel filter** |
| `RestaurantBlueprintViewSet` | `[IsAuthenticatedOrReadOnly]` | Restaurant slug filter |
| `DiningTableViewSet` | `[IsAuthenticatedOrReadOnly]` | Restaurant slug filter |
| `BlueprintObjectTypeViewSet` | `[AllowAny]` | No |
| `BlueprintObjectViewSet` | `[IsAuthenticated]` | Blueprint filter |
| `AvailableTablesView` | `[AllowAny]` | hotel_slug + restaurant_slug |
| `mark_bookings_seen` (FBV) | `[AllowAny]` | hotel_slug |
| `AssignGuestToTableAPIView` | `[IsAuthenticated]` | hotel_slug + restaurant_slug |
| `UnseatBookingAPIView` | **NONE (default: IsAuthenticated)** | Booking by hotel_slug |
| `DeleteBookingAPIView` | **NONE (default: IsAuthenticated)** | Booking by hotel_slug |

### C16. `chat/views.py` (FBVs)

| Function | permission_classes |
|---|---|
| `get_active_rooms` | `[IsAuthenticated]` |
| `get_conversation_messages` | `[IsAuthenticated]` |
| `send_conversation_message` | `[IsAuthenticated]` |
| `get_or_create_conversation_from_room` | `[IsAuthenticated]` |
| `get_active_conversations` | `[IsAuthenticated]` |
| `get_unread_count` | `[IsAuthenticated]` |
| `mark_conversation_read` | `[AllowAny]` |
| `assign_staff_to_conversation` | `[IsAuthenticated]` |
| `upload_message_attachment` | `[IsAuthenticated]` |
| `get_unread_conversation_count` | `[IsAuthenticated]` |
| `update_message` | `[AllowAny]` |
| `delete_message` | `[AllowAny]` |
| `save_fcm_token` | `[AllowAny]` |
| `delete_attachment` | `[AllowAny]` |

### C17. `housekeeping/views.py`

| View Class | permission_classes | Hotel Scoping |
|---|---|---|
| `HousekeepingDashboardViewSet` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | `.filter(hotel=)` + `can_view_dashboard()` |
| `HousekeepingTaskViewSet` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | `.filter(hotel=)` |
| `RoomStatusViewSet` | `[IsAuthenticated, IsStaffMember, IsSameHotel]` | Hotel scoped |

### C18. `maintenance/views.py`

`MaintenanceRequestViewSet`, `MaintenanceCommentViewSet`, `MaintenancePhotoViewSet` — ALL `[IsHotelStaff]`, `HotelScopedQuerysetMixin`

### C19. `attendance/views.py`

All ViewSets inherit `[IsAuthenticated, IsStaffMember, IsSameHotel]` via `AttendanceHotelScopedMixin` or `HotelScopedViewSetMixin`:
`ClockLogViewSet`, `RosterPeriodViewSet`, `StaffRosterViewSet`, `ShiftLocationViewSet`, `DailyPlanViewSet`, `DailyPlanEntryViewSet`, `CopyRosterViewSet`

### C20. `attendance/views_analytics.py`

| View Class | permission_classes |
|---|---|
| `RosterAnalyticsViewSet` | `[IsAuthenticated]` only — missing `IsStaffMember`/`IsSameHotel` |

### C21. `attendance/face_views.py`

| View Class | permission_classes |
|---|---|
| `FaceManagementViewSet` | `[IsAuthenticated]` |
| `force_clock_in_unrostered` (FBV) | `[IsAuthenticated]` |
| `confirm_clock_out_view` (FBV) | `[IsAuthenticated]` |
| `toggle_break_view` (FBV) | `[IsAuthenticated]` |

All missing `IsStaffMember`/`IsSameHotel`.

### C22. `staff_chat/views.py`

| View Class | permission_classes |
|---|---|
| `StaffListViewSet` | `[IsAuthenticated]` |
| `StaffConversationViewSet` | `[IsAuthenticated]` |

### C23. `staff_chat/views_messages.py` + `staff_chat/views_attachments.py`

All FBVs: `[IsAuthenticated, IsStaffMember, IsSameHotel]`

### C24. `room_services/views.py`

| View Class | permission_classes | Hotel Scoping |
|---|---|---|
| `RoomServiceItemViewSet` | `[AllowAny]` | Hotel scoped |
| `BreakfastItemViewSet` | `[AllowAny]` | Hotel scoped |
| `OrderViewSet` | Dynamic: guest=`[AllowAny]`, staff=`[IsAuthenticated, IsStaffMember, IsSameHotel]` | `.filter(hotel=)` |
| `BreakfastOrderViewSet` | Dynamic: guest=`[AllowAny]`, staff=`[IsAuthenticated, IsStaffMember, IsSameHotel]` | `.filter(hotel=)` |
| `save_guest_fcm_token` (FBV) | `[AllowAny]` | Hotel scoped |

### C25. `room_services/staff_views.py`

`StaffRoomServiceItemViewSet`, `StaffBreakfastItemViewSet` — ALL `[IsAuthenticated, IsStaffMember, IsSameHotel]`

### C26. `stock_tracker/views.py` — ALL `[IsHotelStaff]`

`IngredientViewSet`, `CocktailRecipeViewSet`, `CocktailConsumptionViewSet`, `CocktailIngredientConsumptionViewSet`, `IngredientUsageView`, `StockCategoryViewSet`, `LocationViewSet`, `StockPeriodViewSet`, `StockSnapshotViewSet`, `StockItemViewSet`, `StockMovementViewSet`, `StocktakeViewSet`, `StocktakeLineViewSet`, `SaleViewSet`, `KPISummaryView`

### C27. `stock_tracker/report_views.py`

`StockValueReportView`, `SalesReportView` — ALL `[IsAuthenticated, IsSuperStaffAdminForHotel]`

### C28. `stock_tracker/comparison_views.py`

`CompareCategoriesView`, `TopMoversView`, `CostAnalysisView`, `TrendAnalysisView`, `VarianceHeatmapView`, `PerformanceScorecardView` — ALL `[IsHotelStaff]`

### C29. `entertainment/views.py`

| View Class | permission_classes |
|---|---|
| `GameViewSet` | `[AllowAny]` |
| `GameHighScoreViewSet` | `[AllowAny]` (create: `[IsAuthenticated]`) |
| `GameQRCodeViewSet` | `[AllowAny]` |
| `MemoryGameCardViewSet` | `[AllowAny]` |
| `MemoryGameSessionViewSet` | `[AllowAny]` |
| `MemoryGameTournamentViewSet` | `[AllowAny]` (actions vary) |
| `MemoryGameAchievementViewSet` | `[IsAuthenticated]` |
| `DashboardViewSet` | `[IsAuthenticated]` |
| `QuizCategoryViewSet` | `[AllowAny]` |
| `QuizQuestionViewSet` | `[AllowAny]` |
| `QuizSessionViewSet` | `[AllowAny]` |
| `QuizLeaderboardViewSet` | `[AllowAny]` |
| `QuizTournamentViewSet` | `[AllowAny]` |

### C30. `guests/views.py`

| View Class | permission_classes | Hotel Scoping |
|---|---|---|
| `GuestViewSet` | `[IsAuthenticated]` | `.filter(hotel__slug=hotel_slug)` |

### C31. `home/views.py`

`PostViewSet`, `CommentViewSet`, `CommentReplyViewSet` — ALL `[IsAuthenticated]`, hotel slug scoped

### C32. `hotel_info/views.py`

| View Class | permission_classes | Hotel Scoping |
|---|---|---|
| `download_all_qrs` (FBV) | `[IsAuthenticated]` | hotel_slug query param |
| `HotelInfoViewSet` | `[IsAuthenticatedOrReadOnly]` | `hotel__slug` filterset |
| `HotelInfoCategoryViewSet` | `[IsAuthenticatedOrReadOnly]` | `infos__hotel__slug` |
| `HotelInfoCreateView` | `[IsAuthenticated]` | Via request data |
| `CategoryQRView` | `[IsAuthenticated]` | hotel_slug + category_slug |
| `GoodToKnowEntryViewSet` | `[IsAuthenticatedOrReadOnly]` | `.filter(hotel__slug=)` |

### C33. `common/views.py`

| View Class | permission_classes |
|---|---|
| `ThemePreferenceViewSet` | `[IsAuthenticatedOrReadOnly]` |

### C34. `notifications/views.py`

| View Class | permission_classes | authentication_classes |
|---|---|---|
| `PusherAuthView` | `[AllowAny]` | `[]` (custom auth inside) |
| `SaveFcmTokenView` | `[IsAuthenticated]` | default |

### C35. `voice_recognition/views_voice.py`

`VoiceCommandView`, `VoiceCommandConfirmView` — ALL `[IsAuthenticated]`

### C36. `hotel/face_config_views.py`

| View Class | permission_classes |
|---|---|
| `HotelFaceConfigView` | `[AllowAny]` |

### C37. Plain Django Views (not DRF) — `guest_urls.py`

| Function | Auth | Notes |
|---|---|---|
| `guest_home` | None | Plain Django view |
| `guest_rooms` | None | Plain Django view |
| `check_availability` | None | Plain Django view |
| `get_pricing_quote` | None | `@csrf_exempt` |
| `create_booking` | None | `@csrf_exempt` |
| `get_cancellation_policy_details` | None | Plain Django view |

---

## D. Hotel Scoping Table

### D1. Method A — `request.user.staff_profile.hotel` (trusted, server-side)

| File | View/Context | Usage |
|---|---|---|
| `common/mixins.py` | `HotelScopedQuerysetMixin.get_hotel()` | Base mixin |
| `common/mixins.py` | `HotelScopedViewSetMixin.get_staff_hotel()` | URL + profile cross-check |
| `stock_tracker/views.py` | `_get_staff_hotel(request)` helper | Defense-in-depth |
| `attendance/views.py` | `AttendanceOverviewView` | Inline in GET |
| `hotel/overstay_views.py` | 3 overstay action views | Inline |
| `hotel/staff_serializers.py` | Serializer validate method | |
| `hotel/staff_views.py` | **14 places** | `hotel_slug = self.request.user.staff_profile.hotel.slug` |
| `maintenance/views.py` | Maintenance task views | |
| `rooms/serializers.py` | Room serializer cross-hotel validation | |
| `staff/views.py` | `DepartmentViewSet`, `RoleViewSet` | Fallback for queryset |

### D2. Method B — URL `hotel_slug` kwarg

Used in **~28+ views** across: `attendance/views.py`, `attendance/face_views.py`, `bookings/views.py`, `guests/views.py`, `hotel_info/views.py`, `room_services/views.py`, `staff/views.py`, `staff_chat/views.py`

Cross-checked against profile in views using `IsSameHotel` or `HotelScopedViewSetMixin`. **Not cross-checked** in views using only `[IsAuthenticated]`.

### D3. Method C — Query parameter `?hotel_slug=` or `?hotel=`

| File | View | Param | Cross-check |
|---|---|---|---|
| `bookings/views.py` | `BookingCategoryViewSet` | `hotel_slug` | **Optional, not enforced** |
| `bookings/views.py` | `BookingViewSet` | `hotel_slug` | Fallback from URL |
| `attendance/views.py` | Attendance query views | `hotel_slug` | |
| `entertainment/views.py` | All entertainment ViewSets | `hotel` | **Guest-facing, AllowAny** |
| `hotel/public_views.py` | `HotelPublicListView` | `hotel_type` | Public filter |
| `hotel_info/views.py` | QR code lookups | `hotel_slug` | |
| `room_services/views.py` | Order history | `hotel_slug` | |
| `rooms/views.py` | Room list filter | `hotel_id` | |
| `staff/views.py` | Reg code listing | `hotel_slug` | Superuser-only context |
| `staff/views.py` | `NavigationItemViewSet` | `hotel_slug` | Optional filter |

### D4. Method D — `request.data` (POST body, client-controlled)

| File | View | Field | Context |
|---|---|---|---|
| `attendance/views.py` | Attendance settings | `request.data.get("hotel")` | Default hotel for settings |
| `staff/views.py` | Registration code creation | `request.data.get('hotel_slug')` | Reg code creation |

### D5. Method E — `request.user.hotel_id` (direct attribute)

| File | Context |
|---|---|
| `stock_tracker/cocktail_serializers.py` | `validated_data['hotel_id'] = request.user.hotel_id` — anomalous; `User` model has no `hotel_id` field |

### D6. Method F — URL path function param (e.g., `def get(request, hotel_slug)`)

Used in: `bookings/views.py` (3 FBVs), `attendance/face_views.py` (3 FBVs)

---

## E. Duplicated / Scattered Authorization Logic

### E1. `is_superuser` checks — 21+ locations

| File | Context |
|---|---|
| `hotel/provisioning_views.py` | Permission class (Django `is_superuser` only) |
| `rooms/views.py` | `if destructive and not request.user.is_superuser` — bulk update guard |
| `housekeeping/views.py` | `if not (is_manager(staff) or request.user.is_superuser)` — task assignment |
| `stock_tracker/views.py` | Period management, snapshot unlock, snapshot create/finalize, stocktake finalize — **5 separate inline checks** |
| `stock_tracker/stock_serializers.py` | Serializer-level superuser check for hidden fields — **2 places** |
| `staff/views.py` | Registration code listing, `DepartmentViewSet`, `RoleViewSet`, `NavigationItemViewSet` (CUD), `_RegistrationPackageDeliveryMixin` — **6 places** |
| `attendance/admin.py` | Admin delete permission for audit logs |
| `housekeeping/admin.py` | Admin-level superuser check |
| `staff/admin.py` | Admin queryset filtering |

### E2. `is_staff` checks — 2 locations

| File | Context |
|---|---|
| `entertainment/views.py` | `if not (request.user.is_staff or tournament.created_by == request.user)` — tournament delete |
| `entertainment/views.py` | Same pattern — tournament update |

### E3. `access_level` inline checks — 9+ locations

| File | Context |
|---|---|
| `housekeeping/views.py` | `staff.access_level in ['staff_admin', 'super_staff_admin']` — dashboard access |
| `housekeeping/policy.py` | `access_level in ['staff_admin', 'super_staff_admin']` — `is_manager()` |
| `staff/views.py` | `requested_access_level == "super_staff_admin" and requesting_staff.access_level != "super_staff_admin"` — escalation guard |
| `staff/views.py` | `requesting_staff.access_level == 'regular_staff'` → 403 — nav permission updates |
| `staff/views.py` | Same pattern — staff creation |
| `staff/views.py` | `check_write_permission()` — `access_level in ('staff_admin', 'super_staff_admin')` for department/role write |

### E4. `role.slug` hardcoded checks — 4 locations

| File | Slugs | Context |
|---|---|---|
| `staff_chat/permissions.py` → `CanManageConversation` | `['manager', 'admin']` | Manage any conversation |
| `staff_chat/permissions.py` → `CanDeleteMessage` | `['manager', 'admin']` | Hard delete messages |
| `housekeeping/policy.py` → `is_housekeeping()` | `'housekeeping'` | Department or role slug |

### E5. Two different `IsSuperUser` classes with different behavior

| File | Logic |
|---|---|
| `staff/permissions_superuser.py` → `IsSuperUser` | `is_superuser` OR `access_level in ('super_staff_admin', 'staff_admin')` |
| `hotel/provisioning_views.py` → `IsSuperUser` (local) | `is_superuser` only (Django-level) |

Same class name, different behavior, different files.

### E6. `request.user.is_authenticated` in view bodies — 7 locations

| File | Context |
|---|---|
| `chat/views.py` | Inline auth check in Pusher auth |
| `bookings/views.py` | `RestaurantBookingViewSet.get_serializer_class()` |
| `bookings/views.py` | `RestaurantBookingViewSet.perform_create()` |
| `room_services/views.py` | `OrderViewSet` — determines staff vs guest context |
| `room_services/views.py` | `BreakfastOrderViewSet` — same pattern |
| `notifications/views.py` | Anonymous user check |
| `stock_tracker/views.py` | `StocktakeViewSet` — auth-conditional queryset |

### E7. Authorization Helper functions (not centralized)

| Function | File | Logic |
|---|---|---|
| `is_manager(staff)` | `housekeeping/policy.py` | `user.is_superuser` OR `access_level in ['staff_admin', 'super_staff_admin']` |
| `is_housekeeping(staff)` | `housekeeping/policy.py` | `department.slug == 'housekeeping'` OR `role.slug == 'housekeeping'` |
| `can_change_room_status(...)` | `housekeeping/policy.py` | Hotel match + role matrix |
| `can_view_dashboard(staff)` | `housekeeping/policy.py` | `is_manager` or `is_housekeeping` |
| `check_face_attendance_permissions(...)` | `attendance/utils.py` | Hotel match + active status + hotel settings + department restrictions |
| `resolve_staff_navigation(user)` | `staff/permissions.py` | Canonical nav resolver |
| `_resolve_package(request, pk)` | `staff/views.py` | Superuser bypass + same-hotel + admin access level |
| `check_write_permission(hotel)` | `staff/views.py` | Superuser OR admin access levels |
| `HotelSubdomainBackend.authenticate()` | `hotel/auth_backends.py` | Superuser bypasses hotel check |
| `resolve_guest_access()` | `common/guest_access.py` | Guest token auth (GBT/BMT) |

### E8. Navigation/Dashboard Backend Endpoints

**Navigation data returned via:**
- `StaffLoginView` (`staff/views.py`) — merges `resolve_staff_navigation()` into login response
- `StaffMeView` (`staff/me_views.py`) — returns nav data for current user
- `NavigationItemViewSet` (`staff/views.py`) — CRUD for nav items; list uses optional `?hotel_slug=` filter; CUD guarded by inline `is_superuser` check
- `StaffNavigationPermissionsView` (`staff/views.py`) — GET/PATCH for per-staff nav assignments; guarded by `_check_authorization()` which requires superuser OR `access_level in ('super_staff_admin', 'staff_admin')` with same hotel

**Dashboard endpoints:**
- `HousekeepingDashboardViewSet` (`housekeeping/views.py`) — `[IsAuthenticated, IsStaffMember, IsSameHotel]` + `can_view_dashboard(staff)`
- `DashboardViewSet` (`entertainment/views.py`) — `[IsAuthenticated]`, hotel from `?hotel` query param (optional)

### E9. Serializers That Expose Role/Permission Data

| Serializer | File | Exposed Fields |
|---|---|---|
| `StaffSerializer` | `staff/serializers.py` | `role`, `role_detail`, `access_level`, `allowed_navs`, `is_staff_member`, `role_slug`, `hotel_slug`, `department_detail` |
| `StaffLoginOutputSerializer` | `staff/serializers.py` | `is_staff`, `is_superuser`, `hotel_slug`, `access_level`, `allowed_navs[]`, `navigation_items[]`, `isAdmin` (legacy alias), `role`, `department` |
| `StaffAttendanceSummarySerializer` | `staff/serializers.py` | `is_superuser`, `access_level`, `allowed_navs`, `role`, `department` |
| `StaffMinimalSerializer` | `staff/serializers.py` | `role` (nested: id/name/slug/description), `department` |
| `UserSerializer` | `staff/serializers.py` | `staff_profile` (nested `StaffMinimalSerializer`) |
| `StaffMemberSerializer` | `staff_chat/serializers.py` | `role_name` |
| `StaffListSerializer` | `staff_chat/serializers.py` | `role` (id/name/slug), `department` |
| `RoomMessageSerializer` | `chat/serializers.py` | `staff_role_name`, nested `role` |
| `RosterSlotSerializer` | `attendance/serializers.py` | `role` (PK), `role_name` |

---

*End of audit. Facts only, no recommendations.*
