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

## Staff Image Upload Endpoint

### Endpoint
**POST** `/api/staff/hotel/{hotel_slug}/hotel/staff/room-types/{id}/upload-image/`

**Authentication**: Required (Staff only)

**Important**: This endpoint uploads/updates the image for ONE specific room type only. Each room type has its own unique ID, so you can upload different images for each room.

### Request Options

**Option 1: File Upload (multipart/form-data)**
```javascript
const formData = new FormData();
formData.append("photo", fileInput.files[0]);

const response = await fetch(
  `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${roomTypeId}/upload-image/`,
  {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`
    },
    body: formData
  }
);
```

**Option 2: Image URL (application/json)**
```javascript
const response = await fetch(
  `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${roomTypeId}/upload-image/`,
  {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      photo_url: "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800"
    })
  }
);
```

### Response
```json
{
  "message": "Image uploaded successfully",
  "photo_url": "https://res.cloudinary.com/.../room.jpg"
}
```

### React Upload Component Example

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const RoomImageUploader = ({ roomTypeId, hotelSlug, currentImageUrl, onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [imageUrl, setImageUrl] = useState('');

  // Upload file - ONLY updates THIS specific room type (by roomTypeId)
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('photo', file);

    setUploading(true);
    try {
      // This URL targets ONE specific room type by ID
      const response = await axios.post(
        `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${roomTypeId}/upload-image/`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      
      onUploadSuccess(response.data.photo_url);
      alert('Image uploaded successfully!');
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload image');
    } finally {
      setUploading(false);
    }
  };

  // Save URL - ONLY updates THIS specific room type (by roomTypeId)
  const handleUrlSubmit = async (e) => {
    e.preventDefault();
    if (!imageUrl.trim()) return;

    setUploading(true);
    try {
      // This URL targets ONE specific room type by ID
      const response = await axios.post(
        `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${roomTypeId}/upload-image/`,
        { photo_url: imageUrl },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      onUploadSuccess(response.data.photo_url);
      setImageUrl('');
      alert('Image URL saved successfully!');
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to save image URL');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="image-uploader">
      <h4>Upload Room Image</h4>
      
      {/* Current Image Preview */}
      {currentImageUrl && (
        <div className="current-image">
          <img src={currentImageUrl} alt="Current" style={{ maxWidth: '200px' }} />
          <p>Current Image</p>
        </div>
      )}

      {/* File Upload */}
      <div className="upload-section">
        <label>
          <strong>Upload File:</strong>
          <input 
            type="file" 
            accept="image/*"
            onChange={handleFileUpload}
            disabled={uploading}
          />
        </label>
      </div>

      {/* URL Input */}
      <div className="url-section">
        <form onSubmit={handleUrlSubmit}>
          <label>
            <strong>Or use Image URL:</strong>
            <input
              type="url"
              placeholder="https://example.com/image.jpg"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              disabled={uploading}
            />
          </label>
          <button type="submit" disabled={uploading || !imageUrl.trim()}>
            {uploading ? 'Uploading...' : 'Save URL'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default RoomImageUploader;
```

