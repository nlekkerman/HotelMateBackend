# Public Website Content Management – Cards

Goal:  
Allow hotel admin to manage all public "cards" (blocks) on the public hotel website from the backend, **per hotel**, without changing code.

---

## A. Sections to Manage

1. **Rooms & Suites**
   - Shown on: public hotel "Rooms & Suites" section.
   - Admin must be able to:
     - List all room/suite cards for a given hotel.
     - Create a new card.
     - Edit an existing card.
     - Delete a card.
     - Change the display order of cards (e.g. drag & drop or position field).
     - Toggle visibility (publish/unpublish).

2. **Special Offers / Packages**
   - Shown on: "Special Offers" / "Packages" section.
   - Admin must be able to:
     - Create / edit / delete offer cards.
     - Set **active date range** (start/end date).
     - Toggle visibility.
     - Order cards.
   
3. **Leisure & Facilities**
   - Shown on: "Leisure & Facilities" section.
   - Admin must be able to:
     - Create / edit / delete facility cards.
     - Toggle visibility.
     - Order cards.

---

## B. Card Data Structure (per card type)

### 1. Common fields (all card types)

- `id`
- `hotel` (FK or hotel_slug / hotel_identifier)
- `title`
- `subtitle` (optional)
- `short_description` (text for card)
- `full_description` (optional – for detail page or modal)
- `image` (main image URL / upload)
- `badge_label` (e.g. "New", "Best Seller", "Limited Offer" – optional)
- `is_active` (bool – visible on website or not)
- `position` (integer – sort order)

### 2. Extra fields – Rooms & Suites

- `from_price` (e.g. "€129")
- `max_guests`
- `room_type_tag` (e.g. "Suite", "Family", "Deluxe")

### 3. Extra fields – Special Offers / Packages

- `price` or `from_price`
- `valid_from` (date)
- `valid_to` (date)
- `promo_code` (optional)
- `cta_label` (e.g. "Book Offer", "See Details")
- `cta_link` (URL or internal route)

### 4. Extra fields – Leisure & Facilities

- `category` (e.g. "Spa", "Pool", "Gym", "Kids Club")
- `opening_hours` (text)
- `location_note` (e.g. "Ground floor", "Outdoor")

---

## C. Backend Requirements

- Create **separate models** (or clearly separated types) for:
  - RoomsAndSuitesCard
  - SpecialOfferCard
  - LeisureFacilityCard
- Each model:
  - Linked to a specific hotel.
  - Standard CRUD via Django admin or custom admin views / API.
- API endpoints (example, adjust to project style):
  - `GET /api/public/{hotel_slug}/rooms/` → list room cards (active, sorted).
  - `GET /api/public/{hotel_slug}/offers/`
  - `GET /api/public/{hotel_slug}/facilities/`
- Admin endpoints (staff area) for CRUD:
  - `GET/POST/PUT/DELETE /api/admin/{hotel_slug}/rooms-cards/`
  - `GET/POST/PUT/DELETE /api/admin/{hotel_slug}/offers-cards/`
  - `GET/POST/PUT/DELETE /api/admin/{hotel_slug}/facilities-cards/`

---

## D. Frontend Requirements

- On public hotel page:
  - Fetch cards from the public endpoints.
  - Display **only `is_active = true`**, sorted by `position`.
- In staff/admin UI:
  - Simple lists with:
    - Card preview (thumbnail, title, badge).
    - Buttons: Edit, Delete, Toggle Active.
    - Ability to change order (either drag & drop or numeric position field).


