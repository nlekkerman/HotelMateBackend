# HotelMate – CRUD & Public Page Phase 1 (Using Existing Models & Views)

## Context

We already have:

- Rich models:
  - `Hotel`
  - `HotelAccessConfig`
  - `BookingOptions`
  - `HotelPublicSettings`
  - `Offer`
  - `LeisureActivity`
  - `Room`
  - `RoomType` (marketing/public)
  - `RoomBooking`
  - `PricingQuote`

- Existing views:
  - `HotelViewSet`, `HotelBySlugView`
  - `HotelPublicListView`, `HotelPublicDetailView`, `HotelPublicPageView`
  - `HotelAvailabilityView`, `HotelPricingQuoteView`, `HotelBookingCreateView`
  - `HotelPublicSettingsView`, `HotelPublicSettingsStaffView`
  - `StaffBookingsListView`, `StaffBookingConfirmView`

Goal:  
Use these models + views to provide **clean CRUD for staff** and **structured data for the public hotel page**, without touching routing definitions.

---

# BACKEND ISSUES

## B1 – Make sure serializers exist for all public content models

**Goal**  
We need DRF serializers for all content that will be shown/edited via settings and public page.

**Models that must have serializers (create/extend if missing):**

- `Hotel`  
- `HotelPublicSettings`  
- `BookingOptions`  
- `HotelAccessConfig`  
- `Offer`  
- `LeisureActivity`  
- `RoomType` (marketing)  
- `Room` (for staff tooling only)  
- `RoomBooking`  
- `PricingQuote` (if we decide to expose it later)

**Tasks**

- Implement or update serializers in `serializers.py` to:

  - Support read/write where needed (for staff CRUD).
  - Provide a **public-safe** version for:
    - `HotelPublicSettings`
    - `Offer` (public fields only)
    - `LeisureActivity`
    - `RoomType`
    - `BookingOptions`
    - `Hotel` (only public-facing bits like name, tagline, hero, city, etc.)

- Keep separate serializers for:
  - **Staff** (full edit) vs  
  - **Public** (read-only, filtered fields).

**Acceptance Criteria**

- Serializers for each model are ready and used by relevant views.
- Public serializers do not leak internal/irrelevant fields.


---

## B2 – Extend `HotelPublicDetailSerializer` for full public page content

**Goal**  
`HotelPublicPageView` already prefetches `room_types`, `offers`, `leisure_activities`, and selects `booking_options`. We now need `HotelPublicDetailSerializer` to serialize a **full hotel public page payload**.

**Tasks**

- Update `HotelPublicDetailSerializer` so it returns a single structured response that includes:

  1. **Hotel meta & header**
     - Hotel name, slug, city, country
     - Tagline
     - Hero image (from `Hotel` and/or `HotelPublicSettings`)
     - Short/long descriptions (from `Hotel` / `HotelPublicSettings`)

  2. **Booking & CTA info**
     - From `BookingOptions`:
       - primary_cta_label / primary_cta_url
       - secondary_cta_label / secondary_cta_phone
       - terms_url / policies_url

  3. **Room types**
     - List of active `RoomType` records for this hotel:
       - name, code, short_description, max_occupancy,
         bed_setup, photo, starting_price_from, currency,
         availability_message, booking_url

  4. **Offers**
     - List of active, date-valid `Offer` items:
       - title, short_description, tag, valid_from/to, book_now_url, photo

  5. **Leisure & activities**
     - Grouped or tagged by `category` from `LeisureActivity`:
       - name, category, short_description, icon, image

  6. **Public settings & branding**
     - From `HotelPublicSettings`:
       - welcome_message, additional descriptions
       - gallery (image URLs)
       - amenities (list of strings)
       - contact_email, contact_phone, contact_address
       - colors (primary/secondary/accent/background/button)
       - theme_mode

**Acceptance Criteria**

- `HotelPublicPageView` returns a single JSON that contains everything the public hotel page needs.
- All nested sections are serialized using the dedicated public serializers.


---

## B3 – Ensure `HotelPublicSettingsView` (public) returns correct subset

**Goal**  
For public consumers that only need public settings (without full page), `HotelPublicSettingsView` must return the **public-safe subset** of `HotelPublicSettings`.

