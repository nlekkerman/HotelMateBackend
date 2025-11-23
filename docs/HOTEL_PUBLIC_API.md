# Hotel Public API Documentation

## Overview

The Hotel Public API provides comprehensive marketing and booking information for hotels on the HotelsMate platform. This API is designed for **anonymous public access** and powers the public-facing hotel pages for users who are not yet staying at the hotel.

**Purpose:** Power public hotel marketing pages  
**Authentication:** None required (anonymous)  
**Target Users:** Non-staying guests browsing hotels  
**Base URL:** `/api/hotels/`

---

## Endpoints

### 1. List All Active Hotels

**GET** `/api/hotel/public/`

Returns a list of all active hotels with basic information and portal configuration.

#### Response (200 OK)
```json
[
  {
    "id": 1,
    "name": "Grand Hotel Dublin",
    "slug": "grand-hotel-dublin",
    "city": "Dublin",
    "country": "Ireland",
    "short_description": "Luxury 5-star hotel in the heart of Dublin city centre.",
    "logo_url": "https://res.cloudinary.com/.../logo.png",
    "guest_base_path": "/guest/hotels/grand-hotel-dublin/",
    "staff_base_path": "/staff/hotels/grand-hotel-dublin/",
    "guest_portal_enabled": true,
    "staff_portal_enabled": true
  }
]
```

---

### 2. Get Hotel Public Details (Basic)

**GET** `/api/hotel/public/<slug>/`

Returns basic hotel information with portal configuration.

#### Parameters
- `slug` (path parameter) - Hotel slug identifier

#### Response (200 OK)
```json
{
  "id": 1,
  "name": "Grand Hotel Dublin",
  "slug": "grand-hotel-dublin",
  "city": "Dublin",
  "country": "Ireland",
  "short_description": "Luxury 5-star hotel in the heart of Dublin city centre.",
  "logo_url": "https://res.cloudinary.com/.../logo.png",
  "guest_base_path": "/guest/hotels/grand-hotel-dublin/",
  "staff_base_path": "/staff/hotels/grand-hotel-dublin/",
  "guest_portal_enabled": true,
  "staff_portal_enabled": true
}
```

---

### 3. Get Complete Hotel Public Page 🌟 **NEW**

**GET** `/api/hotels/<slug>/public/`

Returns complete hotel page content including marketing information, location, contact details, booking options, room types, offers, and leisure activities. This is the main endpoint for building hotel public pages.

#### Parameters
- `slug` (path parameter) - Hotel slug identifier

