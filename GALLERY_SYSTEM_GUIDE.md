# Gallery System - Complete Integration Guide

## 🎨 Overview

The gallery system allows hotels to organize images into multiple collections (Rooms, Facilities, Dining, Spa, etc.) with captions and custom ordering. Images are saved to the public Hotel model and displayed on the public hotel page.

---

## 📊 Database Models

### **Gallery Model**
Organizes images into named collections by category.

**Fields:**
- `hotel` - ForeignKey to Hotel
- `name` - Gallery name (e.g., "Luxury Rooms", "Pool Area")
- `category` - Choice field: `rooms`, `facilities`, `dining`, `spa`, `events`, `exterior`, `activities`, `other`
- `description` - Optional text description
- `is_active` - Boolean (show on public page)
- `display_order` - Integer for sorting
- `created_at`, `updated_at` - Timestamps

### **GalleryImage Model**
Individual images with metadata within a gallery.

**Fields:**
- `gallery` - ForeignKey to Gallery
- `image` - CloudinaryField
- `caption` - Image description (255 chars)
- `alt_text` - Accessibility text (255 chars)
- `display_order` - Integer for sorting
- `is_featured` - Boolean (use as gallery thumbnail)
- `uploaded_at` - Timestamp

---

## 🔌 API Endpoints

### **Gallery Management**

#### List All Galleries
```http
GET /api/staff/hotel/<hotel_slug>/galleries/
```

**Response:**
```json
[
  {
    "id": 1,
    "hotel": 2,
    "hotel_slug": "killarney",
    "name": "Luxury Rooms",
    "category": "rooms",
    "description": "Our premium accommodation options",
    "is_active": true,
    "display_order": 1,
    "image_count": 5,
    "images": [
      {
        "id": 1,
        "image": "https://res.cloudinary.com/...",
        "image_url": "https://res.cloudinary.com/...",
        "caption": "King Suite with Ocean View",
        "alt_text": "Spacious room with king bed",
        "display_order": 0,
        "is_featured": true,
        "uploaded_at": "2025-11-25T10:00:00Z"
      }
    ],
    "created_at": "2025-11-25T09:00:00Z",
    "updated_at": "2025-11-25T10:00:00Z"
  }
]
```

#### Create New Gallery
```http
POST /api/staff/hotel/<hotel_slug>/galleries/
Content-Type: application/json

{
  "name": "Spa & Wellness",
  "category": "spa",
  "description": "Relax and rejuvenate",
  "is_active": true,
  "display_order": 2
}
```

#### Get Single Gallery
```http
GET /api/staff/hotel/<hotel_slug>/galleries/<gallery_id>/
```

#### Update Gallery
```http
PATCH /api/staff/hotel/<hotel_slug>/galleries/<gallery_id>/
Content-Type: application/json

{
  "name": "Updated Name",
  "is_active": false
}
```

#### Delete Gallery
```http
DELETE /api/staff/hotel/<hotel_slug>/galleries/<gallery_id>/
```

---

### **Image Management**

#### Upload Image to Gallery
```http
POST /api/staff/hotel/<hotel_slug>/galleries/<gallery_id>/upload_image/
Content-Type: multipart/form-data

Form Fields:
- image: [File]
- caption: "King Suite with Ocean View"
- alt_text: "Spacious king bed suite"
- display_order: 0
- is_featured: true
```

**Response:**
```json
{
  "id": 1,
  "image": "image/upload/v1234567890/hotels/killarney/gallery/abc123.jpg",
  "image_url": "https://res.cloudinary.com/.../abc123.jpg",
  "caption": "King Suite with Ocean View",
  "alt_text": "Spacious king bed suite",
  "display_order": 0,
  "is_featured": true,
  "uploaded_at": "2025-11-25T10:05:00Z"
}
```

#### Reorder Images in Gallery
```http
POST /api/staff/hotel/<hotel_slug>/galleries/<gallery_id>/reorder_images/
Content-Type: application/json

{
  "image_ids": [3, 1, 5, 2]
}
```

#### List All Images
```http
GET /api/staff/hotel/<hotel_slug>/gallery-images/
```

#### Update Image Details
```http
PATCH /api/staff/hotel/<hotel_slug>/gallery-images/<image_id>/
Content-Type: application/json

{
  "caption": "Updated caption",
  "alt_text": "Updated alt text",
  "display_order": 2,
  "is_featured": false
}
```

#### Delete Image
```http
DELETE /api/staff/hotel/<hotel_slug>/gallery-images/<image_id>/
```

---

## 🔴 Real-Time Updates with Pusher

### **Channel:**
```javascript
const channel = pusher.subscribe(`hotel-${hotelSlug}`);
```

### **Gallery Events:**

#### `gallery-updated`
Triggered when:
- Image is uploaded to gallery
- Images are reordered
- Image is removed from gallery