**Tasks**

- Confirm or implement `HotelPublicSettingsPublicSerializer` to include:
  - `short_description`, `long_description`, `welcome_message`
  - `hero_image`, `gallery`, `amenities`
  - `contact_email`, `contact_phone`, `contact_address`
  - `primary_color`, `secondary_color`, `accent_color`, `background_color`, `button_color`, `theme_mode`

- Ensure hotel slug is the only filter and only **existing** hotels with settings are returned.

**Acceptance Criteria**

- Public clients can call this view and receive only necessary public settings data (no staff-only fields).


---

## B4 – Extend `HotelPublicSettingsStaffView` for full settings CRUD

**Goal**  
Staff should be able to fully manage `HotelPublicSettings` via this view.

**Tasks**

- Verify `HotelPublicSettingsStaffSerializer` supports:
  - All relevant content, contact, branding fields.
  - Validation for colors (basic HEX format check is enough).
  - Validation for gallery and amenities being arrays.

- Ensure:
  - `GET` returns complete settings object for staff's hotel.
  - `PUT/PATCH` allows editing all fields safely.
  - Permissions (`IsAuthenticated`, `IsStaffMember`, `IsSameHotel`) are enforced as written.

**Acceptance Criteria**

- Changes made via `HotelPublicSettingsStaffView` are reflected on the public page after reload.
- Invalid payloads return clear errors.


---

## B5 – Add staff CRUD API logic for `Offer`, `LeisureActivity`, `RoomType`, `Room`

**Goal**  
Expose staff-only CRUD operations for the main public content entities (offers, leisure activities, marketing room types, and rooms), reusing **existing staff permission patterns**.

**Important:**  
No URL design in this issue. Just the views & logic; routing will use the existing pattern.

**Tasks**

- Implement DRF viewsets or API views for:

  1. `Offer` (staff CRUD)
     - Filter by `hotel` through staff’s hotel.
     - List / create / update / delete.
     - Implement ordering by `sort_order`.

  2. `LeisureActivity` (staff CRUD)
     - Same pattern: scoped to staff.hotel.
     - Manage `is_active`, `category`, `sort_order`, `image`.

  3. `RoomType` (marketing/public)
     - Staff can manage list of room types for their hotel.
     - CRUD with `is_active` and `sort_order`.
     - Keep `starting_price_from`, `availability_message`, `booking_url` editable.

  4. `Room`
     - Staff-facing CRUD to manage physical rooms per hotel.
     - Only for staff of that hotel.
     - Expose simple actions for:
       - Setting `is_occupied`.
       - Regenerating guest PIN (may be separate endpoint/action).

- Reuse permission style from:
  - `HotelPublicSettingsStaffView`
  - `StaffBookingsListView`

**Acceptance Criteria**

- Staff can fully manage these content units via API calls scoped to their hotel.
- No cross-hotel access possible.


---

## B6 – Wire `HotelPricingQuoteView` to `PricingQuote` model (optional Phase)

**Goal**  
Currently `HotelPricingQuoteView` calculates a quote in-memory only. We have a `PricingQuote` model; we should optionally persist quotes.

**Tasks**

- After computing totals inside `HotelPricingQuoteView`, create a `PricingQuote` instance:
  - Use existing pricing fields and relationships:
    - `hotel`, `room_type`, `check_in`, `check_out`, `adults`, `children`, etc.
    - `base_price_per_night`, `number_of_nights`, `subtotal`, `taxes`, `fees`, `discount`, `total`, `currency`.
    - `promo_code`, `applied_offer` (if later linked to `Offer`).
    - `valid_until`, `quote_id`.

- Return existing JSON response as-is, but now backed by a DB row.

**Acceptance Criteria**

- Quotes are persisted and can be validated later via `PricingQuote.is_valid()`.
- Old behavior (pure JSON response) stays compatible.


---

## B7 – Refactor `HotelBookingCreateView` to use `RoomBooking` model

**Goal**  
`HotelBookingCreateView` currently returns booking data without saving to DB. We already have `RoomBooking` model; we should persist the booking.

**Tasks**

