# Hotel Images Frontend Integration Guide

## Overview
This guide explains how to fetch and display hotel images (hero images, room photos, offer photos, and activity images) from the backend API.

---

## Image Storage & URLs

### Cloudinary Integration
All images are stored on **Cloudinary** and served via CDN URLs.

### URL Format
Images are returned as complete URLs in the API responses:
```
https://res.cloudinary.com/YOUR_CLOUD_NAME/image/upload/...
```

**Important**: You do NOT need to construct these URLs manually. The backend returns fully-formed URLs ready to use in `<img>` tags.

---

## Environment Variables Setup

### Backend `.env` Configuration
The backend requires these Cloudinary settings:

```env
# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### How to Get Cloudinary Credentials
1. Sign up at [cloudinary.com](https://cloudinary.com)
2. Go to Dashboard
3. Copy:
   - **Cloud Name**
   - **API Key**
   - **API Secret**

### Frontend Environment Variables
The frontend typically does NOT need Cloudinary credentials since images are served via public URLs from the API.

However, if you need the base URL for any reason:
```env
# Optional - only if needed for direct Cloudinary operations
VITE_CLOUDINARY_CLOUD_NAME=your_cloud_name
```

---

## API Endpoints for Images

### 1. Hotel Hero Image & Basic Info
**Endpoint**: `GET /api/guest/hotels/<hotel_slug>/site/home/`

**Response Example**:
```json
{
  "hotel": {
    "id": 2,
    "name": "The Ross Hotel",
    "slug": "ross",
    "hero_image": "https://res.cloudinary.com/.../hero_image.jpg",
    "description": "Luxury hotel in Killarney...",
    "address": "Town Centre, Killarney",
    "phone": "+353 64 123 4567",
    "email": "info@rosshotel.ie"
  }
}
```

**Frontend Usage**:
```jsx
// React Example
const [hotelData, setHotelData] = useState(null);

useEffect(() => {
  fetch(`/api/guest/hotels/${hotelSlug}/site/home/`)
    .then(res => res.json())
    .then(data => setHotelData(data));
}, [hotelSlug]);

