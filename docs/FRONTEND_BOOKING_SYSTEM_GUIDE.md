# Frontend Booking System Implementation Guide

## What We Have Built (Backend Complete ✅)

### API Endpoint
```
GET /api/hotel/public/page/<slug>/
```

**Example:** `https://hotel-porter-d25ad83b12cf.herokuapp.com/api/hotel/public/page/hotel-killarney/`

### Complete Data Available

The API returns everything needed for a hotel public page:

```json
{
  "slug": "hotel-killarney",
  "name": "Hotel Killarney",
  "tagline": "Your Gateway to Ireland's Natural Beauty",
  "hero_image_url": "https://res.cloudinary.com/.../hero.jpg",
  "logo_url": "https://res.cloudinary.com/.../logo.jpg",
  "long_description": "Nestled in the heart of County Kerry...",
  
  "city": "Killarney",
  "country": "Ireland",
  "address_line_1": "College Street",
  "postal_code": "V93 X2C4",
  "latitude": 52.0599,
  "longitude": -9.5044,
  
  "phone": "+353 64 663 1555",
  "email": "info@hotelkillarney.ie",
  "website_url": "https://www.hotelkillarney.ie",
  
  "booking_options": {
    "primary_cta_label": "Book Now",
    "primary_cta_url": "https://www.hotelkillarney.ie/book",
    "secondary_cta_label": "Call to Book",
    "secondary_cta_phone": "+353 64 663 1555"
  },
  
  "room_types": [
    {
      "code": "",
      "name": "Deluxe Double Room",
      "short_description": "Spacious room with king-size bed and mountain views",
      "max_occupancy": 2,
      "bed_setup": "1 King Bed",
      "photo_url": "https://res.cloudinary.com/.../bedroom.jpg",
      "starting_price_from": "129.00",
      "currency": "EUR",
      "availability_message": "Popular choice"
    }
  ],
  
  "offers": [
    {
      "title": "Winter Escape Special",
      "short_description": "Cozy up in Killarney this winter! 20% off...",
      "details_text": "Valid for stays November through February...",
      "valid_from": "2025-11-23",
      "valid_to": "2026-02-21",
      "tag": "Seasonal",
      "book_now_url": "https://www.hotelkillarney.ie/book?offer=winter",
      "photo_url": "https://res.cloudinary.com/.../bedroom.jpg"
    }
  ],
  
  "leisure_activities": [
    {
      "name": "Spa & Wellness Center",
      "category": "Wellness",
      "short_description": "Luxurious spa with massage therapy...",
      "image_url": "https://res.cloudinary.com/.../laisure.webp"
    }
  ]
}
```

---

## What Frontend Needs to Build Now

### 1. **Hotel Public Page** (Marketing Page)

#### Components Needed:

**A. Hero Section**
```jsx
// Display:
- hero_image_url (full-width background)
- name (large heading)
- tagline (subheading)
- Primary CTA button (booking_options.primary_cta_label + primary_cta_url)
- Secondary CTA button (booking_options.secondary_cta_label + secondary_cta_phone)
```

**B. About Section**
```jsx
// Display:
- long_description (formatted text)
- city, country (with map icon)
- Google Maps integration using latitude/longitude
```

**C. Room Types Section**
```jsx
// For each room_type:
- photo_url (card image)
- name (heading)
- short_description
- bed_setup + max_occupancy (icons)
- starting_price_from + currency ("from €129/night")
- availability_message (badge)
- "View Details" button → links to booking
```

**D. Special Offers Section**
```jsx
// For each offer:
- photo_url (card image)
- title + tag (badge)
- short_description
- valid_from/valid_to dates
- book_now_url button
```

**E. Activities Section**
```jsx
// For each leisure_activity:
- image_url (card image)
- name
- category (icon/badge)
- short_description
```

**F. Contact Footer**
```jsx
// Display:
- phone (with tel: link)
- email (with mailto: link)
- address (formatted: address_line_1, city, postal_code, country)
- website_url (external link)
```

---

### 2. **What's MISSING for Complete Booking System**

The current API provides **marketing content only**. For a complete booking system, frontend needs:

#### ❌ Not Yet Built (Backend Requirements):

1. **Live Availability Check**
   - Check if rooms are available for specific dates
   - Real-time inventory management
   - **Backend needs:** `POST /api/hotel/<slug>/availability/`
   ```json
   {
     "check_in": "2025-12-15",
     "check_out": "2025-12-18",
     "room_type_id": 3
   }
   // Returns: available rooms, actual prices
   ```

2. **Dynamic Pricing**
   - Current API only shows `starting_price_from` (marketing price)
   - Actual prices vary by date, season, demand
   - **Backend needs:** Pricing engine integration

3. **Guest Information Form**
   - Capture guest details (name, email, phone, passport)
   - **Backend needs:** `POST /api/bookings/create/`

