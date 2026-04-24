# Hotel Creation & Staff Creation: Full Backend Analysis

## 1. Hotel Creation (Provisioning)

### The Model

**`Hotel`** in `hotel/models.py` (line 85) is the core tenant entity.

**Required fields** (enforced at DB level):
- `name` (CharField, max 255)
- `slug` (SlugField, unique) — auto-generated from `name` in `save()` if omitted

**Optional fields:**
- `subdomain` (SlugField, unique, nullable)
- `logo`, `hero_image`, `landing_page_image` (Cloudinary)
- `is_active` (default `True`), `sort_order` (default `0`)
- `city`, `country`, `address_line_1`, `address_line_2`, `postal_code`
- `latitude`, `longitude`
- `phone`, `email`, `website_url`, `booking_url`
- `short_description`, `tagline`, `long_description`
- `hotel_type` (20-choice enum, blank allowed)
- `tags` (JSONField, default `list`)
- `default_cancellation_policy` (FK, nullable)
- `timezone` (default `'Europe/Dublin'`)

### Endpoints That Create Hotels

| # | Endpoint | Permission | Location |
|---|----------|------------|----------|
| 1 | **`POST /api/hotels/`** | `IsSuperUser` (Django `is_superuser`) | `hotel/base_views.py` — `HotelViewSet.create()` |
| 2 | **Django Admin** | Django admin superuser | `hotel/admin.py` — `HotelAdmin` |
| 3 | **`manage.py seed_hotels`** | Shell access | Management command |

There is **no public or staff-facing endpoint** to create hotels. Only Django superusers can do it.

### What Happens Automatically on Hotel Creation

Three `post_save` signals fire from `hotel/signals.py`:

**Signal 1: `create_hotel_access_config`** (line 11) — fires only on `created=True`:
- Creates `HotelAccessConfig`

**Signal 2: `save_hotel_access_config`** (line 20) — fires on every save:
- Backfills `HotelAccessConfig` if missing (idempotent safety net)

**Signal 3: `create_hotel_related_objects`** (line 30) — fires on every save:
Creates (if not exists) **7 related OneToOne objects**:

| Object | Purpose | Defaults |
|--------|---------|----------|
| `HotelAccessConfig` | Portal toggles, PIN rules, multi-device limits, approval SLA | guest/staff portals enabled, PIN required (4 digits), max 5 devices |
| `HotelPublicPage` | Public page container | Empty shell |
| `BookingOptions` | CTA labels/URLs | Empty |
| `AttendanceSettings` | Staff attendance policies | Default thresholds |
| `ThemePreference` (from `common.models`) | Hotel theme/styling | Empty |
| `HotelPrecheckinConfig` | Guest pre-checkin field config | 11 fields enabled, nationality + ID# required |
| `HotelSurveyConfig` | Post-checkout survey config | AUTO_DELAYED (24h), 7-day token expiry |

**Important:** Signal 1 and Signal 3 *both* create `HotelAccessConfig` — this is a redundancy. Signal 1 fires first (`created=True`), then Signal 3 checks `hasattr`. On initial creation, the config gets created by Signal 1 and Signal 3 skips it. This works but is messy.

### What Is NOT Created Automatically
- **No rooms or room types** — manual
- **No navigation items** — must be created by Django superuser via NavItem API or admin
- **No staff/admin** — completely separate flow
- **No public page sections** — empty container; must be bootstrapped via `POST /api/staff/hotels/{slug}/hotel/public-page-builder/bootstrap-default/`

---

## 2. Initial Admin / Owner Setup

### There Is No Automatic Admin Creation

When a hotel is created, **no admin user or staff member is created**. The hotel exists as an orphan until someone manually:

1. Creates a Django `User` (via admin or `createsuperuser`)
2. Creates a `Staff` record linking that user to the hotel with `access_level='super_staff_admin'`

### How the First Admin Gets Linked

There is **no provisioning service** or bootstrap command for this. The first admin must be created via:

- **Django Admin UI:** Create `Staff` record manually
- **Django shell:** `Staff.objects.create(user=user, hotel=hotel, access_level='super_staff_admin')`
- **`StaffViewSet.create()` API:** But this requires `IsSuperUser` — which means a Django superuser must already exist