**Payload:**
```json
{
  "gallery_id": 1,
  "gallery_name": "Luxury Rooms",
  "action": "image_added",  // or "images_reordered", "image_removed"
  "image_count": 6
}
```

### **Frontend Implementation:**

```javascript
import Pusher from 'pusher-js';

// Initialize Pusher
const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
  cluster: process.env.VITE_PUSHER_CLUSTER,
});

const hotelSlug = 'killarney';
const channel = pusher.subscribe(`hotel-${hotelSlug}`);

// Listen for gallery updates
channel.bind('gallery-updated', (data) => {
  console.log('Gallery updated:', data);
  
  const { gallery_id, gallery_name, action, image_count } = data;
  
  switch(action) {
    case 'image_added':
      // Refresh gallery or add image to state
      refreshGallery(gallery_id);
      break;
      
    case 'images_reordered':
      // Re-fetch gallery images
      refreshGallery(gallery_id);
      break;
      
    case 'image_removed':
      // Update image count or refresh
      updateGalleryImageCount(gallery_id, image_count);
      break;
  }
});

// Cleanup on unmount
return () => {
  channel.unbind_all();
  pusher.unsubscribe(`hotel-${hotelSlug}`);
};
```

---

## 📱 Frontend Integration

### **React Hook for Gallery Management**

```javascript
import { useState, useEffect } from 'react';
import Pusher from 'pusher-js';

export const useHotelGalleries = (hotelSlug) => {
  const [galleries, setGalleries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch galleries
  const fetchGalleries = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/staff/hotel/${hotelSlug}/galleries/`);
      const data = await response.json();
      setGalleries(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Create gallery
  const createGallery = async (galleryData) => {
    const response = await fetch(`/api/staff/hotel/${hotelSlug}/galleries/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(galleryData)
    });
    const newGallery = await response.json();
    setGalleries([...galleries, newGallery]);
    return newGallery;
  };

  // Upload image
  const uploadImage = async (galleryId, imageFile, caption, altText) => {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('caption', caption);
    formData.append('alt_text', altText);
    formData.append('display_order', 0);
    
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/galleries/${galleryId}/upload_image/`,
      { method: 'POST', body: formData }
    );
    
    return await response.json();
  };

  // Delete image
  const deleteImage = async (imageId) => {
    await fetch(`/api/staff/hotel/${hotelSlug}/gallery-images/${imageId}/`, {
      method: 'DELETE'
    });
  };

  // Update image caption
  const updateImage = async (imageId, updates) => {
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/gallery-images/${imageId}/`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      }
    );
    return await response.json();
  };

  // Reorder images
  const reorderImages = async (galleryId, imageIds) => {
    await fetch(
      `/api/staff/hotel/${hotelSlug}/galleries/${galleryId}/reorder_images/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_ids: imageIds })
      }
    );
  };

  // Real-time updates
  useEffect(() => {
    fetchGalleries();

    // Setup Pusher
    const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
      cluster: process.env.VITE_PUSHER_CLUSTER,
    });

    const channel = pusher.subscribe(`hotel-${hotelSlug}`);

    channel.bind('gallery-updated', (data) => {
      console.log('Gallery updated in real-time:', data);
      // Refresh galleries
      fetchGalleries();
    });

    return () => {
      channel.unbind_all();
      pusher.unsubscribe(`hotel-${hotelSlug}`);
    };
  }, [hotelSlug]);

  return {
    galleries,
    loading,
    error,
    createGallery,
    uploadImage,
    deleteImage,
    updateImage,
    reorderImages,
    refreshGalleries: fetchGalleries
  };
};
```

### **Gallery Management Component (Settings)**

```jsx
import { useHotelGalleries } from './hooks/useHotelGalleries';

