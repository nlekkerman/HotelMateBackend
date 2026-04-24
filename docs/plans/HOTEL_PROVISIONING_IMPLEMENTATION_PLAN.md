# Hotel Provisioning — Backend Implementation Plan

## 1. Recommended Architecture

### Decision: Dedicated provisioning endpoint + service, NOT extending existing HotelViewSet

**Why:**

1. The existing `HotelViewSet` (`hotel/base_views.py`) is a standard `ModelViewSet` backed by `HotelSerializer`. It creates a Hotel and relies on `post_save` signals to build config objects. It knows nothing about users or staff. Bolting user/staff creation onto its `create()` method would violate its single responsibility.

2. A provisioning endpoint is a **composite operation** — it creates entities across three models (`Hotel`, `User`, `Staff`) in two apps (`hotel`, `staff`). This belongs in a dedicated service function, not in a model serializer.

3. The existing `HotelViewSet` should remain for CRUD on the Hotel model itself (name changes, logo upload, etc.). The provisioning endpoint is a one-time lifecycle operation.

4. A dedicated `/api/hotels/provision/` endpoint gives a clean contract boundary and makes it impossible to accidentally create an orphan hotel through the old `POST /api/hotels/` path.

### Architecture

```
hotel/provisioning.py          ← new service module (pure logic, no HTTP)
hotel/provisioning_views.py    ← new view (thin HTTP layer)
hotel/provisioning_serializers.py  ← request/response serializers
hotel/urls.py                  ← new route wired in
```

The existing `HotelViewSet.create()` will be **disabled** (return 405) so all hotel creation goes through the provisioning endpoint. The rest of HotelViewSet (list, retrieve, update, delete) stays unchanged.

---

## 2. Proposed Request Contract

```
POST /api/hotels/provision/
Authorization: Token <superuser-token>
Content-Type: application/json
```

```json
{
  "hotel": {
    "name": "The Grand Dublin",
    "slug": "the-grand-dublin",
    "subdomain": "grand-dublin",
    "city": "Dublin",
    "country": "Ireland",
    "timezone": "Europe/Dublin",
    "email": "info@granddublin.com",
    "phone": "+353 1 234 5678"
  },
  "primary_admin": {
    "first_name": "Jane",
    "last_name": "O'Brien",
    "email": "jane.obrien@granddublin.com"
  },
  "registration_packages": {
    "generate_count": 3
  }
}
```

### Field rules

| Section | Field | Required | Notes |
|---------|-------|----------|-------|
| `hotel.name` | Yes | — |
| `hotel.slug` | No | Auto-generated from `name` if omitted (existing `Hotel.save()` logic) |
| `hotel.subdomain` | No | Nullable in model, but the current `HotelSerializer` marks it required. Provisioning will make it optional to match the model. |
| `hotel.*` | No | All other Hotel fields are optional per the model |
| `primary_admin.first_name` | Yes | Real person name, not placeholder |
| `primary_admin.last_name` | Yes | Real person name, not placeholder |
| `primary_admin.email` | Yes | Must be globally unique across `User.email` and `Staff.email`. Used as username basis. |
| `registration_packages` | No | Entire section optional |
| `registration_packages.generate_count` | No | Default 0, max 10. Number of blank registration codes to pre-generate |

---

## 3. Proposed Response Contract

### Success (201 Created)

```json
{
  "hotel": {
    "id": 42,
    "name": "The Grand Dublin",
    "slug": "the-grand-dublin",
    "subdomain": "grand-dublin"
  },
  "primary_admin": {
    "user_id": 101,
    "username": "jane.obrien-grand-dublin",
    "email": "jane.obrien@granddublin.com",
    "staff_id": 55,
    "access_level": "super_staff_admin",
    "password_setup": "email_sent"
  },
  "config_objects_created": [
    "HotelAccessConfig",
    "HotelPublicPage",
    "BookingOptions",
    "AttendanceSettings",
    "ThemePreference",
    "HotelPrecheckinConfig",
    "HotelSurveyConfig"
  ],
  "registration_packages": [
    {
      "code": "ABCD1234",
      "qr_token": "abc123...",
      "qr_code_url": "https://res.cloudinary.com/..."
    }
  ],
  "warnings": []
}
```

### Partial success example (QR upload failed)

```json
{
  "hotel": { "..." },
  "primary_admin": { "..." },
  "config_objects_created": [ "..." ],
  "registration_packages": [],
  "warnings": [
    "Registration package generation failed: Cloudinary upload error. Hotel and admin were created successfully. Generate packages manually later."
  ]
}
```

### Failure (400/409)

