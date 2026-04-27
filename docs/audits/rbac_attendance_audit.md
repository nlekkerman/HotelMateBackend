# RBAC Backend Audit — `attendance` module

Code-derived audit. No documentation, naming, or prior-summary inputs.
Mark **UNKNOWN** anywhere code did not verify a fact.

---

## 1. Files inspected

- [attendance/urls.py](attendance/urls.py)
- [attendance/views.py](attendance/views.py)
- [attendance/views_analytics.py](attendance/views_analytics.py)
- [attendance/face_views.py](attendance/face_views.py)
- [attendance/serializers.py](attendance/serializers.py) (scanned for legacy gates)
- [attendance/utils.py](attendance/utils.py) (`check_face_attendance_permissions`)
- [staff_urls.py](staff_urls.py) (mount point)
- [staff/permissions.py](staff/permissions.py) (`HasNavPermission`, `CanManageRoster`, `resolve_tier`, `_tier_at_least`, `HasAttendanceNav`, `TIER_DEFAULT_NAVS`)
- [staff/capability_catalog.py](staff/capability_catalog.py) (presets + canonical capability set)
- [staff/module_policy.py](staff/module_policy.py) (`MODULE_POLICY`)
- [common/mixins.py](common/mixins.py) (`HotelScopedViewSetMixin`, `AttendanceHotelScopedMixin`)

Files referenced by the audit task but **NOT present in the workspace** (verified absent in [attendance/](attendance/)):
- `attendance/services.py` — does not exist
- `attendance/policy.py` — does not exist

Other attendance python files NOT inspected for gating (no view classes / not in scope): `business_rules.py`, `models.py`, `admin.py`, `analytics.py`, `analytics_roster.py`, `apps.py`, `filters.py`, `pdf_report.py`, `serializers_analytics.py`, `tests*.py`, `management/`.

---

## 2. Endpoint inventory

### Mount

