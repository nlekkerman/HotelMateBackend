# Backend Issue — Public Hotel Page API + Booking Logic

## Title  
Public Hotel Content API for Non-Staying Guests (Public Page + Booking)

## Body  
Create/extend a **public, anonymous API** that powers the **hotel public page** for users who are **not yet staying** at the hotel, including both:

- public marketing content for the hotel page, and  
- basic booking-related data (CTAs, “from” prices, booking URLs).

This is NOT a live booking engine. It is content + marketing/booking metadata only.

---

## Summary

When a user clicks a hotel on the HotelsMate homepage, they should see a **public hotel page** (mini website) with:

- hero image + branding  
- booking call-to-actions  
- room type overview with “from €X/night”  
- offers / packages  
- leisure activities / facilities  
- contact and basic info  

All of this must be driven by a single public endpoint, safe for anonymous users.

---

## Requirements

### 1. Public hotel endpoint (by slug)

Expose/extend:

- `GET /api/hotels/<slug>/public/`
- Anonymous (no auth, AllowAny)
- Lookup: `hotel.slug`

The response should include:

#### Hotel basics
- `slug`  
- `name`  
- `tagline`  
- `hero_image_url`  
- `logo_url`  
- `short_description`  
- `long_description`  

#### Location
- `city`, `country`  
- `address_line_1`, `address_line_2`, `postal_code`  
- optional `latitude`, `longitude`  

#### Contact
- `phone`  
- `email`  
- `website_url`  
- generic `booking_url` (if configured)  

### 2. Booking options block

Add a nested `booking_options` object, for example:

- `primary_cta_label` (e.g. "Book a Room")  
- `primary_cta_url` (main booking entry link – internal/external)  
- `secondary_cta_label` (e.g. "Call to Book")  
- `secondary_cta_phone`  
- optional:
  - `terms_url`  
  - `policies_url`  

Frontend will use this to build hero/footer booking buttons.

### 3. Room types (public marketing + pricing)

Return a `room_types` list, where each item is a **marketing summary**, not live inventory:

- `code` (optional identifier)  
- `name`  
- `short_description`  
- `max_occupancy`  
- `bed_setup` (optional text)  
- `photo_url`  

Booking-related fields for UI:

- `starting_price_from` (float) — marketing “from €X/night”  
- `currency` (e.g. "EUR")  
- optional:
  - `booking_code`  
  - `booking_url` (deep link to booking engine for that room type)  
  - `availability_message` (short text like “High demand”, “Popular choice”)  

### 4. Offers (public packages + booking)

Return an `offers` list, where each offer includes:

- `title`  
- `short_description`  
- optional:
  - `details_html` or `details_text`  
  - `valid_from`, `valid_to`  
  - `tag` (e.g. "Family Deal", "Weekend Offer")  
- `book_now_url` (link to external or internal booking page for that offer)  

Again, these are marketing-level objects only.

### 5. Leisure activities / facilities

Return a `leisure_activities` list:

- `name`  
- `category` (e.g. Wellness, Family, Dining)  
- `short_description`  
- optional `icon` / `image_url`  
- optional `details_html`  

This is purely informational for the public page.

---

## Constraints

This endpoint MUST NOT:

- expose live availability or dynamic PMS pricing  
- expose any guest/stay/booking records  
- expose staff or internal configuration fields  
- leak internal IDs beyond what is needed for routing or links  

All content must be safe for anonymous public consumption.

---

## Tests

- Valid slug → 200 response, with all expected top-level keys present.  
- Invalid slug → 404.  
- At least one test hotel with:
  - multiple room types  
  - at least one offer  
  - at least one leisure activity  
- Assertions that no guest/stay/staff fields are present in the JSON payload.

---

## Acceptance Criteria

- `/api/hotels/<slug>/public/` returns:
  - hotel marketing content  
  - booking_options  
  - room type data including “from” prices  
  - offers with booking links  
  - leisure/facilities info  
- Response structure is stable and documented for frontend use.  
- Endpoint is anonymous and safe to be called directly from the browser on the public hotel page.