```json
{
  "errors": {
    "hotel": { "slug": ["Hotel with this slug already exists."] },
    "primary_admin": { "email": ["A user with this email already exists."] }
  }
}
```

---

## 4. Execution Sequence

### Phase A — Validation (before any DB writes)

```
1. Validate hotel data
   - name is non-empty
   - slug is unique (or auto-generate and check)
   - subdomain is unique if provided
   
2. Validate primary_admin data
   - first_name and last_name are non-empty
   - email is valid format
   - email does not exist in User.email
   - email does not exist in Staff.email
   
3. Validate registration_packages
   - generate_count is 0..10
```

If any validation fails, return 400 immediately. No DB writes occur.

### Phase B — Atomic transaction (all-or-nothing)

Everything in this phase is wrapped in `django.db.transaction.atomic()`:

```
4. Create Hotel
   - Hotel.objects.create(**hotel_data)
   - post_save signals fire → 7 config objects created
   - Collect created config object names for response

5. Create User for primary admin
   - username = derive_username(email, hotel_slug) 
   - User.objects.create_user(username=username, email=email)
   - user.set_unusable_password()   ← password set via email later
   - user.is_staff = True
   - user.is_superuser = False
   - user.first_name = first_name
   - user.last_name = last_name
   - user.save()
   - (post_save signal creates auth Token automatically)

6. Create Staff profile
   - Staff.objects.create(
       user=user,
       hotel=hotel,
       first_name=first_name,
       last_name=last_name,
       email=email,
       access_level='super_staff_admin',
       is_active=True,
     )
```

If anything in Phase B fails, the entire transaction rolls back. No orphan hotel, no orphan user.

### Phase C — Post-transaction work (non-critical, individually guarded)

```
7. Send password setup email to primary admin
   - Generate password reset token (using Django's default_token_generator)
   - Build setup URL: {frontend_base}/setup-password/{uid}/{token}/
   - Send email via existing send_mail infrastructure
   - If email fails: add warning, do NOT roll back

8. Generate registration packages (if requested)
   - For each requested package:
     - Generate code using secrets.token_hex(4).upper() (8 chars, cryptographically secure)
     - Create RegistrationCode with hotel_slug
     - Generate QR token via secrets.token_urlsafe(32)
     - Generate QR code image and upload to Cloudinary
   - If any package fails: add warning, continue with remaining
   
9. Return response
```

### Summary: Transaction boundary

| Step | In atomic transaction? | Failure behavior |
|------|----------------------|------------------|
| Hotel creation | Yes | Rolls back everything |
| Config objects (signals) | Yes (signals fire inside save) | Rolls back everything |
| User creation | Yes | Rolls back everything |
| Staff creation | Yes | Rolls back everything |
| Password setup email | No | Warning in response |
| Registration packages | No | Warning in response |

---

## 5. Validation Rules

### Hotel slug uniqueness
- If `slug` is provided: validate unique against `Hotel.objects.filter(slug=slug).exists()`
- If `slug` is omitted: auto-generate from `name` using `django.utils.text.slugify()`. If generated slug collides, append a short random suffix (e.g. `the-grand-dublin-a3f2`). Do NOT silently overwrite.

### Subdomain uniqueness
- If `subdomain` is provided: validate unique against `Hotel.objects.filter(subdomain=subdomain).exists()`
- If `subdomain` is omitted: leave as `None` (nullable in model)

### Primary admin email uniqueness
- Check `User.objects.filter(email=email).exists()` — must be globally unique
- Check `Staff.objects.filter(email=email).exists()` — must not collide with existing staff
- If the email already exists on a User: reject with 409 and message `"A user with this email already exists. If this person should admin this hotel, link them manually via Django admin."`
- Rationale: Automatic linking of existing users is a security risk (privilege escalation). Keep it manual for the edge case.

### first_name / last_name 
- Both required, non-empty, stripped of whitespace
- Max 100 chars each (matches Staff model)