4. **Payment Integration**
   - Process payments (Stripe, PayPal, etc.)
   - **Backend needs:** Payment gateway integration

5. **Booking Confirmation**
   - Create reservation in system
   - Send confirmation email
   - Generate booking reference number
   - **Backend needs:** Booking model with status tracking

6. **Room Allocation**
   - Assign specific room numbers
   - Block dates in inventory
   - **Backend needs:** Real Room-to-Booking relationship

---

## Implementation Phases

### ✅ **Phase 1: Public Page (DONE)**
- API endpoint built
- Data populated
- Images uploaded
- Frontend can display hotel information

### 🔨 **Phase 2: Booking Flow (TODO - Backend)**

#### Step 1: Date Selection & Availability
```
Frontend sends:
POST /api/hotel/<slug>/check-availability/
{
  "check_in": "2025-12-15",
  "check_out": "2025-12-18",
  "adults": 2,
  "children": 0
}

Backend returns:
{
  "available_room_types": [
    {
      "room_type_id": 1,
      "name": "Deluxe Double Room",
      "available_rooms": 5,
      "price_per_night": 149.00,
      "total_price": 447.00,
      "currency": "EUR"
    }
  ]
}
```

#### Step 2: Guest Information
```
Frontend form collects:
- First name, Last name
- Email, Phone
- Country
- Special requests
```

#### Step 3: Payment
```
Frontend integrates:
- Stripe Elements / PayPal
- Secure payment form
- PCI compliance

Backend creates:
POST /api/bookings/create/
{
  "hotel_slug": "hotel-killarney",
  "room_type_id": 1,
  "check_in": "2025-12-15",
  "check_out": "2025-12-18",
  "guest": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+353 87 123 4567"
  },
  "payment_method": "stripe",
  "payment_token": "tok_xxxx"
}

Backend returns:
{
  "booking_id": "BK-2025-001234",
  "status": "confirmed",
  "confirmation_email_sent": true
}
```

---

## Frontend Tech Stack Recommendations

```javascript
// Example React implementation
import { useState, useEffect } from 'react';

function HotelPublicPage({ slug }) {
  const [hotel, setHotel] = useState(null);
  
  useEffect(() => {
    fetch(`/api/hotel/public/page/${slug}/`)
      .then(res => res.json())
      .then(data => setHotel(data));
  }, [slug]);
  
  if (!hotel) return <Loading />;
  
  return (
    <>
      <HeroSection 
        image={hotel.hero_image_url}
        title={hotel.name}
        tagline={hotel.tagline}
        ctaLabel={hotel.booking_options.primary_cta_label}
        ctaUrl={hotel.booking_options.primary_cta_url}
      />
      
      <AboutSection description={hotel.long_description} />
      
      <RoomTypesSection roomTypes={hotel.room_types} />
      
      <OffersSection offers={hotel.offers} />
      
      <ActivitiesSection activities={hotel.leisure_activities} />
      
      <ContactSection 
        phone={hotel.phone}
        email={hotel.email}
        address={{
          line1: hotel.address_line_1,
          city: hotel.city,
          postalCode: hotel.postal_code,
          country: hotel.country
        }}
      />
    </>
  );
}
```

---

## Next Backend Development Tasks

To complete the booking system, backend needs:

1. ✅ **Hotel public data API** (DONE)
2. ❌ **Availability checker endpoint**
3. ❌ **Dynamic pricing engine**
4. ❌ **Booking creation endpoint**
5. ❌ **Payment integration (Stripe/PayPal)**
6. ❌ **Email confirmation system**
7. ❌ **Booking management (view, cancel, modify)**
8. ❌ **Inventory management (block dates)**

---

## Current Limitations

⚠️ **What the current system CANNOT do:**
- Check if rooms are actually available
- Calculate real prices for specific dates
- Accept bookings
- Process payments
- Send confirmation emails
- Manage room inventory

✅ **What it CAN do:**
- Display hotel marketing information
- Show room types with "starting from" prices
- Show special offers
- Display contact information
- Provide booking CTAs (links to external booking)

---

## Temporary Solution (Current State)

The `booking_options.primary_cta_url` currently points to:
```
https://www.hotelkillarney.ie/book
```

This can link to:
1. **External booking engine** (e.g., Booking.com, hotel's existing system)
2. **Frontend booking form** (when Phase 2 backend is ready)
3. **Phone booking** (use secondary_cta_phone as fallback)

---

## Summary

**Phase 1 Complete:** Frontend can build a beautiful hotel public/marketing page with all content from the API.

**Phase 2 Required:** To handle actual bookings, backend needs availability checking, pricing, payment, and reservation management systems.

Frontend should:
1. Build the public page now with current API
2. Link "Book Now" buttons to external booking or phone number
3. Wait for Phase 2 backend APIs before implementing booking flow