### What Defines an Admin

| Flag | Meaning | Set By |
|------|---------|--------|
| `Staff.access_level = 'super_staff_admin'` | App-level full admin for one hotel | API or admin |
| `Staff.access_level = 'staff_admin'` | Mid-level admin, can create reg codes | API or admin |
| `User.is_superuser = True` | Django superuser — platform-wide | Only Django admin/CLI |
| `User.is_staff = True` | Django admin access flag | Set `True` on all staff creation |

**Critical distinction:** `super_staff_admin` ≠ `is_superuser`. The API **explicitly forces** `is_superuser = False` on all staff creates (`staff/views.py` lines 338-342 and 1073-1078). Django superusers are platform operators, not hotel admins.

---

## 3. Staff Registration Flow

### The Full Lifecycle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 1: Registration Package (Admin action)                    │
│  POST /api/staff/registration-package/                           │
│  → Creates RegistrationCode + QR token + QR image (Cloudinary)   │
│  Permission: staff_admin or super_staff_admin of the hotel       │
└──────────────────────────────────────────┬───────────────────────┘
                                           │
┌──────────────────────────────────────────▼───────────────────────┐
│  PHASE 2: Employee Self-Registration                             │
│  POST /api/staff/register/                                       │
│  Input: username, password, registration_code, qr_token(opt)     │
│  → Creates: User + UserProfile (linked to RegistrationCode)      │
│  → Marks code as used (used_by=user)                             │
│  → Returns token + "pending" message                             │
│  → Pusher event: 'pending' registration                          │
│  ⚠ NO Staff record created yet                                   │
│  Permission: AllowAny                                            │
└──────────────────────────────────────────┬───────────────────────┘
                                           │
┌──────────────────────────────────────────▼───────────────────────┐
│  PHASE 3: Manager Reviews Pending                                │
│  GET /api/staff/{hotel_slug}/pending-registrations/              │
│  → Returns users who have RegistrationCode.used_by set           │
│    but NO staff_profile (User → Staff OneToOne missing)          │
│  Permission: any staff member of that hotel                      │
└──────────────────────────────────────────┬───────────────────────┘
                                           │