[staff_urls.py](staff_urls.py#L260-L268) generates app-wrapped routes from `STAFF_APPS`:
```
hotel/<str:hotel_slug>/attendance/  →  include('attendance.urls')
```
`'attendance'` is in `STAFF_APPS` at [staff_urls.py L48-L62](staff_urls.py#L48-L62). Effective prefix as documented in view docstrings is `/api/staff/hotel/<hotel_slug>/attendance/`.

### View classes (from [attendance/views.py](attendance/views.py) and [attendance/face_views.py](attendance/face_views.py) and [attendance/views_analytics.py](attendance/views_analytics.py))

| Class | File:Line | Mixin chain |
|---|---|---|
| `ClockLogViewSet` | [views.py L307](attendance/views.py#L307) | `AttendanceHotelScopedMixin, viewsets.ModelViewSet` |
| `RosterPeriodViewSet` | [views.py L944](attendance/views.py#L944) | `AttendanceHotelScopedMixin, viewsets.ModelViewSet` |
| `StaffRosterViewSet` | [views.py L1538](attendance/views.py#L1538) | `AttendanceHotelScopedMixin, viewsets.ModelViewSet` |
| `ShiftLocationViewSet` | [views.py L1827](attendance/views.py#L1827) | `HotelScopedViewSetMixin, viewsets.ModelViewSet` |
| `DailyPlanViewSet` | [views.py L1838](attendance/views.py#L1838) | `HotelScopedViewSetMixin, viewsets.ModelViewSet` |
| `DailyPlanEntryViewSet` | [views.py L1920](attendance/views.py#L1920) | `viewsets.ModelViewSet` (no hotel-scoping mixin) |
| `CopyRosterViewSet` | [views.py L1954](attendance/views.py#L1954) | `AttendanceHotelScopedMixin, viewsets.ViewSet` |
| `RosterAnalyticsViewSet` | [views_analytics.py L26](attendance/views_analytics.py#L26) | `ViewSet` |
| `FaceManagementViewSet` | [face_views.py L30](attendance/face_views.py#L30) | `AttendanceHotelScopedMixin, viewsets.GenericViewSet` |
| `force_clock_in_unrostered` (FBV) | [face_views.py L1060](attendance/face_views.py#L1060) | `@api_view` |
| `confirm_clock_out_view` (FBV) | [face_views.py L1212](attendance/face_views.py#L1212) | `@api_view` |
| `toggle_break_view` (FBV) | [face_views.py L1341](attendance/face_views.py#L1341) | `@api_view` |

### Endpoints

Permission key:
- **A** = `IsAuthenticated, HasNavPermission('attendance'), IsStaffMember, IsSameHotel` (read-tier)
- **A+M** = A plus `CanManageRoster` (writes only ⇒ requires tier `super_staff_admin+`; reads bypass via `safe_methods` check inside `CanManageRoster`)
- **F** = `IsAuthenticated, HasNavPermission('attendance'), IsStaffMember, IsSameHotel` plus inline `check_face_attendance_permissions(staff, hotel)`
- **FBV** = `@permission_classes([IsAuthenticated])` plus inline `HasNavPermission('attendance').has_permission(...)` plus inline `check_face_attendance_permissions(...)` — no class-level `IsStaffMember`/`IsSameHotel`

Routes are mounted under `…/attendance/` (router slugs from [attendance/urls.py](attendance/urls.py#L26-L29) and explicit `path()` entries).

#### `ClockLogViewSet` (router-registered as `clock-logs`, [urls.py L28](attendance/urls.py#L28))
Permissions per [views.py L311-L322](attendance/views.py#L311-L322): A for self-service; A+M for `create/update/partial_update/destroy/approve_log/reject_log/auto_attach_shift/relink_day`. Serializer: `ClockLogSerializer`. Model: `ClockLog`.

| Method | Path (suffix under `clock-logs/`) | Action | Gate |
|---|---|---|---|
| GET | `/` | `list` | A |
| POST | `/` | `create` | A+M |
| GET | `/{pk}/` | `retrieve` | A |
| PUT/PATCH | `/{pk}/` | `update` / `partial_update` | A+M |
| DELETE | `/{pk}/` | `destroy` | A+M |
| POST | `/register-face/` | `register_face` ([L327](attendance/views.py#L327)) | A |
| POST | `/face-clock-in/` | `face_clock_in` ([L353](attendance/views.py#L353)) | A |
| GET | `/status/` | `current_status` ([L457](attendance/views.py#L457)) | A |
| POST | `/detect/` | `detect_face_only` ([L479](attendance/views.py#L479)) | A |
| POST | `/{pk}/auto-attach-shift/` | `auto_attach_shift` ([L517](attendance/views.py#L517)) | A+M |
| POST | `/relink-day/` | `relink_day` ([L543](attendance/views.py#L543)) | A+M |
| GET | `/currently-clocked-in/` | `currently_clocked_in` ([L580](attendance/views.py#L580)) | A |
| GET | `/department-logs/` | `department_logs` ([L601](attendance/views.py#L601)) | A |
| GET | `/department-status/` | `department_status` ([L629](attendance/views.py#L629)) | A |
| POST | `/unrostered-confirm/` | `unrostered_confirm` ([L704](attendance/views.py#L704)) | A (NOT in management set) |
| POST | `/{pk}/approve/` | `approve_log` ([L786](attendance/views.py#L786)) | A+M |
| POST | `/{pk}/reject/` | `reject_log` ([L821](attendance/views.py#L821)) | A+M |
| POST | `/{pk}/stay-clocked-in/` | `stay_clocked_in` ([L869](attendance/views.py#L869)) | A (NOT in management set) |
| POST | `/{pk}/force-clock-out/` | `force_clock_out` ([L901](attendance/views.py#L901)) | A (NOT in management set) |

#### `RosterPeriodViewSet` (explicit bindings; both `roster-periods/…` and alias `periods/…` paths, [urls.py L110-L131](attendance/urls.py#L110-L131))
Permissions per [views.py L948-L953](attendance/views.py#L948-L953): A+M on **all** actions. Serializer: `RosterPeriodSerializer`. Model: `RosterPeriod`.

| Method | Path | Action | Gate |
|---|---|---|---|
| GET / POST | `roster-periods/` and `periods/` | `list` / `create` | A+M |
| GET / PUT / DELETE | `roster-periods/{pk}/` and `periods/{pk}/` | `retrieve` / `update` / `destroy` | A+M |
| POST | `…/{pk}/add-shift/` | `add_shift` ([L961](attendance/views.py#L961)) | A+M |
| POST | `…/{pk}/create-department-roster/` | `create_department_roster` ([L970](attendance/views.py#L970)) | A+M |
| POST | `roster-periods/create-for-week/` and `periods/create-for-week/` | `create_for_week` ([L994](attendance/views.py#L994)) | A+M |
| GET | `periods/{pk}/export-pdf/` | `export_pdf` ([L1029](attendance/views.py#L1029)) | A+M (read passes) |
| POST | `…/{pk}/finalize/` | `finalize_period` ([L1348](attendance/views.py#L1348)) | A+M, plus inline `_tier_at_least(super_staff_admin)` gate on `force=true` ([L1369](attendance/views.py#L1369)) |
| POST | `…/{pk}/unfinalize/` | `unfinalize_period` ([L1421](attendance/views.py#L1421)) | A+M |
| GET | `…/{pk}/finalization-status/` | `finalization_status` ([L1485](attendance/views.py#L1485)) | A+M (read passes) |
| GET | `…/{pk}/finalized-rosters/` | `finalized_rosters_by_department` ([L1512](attendance/views.py#L1512)) | A+M (read passes) |
| POST | `periods/create-custom-period/` | `create_custom_period` ([L1110](attendance/views.py#L1110)) | A+M |
| POST | `periods/{pk}/duplicate-period/` | `duplicate_period` ([L1268](attendance/views.py#L1268)) | A+M |

#### `StaffRosterViewSet` (explicit bindings, [urls.py L137-L139](attendance/urls.py#L137-L139))
Permissions per [views.py L1545-L1550](attendance/views.py#L1545-L1550): A+M on all actions. Serializer: `StaffRosterSerializer`. Model: `StaffRoster`. Filter: `StaffRosterFilter`.

| Method | Path | Action | Gate |
|---|---|---|---|
| GET / POST | `shifts/` | `list` / `create` | A+M |
| GET / PUT / DELETE | `shifts/{pk}/` | `retrieve` / `update` / `destroy` | A+M |
| POST | `shifts/bulk-save/` | `bulk_save` ([L1578](attendance/views.py#L1578)) | A+M |
| GET | `shifts/daily-pdf/` | `daily_pdf` ([L1731](attendance/views.py#L1731)) | A+M (read passes) |
| GET | `shifts/staff-pdf/` | `staff_pdf` ([L1762](attendance/views.py#L1762)) | A+M (read passes) |

#### `ShiftLocationViewSet` (router AND explicit bindings — duplicate route surface, [urls.py L29 + L155-L156](attendance/urls.py#L29))
Permissions per [views.py L1831-L1836](attendance/views.py#L1831-L1836): A+M. Serializer: `ShiftLocationSerializer`. Model: `ShiftLocation`.

| Method | Path | Action | Gate |
|---|---|---|---|
| GET / POST | `shift-locations/` | `list` / `create` | A+M |
| GET / PUT / DELETE | `shift-locations/{pk}/` | `retrieve` / `update` / `destroy` | A+M |

#### `DailyPlanViewSet` (explicit bindings, [urls.py L161-L171](attendance/urls.py#L161-L171))
Permissions per [views.py L1842-L1847](attendance/views.py#L1842-L1847): A+M. Serializer: `DailyPlanSerializer`. Model: `DailyPlan`.

| Method | Path | Action | Gate |
|---|---|---|---|
| GET / POST | `daily-plans/` | `list` / `create` | A+M |
| GET / PUT / DELETE | `daily-plans/{pk}/` | `retrieve` / `update` / `destroy` | A+M |
| GET / POST | `departments/{department_slug}/daily-plans/` | `list` / `create` | A+M |
| GET | `departments/{department_slug}/daily-plans/prepare-daily-plan/` | `prepare_daily_plan` ([L1858](attendance/views.py#L1858)) | A+M (read passes) |
| GET | `departments/{department_slug}/daily-plans/download-pdf/` | `download_pdf` ([UNKNOWN — referenced in urls.py L84 but method body not located in inspected ranges]) | A+M (read passes) |

#### `DailyPlanEntryViewSet` (explicit bindings, [urls.py L165-L166](attendance/urls.py#L165-L166))
Permissions per [views.py L1924-L1929](attendance/views.py#L1924-L1929): A+M. Serializer: `DailyPlanEntrySerializer`. Model: `DailyPlanEntry`.

| Method | Path | Action | Gate |
|---|---|---|---|
| GET / POST | `daily-plans/{daily_plan_pk}/entries/…/` (list mounted; see urls) | `list` / `create` | A+M |
| GET / PUT / DELETE | `daily-plans/{daily_plan_pk}/entries/{pk}/` | `retrieve` / `update` / `destroy` | A+M |

NOTE: This viewset does **not** include `HotelScopedViewSetMixin`. Hotel scoping is enforced inline by `get_daily_plan()` raising `PermissionDenied` if `daily_plan.hotel.id != staff_hotel.id` ([views.py L1933-L1942](attendance/views.py#L1933-L1942)).

#### `CopyRosterViewSet` ([urls.py L173-L177](attendance/urls.py#L173-L177))
Permissions per [views.py L1965-L1970](attendance/views.py#L1965-L1970): A+M. Plus per-action rate limit (`MAX_COPIES_PER_HOUR=10`, [L1956-L1957](attendance/views.py#L1956)) and operation size cap (`MAX_SHIFTS_PER_COPY=500`).

| Method | Path | Action | Gate |
|---|---|---|---|
| POST | `shift-copy/copy-roster-bulk/` | `copy_roster_bulk` ([L2013](attendance/views.py#L2013)) | A+M |
| POST | `shift-copy/copy-roster-day-all/` | `copy_roster_day_all` ([L2160](attendance/views.py#L2160)) | A+M |
| POST | `shift-copy/copy-week-staff/` | `copy_week_staff` ([L2289](attendance/views.py#L2289)) | A+M |
| POST | `shift-copy/copy-entire-period/` | `copy_entire_period` ([UNKNOWN exact line in inspected ranges]) | A+M |

#### `RosterAnalyticsViewSet` (explicit bindings, [urls.py L142-L153](attendance/urls.py#L142-L153))
Permissions per [views_analytics.py L28-L34](attendance/views_analytics.py#L28-L34): A only (no `CanManageRoster`; all actions are GET).

| Method | Path | Action | Gate |
|---|---|---|---|
| GET | `roster-analytics/staff-summary/` | `staff_summary` ([L67](attendance/views_analytics.py#L67)) | A |
| GET | `roster-analytics/department-summary/` | `department_summary` ([L58](attendance/views_analytics.py#L58)) | A |
| GET | `roster-analytics/kpis/` | `kpis` ([L46](attendance/views_analytics.py#L46)) | A |
| GET | `roster-analytics/daily-totals/` | `daily_totals` | A |
| GET | `roster-analytics/daily-by-department/` | `daily_by_department` | A |
| GET | `roster-analytics/daily-by-staff/` | `daily_by_staff` | A |
| GET | `roster-analytics/weekly-totals/` | `weekly_totals` | A |
| GET | `roster-analytics/weekly-by-department/` | `weekly_by_department` | A |
| GET | `roster-analytics/weekly-by-staff/` | `weekly_by_staff` | A |

#### `FaceManagementViewSet` (explicit bindings, [urls.py L181-L189](attendance/urls.py#L181-L189))
Permissions per [face_views.py L41-L47](attendance/face_views.py#L41-L47): A only (no `CanManageRoster`); each action additionally calls `check_staff_permissions(...)` → `check_face_attendance_permissions(...)` ([utils.py L495-L532](attendance/utils.py#L495-L532)).

| Method | Path | Action | Gate |
|---|---|---|---|
| POST | `face-management/register-face/` | `register_face` ([L63](attendance/face_views.py#L63)) | F |
| POST | `face-management/revoke-face/` | `revoke_face` ([L119](attendance/face_views.py#L119)) | F |
| GET | `face-management/list-faces/` | `list_faces` ([L171](attendance/face_views.py#L171)) | F |
| POST | `face-management/face-clock-in/` | `face_clock_in` ([L218](attendance/face_views.py#L218)) | F |
| GET | `face-management/audit-logs/` | `audit_logs` ([L433](attendance/face_views.py#L433)) | F |
| GET | `face-management/face-status/` | `face_status` ([L628](attendance/face_views.py#L628)) | F |
| POST | `face-management/force-clock-in/` | (function `force_clock_in_unrostered` — bound from FBV at urls.py, NOT the viewset's `.force_clock_in_unrostered` action at [L662](attendance/face_views.py#L662)) | FBV |
| POST | `face-management/confirm-clock-out/` | `confirm_clock_out_view` (FBV) | FBV |
| POST | `face-management/toggle-break/` | `toggle_break_view` (FBV) | FBV |

Unmounted (defined in viewset but not in [urls.py](attendance/urls.py)):
- `FaceManagementViewSet.detect_staff_with_status` (`detect-staff`, [L523](attendance/face_views.py#L523))
- `FaceManagementViewSet.force_clock_in_unrostered` ([L662](attendance/face_views.py#L662))
- `FaceManagementViewSet.confirm_clock_out` ([L786](attendance/face_views.py#L786))
- `FaceManagementViewSet.toggle_break` ([L910](attendance/face_views.py#L910))

---

## 3. Current authority checks (per endpoint group)

| Group | Authentication | Same-hotel check | Staff check | Role-string checks | Tier / access_level checks | Nav slug checks | Inline custom logic | Missing checks |
|---|---|---|---|---|---|---|---|---|
| `ClockLogViewSet` self-service (read + clock/face/status/confirm/break) | `IsAuthenticated` | `IsSameHotel` + many actions also do `staff.hotel.slug != hotel_slug` inline (e.g. [L342](attendance/views.py#L342), [L370](attendance/views.py#L370), [L497](attendance/views.py#L497), [L596](attendance/views.py#L596)) | `IsStaffMember`; some actions also re-check `staff_profile` inline | none | `HasNavPermission('attendance')` is nav-slug, not tier; no tier gate | `attendance` | unrostered/break/force-clock-out actions update `Staff.duty_status` directly | No fine-grained capability for `clock_in`, `clock_out`, `break_*`, `unrostered_confirm`, `stay_clocked_in`, `force_clock_out` (any user with attendance nav can invoke) |
| `ClockLogViewSet` management actions (`create`/`update`/`destroy`/`approve_log`/`reject_log`/`auto_attach_shift`/`relink_day`) | `IsAuthenticated` | `IsSameHotel` | `IsStaffMember` | none | `CanManageRoster` ⇒ `_tier_at_least(super_staff_admin)` for write methods only ([permissions.py L333-L344](staff/permissions.py#L333-L344)) | `attendance` | none | No capability separation between `attendance.log.update` vs `attendance.log.approve` vs `attendance.log.delete` |
| `RosterPeriodViewSet` (all actions) | `IsAuthenticated` | `IsSameHotel` | `IsStaffMember` | none | `CanManageRoster` (super_staff_admin+) | `attendance` | `finalize_period` does extra `_tier_at_least('super_staff_admin')` for `force=true` ([L1369](attendance/views.py#L1369)) — redundant with `CanManageRoster` for non-GET | No separation: read-only access to periods is gated at the same tier as create/finalize. `finalization_status` (GET) and `export_pdf` (GET) bypass the tier check via `safe_methods` so anyone with attendance-nav reads them. |
| `StaffRosterViewSet` | `IsAuthenticated` | `IsSameHotel` | `IsStaffMember` | none | `CanManageRoster` | `attendance` | none | Same — reads (GET) pass on nav alone; writes need super_staff_admin |
| `ShiftLocationViewSet` | same as above | same | same | none | `CanManageRoster` | `attendance` | none | Same |
| `DailyPlanViewSet` | same | same | same | none | `CanManageRoster` | `attendance` | none | Same |
| `DailyPlanEntryViewSet` | `IsAuthenticated` | NO class-level `IsSameHotel` (mixin not applied); inline `daily_plan.hotel.id != staff_hotel.id` only ([L1939-L1942](attendance/views.py#L1939-L1942)) | `IsStaffMember` | none | `CanManageRoster` | `attendance` | inline hotel check via `get_daily_plan` | Slight inconsistency vs peers (no `HotelScopedViewSetMixin`) — relies entirely on `get_daily_plan` |
| `CopyRosterViewSet` | `IsAuthenticated` | `IsSameHotel` | `IsStaffMember` | none | `CanManageRoster` | `attendance` | rate-limit + operation-size guards, audit logging | None for tier/nav |
| `RosterAnalyticsViewSet` | `IsAuthenticated` | `IsSameHotel` | `IsStaffMember` | none | NONE — analytics readable by anyone with attendance nav | `attendance` | none | No supervisor/manager capability gate on analytics — every staff with the nav can read hotel-wide hours/KPIs |
| `FaceManagementViewSet` | `IsAuthenticated` | `IsSameHotel` | `IsStaffMember` | none | NONE | `attendance` | inline `check_face_attendance_permissions(staff, hotel)` ([utils.py L495](attendance/utils.py#L495)) — checks `staff.hotel_id`, `is_active`, hotel `attendance_settings.face_attendance_enabled`, optional dept allowlist | No tier separation: `revoke_face` and `audit_logs` have the same gate as `register_face` and `face-clock-in` |
| FBVs (`force_clock_in_unrostered`, `confirm_clock_out_view`, `toggle_break_view`) | `IsAuthenticated` | NO class-level `IsSameHotel`; inline `check_face_attendance_permissions` enforces `staff.hotel_id == hotel.id` | NO class-level `IsStaffMember`; inline `getattr(request.user, 'staff_profile', None)` check | none | NONE | inline `HasNavPermission('attendance').has_permission(request, None)` — note `view=None` (works because `HasNavPermission.has_permission` does not consult `view`) | none | Inconsistent gating shape vs peer endpoints (instance call vs class registration); no tier gate on `force_clock_in_unrostered` (creates an unrostered, pending-approval log) |

Module visibility resolver: `HasNavPermission` ([staff/permissions.py L249-L283](staff/permissions.py#L249-L283)) calls `resolve_effective_access(user)` and checks `'attendance' in allowed_navs`. `'attendance'` is in `TIER_DEFAULT_NAVS` for both `super_staff_admin` and `staff_admin` ([staff/permissions.py L40-L52](staff/permissions.py#L40-L52)); not in `regular_staff` defaults — so `regular_staff` only gets attendance nav if explicitly granted via the staff's `allowed_navs` overrides (mechanism in `resolve_effective_access`, not re-verified here).

---

## 4. Action surface (derived from real endpoints)

Self-service / user actions (any staff w/ attendance nav):
- `clock_in` (face-recognition path: `ClockLog.face_clock_in`, `unrostered_confirm`, FBV `force_clock_in_unrostered`)
- `clock_out` (`ClockLog.face_clock_in` toggles, FBV `confirm_clock_out_view`, `force_clock_out`)
- `break_start` / `break_end` (FBV `toggle_break_view`, `FaceManagementViewSet.toggle_break`)
- `clock_status_read` (`current_status`, `currently_clocked_in`, `department_logs`, `department_status`)
- `face_register_self` (`register_face` — staff registers own face)
- `face_status_read_self` (`face_status`)
- `face_detect` (`detect_face_only`)

Management / supervisory actions (currently gated by tier `super_staff_admin+`):
- `clock_log_create` / `clock_log_update` / `clock_log_delete` (`ClockLogViewSet` CRUD)
- `clock_log_approve` (`approve_log`)
- `clock_log_reject` (`reject_log`)
- `clock_log_relink` (`auto_attach_shift`, `relink_day`)
- `roster_period_create` / `update` / `delete`
- `roster_period_create_for_week`, `create_custom_period`, `duplicate_period`
- `roster_period_finalize` / `unfinalize`
- `roster_period_force_finalize` (override of validation — extra tier check)
- `roster_period_export_pdf`, `finalization_status`, `finalized_rosters_by_department` (read, currently bypasses tier via safe_methods)
- `roster_shift_create` / `update` / `delete` / `bulk_save`
- `roster_shift_export_daily_pdf` / `export_staff_pdf`
- `shift_location_crud`
- `daily_plan_crud` and `daily_plan_entry_crud`, `prepare_daily_plan`, `download_daily_plan_pdf`
- `roster_copy_bulk`, `copy_roster_day_all`, `copy_week_staff`, `copy_entire_period`

Read / analytics actions (currently A only — no tier gate, anyone with attendance nav can read):
- `roster_analytics_kpis`
- `roster_analytics_department_summary` / `staff_summary`
- `roster_analytics_daily_totals` / `daily_by_department` / `daily_by_staff`
- `roster_analytics_weekly_totals` / `weekly_by_department` / `weekly_by_staff`

Face-management admin actions (currently F only — no tier gate beyond `check_face_attendance_permissions`):
- `face_register_other` (register_face supports `staff_id` in body)
- `face_revoke`
- `face_list`
- `face_audit_logs_read`

---

## 5. RBAC gap table

| Endpoint | Current gate | Missing gate | Required capability (proposed) | Risk |
|---|---|---|---|---|
| `ClockLogViewSet.list/retrieve` | A (nav only) | per-staff scoping for non-managers | `attendance.log.read` (own); `attendance.log.read_all` (manager) | Any staff with nav can list every clock log in the hotel |
| `ClockLogViewSet.face_clock_in` / `current_status` / `register_face` (self) | A (nav only) | self-target enforcement is implicit only | `attendance.clock.self_register` / `attendance.clock.in_out` | A staff with `staff_id` knowledge could be impersonated by a `register_face` payload (the action itself uses `request.user.staff_profile`) — currently OK, but no capability distinction |
| `ClockLogViewSet.unrostered_confirm` | A (nav only) | should require `clock.unrostered` capability or be supervisor-gated | `attendance.clock.unrostered_request` | Self-service unrostered creation; manager approval is a separate endpoint, but creation should still be gated |
| `ClockLogViewSet.stay_clocked_in` / `force_clock_out` | A (nav only) | should be self-only or capability-gated | `attendance.clock.self_acknowledge` | Any staff can call against any pk currently (no ownership check inside actions, only `get_object()` which returns the row by pk in the hotel queryset) |
| `ClockLogViewSet.approve_log` / `reject_log` | A+M (tier super_staff_admin+) | capability check independent of tier | `attendance.log.approve` | Tier-only; no department-scoped variant |
| `ClockLogViewSet.auto_attach_shift` / `relink_day` | A+M | capability | `attendance.log.relink` | Same |
| `ClockLogViewSet.create/update/destroy` | A+M | capability | `attendance.log.create` / `update` / `delete` | Same |
| `RosterPeriodViewSet` (all) incl. finalize/unfinalize | A+M (reads bypass) | reads not differentiated; no finalize-specific capability | `attendance.period.read` / `create` / `update` / `delete` / `finalize` / `unfinalize` / `force_finalize` | Reads of period state currently require only nav (manager actions block writes via tier) |
| `RosterPeriodViewSet.finalize_period` `force=true` | A+M + inline tier check | capability | `attendance.period.force_finalize` | Inline tier check duplicates `CanManageRoster`; no capability slug |
| `StaffRosterViewSet` (all) | A+M (reads bypass) | capability | `attendance.shift.read` / `create` / `update` / `delete` / `bulk_write` / `export_pdf` | Reads on nav alone |
| `StaffRosterViewSet.bulk_save` | A+M | capability + size cap is local | `attendance.shift.bulk_write` | OK behaviorally; gap is only RBAC granularity |
| `ShiftLocationViewSet` | A+M | capability | `attendance.shift_location.read` / `manage` | Same nav-bypass-on-read pattern |
| `DailyPlanViewSet` / `DailyPlanEntryViewSet` | A+M | capability; entry viewset lacks `HotelScopedViewSetMixin` | `attendance.daily_plan.read` / `manage` / `entry.read` / `entry.manage` | Entry viewset enforces hotel only via inline `get_daily_plan` |
| `CopyRosterViewSet` (all 4 actions) | A+M | capability | `attendance.shift.copy` (or split into `copy.bulk` / `copy.day` / `copy.staff` / `copy.period`) | Tier-only |
| `RosterAnalyticsViewSet` (all 9 GETs) | **A only** | tier or capability separating staff-wide hours from self-data | `attendance.analytics.read` (manager) and/or `attendance.analytics.read_self` | **Any staff with attendance nav can read hotel-wide payroll-relevant data** |
| `FaceManagementViewSet.register_face` (other-than-self path via `staff_id`) | F (nav + face-attendance-enabled check) | tier/capability for managing other staff's biometrics | `attendance.face.register_self` vs `attendance.face.register_other` | Any staff with nav can supply `staff_id` to register a colleague's face — relies on serializer-level checks (UNKNOWN whether `FaceRegistrationSerializer` enforces self-only) |
| `FaceManagementViewSet.revoke_face` | F | capability | `attendance.face.revoke` (manager) | No tier gate |
| `FaceManagementViewSet.list_faces` | F | capability | `attendance.face.read` | No tier gate |
| `FaceManagementViewSet.audit_logs` | F | capability | `attendance.face.audit_read` | Audit log readable by anyone with attendance nav |
| `FaceManagementViewSet.face_clock_in` | F | capability for the kiosk action | `attendance.clock.face_in_out` (or kiosk-token auth) | No tier gate |
| FBV `force_clock_in_unrostered` | FBV (auth + inline nav + inline face-perm) | class-level `IsStaffMember`/`IsSameHotel`; capability | `attendance.clock.unrostered_request` | Inconsistent gate shape vs peers |
| FBV `confirm_clock_out_view` | FBV | class-level same-hotel/staff; capability | `attendance.clock.in_out` | Same |
| FBV `toggle_break_view` | FBV | class-level same-hotel/staff; capability | `attendance.break.toggle` | Same |
| `RosterPeriodViewSet.export_pdf` / `finalization_status` / `finalized_rosters_by_department` | A+M (read bypass) | capability for read | `attendance.period.read` | Anyone with nav reads finalized rosters / status |
| `StaffRosterViewSet.daily_pdf` / `staff_pdf` | A+M (read bypass) | capability for read | `attendance.shift.export_pdf` | Anyone with nav can download roster PDFs |

---

## 6. Capability / registry status

Verified by code inspection of [staff/capability_catalog.py](staff/capability_catalog.py) and [staff/module_policy.py](staff/module_policy.py):

- **`CANONICAL_CAPABILITIES`**: NO `attendance.*` capability slugs are defined. `attendance` appears only in a docstring at [capability_catalog.py L356](staff/capability_catalog.py#L356) as a phrase "(by_hotel, attendance-summary)" — not a defined slug.
- **Preset bundles**: NO `_ATTENDANCE_*` or `_ROSTER_*` preset frozensets are defined. The only roster-related cross-reference is `_SUPERVISOR_AUTHORITY` ([L697](staff/capability_catalog.py#L697)) — which contains housekeeping/staff_chat moderation caps, not attendance.
- **`MODULE_POLICY`**: `MODULE_POLICY` ([staff/module_policy.py L162](staff/module_policy.py#L162)) currently registers `bookings`, `chat`, `guests`, `hotel_info`, `rooms`, `staff_chat`, `housekeeping`, `maintenance`, `staff_management`. **`'attendance'` key is NOT present**.
- **Nav slug**: `'attendance'` IS a recognized nav slug in `TIER_DEFAULT_NAVS` ([staff/permissions.py L40-L52](staff/permissions.py#L40-L52)) and is the slug enforced by `HasNavPermission('attendance')` and `HasAttendanceNav` ([staff/permissions.py L428-L429](staff/permissions.py#L428-L429)).
- **Tier gate**: `CanManageRoster` ([staff/permissions.py L333-L344](staff/permissions.py#L333-L344)) is the only non-nav backend gate enforcing attendance writes; it requires tier `super_staff_admin+`.

Conclusion: attendance is **module-visibility-aware** (nav slug present) and **tier-gated for writes**, but **has no capability surface** in the canonical catalog or the normalized `MODULE_POLICY`. It is the next module to be onboarded into the Phase 6 / Wave RBAC shape.

---

## 7. Implementation plan (NO CODE)

**Module name**: `attendance`

### 7.1 Capabilities to create (in `staff/capability_catalog.py`)

Module visibility:
- `attendance.module.view`

Self-service (clock):
- `attendance.clock.self_register` — staff registers own face / status
- `attendance.clock.in_out` — clock in / clock out (rostered)
- `attendance.clock.face_kiosk` — kiosk-mode face clock-in/out (FBV + FaceManagement face_clock_in)
- `attendance.clock.unrostered_request` — `unrostered_confirm`, FBV `force_clock_in_unrostered`
- `attendance.clock.self_acknowledge` — `stay_clocked_in`, `force_clock_out` (long-session ack)
- `attendance.break.toggle` — break start/end

Read:
- `attendance.log.read` — own clock logs
- `attendance.log.read_all` — hotel-wide logs (department-status, currently-clocked-in, list)
- `attendance.period.read`
- `attendance.shift.read`
- `attendance.shift_location.read`
- `attendance.daily_plan.read` (incl. entries)
- `attendance.analytics.read` — RosterAnalytics endpoints

Write / management:
- `attendance.log.create`, `attendance.log.update`, `attendance.log.delete`
- `attendance.log.approve`, `attendance.log.reject`
- `attendance.log.relink` — `auto_attach_shift`, `relink_day`
- `attendance.period.create`, `attendance.period.update`, `attendance.period.delete`
- `attendance.period.finalize`, `attendance.period.unfinalize`
- `attendance.period.force_finalize` — supervises validation override
- `attendance.shift.create`, `attendance.shift.update`, `attendance.shift.delete`, `attendance.shift.bulk_write`
- `attendance.shift.copy` (single capability for the four CopyRoster actions; or split into `.copy_bulk`, `.copy_day`, `.copy_staff`, `.copy_period`)
- `attendance.shift.export_pdf` (daily / staff / period PDFs)
- `attendance.shift_location.manage`
- `attendance.daily_plan.manage`, `attendance.daily_plan.entry.manage`

Face-biometrics admin:
- `attendance.face.read` — `list_faces`, `face_status` (other-than-self)
- `attendance.face.register_other`
- `attendance.face.revoke`
- `attendance.face.audit_read` — `audit_logs`

All MUST be added to `CANONICAL_CAPABILITIES`.

### 7.2 Permission classes needed (in `staff/permissions.py`)

Pattern from prior waves: one class per capability, plus a module-view class:
- `CanViewAttendanceModule` (gates `attendance.module.view`)
- `CanReadAttendanceLog` / `CanReadAllAttendanceLogs`
- `CanClockInOut` / `CanToggleBreak` / `CanRequestUnrosteredClockIn` / `CanAcknowledgeLongSession`
- `CanReadRosterPeriod` / `CanManageRosterPeriod` / `CanFinalizeRosterPeriod` / `CanForceFinalizeRosterPeriod`
- `CanReadStaffRoster` / `CanManageStaffRoster` / `CanBulkWriteStaffRoster` / `CanExportRosterPdf`
- `CanCopyRoster`
- `CanReadShiftLocation` / `CanManageShiftLocation`
- `CanReadDailyPlan` / `CanManageDailyPlan` / `CanManageDailyPlanEntry`
- `CanReadAttendanceAnalytics`
- `CanReadStaffFace` / `CanRegisterOtherFace` / `CanRevokeStaffFace` / `CanReadFaceAuditLog`

Per repo convention, write classes should set `safe_methods_bypass=False` so reads do not silently pass. Read classes are independent.

### 7.3 Endpoints to update

For each endpoint listed in §2, replace the current `[IsAuthenticated, HasNavPermission('attendance'), IsStaffMember, IsSameHotel, (CanManageRoster?)]` chain with:
```
[IsAuthenticated, IsStaffMember, IsSameHotel, CanViewAttendanceModule, <PerActionCapability>]
```
Drop `HasNavPermission('attendance')` (replaced by `CanViewAttendanceModule`). Drop `CanManageRoster` (replaced by capability classes per action).

The three FBVs in `face_views.py` should be **converted into ViewSet actions or DRF class-based views** to use `permission_classes` consistently; or, if kept as FBVs, must use `@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel, CanViewAttendanceModule, <PerActionCapability>])`.

`DailyPlanEntryViewSet` should adopt `HotelScopedViewSetMixin` to align with peers (currently relies on inline `get_daily_plan` only).

`ShiftLocationViewSet` is registered both via the router AND via explicit `path()` bindings — confirm whether one set should be removed (UNKNOWN whether intentional). RBAC implementation must apply to both surfaces.

### 7.4 Ownership rules

- `ClockLogViewSet.register_face` (no `staff_id` body) → uses `request.user.staff_profile`. Capability `attendance.clock.self_register` is sufficient.
- `FaceManagementViewSet.register_face` (accepts `staff_id`) → if `staff_id` differs from requester's `staff_profile.id`, require `attendance.face.register_other`; else `attendance.clock.self_register`.
- `ClockLogViewSet.stay_clocked_in` / `force_clock_out` → currently no ownership check. Implementation must require `log.staff_id == request.user.staff_profile.id` OR capability `attendance.log.update`.
- `ClockLogViewSet.unrostered_confirm` → action accepts `staff_id`; require `staff_id == request.user.staff_profile.id` OR capability `attendance.log.create`.
- `RosterAnalyticsViewSet` → no per-staff filtering; new capability `attendance.analytics.read` should be the gate (manager-tier preset only).
- `DailyPlanEntryViewSet` → already enforces hotel via `get_daily_plan`; add capability gate, keep inline ownership.

### 7.5 Validation steps

After implementation, the following must succeed/produce empty lists:
1. `CANONICAL_CAPABILITIES` contains every new `attendance.*` slug.
2. `MODULE_POLICY['attendance']` defined with `visible`, `read`, `actions` keys; every referenced slug is in `CANONICAL_CAPABILITIES`.
3. At least one role/department/tier preset bundle in `capability_catalog.py` grants the new self-service caps to `regular_staff` (clock/break/self-register), and the management caps to `super_staff_admin+` (or appropriate role preset).
4. No view in `attendance/` references `HasNavPermission('attendance')`, `CanManageRoster`, `_tier_at_least`, or `resolve_tier` after the migration (only the new capability classes).

---

## 8. Validation commands

```bash
python manage.py check
python -c "from staff.module_policy import validate_module_policy; print(validate_module_policy())"
python -c "from staff.capability_catalog import validate_preset_maps; print(validate_preset_maps())"
```

Expected post-implementation: `check` clean, both `validate_*()` return `[]`.

Pre-implementation (current state) expected: `check` clean (attendance not yet onboarded); both validators return `[]` because they currently do not reference `attendance` at all.

---

## Notes / UNKNOWNs

- `DailyPlanViewSet.download_pdf` action body was not located in the inspected ranges of [attendance/views.py](attendance/views.py); URL is mounted at [urls.py L84](attendance/urls.py#L84). Permission class derives from `DailyPlanViewSet.get_permissions` (A+M).
- `CopyRosterViewSet.copy_entire_period` body was not fully read; permission class confirmed via class-level `get_permissions`.
- Whether `FaceRegistrationSerializer` enforces `staff_id == request.user.staff_profile.id` on the self path is **UNKNOWN** (serializers.py not opened beyond the legacy-pattern scan).
- The router `clock-logs` registration and the `clock-logs/register-face/` route mean the same logic exists on both `ClockLogViewSet` AND `FaceManagementViewSet` (different gates). Audit accounts for both; consolidation is out of audit scope.
- `'attendance'` is in `regular_staff` defaults: **NO** ([staff/permissions.py L57-L59](staff/permissions.py#L57-L59) shows `regular_staff = {'home', 'chat'}`). Therefore current behavior: regular staff cannot reach attendance endpoints at all unless given the nav explicitly via per-staff overrides. RBAC implementation must decide whether basic clock-in is granted to regular staff via preset or remains opt-in via `allowed_navs`.
