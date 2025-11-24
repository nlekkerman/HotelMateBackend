# Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings

Context:
We already have:
- Staff auth using Django User + Staff model (user.staff_profile)
- Hotel relation via staff.hotel
- Permission helpers: IsStaffMember, IsSameHotel, plus access_level/role checks
- Booking + Stripe payment logic in place

Goal:
Add/extend backend pieces needed for:
- Public hotel page settings (content + branding)
- Staff editing of those settings (per hotel)
- Staff booking list + booking confirmation
- Confirmation email sending

All new staff endpoints must follow the existing auth patterns:
- Use `IsAuthenticated`, `IsStaffMember`, `IsSameHotel` where hotel_slug is in URL
- For admin-only actions, check `staff.access_level` and/or `staff.role.slug`
  as described in STAFF_AUTHENTICATION_PERMISSIONS.md.

---

## Issue 1 – [Backend] Finalize/extend HotelPublicSettings model

Goal:
Ensure the HotelPublicSettings model covers all fields needed by the public page editor.

Tasks:
- If model already exists, extend it minimally with any missing fields:

  Required content fields:
  - `short_description` (TextField)
  - `long_description` (TextField)
  - `welcome_message` (TextField, optional)
  - `hero_image` (URLField, optional)
  - `gallery` (JSONField or equivalent – list of image URLs)
  - `amenities` (JSONField – list of strings)
  - `contact_email` (EmailField)
  - `contact_phone` (CharField)
  - `contact_address` (TextField)

  Optional branding fields:
  - `primary_color`, `secondary_color`, `accent_color`,
    `background_color`, `button_color` (CharField, HEX)
  - `theme_mode` (CharField, e.g. choices: `light`, `dark`, `custom`)

- Enforce one settings row per hotel:
  - Make `hotel` a `OneToOneField` to `Hotel` (or add unique constraint on hotel FK).

- Add sensible defaults:
  - Empty strings / empty lists where appropriate
  - Default theme values if branding fields are blank

- Create/adjust migrations.

Deliverable:
- Updated model + migration file.

---

## Issue 2 – [Backend] Public read-only endpoint for hotel settings

Goal:
Expose current hotel public settings to the frontend for rendering the public page.

Endpoint:
- `GET /api/public/hotels/<hotel_slug>/settings/`

Tasks:
- Permissions: `AllowAny` (public endpoint).
- Resolve hotel by `<hotel_slug>` using existing `Hotel` model.
- Get or create a `HotelPublicSettings` instance for that hotel.
- Use a read-only serializer (e.g. `HotelPublicSettingsPublicSerializer`) to serialize all fields needed by frontend:
  - content fields (descriptions, welcome, hero, gallery, amenities, contact)
  - branding fields (colors, theme_mode)
- Return JSON.

Deliverable:
- View class or DRF viewset method
- Serializer class
- URL route wired into public API namespace

---

## Issue 3 – [Backend] Staff-only endpoint to update hotel public settings

Goal:
Allow authenticated hotel staff to update their own hotel’s public page settings.

Endpoint:
- `PUT /api/staff/hotels/<hotel_slug>/settings/`
- Optionally allow `PATCH` for partial updates.

Tasks:
- Use permission classes consistent with existing pattern:
  - `permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]`
  - This ensures:
    - User is authenticated
    - User has `staff_profile`
    - `staff.hotel.slug == hotel_slug`
- Inside the view:
  - Get `staff = request.user.staff_profile`
  - Optionally restrict editing to admins/manager roles:
    - e.g. require `staff.access_level in ['super_staff_admin', 'staff_admin']`
      OR `staff.role.slug in ['manager', 'admin']`
  - Get or create `HotelPublicSettings` for `staff.hotel`.
  - Use a write-enabled serializer (e.g. `HotelPublicSettingsStaffSerializer`).
  - Validate and save incoming data.
- Return updated settings JSON.

Deliverable:
- View class using `IsStaffMember` + `IsSameHotel`
- Serializer for write operations
- URL route under `/api/staff/hotels/<hotel_slug>/settings/`

---

## Issue 4 – [Backend] Adjust/extend auth/me endpoint for frontend permission checks

Goal:
Expose enough data from the existing staff auth system so frontend can:
- Know if current user is staff
- Know which hotel they belong to
- Know if they are allowed to edit the public page for a given hotel

Tasks:
- Update `GET /api/auth/me/` (or equivalent) to include:
  - Flag: `is_staff_member = bool(hasattr(user, "staff_profile"))`
  - If staff:
    - `hotel_slug = user.staff_profile.hotel.slug`
    - `access_level = user.staff_profile.access_level`
    - `role_slug = user.staff_profile.role.slug` (if role exists)
  - Frontend can then derive `canEditPublicPage` based on access_level/role_slug.
- Maintain backward compatibility with current consumers.

