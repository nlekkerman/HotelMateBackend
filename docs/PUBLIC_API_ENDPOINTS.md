# Public API Endpoints

## Overview

Public endpoints for the HotelMates landing page and hotel discovery. **No authentication required.**

All public endpoints are prefixed with `/api/public/`

---

## Endpoints

### 1. List All Hotels

**GET** `/api/public/hotels/`

Returns all active hotels for the landing page with filtering and sorting.

**Query Parameters:**
- `city` - Filter by city (e.g., `?city=Killarney`)
- `country` - Filter by country (e.g., `?country=Ireland`)
- `hotel_type` - Filter by type (e.g., `?hotel_type=Resort`)
- `tags` - Filter by tags (e.g., `?tags=Family,Spa`)
- `sort_by` - Sort order: `name`, `city`, `sort_order` (default)

**Example Request:**
```
GET http://localhost:8000/api/public/hotels/?city=Killarney&hotel_type=Resort
```

**Example Response:**
```json
{
  "count": 2,
  "results": [
    {
      "id": 2,
      "name": "Hotel Killarney",
      "slug": "hotel-killarney",
      "city": "Killarney",
      "country": "Ireland",
      "hotel_type": "Resort",
      "tags": ["Family", "Spa", "Nature"],
      "short_description": "Family-friendly hotel in Kerry...",
      "tagline": "Your perfect stay in the heart of Kerry",
      "landing_page_image": "https://cloudinary.com/...",
      "sort_order": 0
    }
  ]
}
```

---

### 2. Get Filter Options

**GET** `/api/public/hotels/filters/`

Returns available filter options for the hotel search.

**Example Request:**
```
GET http://localhost:8000/api/public/hotels/filters/
```

**Example Response:**
```json
{
  "cities": ["Dublin", "Killarney", "Cork", "Galway"],
  "countries": ["Ireland", "UK", "France"],
  "hotel_types": [
    {"value": "Resort", "label": "Resort"},
    {"value": "SpaHotel", "label": "Spa Hotel"},
    {"value": "FamilyHotel", "label": "Family Hotel"}
  ],
  "tags": ["Family", "Spa", "Business", "Pet Friendly", "WiFi"]
}
```

---

### 3. Get Hotel Public Page

**GET** `/api/public/hotel/{slug}/page/`

Returns complete page structure with all sections, elements, and items for a specific hotel.

**Path Parameters:**
- `slug` - Hotel slug (e.g., `hotel-killarney`)

**Example Request:**
```
GET http://localhost:8000/api/public/hotel/hotel-killarney/page/
```

**Example Response:**
```json
{
  "hotel": {
    "id": 2,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney",
    "city": "Killarney",
    "country": "Ireland"
  },
  "sections": [
    {
      "id": 1,
      "position": 0,
      "name": "hero",
      "element": {
        "id": 1,
        "element_type": "hero",
        "title": "Welcome to Hotel Killarney",
        "subtitle": "Your perfect stay in the heart of Kerry",
        "body": "Enjoy comfortable rooms, great food...",
        "image_url": "https://...",
        "settings": {
          "primary_cta_label": "Book Now",
          "primary_cta_url": "/guest/hotels/hotel-killarney/book/",
          "align": "center"
        },
        "items": []
      }
    },
    {
      "id": 2,
      "position": 1,
      "name": "rooms",
      "element": {
        "id": 2,
        "element_type": "rooms_list",
        "title": "Our Rooms & Suites",
        "subtitle": "Find the perfect room for your stay",
        "settings": {
          "show_price_from": true,
          "show_occupancy": true,
          "columns": 2
        },
        "rooms": [
          {
            "id": 5,
            "name": "Deluxe Suite",
            "short_description": "Spacious suite with...",
            "max_occupancy": 4,
            "bed_setup": "King Bed + Sofa Bed",
            "photo": "https://cloudinary.com/...",
            "starting_price_from": "199.00",
            "currency": "EUR",
            "booking_url": "/book/deluxe-suite"
          }
        ],
        "items": []
      }
    },
    {
      "id": 3,
      "position": 2,
      "name": "highlights",
      "element": {
        "id": 3,
        "element_type": "cards_list",
        "title": "Why Guests Love Us",
        "settings": {
          "columns": 3
        },
        "items": [
          {
            "id": 1,
            "title": "Family Friendly",
            "subtitle": "Perfect for all ages",
            "body": "Spacious family rooms, kids' activities...",
            "badge": "Families",
            "meta": {"icon": "family"}
          }
        ]
      }
    }
  ]
}
```

**Element Types:**
- `hero` - Hero banner with CTA
- `rooms_list` - Room types (uses `rooms` array, NOT `items`)
- `cards_list` - Feature cards grid
- `gallery` - Image gallery
- `reviews_list` - Customer testimonials
- `contact_block` - Contact information and map

**See:** `docs/FRONTEND_DYNAMIC_PAGE_BUILDER_GUIDE.md` for detailed implementation guide.

---

## URL Structure Summary

```
/api/public/
├── hotels/                          # List all hotels
├── hotels/filters/                  # Get filter options
└── hotel/{slug}/page/              # Get hotel public page structure
```

---

## Testing

### Using cURL

```bash
# List all hotels
curl http://localhost:8000/api/public/hotels/

# Filter hotels by city
curl "http://localhost:8000/api/public/hotels/?city=Killarney"

# Get filter options
curl http://localhost:8000/api/public/hotels/filters/

# Get Hotel Killarney public page
curl http://localhost:8000/api/public/hotel/hotel-killarney/page/
```

### Using Browser

Simply visit:
- http://localhost:8000/api/public/hotels/
- http://localhost:8000/api/public/hotel/hotel-killarney/page/

---

## Seeding Test Data

To populate Hotel Killarney with sample sections:

```bash
python manage.py seed_killarney_public_page
```

This creates:
- Hero section
- Rooms list (auto-populated from RoomType model)
- Highlights cards (3 features)
- Gallery (3 images)
- Reviews (2 testimonials)
- Contact block

---

## Related Documentation

- **Frontend Integration Guide:** `docs/FRONTEND_DYNAMIC_PAGE_BUILDER_GUIDE.md`
- **Models:** `hotel/models.py` (PublicSection, PublicElement, PublicElementItem)
- **Views:** `hotel/views.py` (HotelPublicPageView, HotelPublicListView)
- **Management Command:** `hotel/management/commands/seed_killarney_public_page.py`

---

## Notes

- ✅ All endpoints are **public** - no authentication required
- ✅ CORS is enabled for these endpoints
- ✅ Response data is read-only (GET only)
- ✅ Hotels must have `is_active=True` to appear in listings
- ✅ Sections must have `is_active=True` to appear in page structure
- ⚠️ The `rooms_list` element type returns `rooms` array from RoomType model, not `items`