#### Response (200 OK)
```json
{
  "slug": "grand-hotel-dublin",
  "name": "Grand Hotel Dublin",
  "tagline": "Luxury in the heart of the city",
  "hero_image_url": "https://res.cloudinary.com/.../hero.jpg",
  "logo_url": "https://res.cloudinary.com/.../logo.png",
  "short_description": "Luxury 5-star hotel in the heart of Dublin city centre.",
  "long_description": "Experience unparalleled luxury at Grand Hotel Dublin...",
  
  "city": "Dublin",
  "country": "Ireland",
  "address_line_1": "123 O'Connell Street",
  "address_line_2": "Dublin City Centre",
  "postal_code": "D01 ABC1",
  "latitude": "53.349804",
  "longitude": "-6.260310",
  
  "phone": "+353 1 234 5678",
  "email": "info@grandhoteldublin.ie",
  "website_url": "https://grandhoteldublin.ie",
  "booking_url": "https://booking.grandhoteldublin.ie",
  
  "booking_options": {
    "primary_cta_label": "Book a Room",
    "primary_cta_url": "https://booking.grandhoteldublin.ie",
    "secondary_cta_label": "Call to Book",
    "secondary_cta_phone": "+353 1 234 5678",
    "terms_url": "https://grandhoteldublin.ie/terms",
    "policies_url": "https://grandhoteldublin.ie/policies"
  },
  
  "room_types": [
    {
      "code": "STD",
      "name": "Standard Room",
      "short_description": "Comfortable room with modern amenities and city views.",
      "max_occupancy": 2,
      "bed_setup": "Queen Bed",
      "photo_url": "https://res.cloudinary.com/.../standard-room.jpg",
      "starting_price_from": "89.00",
      "currency": "EUR",
      "booking_code": "STD-ROOM",
      "booking_url": "https://booking.grandhoteldublin.ie/rooms/standard",
      "availability_message": "High demand"
    },
    {
      "code": "DLX",
      "name": "Deluxe Suite",
      "short_description": "Spacious suite with separate living area and premium amenities.",
      "max_occupancy": 4,
      "bed_setup": "King Bed + Sofa Bed",
      "photo_url": "https://res.cloudinary.com/.../deluxe-suite.jpg",
      "starting_price_from": "159.00",
      "currency": "EUR",
      "booking_code": "DLX-SUITE",
      "booking_url": "https://booking.grandhoteldublin.ie/rooms/deluxe",
      "availability_message": "Popular choice"
    }
  ],
  
  "offers": [
    {
      "title": "Weekend Getaway Package",
      "short_description": "2 nights with breakfast included and late checkout.",
      "details_html": "<p>Enjoy a relaxing weekend with...</p>",
      "valid_from": "2025-01-01",
      "valid_to": "2025-03-31",
      "tag": "Weekend Offer",
      "book_now_url": "https://booking.grandhoteldublin.ie/offers/weekend-getaway",
      "photo_url": "https://res.cloudinary.com/.../weekend-offer.jpg"
    },
    {
      "title": "Family Summer Deal",
      "short_description": "Special rates for families with kids activities included.",
      "details_html": "<p>Perfect for families...</p>",
      "valid_from": "2025-06-01",
      "valid_to": "2025-08-31",
      "tag": "Family Deal",
      "book_now_url": "https://booking.grandhoteldublin.ie/offers/family-summer",
      "photo_url": "https://res.cloudinary.com/.../family-deal.jpg"
    }
  ],
  
  "leisure_activities": [
    {
      "name": "Indoor Pool",
      "category": "Wellness",
      "short_description": "Heated indoor pool open year-round.",
      "details_html": "<p>25-meter heated pool with...</p>",
      "icon": "swimming-pool",
      "image_url": "https://res.cloudinary.com/.../pool.jpg"
    },
    {
      "name": "Kids Club",
      "category": "Family",
      "short_description": "Supervised activities for children aged 4-12.",
      "details_html": "<p>Daily activities include...</p>",
      "icon": "child",
      "image_url": "https://res.cloudinary.com/.../kids-club.jpg"
    },
    {
      "name": "The Grand Restaurant",
      "category": "Dining",
      "short_description": "Fine dining with locally sourced ingredients.",
      "details_html": "<p>Open for breakfast, lunch, and dinner...</p>",
      "icon": "restaurant",
      "image_url": "https://res.cloudinary.com/.../restaurant.jpg"
    },
    {
      "name": "Fitness Center",
      "category": "Sports",
      "short_description": "24/7 gym with modern equipment.",
      "details_html": "<p>Fully equipped gym with...</p>",
      "icon": "dumbbell",
      "image_url": "https://res.cloudinary.com/.../gym.jpg"
    },
    {
      "name": "Spa & Wellness",
      "category": "Wellness",
      "short_description": "Relaxing treatments and massages.",
      "details_html": "<p>Full-service spa offering...</p>",
      "icon": "spa",
      "image_url": "https://res.cloudinary.com/.../spa.jpg"
    }
  ]
}
```

#### Response (404 Not Found)
```json
{
  "detail": "Not found."
}
```

---

## Frontend Integration Guide

### Building a Hotel Public Page

Use the complete endpoint `/api/hotels/<slug>/public/` to build the entire hotel public page:

```javascript
// Example: Fetch hotel data
const hotelSlug = 'grand-hotel-dublin';
const response = await fetch(`/api/hotels/${hotelSlug}/public/`);
const hotel = await response.json();

// Now you have access to:
// - hotel.hero_image_url (for hero section)
// - hotel.booking_options (for CTA buttons)
// - hotel.room_types (for room listings)
// - hotel.offers (for special offers section)
// - hotel.leisure_activities (for facilities section)
```

### Recommended Page Structure

1. **Hero Section**
   - Background: `hero_image_url`
   - Title: `name`
   - Tagline: `tagline`
   - Primary CTA: `booking_options.primary_cta_label` → `booking_options.primary_cta_url`

2. **About Section**
   - `short_description` or `long_description`
   - Location: `city`, `country`
   - Contact: `phone`, `email`

3. **Room Types Section**
   - Display all `room_types` (filtered to `is_active=true`)
   - Show: name, photo, description, price from, max occupancy
   - CTA: Link to `room_types[].booking_url`

4. **Special Offers Section**
   - Display all `offers` (filtered to `is_active=true`)
   - Show: title, photo, description, validity dates, tag
   - CTA: Link to `offers[].book_now_url`

5. **Facilities Section**
   - Group `leisure_activities` by `category`
   - Show: icon, name, description
   - Categories: Wellness, Family, Dining, Sports, Entertainment, Business