function GalleryManager({ hotelSlug }) {
  const {
    galleries,
    loading,
    createGallery,
    uploadImage,
    deleteImage,
    updateImage
  } = useHotelGalleries(hotelSlug);

  const [selectedGallery, setSelectedGallery] = useState(null);

  const handleCreateGallery = async () => {
    await createGallery({
      name: 'New Gallery',
      category: 'other',
      description: '',
      is_active: true,
      display_order: galleries.length
    });
  };

  const handleUploadImage = async (galleryId, file) => {
    const caption = prompt('Enter image caption:');
    if (caption) {
      await uploadImage(galleryId, file, caption, caption);
    }
  };

  if (loading) return <div>Loading galleries...</div>;

  return (
    <div className="gallery-manager">
      <header>
        <h2>Gallery Management</h2>
        <button onClick={handleCreateGallery}>Create Gallery</button>
      </header>

      <div className="gallery-list">
        {galleries.map(gallery => (
          <div key={gallery.id} className="gallery-item">
            <h3>{gallery.name}</h3>
            <p>Category: {gallery.category}</p>
            <p>{gallery.image_count} images</p>
            
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handleUploadImage(gallery.id, e.target.files[0])}
            />

            <div className="gallery-images">
              {gallery.images.map(image => (
                <div key={image.id} className="image-item">
                  <img src={image.image_url} alt={image.alt_text} />
                  <input
                    value={image.caption}
                    onChange={(e) => updateImage(image.id, { 
                      caption: e.target.value 
                    })}
                    placeholder="Caption"
                  />
                  <button onClick={() => deleteImage(image.id)}>
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### **Public Gallery Display Component**

```jsx
import { useState, useEffect } from 'react';

function PublicGallerySection({ hotelSlug }) {
  const [galleries, setGalleries] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    fetch(`/api/staff/hotel/${hotelSlug}/galleries/`)
      .then(res => res.json())
      .then(data => {
        // Filter active galleries only
        const active = data.filter(g => g.is_active);
        setGalleries(active);
      });
  }, [hotelSlug]);

  const filteredGalleries = selectedCategory === 'all'
    ? galleries
    : galleries.filter(g => g.category === selectedCategory);

  return (
    <section className="public-galleries">
      <h2>Explore Our Hotel</h2>

      {/* Category Filter */}
      <div className="category-filters">
        <button onClick={() => setSelectedCategory('all')}>All</button>
        <button onClick={() => setSelectedCategory('rooms')}>Rooms</button>
        <button onClick={() => setSelectedCategory('facilities')}>Facilities</button>
        <button onClick={() => setSelectedCategory('dining')}>Dining</button>
        <button onClick={() => setSelectedCategory('spa')}>Spa</button>
      </div>

      {/* Galleries */}
      {filteredGalleries.map(gallery => (
        <div key={gallery.id} className="gallery-section">
          <h3>{gallery.name}</h3>
          <p>{gallery.description}</p>

          <div className="image-grid">
            {gallery.images.map(image => (
              <figure key={image.id}>
                <img
                  src={image.image_url}
                  alt={image.alt_text || image.caption}
                  loading="lazy"
                />
                {image.caption && (
                  <figcaption>{image.caption}</figcaption>
                )}
              </figure>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}
```

---

## 🎯 Complete Workflow

### **Staff Workflow:**

1. **Create Gallery**
   - Go to Settings → Galleries
   - Click "Create Gallery"
   - Enter name, select category, add description
   - Save

2. **Upload Images**
   - Select gallery
   - Click "Upload Image"
   - Choose file, add caption and alt text
   - Upload

3. **Manage Images**
   - Edit captions directly
   - Drag to reorder (calls reorder_images endpoint)
   - Delete unwanted images
   - Mark one as featured for gallery thumbnail

4. **Organize Galleries**
   - Create multiple galleries by category
   - Reorder galleries by display_order
   - Toggle is_active to show/hide on public page

### **Public Display:**

- Fetch all active galleries
- Display by category tabs or sections
- Show images in order with captions
- Use featured image as gallery thumbnail
- Responsive image grid/carousel

---

## ✅ Real-Time Features

- ✅ Upload image → Pusher broadcasts `gallery-updated` → UI updates
- ✅ Delete image → Pusher broadcasts `gallery-updated` → UI refreshes
- ✅ Reorder images → Pusher broadcasts `gallery-updated` → UI updates
- ✅ Multi-user editing → All staff see changes instantly

---

## 🔒 Permissions

All gallery endpoints require:
- `IsAuthenticated` - User must be logged in
- `IsStaffMember` - User must have staff profile
- `IsSameHotel` - Staff can only manage their own hotel's galleries

---

## 📋 Categories Available

- `rooms` - Room types and accommodations
- `facilities` - Hotel facilities and amenities
- `dining` - Restaurant, bar, dining areas
- `spa` - Spa, wellness, fitness
- `events` - Event spaces, conferences
- `exterior` - Building exterior, grounds
- `activities` - Activities and experiences
- `other` - Miscellaneous

---

## 🎨 Best Practices

1. **Image Optimization**
   - Upload high-quality images
   - Cloudinary handles optimization automatically
   - Use alt_text for accessibility

2. **Caption Writing**
   - Be descriptive but concise
   - Highlight key features
   - Use engaging language

3. **Gallery Organization**
   - Create logical categories
   - Use display_order consistently
   - Feature best images

4. **Performance**
   - Lazy load images on public page
   - Use featured images for thumbnails
   - Limit images per gallery (10-20 recommended)

---

## 🐛 Troubleshooting

**Images not appearing:**
- Check `is_active` is `true`
- Verify Cloudinary upload successful
- Check image permissions

**Real-time not working:**
- Verify Pusher credentials
- Check channel subscription
- Ensure hotel_slug is correct

**Upload fails:**
- Check file size (<10MB recommended)
- Verify file format (jpg, png, webp)
- Check Cloudinary quotas