// Display hero image
{hotelData?.hotel?.hero_image && (
  <img 
    src={hotelData.hotel.hero_image} 
    alt={hotelData.hotel.name}
    className="hero-image"
  />
)}
```

---

### 2. Room Types with Photos
**Endpoint**: `GET /api/guest/hotels/<hotel_slug>/site/rooms/`

**Response Example**:
```json
{
  "rooms": [
    {
      "id": 1,
      "name": "Deluxe King Room",
      "code": "DLX-KING",
      "photo": "https://res.cloudinary.com/.../deluxe_king.jpg",
      "description": "Spacious room with king bed...",
      "base_price": "150.00",
      "max_occupancy": 2,
      "amenities": ["WiFi", "TV", "Mini Bar"]
    },
    {
      "id": 2,
      "name": "Superior Suite",
      "code": "SUP-SUITE",
      "photo": "https://res.cloudinary.com/.../superior_suite.jpg",
      "description": "Luxury suite with separate living area...",
      "base_price": "250.00",
      "max_occupancy": 4,
      "amenities": ["WiFi", "TV", "Mini Bar", "Balcony"]
    }
  ]
}
```

**Frontend Usage**:
```jsx
// Display room cards with images
{rooms.map(room => (
  <div key={room.id} className="room-card">
    {room.photo && (
      <img 
        src={room.photo} 
        alt={room.name}
        className="room-image"
      />
    )}
    <h3>{room.name}</h3>
    <p>{room.description}</p>
    <p className="price">From €{room.base_price}/night</p>
  </div>
))}
```

---

### 3. Special Offers with Photos
**Endpoint**: `GET /api/guest/hotels/<hotel_slug>/site/offers/`

**Response Example**:
```json
{
  "offers": [
    {
      "id": 1,
      "title": "Early Bird Special",
      "photo": "https://res.cloudinary.com/.../early_bird.jpg",
      "description": "Book 30 days in advance and save 20%",
      "discount_percentage": "20.00",
      "valid_from": "2025-01-01",
      "valid_until": "2025-12-31",
      "is_active": true
    },
    {
      "id": 2,
      "title": "Weekend Getaway",
      "photo": "https://res.cloudinary.com/.../weekend.jpg",
      "description": "Special weekend rates",
      "discount_percentage": "15.00",
      "valid_from": "2025-01-01",
      "valid_until": "2025-12-31",
      "is_active": true
    }
  ]
}
```

**Frontend Usage**:
```jsx
// Display offer cards
{offers.map(offer => (
  <div key={offer.id} className="offer-card">
    {offer.photo && (
      <img 
        src={offer.photo} 
        alt={offer.title}
        className="offer-image"
      />
    )}
    <div className="offer-badge">{offer.discount_percentage}% OFF</div>
    <h3>{offer.title}</h3>
    <p>{offer.description}</p>
    <p className="validity">
      Valid: {offer.valid_from} to {offer.valid_until}
    </p>
  </div>
))}
```

---

### 4. Leisure Activities with Images
**Endpoint**: `GET /api/guest/hotels/<hotel_slug>/site/activities/` *(if implemented)*

**Expected Response**:
```json
{
  "activities": [
    {
      "id": 1,
      "name": "Spa & Wellness",
      "image": "https://res.cloudinary.com/.../spa.jpg",
      "description": "Relax in our luxury spa...",
      "category": "wellness"
    },
    {
      "id": 2,
      "name": "Golf Course",
      "image": "https://res.cloudinary.com/.../golf.jpg",
      "description": "18-hole championship course...",
      "category": "sports"
    }
  ]
}
```

---

## Image Display Best Practices

### 1. Fallback Images
Always handle missing images gracefully:

```jsx
const defaultImage = '/assets/placeholder.jpg';

<img 
  src={room.photo || defaultImage}
  alt={room.name}
  onError={(e) => { e.target.src = defaultImage; }}
/>
```

### 2. Lazy Loading
Use lazy loading for better performance:

```jsx
<img 
  src={room.photo}
  alt={room.name}
  loading="lazy"
/>
```

### 3. Responsive Images
Use CSS for responsive display:

```css
.room-image {
  width: 100%;
  height: 250px;
  object-fit: cover;
  border-radius: 8px;
}

.hero-image {
  width: 100%;
  height: 400px;
  object-fit: cover;
}

@media (max-width: 768px) {
  .hero-image {
    height: 250px;
  }
}
```

### 4. Image Optimization
Cloudinary URLs support transformation parameters. If needed, you can optimize images:

```javascript
// Example: Add transformations to Cloudinary URL
const optimizeImage = (url, width = 800, quality = 80) => {
  if (!url?.includes('cloudinary.com')) return url;
  
  const parts = url.split('/upload/');
  return `${parts[0]}/upload/w_${width},q_${quality},f_auto/${parts[1]}`;
};

// Usage
<img src={optimizeImage(room.photo, 400)} alt={room.name} />
```

---

## Complete Frontend Example

### React Component Example
```jsx
import { useState, useEffect } from 'react';

