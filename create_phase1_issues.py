#!/usr/bin/env python3
"""
Create GitHub issues for Phase 1 Backend implementation
"""
import os
import subprocess
import sys

# Define all labels to create
LABELS = [
    {"name": "backend", "color": "0052CC", "description": "Backend development tasks"},
    {"name": "api", "color": "FBCA04", "description": "API endpoints and serializers"},
    {"name": "models", "color": "5319E7", "description": "Database models and migrations"},
    {"name": "permissions", "color": "D93F0B", "description": "Authentication and permissions"},
    {"name": "tests", "color": "1D76DB", "description": "Test coverage"},
    {"name": "phase-1", "color": "0E8A16", "description": "Phase 1 implementation"},
    {"name": "hotel-settings", "color": "C2E0C6", "description": "Hotel public settings feature"},
    {"name": "bookings", "color": "FEF2C0", "description": "Booking system related"},
    {"name": "email", "color": "F9D0C4", "description": "Email functionality"},
]

# Define all issues
ISSUES = [
    {
        "title": "[Backend] Finalize/extend HotelPublicSettings model",
        "body": """## Goal
Ensure the HotelPublicSettings model covers all fields needed by the public page editor.

## Tasks

- [ ] If model already exists, extend it minimally with any missing fields:

  **Required content fields:**
  - `short_description` (TextField)
  - `long_description` (TextField)
  - `welcome_message` (TextField, optional)
  - `hero_image` (URLField, optional)
  - `gallery` (JSONField or equivalent – list of image URLs)
  - `amenities` (JSONField – list of strings)
  - `contact_email` (EmailField)
  - `contact_phone` (CharField)
  - `contact_address` (TextField)

  **Optional branding fields:**
  - `primary_color`, `secondary_color`, `accent_color`, `background_color`, `button_color` (CharField, HEX)
  - `theme_mode` (CharField, e.g. choices: `light`, `dark`, `custom`)

- [ ] Enforce one settings row per hotel:
  - Make `hotel` a `OneToOneField` to `Hotel` (or add unique constraint on hotel FK).

- [ ] Add sensible defaults:
  - Empty strings / empty lists where appropriate
  - Default theme values if branding fields are blank

- [ ] Create/adjust migrations.

## Deliverable
- Updated model + migration file.

## Context
Part of Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings

All new staff endpoints must follow the existing auth patterns:
- Use `IsAuthenticated`, `IsStaffMember`, `IsSameHotel` where hotel_slug is in URL
- For admin-only actions, check `staff.access_level` and/or `staff.role.slug` as described in STAFF_AUTHENTICATION_PERMISSIONS.md.
""",
        "labels": ["backend", "models", "phase-1", "hotel-settings"]
    },
    {
        "title": "[Backend] Public read-only endpoint for hotel settings",
        "body": """## Goal
Expose current hotel public settings to the frontend for rendering the public page.

## Endpoint
- `GET /api/public/hotels/<hotel_slug>/settings/`

## Tasks

- [ ] Permissions: `AllowAny` (public endpoint).
- [ ] Resolve hotel by `<hotel_slug>` using existing `Hotel` model.
- [ ] Get or create a `HotelPublicSettings` instance for that hotel.
- [ ] Use a read-only serializer (e.g. `HotelPublicSettingsPublicSerializer`) to serialize all fields needed by frontend:
  - content fields (descriptions, welcome, hero, gallery, amenities, contact)
  - branding fields (colors, theme_mode)
- [ ] Return JSON.

## Deliverable
- View class or DRF viewset method
- Serializer class
- URL route wired into public API namespace

## Context
Part of Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings
""",
        "labels": ["backend", "api", "phase-1", "hotel-settings"]
    },
    {
        "title": "[Backend] Staff-only endpoint to update hotel public settings",
        "body": """## Goal
Allow authenticated hotel staff to update their own hotel's public page settings.

## Endpoint
- `PUT /api/staff/hotels/<hotel_slug>/settings/`
- Optionally allow `PATCH` for partial updates.

## Tasks

- [ ] Use permission classes consistent with existing pattern:
  - `permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]`
  - This ensures:
    - User is authenticated
    - User has `staff_profile`
    - `staff.hotel.slug == hotel_slug`

- [ ] Inside the view:
  - Get `staff = request.user.staff_profile`
  - Optionally restrict editing to admins/manager roles:
    - e.g. require `staff.access_level in ['super_staff_admin', 'staff_admin']` OR `staff.role.slug in ['manager', 'admin']`
  - Get or create `HotelPublicSettings` for `staff.hotel`.
  - Use a write-enabled serializer (e.g. `HotelPublicSettingsStaffSerializer`).
  - Validate and save incoming data.

- [ ] Return updated settings JSON.

## Deliverable
- View class using `IsStaffMember` + `IsSameHotel`
- Serializer for write operations
- URL route under `/api/staff/hotels/<hotel_slug>/settings/`

## Context
Part of Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings

All new staff endpoints must follow the existing auth patterns as described in STAFF_AUTHENTICATION_PERMISSIONS.md.
""",
        "labels": ["backend", "api", "permissions", "phase-1", "hotel-settings"]
    },
    {
        "title": "[Backend] Adjust/extend auth/me endpoint for frontend permission checks",
        "body": """## Goal
Expose enough data from the existing staff auth system so frontend can:
- Know if current user is staff
- Know which hotel they belong to
- Know if they are allowed to edit the public page for a given hotel

## Tasks

- [ ] Update `GET /api/auth/me/` (or equivalent) to include:
  - Flag: `is_staff_member = bool(hasattr(user, "staff_profile"))`
  - If staff:
    - `hotel_slug = user.staff_profile.hotel.slug`
    - `access_level = user.staff_profile.access_level`
    - `role_slug = user.staff_profile.role.slug` (if role exists)
  - Frontend can then derive `canEditPublicPage` based on access_level/role_slug.

- [ ] Maintain backward compatibility with current consumers.

## Deliverable
- Updated serializer/response for auth/me endpoint.

## Context
Part of Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings
""",
        "labels": ["backend", "api", "permissions", "phase-1"]
    },
    {
        "title": "[Backend] Tests for public settings API",
        "body": """## Goal
Basic test coverage for public and staff settings endpoints.

## Tasks

### Public GET
- [ ] Test that `GET /api/public/hotels/<hotel_slug>/settings/` returns data for a real hotel.
- [ ] Test handling of missing settings (creates default or returns default values).
- [ ] Test 404 for invalid/non-existing hotel_slug.

### Staff PUT
- [ ] Authenticated staff whose `staff.hotel.slug == hotel_slug` can update settings.
- [ ] Staff for other hotels are denied (403) due to `IsSameHotel`.
- [ ] Non-staff authenticated user is denied (403) due to missing `staff_profile`.
- [ ] Unauthenticated user is denied (401/403).

- [ ] Add focused tests for permission behavior using the patterns in STAFF_AUTHENTICATION_PERMISSIONS.md.

## Deliverable
- Tests in the existing tests structure.

## Context
Part of Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings
""",
        "labels": ["backend", "tests", "phase-1", "hotel-settings"]
    },
    {
        "title": "[Backend] Django admin integration for HotelPublicSettings",
        "body": """## Goal
Allow quick inspection and manual adjustments via Django admin.

## Tasks

- [ ] Register `HotelPublicSettings` in `admin.py`.
- [ ] In the admin class:
  - Show `hotel`, `updated_at`, and a few key fields in `list_display`.
  - Enable search/filter by `hotel`.
- [ ] Keep admin consistent with existing staff/hotel admin style.

## Deliverable
- Admin registration and configuration.

## Context
Part of Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings
""",
        "labels": ["backend", "phase-1", "hotel-settings"]
    },
    {
        "title": "[Backend] Staff bookings list endpoint for each hotel",
        "body": """## Goal
Provide an API for staff to see room bookings for their hotel in the staff app.

## Assumptions
- There is a `Booking` model (or similar) linked to `Hotel` and to guest details.

## Endpoint
- `GET /api/staff/hotels/<hotel_slug>/bookings/`

## Tasks

- [ ] Permission classes:
  - `permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]`

- [ ] In the view:
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

- [ ] Ensure that only bookings for `staff.hotel` are returned.

## Deliverable
- List endpoint + serializer.

## Context
Part of Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings

All new staff endpoints must follow the existing auth patterns as described in STAFF_AUTHENTICATION_PERMISSIONS.md.
""",
        "labels": ["backend", "api", "permissions", "phase-1", "bookings"]
    },
    {
        "title": "[Backend] Booking confirmation endpoint + status update",
        "body": """## Goal
Allow staff to confirm a booking from the staff interface.

## Endpoint
- `POST /api/staff/hotels/<hotel_slug>/bookings/<booking_id>/confirm/`

## Tasks

- [ ] Permission classes:
  - `permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]`

- [ ] In the view:
  - Get `staff = request.user.staff_profile`.
  - Optional: restrict to "admin/manager" type staff:
    - e.g. require `staff.access_level in ['super_staff_admin', 'staff_admin']` OR `staff.role.slug in ['manager', 'admin']`.
  - Fetch the booking and verify it belongs to `staff.hotel`.
  - Update booking status (e.g. from `pending` to `confirmed`).
  - Optionally store:
    - `confirmed_by = staff`
    - `confirmed_at = timezone.now()`

- [ ] Return updated booking JSON.

## Deliverable
- Confirm endpoint with proper permission and hotel scoping.

## Context
Part of Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings

All new staff endpoints must follow the existing auth patterns as described in STAFF_AUTHENTICATION_PERMISSIONS.md.
""",
        "labels": ["backend", "api", "permissions", "phase-1", "bookings"]
    },
    {
        "title": "[Backend] Send booking confirmation email on confirmation",
        "body": """## Goal
When a booking is confirmed, send an email confirmation to the guest.

## Tasks

- [ ] Create a small email helper/service, e.g. `send_booking_confirmation_email(booking)`:
  - To: guest email.
  - Subject: "Your booking at <Hotel Name> is confirmed".
  - Body includes:
    - hotel name
    - check-in / check-out dates
    - room / room type
    - total amount
    - any key instructions (check-in time, etc.)

- [ ] Call this helper in:
  - The booking confirm endpoint (Issue 8).
  - The Stripe webhook flow, if there is an automatic confirmation path when payment succeeds.

- [ ] Ensure email failures:
  - Are logged
  - Do NOT crash the main request (wrap in try/except or use async/email backend).

## Deliverable
- Email helper + integration in confirmation logic.

## Context
Part of Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings
""",
        "labels": ["backend", "email", "phase-1", "bookings"]
    },
    {
        "title": "[Backend] Tests for booking list, confirmation, and email trigger",
        "body": """## Goal
Ensure booking staff APIs and email trigger behave correctly.

## Tasks

### Bookings list endpoint
- [ ] Staff of the correct hotel (matching `hotel_slug`) see only their hotel's bookings.
- [ ] Staff of other hotels are denied (403).
- [ ] Non-staff or unauthenticated are denied.

### Booking confirm endpoint
- [ ] Valid call updates status to confirmed.
- [ ] Confirm by wrong hotel_slug/staff (via IsSameHotel) returns 403.
- [ ] Confirm on already-cancelled booking is rejected (400/409).

### Email
- [ ] Use Django test email backend or mocks to assert:
  - Confirmation email gets sent on successful confirmation.
  - Correct recipient and basic content.

## Deliverable
- Test cases aligned with existing test patterns.

## Context
Part of Phase 1 – Backend Issues: Public Hotel Page Settings & Bookings
""",
        "labels": ["backend", "tests", "phase-1", "bookings", "email"]
    }
]


