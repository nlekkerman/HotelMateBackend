# Frontend Implementation Guide: Rooms Section

## Overview
The backend now supports a **"rooms"** section type that dynamically displays RoomType data on hotel public pages. This guide shows how to consume the API and render the rooms section on the frontend.

---

## 1. API Endpoint

### Public Hotel Page API
**Endpoint:** `GET /api/public/hotel/{slug}/page/`

**Response Structure:**
```json
{
  "hotel": {
    "id": 2,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney",
    "city": "Killarney",
    "country": "Ireland",
    "phone": "+353 64 1234567",
    "email": "info@hotelkillarney.ie"
  },
  "sections": [
    {
      "id": 1,
      "position": 0,
      "is_active": true,
      "name": "Hero Section",
      "section_type": "hero",
      "hero_data": { ... }
    },
    {
      "id": 5,
      "position": 2,
      "is_active": true,
      "name": "Our Rooms & Suites",
      "section_type": "rooms",
      "style_variant": 1,
      "rooms_data": {
        "id": 3,
        "subtitle": "Choose the perfect stay for your visit",
        "description": "",
        "style_variant": 1,
        "room_types": [
          {
            "id": 10,
            "code": "SUP-KING",
            "name": "Superior King Room",
            "short_description": "Spacious room with king bed and modern amenities",
            "max_occupancy": 2,
            "bed_setup": "1 King Bed",
            "photo": "https://res.cloudinary.com/.../room-image.jpg",
            "starting_price_from": "129.00",
            "currency": "EUR",
            "availability_message": "High demand",
            "booking_cta_url": "/public/booking/hotel-killarney?room_type_code=SUP-KING"
          },
          {
            "id": 11,
            "code": "DLX-TWIN",
            "name": "Deluxe Twin Room",
            "short_description": "Comfortable twin room perfect for friends or colleagues",
            "max_occupancy": 2,
            "bed_setup": "2 Twin Beds",
            "photo": "https://res.cloudinary.com/.../twin-room.jpg",
            "starting_price_from": "119.00",
            "currency": "EUR",
            "availability_message": "Available",
            "booking_cta_url": "/public/booking/hotel-killarney?room_type_code=DLX-TWIN"
          }
        ]
      }
    }
  ]
}
```

---

## 2. Frontend API Service (api.js)

Assuming your `api.js` already has a base URL like `const API_BASE = '/api'`, add or verify this function:

```javascript
// api.js

export const getHotelPublicPage = async (hotelSlug) => {
  try {
    const response = await fetch(`${API_BASE}/public/hotel/${hotelSlug}/page/`);
    if (!response.ok) {
      throw new Error(`Failed to fetch hotel page: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching hotel public page:', error);
    throw error;
  }
};
```

---

## 3. React Component Example

### Rooms Section Component

```jsx
// components/sections/RoomsSection.jsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import './RoomsSection.css';