6. **Map Section**
   - Use `latitude` and `longitude` for map integration
   - Display `address_line_1`, `address_line_2`, `postal_code`

7. **Footer**
   - Contact: `phone`, `email`, `website_url`
   - Secondary CTA: `booking_options.secondary_cta_label` with `secondary_cta_phone`
   - Links: `booking_options.terms_url`, `booking_options.policies_url`

---

## Data Filtering

### Active Items Only

The API automatically filters nested collections to return only active items:

- ✅ `room_types` where `is_active=true`
- ✅ `offers` where `is_active=true`
- ✅ `leisure_activities` where `is_active=true`

### Ordering

Collections are returned in their natural display order:

- **room_types**: Ordered by `sort_order`, then `name`
- **offers**: Ordered by `sort_order`, then newest first (`-created_at`)
- **leisure_activities**: Ordered by `category`, `sort_order`, then `name`

---

## CORS Configuration

All public endpoints are CORS-enabled for browser access. No authentication required.

**Allowed Origins:**
- `https://hotelsmates.com`
- `https://www.hotelsmates.com`
- Development: `http://localhost:*`

---

## Security & Privacy

### What's Exposed ✅
- Marketing content (descriptions, images, prices)
- Location and contact information
- Public booking links and CTAs
- Facility information

### What's NOT Exposed ❌
- Live availability or inventory
- Dynamic PMS pricing
- Guest/stay/booking records
- Staff information or internal configs
- Sensitive internal IDs
- Real-time room occupancy

This is **marketing content only** - not a live booking engine.

---

## Error Responses

### 404 - Hotel Not Found
```json
{
  "detail": "Not found."
}
```

**Causes:**
- Invalid hotel slug
- Hotel is not active (`is_active=false`)
- Hotel does not exist

### 500 - Server Error
```json
{
  "detail": "Internal server error"
}
```

Contact support if this occurs.

---

## Performance Notes

### Optimized Queries

The endpoint uses Django's `select_related()` and `prefetch_related()` for optimal performance:

```python
Hotel.objects.filter(is_active=True)
    .select_related('booking_options')
    .prefetch_related('room_types', 'offers', 'leisure_activities')
```

### Caching Recommendations

Consider caching this endpoint on the frontend:
- Cache TTL: 5-15 minutes
- Invalidate on hotel content updates
- Use hotel `slug` as cache key

---

## Testing the API

### Using curl

```bash
# List all hotels
curl -X GET https://api.hotelsmates.com/api/hotel/public/

# Get specific hotel (basic)
curl -X GET https://api.hotelsmates.com/api/hotel/public/grand-hotel-dublin/

# Get complete hotel page (NEW)
curl -X GET https://api.hotelsmates.com/api/hotels/grand-hotel-dublin/public/
```

### Using JavaScript

```javascript
// Fetch complete hotel data
const fetchHotelPage = async (slug) => {
  try {
    const response = await fetch(`/api/hotels/${slug}/public/`);
    if (!response.ok) {
      throw new Error('Hotel not found');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching hotel:', error);
    return null;
  }
};

// Usage
const hotel = await fetchHotelPage('grand-hotel-dublin');
console.log(hotel.room_types); // Array of room types
console.log(hotel.offers);     // Array of offers
```

---

## Migration from Legacy Endpoints

If you're currently using the basic endpoint:

### Before (Basic Info Only)
```javascript
GET /api/hotel/public/grand-hotel-dublin/
// Returns: basic hotel info + portal config
```

### After (Complete Page)
```javascript
GET /api/hotels/grand-hotel-dublin/public/
// Returns: everything above + room_types + offers + leisure_activities
```

Both endpoints remain available. Use the complete endpoint for building public pages.

---

## Support & Questions

For API support or questions:
- **Email:** dev@hotelsmates.com
- **GitHub Issues:** [HotelMateBackend Issues](https://github.com/nlekkerman/HotelMateBackend/issues)

---

## Changelog

### v1.1.0 (November 2025)
- ✨ NEW: Complete hotel public page endpoint `/api/hotels/<slug>/public/`
- ✨ NEW: BookingOptions model for CTA configuration
- ✨ NEW: RoomType model for room marketing
- ✨ NEW: Offer model for packages and deals
- ✨ NEW: LeisureActivity model for facilities
- ✨ Extended Hotel model with marketing fields (tagline, hero_image, long_description)
- ✨ Extended Hotel model with location fields (address, coordinates)
- ✨ Extended Hotel model with contact fields (phone, email, website_url, booking_url)

### v1.0.0 (Initial Release)
- Basic hotel listing endpoint
- Basic hotel detail endpoint with portal configuration