def run_command(cmd):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False, result.stderr
    print(f"Success: {result.stdout}")
    return True, result.stdout


def create_labels():
    """Create all labels in the repository."""
    print("\n=== Creating Labels ===\n")
    
    for label in LABELS:
        cmd = f'gh label create "{label["name"]}" --color {label["color"]} --description "{label["description"]}" --force'
        success, output = run_command(cmd)
        if not success and "already exists" not in output.lower():
            print(f"Warning: Failed to create label {label['name']}")
    
    print("\n=== Labels created successfully ===\n")


def create_issues():
    """Create all issues in the repository."""
    print("\n=== Creating Issues ===\n")
    
    created_issues = []
    
    for i, issue in enumerate(ISSUES, 1):
        print(f"\nCreating Issue {i}/{len(ISSUES)}: {issue['title']}")
        
        # Prepare labels as comma-separated string
        labels_str = ",".join(issue["labels"])
        
        # Create a temporary file for the body
        temp_file = f"issue_body_{i}.txt"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(issue["body"])
        
        # Create the issue using gh CLI
        cmd = f'gh issue create --title "{issue["title"]}" --body-file {temp_file} --label "{labels_str}"'
        success, output = run_command(cmd)
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        if success:
            created_issues.append(issue["title"])
            print(f"✓ Created: {issue['title']}")
        else:
            print(f"✗ Failed: {issue['title']}")
    
    print("\n=== Summary ===")
    print(f"Successfully created {len(created_issues)}/{len(ISSUES)} issues")
    
    if created_issues:
        print("\nCreated issues:")
        for title in created_issues:
            print(f"  - {title}")
    
    return len(created_issues) == len(ISSUES)


def main():
    """Main function to create labels and issues."""
    print("=" * 60)
    print("Creating Phase 1 Backend Issues")
    print("=" * 60)
    
    # Check if gh CLI is available
    result = subprocess.run("gh --version", shell=True, capture_output=True)
    if result.returncode != 0:
        print("Error: GitHub CLI (gh) is not installed or not in PATH")
        print("Please install it from: https://cli.github.com/")
        sys.exit(1)
    
    # Create labels first
    create_labels()
    
    # Create issues
    success = create_issues()
    
    if success:
        print("\n✓ All issues created successfully!")
        sys.exit(0)
    else:
        print("\n✗ Some issues failed to create")
        sys.exit(1)


if __name__ == "__main__":
    main()