### Username derivation
- Strategy: `{email_local_part}-{hotel_slug}` lowercased, truncated to 150 chars (Django's max)
- Example: `jane.obrien@granddublin.com` + slug `the-grand-dublin` → `jane.obrien-the-grand-dublin`
- If collision: append `-2`, `-3`, etc.
- Username is an internal artifact, not shown to admin. Login should use email.

### Password setup strategy
- **Do NOT generate a temporary password.** Temporary passwords get shared, reused, or forgotten.
- **Do NOT set a random password.** The admin can't log in without it.
- **Do:** Set `user.set_unusable_password()` at creation time, then immediately send a password-setup email using Django's `default_token_generator` (same mechanism as existing `PasswordResetRequestView`).
- The email should use a "Set Up Your Account" template, not "Reset Your Password" — but the underlying mechanism is identical.
- Frontend needs a `/setup-password/{uid}/{token}/` route that hits the existing `PasswordResetConfirmView`. No backend change needed for the confirm step — the POST contract is the same.

---

## 6. Model / Service / View Changes

### New files

#### `hotel/provisioning.py` — Provisioning service

```
Purpose: Pure business logic, no HTTP dependencies
Contains:
  - provision_hotel(hotel_data, admin_data, reg_package_count, frontend_base_url) -> ProvisioningResult
  - _create_hotel_atomic(hotel_data, admin_data) -> (Hotel, User, Staff)
  - _derive_username(email, hotel_slug) -> str
  - _send_admin_setup_email(user, hotel, frontend_base_url) -> bool
  - _generate_registration_packages(hotel_slug, count) -> list[dict]

Transaction boundary lives here.
All validation happens at serializer level before this is called.
```

Why a service not a fat view: The provisioning logic can be reused from management commands, tests, or future API versions without duplicating code.

#### `hotel/provisioning_serializers.py` — Request/response serializers

```
Purpose: Validate and shape HTTP payloads
Contains:
  - HotelProvisioningRequestSerializer
    - hotel (nested): name, slug, subdomain, city, country, etc.
    - primary_admin (nested): first_name, last_name, email
    - registration_packages (nested, optional): generate_count
    - Custom validate() for cross-field uniqueness checks
  - HotelProvisioningResponseSerializer
    - hotel summary
    - primary_admin summary
    - config_objects_created list
    - registration_packages list
    - warnings list
```

#### `hotel/provisioning_views.py` — Provisioning endpoint

```
Purpose: Thin HTTP layer
Contains:
  - HotelProvisioningView(APIView)
    - permission_classes = [IsSuperUser]  (from staff/permissions_superuser.py)
    - POST: deserialize → call provisioning service → serialize response
```

### Modified files

#### `hotel/urls.py`

```
Change: Add route for provisioning endpoint
Add:
  path("provision/", HotelProvisioningView.as_view(), name="hotel-provision"),
Wire it BEFORE the router.urls catch-all.
```

#### `hotel/base_views.py` — `HotelViewSet`

```
Change: Disable create() to force all creation through provisioning
Add:
  def create(self, request, *args, **kwargs):
      return Response(
          {"detail": "Hotel creation is only available through /api/hotels/provision/"},
          status=status.HTTP_405_METHOD_NOT_ALLOWED
      )
```

#### `staff/views.py` — `CreateStaffFromUserAPIView`

```
Change: Add access level enforcement (security fix)
Current: Any staff member of the hotel can create staff profiles with any access_level
Fix: 
  - Only staff_admin and super_staff_admin can call this endpoint
  - Only super_staff_admin can set access_level='super_staff_admin'
  - Only super_staff_admin can set access_level='staff_admin'
  - staff_admin can only create regular_staff
```

#### `staff/views.py` — `PendingRegistrationsAPIView`

```
Change: Add access level enforcement (security fix)
Current: Any staff member can view pending registrations
Fix: Require staff_admin or super_staff_admin access_level
```

#### `staff/signals.py` — `create_staff_from_registration_code`

```
Change: Remove broken signal entirely
Current: References non-existent Staff.hotel_slug field, silently fails
Fix: Delete the entire signal function and its @receiver decorator
Why: Dead code that masks bugs. Staff creation from registration codes is handled in views.
```

#### `hotel/signals.py` — `create_hotel_access_config` (first signal)

```
Change: Remove redundant signal
Current: Signal 1 creates HotelAccessConfig on created=True. Signal 3 also creates it via hasattr check.
Fix: Remove signal 1 (create_hotel_access_config) and signal 2 (save_hotel_access_config). 
     Signal 3 (create_hotel_related_objects) already handles all OneToOne creation idempotently.
Why: Three signals doing overlapping work is fragile. One idempotent signal is correct.
```

#### `staff/views.py` — `GenerateRegistrationPackageAPIView`

```
Change: Replace random.choices with secrets for code generation
Current: Uses random.choices (not cryptographically secure)
Fix: Use secrets.token_hex(4).upper() for 8-char code, matching qr_token's security level
```

### Files NOT changed

- `staff/models.py` — Staff model is adequate as-is. `OneToOneField(User)` is correct for this flow.
- `hotel/models.py` — Hotel model is adequate. No new fields needed.
- `common/mixins.py` — Hotel scoping mixins are unrelated to provisioning.
- `staff/permissions.py` — `resolve_staff_navigation` is unrelated.

---

## 7. Security Rules

### Permission matrix

| Action | Django superuser | super_staff_admin | staff_admin | regular_staff |
|--------|:---:|:---:|:---:|:---:|
| Create hotel (provision) | ✅ | ❌ | ❌ | ❌ |
| Provision first hotel admin | ✅ (part of provisioning) | ❌ | ❌ | ❌ |
| Generate registration packages | ✅ | ✅ (own hotel) | ✅ (own hotel) | ❌ |
| View pending registrations | ✅ | ✅ (own hotel) | ✅ (own hotel) | ❌ |
| Create staff from pending user | ✅ | ✅ (own hotel) | ✅ (own hotel, regular_staff only) | ❌ |
| Assign access_level=regular_staff | ✅ | ✅ | ✅ | ❌ |
| Assign access_level=staff_admin | ✅ | ✅ | ❌ | ❌ |
| Assign access_level=super_staff_admin | ✅ | ✅ | ❌ | ❌ |
| Create NavigationItems | ✅ | ❌ | ❌ | ❌ |
| Assign nav permissions to staff | ✅ | ✅ (own hotel) | ❌ | ❌ |

### Key rules

1. **`is_superuser` is never set via API.** The provisioning service creates users with `is_superuser=False`. Platform superusers are created via CLI only.

2. **Privilege escalation is blocked.** `staff_admin` cannot create `staff_admin` or `super_staff_admin`. Only `super_staff_admin` can assign elevated access levels.

3. **Hotel scoping is mandatory.** Every staff action that involves another staff member must verify both the requester and target belong to the same hotel.

4. **`regular_staff` has no administrative capabilities.** Cannot generate codes, view pending registrations, or create staff profiles.

---

## 8. Existing Weak Points To Fix Immediately

These fixes should be merged **before** the provisioning endpoint is built, in priority order:

### Fix 1 (CRITICAL): Access level enforcement on `CreateStaffFromUserAPIView`

**File:** `staff/views.py`, `CreateStaffFromUserAPIView.post()`  
**Current behavior:** Any staff member of the hotel can create staff profiles and assign any access_level including `super_staff_admin`.  
**Fix:**
```python
# After verifying requesting_staff exists and belongs to hotel:

# Only staff_admin and super_staff_admin can create staff
if requesting_staff.access_level == 'regular_staff':
    return Response(
        {'error': 'You do not have permission to create staff profiles.'},
        status=403
    )

# Escalation guard: only super_staff_admin can assign elevated roles
if access_level in ('staff_admin', 'super_staff_admin') and requesting_staff.access_level != 'super_staff_admin':
    return Response(
        {'error': 'Only super_staff_admin can assign staff_admin or super_staff_admin access levels.'},
        status=403
    )
```

### Fix 2 (CRITICAL): Access level enforcement on `PendingRegistrationsAPIView`

**File:** `staff/views.py`, `PendingRegistrationsAPIView.get()`  
**Current behavior:** Any staff member can view pending registrations.  
**Fix:** Add check that `requesting_staff.access_level in ('staff_admin', 'super_staff_admin')`.

### Fix 3 (HIGH): Remove broken signal

**File:** `staff/signals.py`  
**Remove:** `create_staff_from_registration_code` function and its `@receiver` decorator.  
**Why:** It references `Staff.hotel_slug` which doesn't exist. It silently fails on every user creation. Dead code that pollutes the signal chain.

### Fix 4 (HIGH): Consolidate redundant hotel signals

**File:** `hotel/signals.py`  
**Remove:** `create_hotel_access_config` and `save_hotel_access_config`.  
**Keep:** `create_hotel_related_objects` (which already handles HotelAccessConfig creation via `hasattr` check).  
**Why:** Three signals creating the same object is fragile. One idempotent path is correct.

### Fix 5 (MEDIUM): Replace `random.choices` with `secrets`

**File:** `staff/views.py`, `GenerateRegistrationPackageAPIView.post()`  
**Current:** `random.choices(string.ascii_uppercase + string.digits, k=8)`  
**Fix:** `secrets.token_hex(4).upper()` — same length, cryptographically secure.

### Fix 6 (MEDIUM): Duplicate `IsSuperUser` class

**File:** `hotel/base_views.py`  
**Fix:** Remove the local `IsSuperUser` class, import from `staff.permissions_superuser.IsSuperUser` instead.  
**Why:** Two identical permission classes is a maintenance trap.

---

## 9. Migration / Rollout Plan

### Phase 1: Security fixes (no new features, deploy independently)

```
Commit 1: Fix CreateStaffFromUserAPIView access level enforcement
Commit 2: Fix PendingRegistrationsAPIView access level enforcement  
Commit 3: Remove broken staff signal (create_staff_from_registration_code)
Commit 4: Consolidate hotel signals (remove 2 redundant, keep 1)
Commit 5: Replace random.choices with secrets in reg code generation
Commit 6: Remove duplicate IsSuperUser from hotel/base_views.py
```

These 6 commits are safe, backward-compatible, and independently deployable. They require no frontend changes. Deploy and verify before proceeding.

### Phase 2: Provisioning endpoint (new feature)

```
Commit 7: Create hotel/provisioning.py (service module)
Commit 8: Create hotel/provisioning_serializers.py
Commit 9: Create hotel/provisioning_views.py
Commit 10: Wire route in hotel/urls.py
Commit 11: Disable HotelViewSet.create() (return 405)
```

After deploy:
- Test: `POST /api/hotels/provision/` creates hotel + admin + config objects in one call
- Test: Old `POST /api/hotels/` returns 405
- Test: Primary admin receives password setup email
- Test: Primary admin can set password and log in
- Test: Primary admin sees correct `super_staff_admin` permissions
- Test: Registration packages are generated if requested
- Test: If admin email is duplicate, 400 returned and nothing created
- Test: If hotel slug is duplicate, 400 returned and nothing created

### Phase 3: Move bootstrap responsibilities backend-side

```
Commit 12: Add default NavigationItem seeding to provisioning service
           (currently NavigationItems must be created manually by superuser)
           Define a STANDARD_NAV_ITEMS list in provisioning.py:
             home, chat, bookings, room_services, housekeeping, maintenance,
             stock_tracker, attendance, entertainment, hotel_info, issues, settings
           Provisioning creates these for the hotel automatically.
           Primary admin gets all items assigned via M2M.

Commit 13: Add public page bootstrap to provisioning service (optional)
           Currently done via POST .../public-page-builder/bootstrap-default/
           Move that logic into provisioning.py so it runs as Phase C work.
```

### Phase 4: Cleanup

```
Commit 14: Remove frontend hotel creation flow (frontend-side change)
Commit 15: Remove frontend public page bootstrap call if now backend-handled
Commit 16: Audit and remove any orphaned seed/test scripts
```

---

## 10. Legacy Removal

Once the provisioning endpoint is live and verified:

| Remove | Location | Reason |
|--------|----------|--------|
| `HotelViewSet.create()` body | `hotel/base_views.py` | Replaced by provisioning. Keep as 405 stub. |
| `create_hotel_access_config` signal | `hotel/signals.py` | Redundant with `create_hotel_related_objects` |
| `save_hotel_access_config` signal | `hotel/signals.py` | Redundant with `create_hotel_related_objects` |
| `create_staff_from_registration_code` signal | `staff/signals.py` | Broken. References non-existent field. Dead code. |
| Local `IsSuperUser` class | `hotel/base_views.py` | Duplicate of `staff.permissions_superuser.IsSuperUser` |
| `random.choices` code path | `staff/views.py` (GenerateRegistrationPackageAPIView) | Replaced by `secrets`-based generation |
| `manage.py seed_hotels` command | `hotel/management/commands/seed_hotels.py` | Dev convenience only. Should not be a production creation path. Keep but document as dev-only. |

### Code paths to explicitly NOT remove

| Keep | Reason |
|------|--------|
| `StaffRegisterAPIView` (POST /api/staff/register/) | Normal staff self-registration flow. Unchanged. |
| `GenerateRegistrationPackageAPIView` | Normal ongoing registration package generation. Unchanged. |
| `PendingRegistrationsAPIView` | Normal pending review flow. Fixed in Phase 1, then unchanged. |
| `CreateStaffFromUserAPIView` | Normal staff approval flow. Fixed in Phase 1, then unchanged. |
| `HotelViewSet` (list, retrieve, update, delete) | Normal hotel CRUD. Only `create` is disabled. |
| `create_hotel_related_objects` signal | Still needed for backfill when existing hotels are re-saved. |

---

## Summary: What changes vs stays the same

```
PROVISIONING (NEW)
==================
POST /api/hotels/provision/  →  Hotel + User + Staff + Config + optional RegPackages
                                 All atomic. No orphan state possible.

EXISTING FLOWS (UNCHANGED after security fixes)
================================================
Registration Package → Self-Register → Pending → Admin Creates Staff Profile
                       (this entire chain stays exactly as-is)

DISABLED
========
POST /api/hotels/  →  405 Method Not Allowed
                       (forces all hotel creation through provisioning)
```