### Full Staff Room Edit Modal Example

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const EditRoomTypeModal = ({ roomType, hotelSlug, onClose, onUpdate }) => {
  const [formData, setFormData] = useState({
    name: roomType?.name || '',
    code: roomType?.code || '',
    short_description: roomType?.short_description || '',
    max_occupancy: roomType?.max_occupancy || 2,
    bed_setup: roomType?.bed_setup || '',
    starting_price_from: roomType?.starting_price_from || '',
    currency: roomType?.currency || 'EUR',
  });
  
  const [photoFile, setPhotoFile] = useState(null);
  const [photoUrl, setPhotoUrl] = useState('');
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  
  const isNewRoom = !roomType?.id;

  // Step 1: Save room data first
  const handleSaveRoom = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      const url = isNewRoom
        ? `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/`
        : `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${roomType.id}/`;
      
      const method = isNewRoom ? 'post' : 'put';
      
      const response = await axios[method](url, formData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      const savedRoom = response.data;
      
      // Step 2: If image was selected, upload it separately
      if (photoFile || photoUrl) {
        await handleUploadImage(savedRoom.id);
      } else {
        onUpdate(savedRoom);
        alert('Room saved successfully!');
        onClose();
      }
    } catch (error) {
      console.error('Failed to save room:', error);
      alert('Failed to save room');
    } finally {
      setSaving(false);
    }
  };

  // Step 2: Upload image AFTER room is saved
  const handleUploadImage = async (roomId) => {
    setUploading(true);
    
    try {
      let response;
      
      // Option A: Upload file
      if (photoFile) {
        const formData = new FormData();
        formData.append('photo', photoFile);
        
        response = await axios.post(
          `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${roomId}/upload-image/`,
          formData,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'multipart/form-data'
            }
          }
        );
      }
      // Option B: Save URL
      else if (photoUrl) {
        response = await axios.post(
          `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${roomId}/upload-image/`,
          { photo_url: photoUrl },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json'
            }
          }
        );
      }

      if (response) {
        alert('Room and image saved successfully!');
        onUpdate({ ...formData, id: roomId, photo_url: response.data.photo_url });
        onClose();
      }
    } catch (error) {
      console.error('Failed to upload image:', error);
      alert('Room saved but image upload failed. You can try uploading the image again.');
      onClose();
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>{isNewRoom ? 'Add Room Type' : 'Edit Room Type'}</h2>
        
        <form onSubmit={handleSaveRoom}>
          {/* Room Name */}
          <div className="form-group">
            <label>Room Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>

          {/* Room Code */}
          <div className="form-group">
            <label>Room Code *</label>
            <input
              type="text"
              value={formData.code}
              onChange={(e) => setFormData({...formData, code: e.target.value})}
              disabled={!isNewRoom} // Can't change after creation
              required
            />
          </div>

          {/* Short Description */}
          <div className="form-group">
            <label>Short Description</label>
            <textarea
              value={formData.short_description}
              onChange={(e) => setFormData({...formData, short_description: e.target.value})}
              rows={3}
            />
          </div>

          {/* Room Photo - Will be uploaded AFTER save */}
          <div className="form-group">
            <label>Room Photo</label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                setPhotoFile(e.target.files[0]);
                setPhotoUrl(''); // Clear URL if file selected
              }}
            />
            <span>or enter URL below</span>
            <input
              type="url"
              placeholder="https://example.com/room-photo.jpg"
              value={photoUrl}
              onChange={(e) => {
                setPhotoUrl(e.target.value);
                setPhotoFile(null); // Clear file if URL entered
              }}
            />
            {roomType?.photo_url && !photoFile && !photoUrl && (
              <div className="current-image">
                <img src={roomType.photo_url} alt="Current" style={{maxWidth: '200px'}} />
                <p>Current image (will remain unchanged if no new image provided)</p>
              </div>
            )}
          </div>

          {/* Max Occupancy */}
          <div className="form-group">
            <label>Max Occupancy</label>
            <input
              type="number"
              min="1"
              value={formData.max_occupancy}
              onChange={(e) => setFormData({...formData, max_occupancy: parseInt(e.target.value)})}
            />
          </div>

          {/* Bed Setup */}
          <div className="form-group">
            <label>Bed Setup</label>
            <input
              type="text"
              placeholder="e.g., 1 King Bed"
              value={formData.bed_setup}
              onChange={(e) => setFormData({...formData, bed_setup: e.target.value})}
            />
          </div>

          {/* Starting Price */}
          <div className="form-group">
            <label>Starting Price (per night)</label>
            <input
              type="number"
              step="0.01"
              value={formData.starting_price_from}
              onChange={(e) => setFormData({...formData, starting_price_from: e.target.value})}
            />
          </div>

          {/* Currency */}
          <div className="form-group">
            <label>Currency</label>
            <select
              value={formData.currency}
              onChange={(e) => setFormData({...formData, currency: e.target.value})}
            >
              <option value="EUR">EUR (€)</option>
              <option value="USD">USD ($)</option>
              <option value="GBP">GBP (£)</option>
            </select>
          </div>

          {/* Action Buttons */}
          <div className="modal-actions">
            <button type="button" onClick={onClose} disabled={saving || uploading}>
              Cancel
            </button>
            <button type="submit" disabled={saving || uploading}>
              {saving ? 'Saving...' : uploading ? 'Uploading Image...' : 'Save Room'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditRoomTypeModal;
```

**Key Points:**
- ✅ **Step 1**: Save room data first (POST/PUT to `/room-types/`)
- ✅ **Step 2**: Upload image separately (POST to `/room-types/{id}/upload-image/`)
- ✅ Room must have an ID before image upload
- ✅ Each room type has its own unique ID
- ✅ Only the selected room's image is updated
- ✅ Other rooms remain unchanged

**Workflow:**
```
1. User fills out room form (name, price, etc.)
2. User clicks "Save Room"
   → POST/PUT to /api/staff/hotel/{slug}/hotel/staff/room-types/
   → Backend returns room with ID
3. If user selected an image:
   → POST to /api/staff/hotel/{slug}/hotel/staff/room-types/{id}/upload-image/
   → Upload completes
4. Room is saved with image!
```

**Why Two Steps?**
- The room must exist (have an ID) before you can upload an image
- Image upload endpoint requires: `/room-types/{id}/upload-image/`
- Can't upload to an ID that doesn't exist yet

**Example for Hotel Killarney:**
- Deluxe Double Room (ID: 1) → `/room-types/1/upload-image/`
- Standard Room (ID: 10) → `/room-types/10/upload-image/`
- Family Suite (ID: 2) → `/room-types/2/upload-image/`

Each upload affects ONLY that specific room type! 🎯

---

## Frontend Implementation

### Public Page - Room Card Display

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

## Common Frontend Errors & Fixes

### Error: `/room-types/undefined/` - 404 Not Found

**Problem**: The room ID is `undefined` in the API call.

**Cause**: Your frontend is trying to upload/update before the room is saved, or the room ID isn't being passed correctly.

**Fix:**

```jsx
// ❌ WRONG - Using undefined ID
const handleSave = async () => {
  // Room not saved yet, no ID exists
  await uploadImage(roomType.id); // ← roomType.id is undefined!
};

// ✅ CORRECT - Save room first, then use returned ID
const handleSave = async () => {
  // Step 1: Save room and get ID back
  const response = await axios.post(
    `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/`,
    roomData
  );
  
  const newRoomId = response.data.id; // ← Get ID from response
  
  // Step 2: Now upload image with that ID
  if (photoFile || photoUrl) {
    await uploadImage(newRoomId); // ← Use the actual ID
  }
};

// ✅ CORRECT - For editing existing rooms
const handleUpdate = async () => {
  // Make sure room.id exists before using it
  if (!room?.id) {
    console.error('Room ID is missing!');
    return;
  }
  
  await axios.patch(
    `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${room.id}/`,
    roomData
  );
};
```

**Debugging checklist:**
```javascript
// Before making API call, verify:
console.log('Room ID:', roomType.id); // Should be a number, not undefined
console.log('Hotel Slug:', hotelSlug); // Should be a string
console.log('Full URL:', `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${roomType.id}/`);

// If ID is undefined:
// 1. Check if room was saved first
// 2. Check if you're using the response from save
// 3. Check if the correct prop is being passed to component
```

---

### Error: "Encountered two children with the same key"

**Problem**: React warning about duplicate or empty keys in lists.

**Root Cause**: The backend was not returning `id` field in the public RoomTypeSerializer.

**Backend Fix Applied**: ✅ Added `id` to `RoomTypeSerializer` fields list.

**Frontend Defensive Coding:**

```jsx
// ❌ WRONG - Missing or duplicate keys
{rooms.map(room => (
  <div>  {/* No key! */}
    {room.name}
  </div>
))}

// ❌ WRONG - Using empty code as key
{rooms.map(room => (
  <div key={room.code}>  {/* code might be empty string "" */}
    {room.name}
  </div>
))}

// ✅ CORRECT - Use unique ID with fallback
{rooms.map((room, index) => (
  <div key={room.id || `room-fallback-${index}`}>
    {room.name}
  </div>
))}

// ✅ BEST - Filter out invalid data + use ID
{rooms
  .filter(room => room.id && room.name)  // Remove incomplete items
  .map(room => (
    <div key={room.id}>
      {room.name}
    </div>
  ))
}

// ✅ CORRECT - Defensive with multiple identifiers
{rooms.map((room, index) => (
  <div key={room.id || room.code || `temp-${index}`}>
    <h3>{room.name || 'Unnamed Room'}</h3>
    {room.amenities?.map(amenity => (
      <span key={`amenity-${room.id}-${amenity.id || amenity.name}`}>
        {amenity.name}
      </span>
    ))}
  </div>
))}
```

**Defensive Data Validation:**

```jsx
// Validate data when it arrives from API
useEffect(() => {
  fetchRoomTypes().then(data => {
    // Filter out incomplete rooms
    const validRooms = data.filter(room => {
      if (!room.id) {
        console.warn('Room missing ID:', room);
        return false;
      }
      if (!room.name) {
        console.warn('Room missing name:', room);
        return false;
      }
      return true;
    });
    
    setRoomTypes(validRooms);
  });
}, []);

// Or add default values
const normalizeRoomData = (rooms) => {
  return rooms.map((room, index) => ({
    id: room.id || `temp-${Date.now()}-${index}`,
    code: room.code || '',
    name: room.name || 'Unnamed Room',
    short_description: room.short_description || '',
    max_occupancy: room.max_occupancy || 2,
    bed_setup: room.bed_setup || '',
    photo_url: room.photo_url || null,
    starting_price_from: room.starting_price_from || '0.00',
    currency: room.currency || 'EUR',
    ...room
  }));
};
```

**Common scenarios:**

```jsx
// Gallery images with indices
{galleryImages.map((img, idx) => (
  <div key={`gallery-${idx}`}>  {/* Use descriptive prefix */}
    <img src={img} alt={`Gallery ${idx + 1}`} />
  </div>
))}

// Conditional rendering - both branches need keys
{isEditing ? (
  <EditForm key="edit-form" />  {/* ← Key here */}
) : (
  <DisplayView key="display-view" />  {/* ← And here */}
)}
```

---

### Error: "Please save the room first, then you can upload an image"

**Problem**: Your backend validation is preventing image upload.

**Solution**: This is the **correct workflow**. Follow this order:

```jsx
const handleSubmit = async (e) => {
  e.preventDefault();
  
  try {
    // 1️⃣ Save room data first
    const method = isNewRoom ? 'post' : 'patch';
    const url = isNewRoom 
      ? `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/`
      : `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${roomId}/`;
    
    const roomResponse = await axios[method](url, {
      name: formData.name,
      code: formData.code,
      short_description: formData.description,
      max_occupancy: formData.maxOccupancy,
      bed_setup: formData.bedSetup,
      starting_price_from: formData.price,
      currency: formData.currency
    });
    
    const savedRoomId = roomResponse.data.id;
    console.log('✓ Room saved with ID:', savedRoomId);
    
    // 2️⃣ Now upload image if one was selected
    if (photoFile || photoUrl) {
      console.log('Uploading image for room ID:', savedRoomId);
      
      const formData = new FormData();
      if (photoFile) {
        formData.append('photo', photoFile);
      } else {
        formData.append('photo_url', photoUrl);
      }
      
      await axios.post(
        `/api/staff/hotel/${hotelSlug}/hotel/staff/room-types/${savedRoomId}/upload-image/`,
        formData
      );
      
      console.log('✓ Image uploaded successfully');
    }
    
    alert('Room saved successfully!');
    onSuccess();
    
  } catch (error) {
    console.error('Error:', error.response?.data || error);
    alert('Failed to save room');
  }
};
```

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