- Update `HotelBookingCreateView` to:

  - Create a `RoomBooking` instance:
    - `hotel`, `room_type`
    - `check_in`, `check_out`
    - guest fields (first/last name, email, phone)
    - `adults`, `children`
    - `total_amount`, `currency`
    - `status` initial value as `PENDING_PAYMENT`
    - `special_requests`, `promo_code`
    - `payment_reference` left empty for now
  - Let `RoomBooking.save()` generate `booking_id` and `confirmation_number`.

- Return response based on the saved `RoomBooking` instance:
  - Use `RoomBooking` fields instead of custom generated IDs.
  - Keep response structure similar to current one so frontend work is minimal.

**Acceptance Criteria**

- Each booking created via this endpoint is persisted as `RoomBooking`.
- `StaffBookingsListView` and `StaffBookingConfirmView` continue to work with no changes (they already use `RoomBooking`).


---

## B8 – Improve `StaffBookingsListView` & `StaffBookingConfirmView` robustness

**Goal**  
Tighten staff booking management using existing views.

**Tasks**

- Ensure filters:
  - `status` filter uses uppercased codes (`PENDING_PAYMENT`, `CONFIRMED`, etc.).
  - `start_date` and `end_date` parsing handles invalid format gracefully (already partly done).

- Confirm:
  - Only bookings for `staff.hotel` are returned.
  - Confirm action handles edge cases:
    - Already confirmed
    - Cancelled
    - Not found

**Acceptance Criteria**

- Staff booking list & confirm behavior is predictable and stable.
- Error messages are clear and consistent.

---

# FRONTEND ISSUES

## F1 – Use `HotelPublicPageView` JSON to render the full public hotel page

**Goal**  
The public hotel page (Hotel Killarney, etc.) should consume `HotelPublicPageView` and render all sections from its payload.

**Sections to render:**

1. Hero/Header
   - Hotel name, tagline, hero image
   - Location (city, country)
   - Primary / secondary CTAs (from `BookingOptions`)

2. Rooms & Suites
   - Cards from `room_types`:
     - name, description, max_occupancy, bed_setup, price, highlight/availability_message, photo.

3. Special Offers & Packages
   - Cards from `offers`:
     - title, short_description, tag, valid date range, photo, CTA.

4. Leisure & Facilities
   - Grouped display by category:
     - Wellness, Family, Dining, Sports, Entertainment, etc.

5. Contact & Footer
   - From `HotelPublicSettings` + `Hotel`:
     - address, email, phone, footer headline/subtitle, guest portal text.

**Acceptance Criteria**

- UI matches existing design but uses live data from API.
- When staff changes content in settings and page is refreshed, new content appears.


---

## F2 – Hotel Settings: “Public Page Content & Branding” section

**Goal**  
Provide a single clean section in Hotel Settings that edits `HotelPublicSettings` content & branding fields.

**Tasks**

- Build a section using `HotelPublicSettingsStaffView`:

  - Content:
    - welcome_message
    - short_description
    - long_description
    - hero_image URL field or uploader
    - gallery management (add/remove string URLs or uploads)
    - amenities as tag list

  - Contact:
    - contact_email, contact_phone, contact_address

  - Branding:
    - primary_color, secondary_color, accent_color, background_color, button_color, theme_mode

- Include:
  - Validation (HEX color sanity, email format).
  - Save button with success/error feedback.

**Acceptance Criteria**

- Staff can adjust public copy and colors in one place.
- Changes are reflected on the public page.


---

## F3 – Hotel Settings: “Booking & CTA Options” section

**Goal**  
Use `BookingOptions` to let staff control labels and booking links.

**Tasks**

- Create a settings section for booking CTAs:

  - Fields:
    - primary_cta_label, primary_cta_url
    - secondary_cta_label, secondary_cta_phone
    - terms_url, policies_url

- Wire section to `BookingOptions` API (read/update only).

**Acceptance Criteria**

- Staff can change button labels/links without touching code.
- Public page hero/footer CTAs reflect these fields.


---

## F4 – Hotel Settings: “Rooms & Suites (Public)” section

**Goal**  
Manage `RoomType` records that show on the public page.

