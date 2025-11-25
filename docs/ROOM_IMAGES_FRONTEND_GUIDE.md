# Room Images Frontend Integration Guide

## Overview
Your backend is already configured to return room images. This guide shows you how to display them on the frontend.

---

## Backend Status ✅

### Already Implemented:
- ✅ `RoomType` model has `photo` field (CloudinaryField)
- ✅ `RoomTypeSerializer` includes `photo_url` field
- ✅ Public hotel API returns room images
- ✅ Admin panel supports image uploads
- ✅ Image preview in admin panel

**You're ready to display images on the frontend!**

---

## API Endpoints

### 1. Public Hotel Page
**Endpoint**: `GET /api/hotel/public/page/{slug}/`

**Response includes room_types with photos**:
```json
{
  "id": 1,
  "name": "Hotel Killarney",
  "slug": "hotel-killarney",
  "room_types": [
    {
      "code": "DLX",
      "name": "Deluxe Double Room",
      "short_description": "Spacious room with mountain views",
      "max_occupancy": 2,
      "bed_setup": "1 King Bed",
      "photo_url": "https://res.cloudinary.com/.../room.jpg",
      "starting_price_from": "129.00",
      "currency": "EUR",
      "booking_code": "",
      "booking_url": "",
      "availability_message": ""
    }
  ]
}
```

### 2. Availability Check
**Endpoint**: `GET /api/hotel/availability/{slug}/?check_in=2024-01-01&check_out=2024-01-03`

**Response includes photo field**:
```json
{
  "hotel": { ... },
  "search_params": { ... },
  "available_rooms": [
    {
      "room_type_name": "Deluxe Double Room",
      "photo": "https://res.cloudinary.com/.../room.jpg",
      "starting_price_from": "129.00",
      "is_available": true
    }
  ]
}
```

---

## Frontend Implementation

### React Component Example

```jsx
import React from 'react';

const RoomCard = ({ room }) => {
  return (
    <div className="room-card">
      {/* Room Image */}
      <div className="room-image-container">
        {room.photo_url ? (
          <img 
            src={room.photo_url} 
            alt={room.name}
            className="room-image"
            onError={(e) => {
              // Fallback image if URL fails
              e.target.src = '/images/room-placeholder.jpg';
            }}
          />
        ) : (
          <div className="room-image-placeholder">
            <span>No image available</span>
          </div>
        )}
      </div>

      {/* Room Details */}
      <div className="room-details">
        <h3 className="room-name">{room.name}</h3>
        
        <p className="room-description">
          {room.short_description}
        </p>

        <div className="room-specs">
          <span className="occupancy">
            👥 Up to {room.max_occupancy} guests
          </span>
          {room.bed_setup && (
            <span className="bed-setup">
              🛏️ {room.bed_setup}
            </span>
          )}
        </div>

        <div className="room-footer">
          <div className="price">
            <span className="from-label">From</span>
            <span className="price-amount">
              {room.currency} {room.starting_price_from}
            </span>
            <span className="per-night">/night</span>
          </div>
          
          <button className="book-btn">View Details</button>
        </div>
      </div>
    </div>
  );
};

export default RoomCard;
```

### CSS Styling Example

```css
.room-card {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
  background: white;
}

.room-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

.room-image-container {
  width: 100%;
  height: 240px;
  overflow: hidden;
  background: #f5f5f5;
}

.room-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.room-card:hover .room-image {
  transform: scale(1.05);
}

.room-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 14px;
}

.room-details {
  padding: 20px;
}

.room-name {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #2d3748;
}

.room-description {
  font-size: 14px;
  color: #718096;
  margin-bottom: 16px;
  line-height: 1.6;
}

.room-specs {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #4a5568;
}

.room-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.price {
  display: flex;
  flex-direction: column;
}

.from-label {
  font-size: 12px;
  color: #718096;
}

.price-amount {
  font-size: 24px;
  font-weight: 700;
  color: #2d3748;
}

.per-night {
  font-size: 12px;
  color: #718096;
}

.book-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}

.book-btn:hover {
  background: #5568d3;
}
```

### Full Page Example