const RoomsSection = ({ section }) => {
  const navigate = useNavigate();
  const { rooms_data } = section;

  if (!rooms_data || !rooms_data.room_types || rooms_data.room_types.length === 0) {
    return null;
  }

  const handleBookNow = (roomType) => {
    // Navigate to booking page with room type pre-selected
    navigate(roomType.booking_cta_url);
  };

  return (
    <section className={`rooms-section style-variant-${rooms_data.style_variant}`}>
      <div className="container">
        {/* Section Header */}
        <div className="section-header">
          <h2 className="section-title">{section.name}</h2>
          {rooms_data.subtitle && (
            <p className="section-subtitle">{rooms_data.subtitle}</p>
          )}
          {rooms_data.description && (
            <p className="section-description">{rooms_data.description}</p>
          )}
        </div>

        {/* Room Cards Grid */}
        <div className="room-cards-grid">
          {rooms_data.room_types.map((roomType) => (
            <div key={roomType.id} className="room-card">
              {/* Room Image */}
              {roomType.photo && (
                <div className="room-image">
                  <img src={roomType.photo} alt={roomType.name} />
                  {roomType.availability_message && (
                    <span className="availability-badge">
                      {roomType.availability_message}
                    </span>
                  )}
                </div>
              )}

              {/* Room Info */}
              <div className="room-info">
                <h3 className="room-name">{roomType.name}</h3>
                <p className="room-description">{roomType.short_description}</p>

                {/* Room Details */}
                <div className="room-details">
                  <div className="detail-item">
                    <span className="icon">👥</span>
                    <span>Up to {roomType.max_occupancy} guests</span>
                  </div>
                  {roomType.bed_setup && (
                    <div className="detail-item">
                      <span className="icon">🛏️</span>
                      <span>{roomType.bed_setup}</span>
                    </div>
                  )}
                </div>

                {/* Pricing & CTA */}
                <div className="room-footer">
                  <div className="pricing">
                    <span className="price-label">From</span>
                    <span className="price-amount">
                      {roomType.currency === 'EUR' ? '€' : '$'}
                      {roomType.starting_price_from}
                    </span>
                    <span className="price-period">/ night</span>
                  </div>
                  <button
                    className="btn-book-now"
                    onClick={() => handleBookNow(roomType)}
                  >
                    Book Now
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default RoomsSection;
```

---

## 4. CSS Styling Example

```css
/* RoomsSection.css */

.rooms-section {
  padding: 4rem 0;
  background: #f9f9f9;
}

.rooms-section .container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* Section Header */
.section-header {
  text-align: center;
  margin-bottom: 3rem;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 1rem;
}

.section-subtitle {
  font-size: 1.25rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.section-description {
  font-size: 1rem;
  color: #888;
  max-width: 600px;
  margin: 0 auto;
}

/* Room Cards Grid */
.room-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 2rem;
}

.room-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.room-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* Room Image */
.room-image {
  position: relative;
  width: 100%;
  height: 220px;
  overflow: hidden;
}

.room-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.availability-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(255, 255, 255, 0.95);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #2ecc71;
}

/* Room Info */
.room-info {
  padding: 1.5rem;
}

.room-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.75rem;
}

.room-description {
  font-size: 0.95rem;
  color: #666;
  line-height: 1.5;
  margin-bottom: 1rem;
}

/* Room Details */
.room-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f7f7f7;
  border-radius: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #555;
}

.detail-item .icon {
  font-size: 1.2rem;
}

/* Room Footer */
.room-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.pricing {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.price-label {
  font-size: 0.85rem;
  color: #888;
}

.price-amount {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2c3e50;
}

.price-period {
  font-size: 0.85rem;
  color: #888;
}

.btn-book-now {
  padding: 0.75rem 1.5rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s ease;
}

.btn-book-now:hover {
  background: #2980b9;
}

/* Style Variants (optional) */
.rooms-section.style-variant-2 {
  background: white;
}

.rooms-section.style-variant-3 .room-cards-grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

/* Responsive */
@media (max-width: 768px) {
  .room-cards-grid {
    grid-template-columns: 1fr;
  }
  
  .section-title {
    font-size: 2rem;
  }
}
```

---

## 5. Main Page Component Integration

```jsx
// pages/HotelPublicPage.jsx

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getHotelPublicPage } from '../api/api';
import HeroSection from '../components/sections/HeroSection';
import GallerySection from '../components/sections/GallerySection';
import RoomsSection from '../components/sections/RoomsSection';
import ListSection from '../components/sections/ListSection';
import NewsSection from '../components/sections/NewsSection';

const HotelPublicPage = () => {
  const { hotelSlug } = useParams();
  const [pageData, setPageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPage = async () => {
      try {
        setLoading(true);
        const data = await getHotelPublicPage(hotelSlug);
        setPageData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPage();
  }, [hotelSlug]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!pageData) return <div>No data available</div>;

  // Render sections based on type
  const renderSection = (section) => {
    switch (section.section_type) {
      case 'hero':
        return <HeroSection key={section.id} section={section} />;
      case 'gallery':
        return <GallerySection key={section.id} section={section} />;
      case 'rooms':
        return <RoomsSection key={section.id} section={section} />;
      case 'list':
        return <ListSection key={section.id} section={section} />;
      case 'news':
        return <NewsSection key={section.id} section={section} />;
      default:
        return null;
    }
  };

  return (
    <div className="hotel-public-page">
      {pageData.sections.map(renderSection)}
    </div>
  );
};

export default HotelPublicPage;
```

---

## 6. Booking Flow Integration

When a user clicks "Book Now" on a room card, they're redirected to:
```
/public/booking/{hotelSlug}?room_type_code={code}
```

### Example Booking Page Hook

```jsx
// pages/BookingPage.jsx

import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';

const BookingPage = () => {
  const { hotelSlug } = useParams();
  const [searchParams] = useSearchParams();
  const roomTypeCode = searchParams.get('room_type_code');

  const [selectedRoom, setSelectedRoom] = useState(null);

  useEffect(() => {
    if (roomTypeCode) {
      // Pre-select the room type in your booking wizard
      console.log('Pre-selecting room:', roomTypeCode);
      // You can fetch room details or set state here
    }
  }, [roomTypeCode]);

  return (
    <div className="booking-page">
      <h1>Book Your Stay at {hotelSlug}</h1>
      {roomTypeCode && <p>Selected Room: {roomTypeCode}</p>}
      {/* Your booking wizard components */}
    </div>
  );
};

export default BookingPage;
```

---

## 7. Testing the Implementation

### Test URLs:
1. **Public Hotel Page:**
   ```
   GET http://localhost:8000/api/public/hotel/hotel-killarney/page/
   ```

2. **Expected Response:**
   - Look for a section with `"section_type": "rooms"`
   - Verify `rooms_data` contains `room_types` array
   - Each room type should have all required fields

### Frontend Testing:
1. Navigate to your hotel public page component
2. Verify the rooms section renders after hero/gallery sections
3. Click "Book Now" button on a room card
4. Confirm navigation to `/public/booking/{slug}?room_type_code={code}`

---

## 8. Staff Management (Optional Frontend)

If you want staff to manage rooms sections:

### Staff API Endpoints:
```javascript
// Staff can view/edit rooms section configuration
GET    /api/staff/hotels/{slug}/hotel/staff/rooms-sections/
GET    /api/staff/hotels/{slug}/hotel/staff/rooms-sections/{id}/
PATCH  /api/staff/hotels/{slug}/hotel/staff/rooms-sections/{id}/
```

### Example Staff Edit Form:
```jsx
const updateRoomsSection = async (sectionId, data) => {
  const response = await fetch(
    `${API_BASE}/staff/hotels/${hotelSlug}/hotel/staff/rooms-sections/${sectionId}/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${authToken}`,
      },
      body: JSON.stringify({
        subtitle: data.subtitle,
        description: data.description,
        style_variant: data.style_variant,
      }),
    }
  );
  return await response.json();
};
```

---

## 9. Key Points

✅ **Room types are live** - No caching, always shows current PMS data  
✅ **Booking URLs match** - `/public/booking/{slug}?room_type_code={code}`  
✅ **No duplication** - Room data comes from `rooms.RoomType` model  
✅ **Staff control** - Can edit section subtitle, description, style_variant  
✅ **Staff cannot** - Attach lists/cards to rooms sections (validation enforced)

---

## 10. Troubleshooting

### Issue: Section not showing
- Check if hotel has an active rooms section: `section_type === 'rooms'`
- Verify `rooms_data` exists in API response
- Check `room_types` array is not empty

### Issue: Photos not loading
- Verify Cloudinary URLs are valid
- Check `photo` field is not null in API response

### Issue: Booking link broken
- Ensure React Router route matches: `/public/booking/:hotelSlug`
- Verify `room_type_code` query param is being read correctly

---

**Implementation Complete!** 🎉

Your frontend should now be able to:
- Fetch and display rooms sections dynamically
- Show live room type data from the PMS
- Navigate to booking wizard with pre-selected room type
- Handle different style variants