**Tasks**

- List view:
  - name
  - max_occupancy
  - starting_price_from
  - availability_message
  - active state
  - sort order

- CRUD:
  - Add new room type
  - Edit existing
  - Delete
  - Reorder by sort_order (drag or up/down buttons)

- Form includes:
  - code
  - name
  - short_description
  - max_occupancy
  - bed_setup
  - photo (upload widget)
  - starting_price_from
  - currency
  - booking_code
  - booking_url
  - availability_message
  - is_active

**Acceptance Criteria**

- Public “Rooms & Suites” section is fully editable by staff.
- Sorting and activation flags work as expected.


---

## F5 – Hotel Settings: “Offers & Packages” section

**Goal**  
Expose full CRUD for `Offer` records.

**Tasks**

- List view:
  - title
  - tag
  - valid_from – valid_to
  - is_active
  - sort_order

- CRUD:
  - Add / Edit / Delete
  - Reorder via sort_order

- Form fields:
  - title
  - short_description
  - details_text (optional plain text)
  - details_html (for rich content)
  - valid_from / valid_to (date pickers)
  - tag
  - book_now_url
  - photo
  - is_active

**Acceptance Criteria**

- Special offers on the public page are driven entirely from this section.
- Date restrictions are visually clear (expired offers can be styled differently if needed).


---

## F6 – Hotel Settings: “Leisure & Facilities” section

**Goal**  
CRUD UI for `LeisureActivity`.

**Tasks**

- List view:
  - name
  - category (badge)
  - is_active
  - sort_order

- CRUD:
  - Add / Edit / Delete
  - Reorder via sort_order

- Form fields:
  - name
  - category (select from `CATEGORY_CHOICES`)
  - short_description
  - details_html
  - icon
  - image
  - is_active

**Acceptance Criteria**

- Leisure/facility cards visible on public page are 100% managed here.
- Inactive activities are not shown publicly.


---

## F7 – Hotel Settings: “Rooms (Inventory)” section

**Goal**  
Basic staff-only CRUD UI for `Room` entities (not marketing, but real inventory).

**Tasks**

- List:
  - room_number
  - is_occupied
  - guest_id_pin
  - indicators for QR codes (room_service, breakfast, dinner_booking, chat_pin)

- Actions:
  - Add Room
  - Edit Room fields (room_number, is_occupied)
  - Delete Room

- Extra actions (calls to dedicated endpoints or actions):
  - Generate guest PIN (calls `generate_guest_pin`)
  - Generate room service QR
  - Generate breakfast QR
  - Generate restaurant booking QR
  - Generate chat PIN QR

**Acceptance Criteria**

- Staff can manage physical rooms and their QR assets.
- Public / guest flows that depend on QR codes can be tested easily.


---

## F8 – Hotel Settings: “Access Configuration” section

**Goal**  
Expose `HotelAccessConfig` fields in a simple settings section.

**Tasks**

- Form fields (toggles & numbers):
  - guest_portal_enabled
  - staff_portal_enabled
  - requires_room_pin
  - room_pin_length
  - rotate_pin_on_checkout
  - allow_multiple_guest_sessions
  - max_active_guest_devices_per_room

- Save with clear validation.

**Acceptance Criteria**

- Portal & PIN behavior is centrally controlled per hotel.
- Frontend and mobile flows can adapt based on these settings.


---

## F9 – Staff bookings management UI (using existing staff booking views)

**Goal**  
Use `StaffBookingsListView` and `StaffBookingConfirmView` to provide a bookings management UI for staff.

**Tasks**

- Bookings list:
  - booking_id
  - confirmation_number
  - guest name
  - dates (check_in → check_out)
  - room type
  - status
  - total_amount

- Filters:
  - status filter (pending, confirmed, cancelled, completed)
  - date range (start_date, end_date)

- Detail drawer/modal:
  - Show full booking details (guest, promo_code, special_requests, etc.)

- Actions:
  - Confirm booking (uses `StaffBookingConfirmView`)
  - Optional future: cancel booking

**Acceptance Criteria**

- Staff can see and confirm bookings from a simple list.
- Confirm action updates status and shows proper success feedback.

---

# END