Deliverable:
- Updated serializer/response for auth/me endpoint.

---

## Issue 5 – [Backend] Tests for public settings API

Goal:
Basic test coverage for public and staff settings endpoints.

Tasks:
- Public GET:
  - Test that `GET /api/public/hotels/<hotel_slug>/settings/` returns data for a real hotel.
  - Test handling of missing settings (creates default or returns default values).
  - Test 404 for invalid/non-existing hotel_slug.
- Staff PUT:
  - Authenticated staff whose `staff.hotel.slug == hotel_slug` can update settings.
  - Staff for other hotels are denied (403) due to `IsSameHotel`.
  - Non-staff authenticated user is denied (403) due to missing `staff_profile`.
  - Unauthenticated user is denied (401/403).
- Add focused tests for permission behavior using the patterns in STAFF_AUTHENTICATION_PERMISSIONS.md.

Deliverable:
- Tests in the existing tests structure.

---

## Issue 6 – [Backend] Django admin integration for HotelPublicSettings

Goal:
Allow quick inspection and manual adjustments via Django admin.

Tasks:
- Register `HotelPublicSettings` in `admin.py`.
- In the admin class:
  - Show `hotel`, `updated_at`, and a few key fields in `list_display`.
  - Enable search/filter by `hotel`.
- Keep admin consistent with existing staff/hotel admin style.

Deliverable:
- Admin registration and configuration.

---

## Issue 7 – [Backend] Staff bookings list endpoint for each hotel

Goal:
Provide an API for staff to see room bookings for their hotel in the staff app.

Assumptions:
- There is a `Booking` model (or similar) linked to `Hotel` and to guest details.

Endpoint:
- `GET /api/staff/hotels/<hotel_slug>/bookings/`

Tasks:
- Permission classes:
  - `permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]`
- In the view:
  - Use `staff = request.user.staff_profile` and `staff.hotel` to filter bookings.
  - Filter by query params:
    - `status` (e.g. pending, confirmed, cancelled)
    - optional `start_date` / `end_date` range for check-in/check-out.
  - Return a list serializer with:
    - booking id / reference code
    - guest name + email
    - room / room type
    - check-in / check-out
    - total amount
    - booking/payment status.
- Ensure that only bookings for `staff.hotel` are returned.

Deliverable:
- List endpoint + serializer.

---

## Issue 8 – [Backend] Booking confirmation endpoint + status update

Goal:
Allow staff to confirm a booking from the staff interface.

Endpoint:
- `POST /api/staff/hotels/<hotel_slug>/bookings/<booking_id>/confirm/`

Tasks:
- Permission classes:
  - `permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]`
- In the view:
  - Get `staff = request.user.staff_profile`.
  - Optional: restrict to “admin/manager” type staff:
    - e.g. require `staff.access_level in ['super_staff_admin', 'staff_admin']`
      OR `staff.role.slug in ['manager', 'admin']`.
  - Fetch the booking and verify it belongs to `staff.hotel`.
  - Update booking status (e.g. from `pending` to `confirmed`).
  - Optionally store:
    - `confirmed_by = staff`
    - `confirmed_at = timezone.now()`
- Return updated booking JSON.

Deliverable:
- Confirm endpoint with proper permission and hotel scoping.

---

## Issue 9 – [Backend] Send booking confirmation email on confirmation

Goal:
When a booking is confirmed, send an email confirmation to the guest.

Tasks:
- Create a small email helper/service, e.g. `send_booking_confirmation_email(booking)`:
  - To: guest email.
  - Subject: "Your booking at <Hotel Name> is confirmed".
  - Body includes:
    - hotel name
    - check-in / check-out dates
    - room / room type
    - total amount
    - any key instructions (check-in time, etc.)
- Call this helper in:
  - The booking confirm endpoint (Issue 8).
  - The Stripe webhook flow, if there is an automatic confirmation path when payment succeeds.
- Ensure email failures:
  - Are logged
  - Do NOT crash the main request (wrap in try/except or use async/email backend).

Deliverable:
- Email helper + integration in confirmation logic.

---

## Issue 10 – [Backend] Tests for booking list, confirmation, and email trigger

Goal:
Ensure booking staff APIs and email trigger behave correctly.

Tasks:
- Bookings list endpoint:
  - Staff of the correct hotel (matching `hotel_slug`) see only their hotel’s bookings.
  - Staff of other hotels are denied (403).
  - Non-staff or unauthenticated are denied.
- Booking confirm endpoint:
  - Valid call updates status to confirmed.
  - Confirm by wrong hotel_slug/staff (via IsSameHotel) returns 403.
  - Confirm on already-cancelled booking is rejected (400/409).
- Email:
  - Use Django test email backend or mocks to assert:
    - Confirmation email gets sent on successful confirmation.
    - Correct recipient and basic content.

Deliverable:
- Test cases aligned with existing test patterns.