┌──────────────────────────────────────────▼───────────────────────┐
│  PHASE 4: Manager Creates Staff Profile                          │
│  POST /api/staff/{hotel_slug}/create-staff/                      │
│  Input: user_id, first_name, last_name, email, department_id,    │
│         role_id, access_level (default: regular_staff)           │
│  → Creates Staff record                                          │
│  → Sets User.is_staff=True, User.is_superuser=False              │
│  → DELETES the RegistrationCode                                  │
│  → Pusher events: 'created' + 'approved'                         │
│  Permission: any staff member of that hotel (⚠ NO access_level   │
│  check — see Risks)                                              │
└──────────────────────────────────────────────────────────────────┘
```

### Models Involved

| Model | Location | Purpose |
|-------|----------|---------|
| `RegistrationCode` | `staff/models.py` line 241 | One-time invite code with QR token, linked to hotel_slug |
| `UserProfile` | `staff/models.py` line 315 | Bridges User ↔ RegistrationCode during pending state |
| `User` | Django built-in (NOT customized) | Authentication entity |
| `Staff` | `staff/models.py` line 92 | The real staff record, linked to User + Hotel |
| `NavigationItem` | `staff/models.py` line 10 | Per-hotel nav links, M2M on Staff |
| `Department` | `staff/models.py` line 56 | Global department catalog |
| `Role` | `staff/models.py` line 67 | Global role catalog (optionally linked to Department) |

---

## 4. Staff Approval / Activation

### Pending State

The "pending" state is **implicit**, not a field. A user is pending when:
- `RegistrationCode.used_by` is set (user registered)
- `User` has no `staff_profile` reverse relation (Staff not yet created)

`PendingRegistrationsAPIView` (`staff/views.py` lines 962-994) queries this by iterating used registration codes and checking `hasattr(user, 'staff_profile')`.

### Approval Process

`CreateStaffFromUserAPIView` (`staff/views.py` lines 1003-1119) converts pending user → full staff member. When this runs:

1. `Staff.objects.create(...)` — user gains staff profile
2. `User.is_staff = True` — Django admin flag set
3. `User.is_superuser = False` — explicitly locked
4. `RegistrationCode.delete()` — code consumed
5. Pusher events fire for real-time UI updates

### When Does Staff Gain Access?

**Immediately** after `CreateStaffFromUserAPIView` completes. There is no secondary activation step. Once the `Staff` record exists, `CustomAuthToken` (login) will succeed.

However, the staff member starts with **no navigation items** assigned (`allowed_navigation_items` M2M is empty). A `super_staff_admin` must assign permissions via `PATCH /api/staff/{staff_id}/permissions/`.

---

## 5. Roles and Permissions

### Permission Architecture

```
┌─────────────────────────────────────────────┐
│              LAYER 1: Django Auth            │
│  User.is_superuser  →  Platform operator    │
│  User.is_staff      →  Always True for staff│
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         LAYER 2: App Access Levels          │
│  Staff.access_level:                        │
│    'super_staff_admin' → Full hotel admin   │
│    'staff_admin'       → Mid-level admin    │
│    'regular_staff'     → Basic access       │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│    LAYER 3: Navigation-Based Permissions    │
│  Staff.allowed_navigation_items (M2M)       │
│  → Controls which frontend routes visible   │
│  → HasNavPermission class checks slugs      │
│  → Superusers bypass (get ALL nav items)    │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│       LAYER 4: Hotel Scoping Mixins         │
│  HotelScopedViewSetMixin                    │
│  HotelScopedQuerysetMixin                   │
│  → Enforces URL hotel_slug == staff.hotel   │
│  → Filters querysets to staff's hotel       │
└─────────────────────────────────────────────┘
```

### Permission Classes In Use

| Class | File | Purpose |
|-------|------|---------|
| `IsSuperUser` | `staff/permissions_superuser.py` | `user.is_superuser` check |
| `IsSuperUser` (hotel copy) | `hotel/base_views.py` line 20 | Duplicate of above |
| `IsHotelStaff` | `hotel/permissions.py` line 8 | Staff belongs to URL hotel |
| `IsSuperStaffAdminForHotel` | `hotel/permissions.py` line 35 | `super_staff_admin` + same hotel |
| `HasNavPermission` | `staff/permissions.py` line 81 | Checks specific nav slug assignment |
| `IsStaffMember` / `IsSameHotel` | `staff_chat/permissions.py` | Used by `HotelScopedViewSetMixin` |
| `HotelScopedQuerysetMixin` | `common/mixins.py` line 12 | Derives hotel from `staff_profile`, not URL |
| `HotelScopedViewSetMixin` | `common/mixins.py` line 47 | URL-based hotel scoping + validation |

### The Canonical Permissions Resolver

`resolve_staff_navigation()` in `staff/permissions.py` line 19 is the **single source of truth** for staff permissions. Called during login and permission checks, it returns:

```python
{
    'is_staff': bool,
    'is_superuser': bool,
    'hotel_slug': str | None,
    'access_level': str | None,
    'allowed_navs': ['home', 'chat', ...],  # slug list
    'navigation_items': [{ full nav objects }]
}
```

Superusers get ALL active nav items for their hotel. Regular staff get only their M2M-assigned items.

---

## 6. Dependency Chain

```
PLATFORM SUPERUSER (Django admin/CLI)
    │
    ├── Creates Hotel ──────────────────────► post_save signals
    │      │                                     └── 7 config objects
    │      │
    │      ├── Creates NavigationItems for hotel (via API or admin)
    │      │
    │      └── Creates first Staff(super_staff_admin) ◄── manual step, no automation
    │              │
    │              ├── Generates RegistrationPackage (code + QR)
    │              │      │
    │              │      └── Employee self-registers (User + UserProfile)
    │              │             │
    │              │             └── Any staff member creates Staff profile
    │              │                    │
    │              │                    └── super_staff_admin assigns nav permissions
    │              │
    │              └── Can also directly create staff via StaffViewSet
    │
    └── Creates Departments + Roles (global, not per-hotel)