function HotelPage({ hotelSlug }) {
  const [hotel, setHotel] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`/api/guest/hotels/${hotelSlug}/site/home/`).then(r => r.json()),
      fetch(`/api/guest/hotels/${hotelSlug}/site/rooms/`).then(r => r.json()),
      fetch(`/api/guest/hotels/${hotelSlug}/site/offers/`).then(r => r.json())
    ])
    .then(([homeData, roomsData, offersData]) => {
      setHotel(homeData.hotel);
      setRooms(roomsData.rooms);
      setOffers(offersData.offers);
      setLoading(false);
    })
    .catch(error => {
      console.error('Error fetching hotel data:', error);
      setLoading(false);
    });
  }, [hotelSlug]);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="hotel-page">
      {/* Hero Section */}
      <section className="hero">
        {hotel?.hero_image && (
          <img 
            src={hotel.hero_image} 
            alt={hotel.name}
            className="hero-image"
          />
        )}
        <div className="hero-content">
          <h1>{hotel?.name}</h1>
          <p>{hotel?.description}</p>
        </div>
      </section>

      {/* Offers Section */}
      <section className="offers">
        <h2>Special Offers</h2>
        <div className="offers-grid">
          {offers.map(offer => (
            <div key={offer.id} className="offer-card">
              {offer.photo && (
                <img 
                  src={offer.photo} 
                  alt={offer.title}
                  loading="lazy"
                />
              )}
              <div className="discount-badge">
                {offer.discount_percentage}% OFF
              </div>
              <h3>{offer.title}</h3>
              <p>{offer.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Rooms Section */}
      <section className="rooms">
        <h2>Our Rooms</h2>
        <div className="rooms-grid">
          {rooms.map(room => (
            <div key={room.id} className="room-card">
              {room.photo && (
                <img 
                  src={room.photo} 
                  alt={room.name}
                  loading="lazy"
                />
              )}
              <h3>{room.name}</h3>
              <p>{room.description}</p>
              <p className="price">From €{room.base_price}/night</p>
              <button>Book Now</button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default HotelPage;
```

---

## Testing Image Display

### Backend Shell Commands
Check what images are available for a hotel:

```bash
python manage.py shell -c "
from hotel.models import Hotel, Offer, LeisureActivity
from rooms.models import RoomType

h = Hotel.objects.get(slug='ross')

print(f'Hero Image: {h.hero_image.url if h.hero_image else \"None\"}')
print(f'\nRoom Types:')
[print(f'  - {r.name}: {r.photo.url if r.photo else \"No photo\"}') 
 for r in RoomType.objects.filter(hotel=h)]
print(f'\nOffers:')
[print(f'  - {o.title}: {o.photo.url if o.photo else \"No photo\"}') 
 for o in Offer.objects.filter(hotel=h)]
"
```

### API Testing with curl
```bash
# Test hero image endpoint
curl http://localhost:8000/api/guest/hotels/ross/site/home/

# Test rooms with photos
curl http://localhost:8000/api/guest/hotels/ross/site/rooms/

# Test offers with photos
curl http://localhost:8000/api/guest/hotels/ross/site/offers/
```

---

## Troubleshooting

### Issue: Images not loading
**Possible causes**:
1. Cloudinary credentials not set in backend `.env`
2. Images not uploaded to Cloudinary
3. CORS issues (if frontend on different domain)

**Solution**:
```python
# settings.py - Add CORS headers for Cloudinary
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite default
]
```

### Issue: Broken image URLs
**Check**:
1. Backend: `python manage.py shell` - verify `hotel.hero_image.url` returns valid URL
2. Cloudinary dashboard - confirm images are uploaded
3. Network tab - check actual URL being requested

### Issue: Images too slow to load
**Solutions**:
1. Use Cloudinary transformations for smaller sizes
2. Implement lazy loading
3. Add loading placeholders/skeletons
4. Consider using WebP format: Add `f_auto` to Cloudinary URLs

---

## Summary Checklist

- [ ] Backend `.env` has Cloudinary credentials configured
- [ ] Images uploaded to Cloudinary via Django admin
- [ ] API endpoints return complete image URLs
- [ ] Frontend fetches data from `/api/guest/hotels/<slug>/site/...`
- [ ] Images displayed with proper fallbacks
- [ ] Lazy loading implemented
- [ ] Responsive CSS applied
- [ ] Error handling in place

---

## Support

For issues:
1. Check backend logs for Cloudinary connection errors
2. Verify image URLs in API responses
3. Check browser console for frontend errors
4. Review Cloudinary dashboard for uploaded images

**Backend repo**: [HotelMateBackend](https://github.com/nlekkerman/HotelMateBackend)