```jsx
import React, { useEffect, useState } from 'react';
import RoomCard from './RoomCard';

const HotelPublicPage = ({ slug }) => {
  const [hotelData, setHotelData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/hotel/public/page/${slug}/`)
      .then(res => res.json())
      .then(data => {
        setHotelData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching hotel data:', error);
        setLoading(false);
      });
  }, [slug]);

  if (loading) return <div>Loading...</div>;
  if (!hotelData) return <div>Hotel not found</div>;

  return (
    <div className="hotel-page">
      {/* Hero Section */}
      <div className="hero">
        {hotelData.hero_image_url && (
          <img src={hotelData.hero_image_url} alt={hotelData.name} />
        )}
        <h1>{hotelData.name}</h1>
        <p>{hotelData.tagline}</p>
      </div>

      {/* Room Types Section */}
      <section className="rooms-section">
        <h2>Our Rooms & Suites</h2>
        <div className="rooms-grid">
          {hotelData.room_types?.map(room => (
            <RoomCard key={room.code} room={room} />
          ))}
        </div>
      </section>
    </div>
  );
};

export default HotelPublicPage;
```

---

## Adding Images via Django Admin

### Option 1: Upload Files
1. Go to Django Admin: `/admin/rooms/roomtype/`
2. Click on a room type
3. Scroll to "Room Details" section
4. Click "Choose File" next to Photo field
5. Upload your image
6. Click "Save"

### Option 2: Use Image URLs
1. Go to Django Admin
2. Click on a room type
3. In the Photo field, paste the image URL directly
4. Click "Save"

**Supported URL formats:**
- Cloudinary URLs
- Unsplash URLs
- Any publicly accessible image URL

---

## Using the Upload Script

### Quick Setup:

```python
# 1. Edit upload_room_images.py
HOTEL_SLUG = "hotel-killarney"

ROOM_IMAGES_URLS = {
    "Deluxe Double Room": "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800",
    "Standard Room": "https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=800",
    "Family Suite": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800",
}

# 2. Run the script
python upload_room_images.py
```

---

## Testing

### 1. Check API Response
```bash
# Test public page endpoint
curl http://localhost:8000/api/hotel/public/page/hotel-killarney/

# Check room_types array has photo_url field
```

### 2. Check in Browser
Visit: `http://localhost:8000/api/hotel/public/page/hotel-killarney/`

Look for:
```json
"room_types": [
  {
    "name": "...",
    "photo_url": "https://..."  // ← Should be present
  }
]
```

### 3. Test Frontend
- Open your React app
- Navigate to hotel public page
- Images should appear in room cards
- Test fallback for missing images

---

## Troubleshooting

### Images not showing on frontend?

**Check 1: API returns photo_url**
```bash
curl http://localhost:8000/api/hotel/public/page/YOUR-SLUG/
```
Look for `photo_url` in room_types array.

**Check 2: Image URL is valid**
- Copy the URL from API response
- Paste in browser address bar
- Image should load

**Check 3: CORS settings**
If using external images (Unsplash, etc), ensure CORS is configured.

**Check 4: Frontend code**
```jsx
// Make sure you're accessing the right field
room.photo_url  // ✅ Correct
room.photo      // ✅ Also works (availability endpoint)
room.image      // ❌ Wrong field name
```

### Images not uploading in admin?

**Check 1: Cloudinary configured**
In `settings.py`:
```python
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'your-cloud-name',
    'API_KEY': 'your-api-key',
    'API_SECRET': 'your-api-secret'
}
```

**Check 2: Check error logs**
```bash
python manage.py runserver
# Watch for upload errors
```

---

## Image Recommendations

### Optimal Dimensions:
- **Width**: 800-1200px
- **Height**: 600-800px
- **Aspect ratio**: 4:3 or 3:2
- **Format**: JPG or WebP
- **Size**: < 500KB per image

### Free Image Sources:
- **Unsplash**: https://unsplash.com/s/photos/hotel-room
- **Pexels**: https://www.pexels.com/search/hotel%20room/
- **Pixabay**: https://pixabay.com/images/search/hotel%20room/

---

## Summary

✅ **Backend is ready** - Models, serializers, and API are configured  
✅ **Admin panel works** - Can upload images via Django admin  
✅ **API returns images** - `photo_url` field is included  
✅ **Upload script available** - `upload_room_images.py` for bulk uploads

**Next steps:**
1. Add images to your room types (admin or script)
2. Implement frontend components (React example above)
3. Test API response includes `photo_url`
4. Style room cards with CSS

Your room images will automatically appear on the public hotel page once uploaded! 🎉