```

**What must exist before each step:**

| Step | Prerequisites |
|------|--------------|
| Hotel | Django superuser |
| NavigationItems | Hotel + Django superuser |
| First super_staff_admin | Hotel + User + manual Staff creation |
| RegistrationCode | Hotel + staff_admin/super_staff_admin |
| Employee self-registration | RegistrationCode |
| Staff profile creation | Pending user + any staff member of hotel |
| Nav permissions assignment | Staff record + super_staff_admin or superuser |

---

## 7. Risks / Gaps

### CRITICAL

**1. Broken Signal: `create_staff_from_registration_code`**
- `staff/signals.py` lines 15-24 tries `Staff.objects.get_or_create(user=instance, hotel_slug=reg_code.hotel_slug)`
- **`Staff` has no `hotel_slug` field** — it has `hotel` (FK). This signal raises a `FieldError` silently (wrapped in try/except).
- Impact: Dead code. Does nothing. Staff creation relies entirely on the manual view flow.

**2. No Access Level Check on `CreateStaffFromUserAPIView`**
- `staff/views.py` lines 1012-1018: Any staff member of the hotel can create other staff profiles. A `regular_staff` can promote someone to `super_staff_admin`.
- The `StaffViewSet.create()` endpoint correctly blocks this (checks `requesting_staff.access_level`), but `CreateStaffFromUserAPIView` does not.

**3. No Escalation Guard on `CreateStaffFromUserAPIView`**
- A `staff_admin` can set `access_level='super_staff_admin'` on the new staff they create. Only `StaffViewSet.create()` has the guard that only `super_staff_admin` can create other `super_staff_admin`.

### HIGH

**4. Duplicate `IsSuperUser` Permission Classes**
- One in `staff/permissions_superuser.py`, another in `hotel/base_views.py` line 20. They behave identically but are separate classes.

**5. `Department` and `Role` Are Global, Not Per-Hotel**
- `Department` and `Role` have no `hotel` FK. They're shared across all hotels.
- The queryset filtering in `DepartmentViewSet` / `RoleViewSet` scopes by usage (departments that have staff in the hotel), but any department name collision affects all hotels.
- A superuser creating "Front Desk" creates it for all hotels.

**6. `RegistrationCode.hotel_slug` Is a String, Not FK**
- The `RegistrationCode` stores `hotel_slug` as a plain `SlugField`, not a ForeignKey to Hotel. If a hotel slug changes, orphaned codes break. No referential integrity.

**7. `PendingRegistrationsAPIView` Has No Access Level Check**
- Any staff member can view pending registrations. This leaks registration activity to all staff.

### MEDIUM

**8. `StaffViewSet` Uses `IsSuperUser` For All Actions**
- The `permission_classes = [IsSuperUser]` on `StaffViewSet` means list/retrieve also require superuser. But `StaffViewSet.create()` then does its own staff-of-hotel check internally, which is redundant since `IsSuperUser` already passed.

**9. `NavigationItem` Write Operations Are Not Properly Guarded**
- `NavigationItemViewSet` checks superuser in `perform_create`/`perform_update`/`perform_destroy` rather than in `get_permissions()`. The `permission_classes` is just `IsAuthenticated`, so non-superusers can make GET requests to see all nav items across all hotels (no hotel scoping on list).

**10. No Bootstrap for Navigation Items**
- Hotels are created with zero `NavigationItem` records. There's no "default set" seeded. Every hotel needs manual nav item creation by a Django superuser. Without this, staff get zero allowed navigation even after permissions are assigned.

**11. Multi-Hotel Staff Warning Is Dead Code**
- `Staff.user` is `OneToOneField` — a User can only have one Staff record. But the login flow does `Staff.objects.filter(user=user).count()` and logs a warning if >1. This is impossible with OneToOne at DB level, so the warning is dead code.

**12. `UserProfile` Is Orphaned After Staff Creation**
- The `UserProfile` created during registration is never deleted or updated after the `Staff` record is created. It persists as dead data with a reference to a deleted `RegistrationCode`.

**13. `random.choices` for Registration Code Generation**
- `staff/views.py` lines 745-750 uses `random.choices()` (not cryptographically secure) for code generation, while `qr_token` correctly uses `secrets.token_urlsafe()`. Minor but inconsistent.
