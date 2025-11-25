# Hotel Gallery Management Guide

## Overview
The hotel gallery allows staff to upload and manage multiple images that are displayed on the public hotel page. Images are stored on Cloudinary and URLs are saved in the `gallery` JSONField.

---

## Backend API

### Get Current Gallery
**Endpoint:** `GET /api/staff/hotels/<hotel_slug>/hotel/settings/`

**Response:**
```json
{
  "gallery": [
    "https://res.cloudinary.com/demo/image/upload/v1234567890/hotel1.jpg",
    "https://res.cloudinary.com/demo/image/upload/v1234567890/hotel2.jpg",
    "https://res.cloudinary.com/demo/image/upload/v1234567890/hotel3.jpg"
  ]
}
```

### Update Gallery
**Endpoint:** `PATCH /api/staff/hotels/<hotel_slug>/hotel/settings/`

**Request Body:**
```json
{
  "gallery": [
    "https://res.cloudinary.com/demo/image/upload/v1234567890/hotel1.jpg",
    "https://res.cloudinary.com/demo/image/upload/v1234567890/hotel2.jpg"
  ]
}
```

---

## Frontend Implementation

### Step 1: Upload Images to Cloudinary

#### Option A: Direct Upload Widget (Recommended)
```javascript
import { useEffect, useState } from 'react';

const GalleryManager = ({ hotelSlug }) => {
  const [gallery, setGallery] = useState([]);
  const [cloudinaryWidget, setCloudinaryWidget] = useState(null);

  // Initialize Cloudinary Widget
  useEffect(() => {
    const widget = window.cloudinary.createUploadWidget(
      {
        cloudName: 'YOUR_CLOUD_NAME',
        uploadPreset: 'YOUR_UPLOAD_PRESET',
        folder: `hotels/${hotelSlug}/gallery`,
        sources: ['local', 'url', 'camera'],
        multiple: true,
        maxFiles: 20,
        clientAllowedFormats: ['jpg', 'jpeg', 'png', 'webp'],
        maxFileSize: 5000000, // 5MB
      },
      (error, result) => {
        if (!error && result && result.event === 'success') {
          const imageUrl = result.info.secure_url;
          // Add new image to gallery
          setGallery(prev => [...prev, imageUrl]);
        }
      }
    );
    setCloudinaryWidget(widget);
  }, [hotelSlug]);

  const handleUpload = () => {
    cloudinaryWidget?.open();
  };

  return (
    <button onClick={handleUpload}>
      Upload Images
    </button>
  );
};
```

#### Option B: File Upload with Backend Proxy
```javascript
const uploadToCloudinary = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('upload_preset', 'YOUR_UPLOAD_PRESET');
  formData.append('folder', `hotels/${hotelSlug}/gallery`);

  const response = await fetch(
    'https://api.cloudinary.com/v1_1/YOUR_CLOUD_NAME/image/upload',
    {
      method: 'POST',
      body: formData,
    }
  );

  const data = await response.json();
  return data.secure_url;
};

const handleFileUpload = async (e) => {
  const files = Array.from(e.target.files);
  
  // Upload all files
  const uploadPromises = files.map(file => uploadToCloudinary(file));
  const imageUrls = await Promise.all(uploadPromises);
  
  // Add to gallery
  setGallery(prev => [...prev, ...imageUrls]);
};
```

### Step 2: Display Gallery Grid

```jsx
const GalleryGrid = ({ gallery, onRemove, onReorder }) => {
  return (
    <div className="gallery-grid">
      {gallery.map((imageUrl, index) => (
        <div key={index} className="gallery-item">
          <img src={imageUrl} alt={`Gallery ${index + 1}`} />
          <div className="gallery-item-actions">
            <button onClick={() => onRemove(index)}>
              Remove
            </button>
            {index > 0 && (
              <button onClick={() => onReorder(index, index - 1)}>
                ↑ Move Up
              </button>
            )}
            {index < gallery.length - 1 && (
              <button onClick={() => onReorder(index, index + 1)}>
                ↓ Move Down
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
```

**CSS:**
```css
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  padding: 1rem;
}

.gallery-item {
  position: relative;
  aspect-ratio: 4/3;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.gallery-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gallery-item-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.gallery-item:hover .gallery-item-actions {
  opacity: 1;
}

.gallery-item-actions button {
  flex: 1;
  padding: 0.5rem;
  font-size: 0.75rem;
  background: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
```

### Step 3: Gallery Management Functions

```javascript
const GalleryManager = ({ hotelSlug }) => {
  const [gallery, setGallery] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch current gallery
  useEffect(() => {
    fetchGallery();
  }, [hotelSlug]);

  const fetchGallery = async () => {
    const response = await fetch(
      `/api/staff/hotels/${hotelSlug}/hotel/settings/`
    );
    const data = await response.json();
    setGallery(data.gallery || []);
  };

  // Add image to gallery
  const addImage = (imageUrl) => {
    setGallery(prev => [...prev, imageUrl]);
  };

  // Remove image from gallery
  const removeImage = (index) => {
    setGallery(prev => prev.filter((_, i) => i !== index));
  };

  // Reorder images
  const reorderImages = (fromIndex, toIndex) => {
    setGallery(prev => {
      const newGallery = [...prev];
      const [removed] = newGallery.splice(fromIndex, 1);
      newGallery.splice(toIndex, 0, removed);
      return newGallery;
    });
  };

  // Save gallery to backend
  const saveGallery = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/staff/hotels/${hotelSlug}/hotel/settings/`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${yourAuthToken}`,
          },
          body: JSON.stringify({ gallery }),
        }
      );

      if (response.ok) {
        alert('Gallery saved successfully!');
      } else {
        alert('Failed to save gallery');
      }
    } catch (error) {
      console.error('Error saving gallery:', error);
      alert('Error saving gallery');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="gallery-manager">
      <div className="gallery-header">
        <h2>Hotel Gallery</h2>
        <button onClick={handleUploadClick}>
          Add Images
        </button>
      </div>

      <GalleryGrid
        gallery={gallery}
        onRemove={removeImage}
        onReorder={reorderImages}
      />

      <div className="gallery-footer">
        <button
          onClick={saveGallery}
          disabled={loading}
          className="save-button"
        >
          {loading ? 'Saving...' : 'Save Gallery'}
        </button>
      </div>
    </div>
  );
};
```

### Step 4: Drag & Drop Reordering (Optional)

Using `react-beautiful-dnd`:

```javascript
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

const DraggableGallery = ({ gallery, setGallery, onRemove }) => {
  const handleDragEnd = (result) => {
    if (!result.destination) return;

    const items = Array.from(gallery);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    setGallery(items);
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Droppable droppableId="gallery" direction="horizontal">
        {(provided) => (
          <div
            className="gallery-grid"
            {...provided.droppableProps}
            ref={provided.innerRef}
          >
            {gallery.map((imageUrl, index) => (
              <Draggable
                key={imageUrl}
                draggableId={imageUrl}
                index={index}
              >
                {(provided) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                    className="gallery-item"
                  >
                    <img src={imageUrl} alt={`Gallery ${index + 1}`} />
                    <button
                      onClick={() => onRemove(index)}
                      className="remove-btn"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
};
```

---

## Public Hotel Page Display

### Lightbox Gallery Component

```javascript
import { useState } from 'react';

const HotelGallery = ({ gallery }) => {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  const openLightbox = (index) => {
    setCurrentIndex(index);
    setLightboxOpen(true);
  };

  const closeLightbox = () => {
    setLightboxOpen(false);
  };

  const nextImage = () => {
    setCurrentIndex((prev) => (prev + 1) % gallery.length);
  };

  const prevImage = () => {
    setCurrentIndex((prev) => (prev - 1 + gallery.length) % gallery.length);
  };

  if (!gallery || gallery.length === 0) return null;

  return (
    <>
      <div className="hotel-gallery">
        <h2>Gallery</h2>
        <div className="gallery-grid">
          {gallery.map((imageUrl, index) => (
            <img
              key={index}
              src={imageUrl}
              alt={`Hotel view ${index + 1}`}
              onClick={() => openLightbox(index)}
              className="gallery-thumbnail"
            />
          ))}
        </div>
      </div>

      {lightboxOpen && (
        <div className="lightbox" onClick={closeLightbox}>
          <button className="lightbox-close" onClick={closeLightbox}>
            ✕
          </button>
          <button className="lightbox-prev" onClick={prevImage}>
            ‹
          </button>
          <img
            src={gallery[currentIndex]}
            alt={`Gallery ${currentIndex + 1}`}
            onClick={(e) => e.stopPropagation()}
          />
          <button className="lightbox-next" onClick={nextImage}>
            ›
          </button>
          <div className="lightbox-counter">
            {currentIndex + 1} / {gallery.length}
          </div>
        </div>
      )}
    </>
  );
};
```

**Lightbox CSS:**
```css
.lightbox {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.lightbox img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
}

.lightbox-close,
.lightbox-prev,
.lightbox-next {
  position: absolute;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 2rem;
  cursor: pointer;
  padding: 1rem;
  transition: background 0.2s;
}

.lightbox-close {
  top: 1rem;
  right: 1rem;
}

.lightbox-prev {
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
}

.lightbox-next {
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
}

.lightbox-counter {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  color: white;
  font-size: 1rem;
}
```

---

## Best Practices

1. **Image Optimization:**
   - Use Cloudinary transformations for thumbnails
   - Example: `imageUrl.replace('/upload/', '/upload/w_400,h_300,c_fill/')`

2. **Validation:**
   - Limit gallery to 20-30 images max
   - Validate file types (jpg, jpeg, png, webp)
   - Set max file size (5MB recommended)

3. **User Experience:**
   - Show upload progress
   - Preview images before saving
   - Confirm before deletion
   - Auto-save on reorder (optional)

4. **Performance:**
   - Lazy load gallery images
   - Use responsive images with srcset
   - Implement image compression

---

## Example: Complete Gallery Manager Component

```javascript
import { useState, useEffect } from 'react';

const CompleteGalleryManager = ({ hotelSlug }) => {
  const [gallery, setGallery] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchGallery();
  }, [hotelSlug]);

  const fetchGallery = async () => {
    setLoading(true);
    const response = await fetch(
      `/api/staff/hotels/${hotelSlug}/hotel/settings/`
    );
    const data = await response.json();
    setGallery(data.gallery || []);
    setLoading(false);
  };

  const uploadImage = async (file) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('upload_preset', 'YOUR_UPLOAD_PRESET');
    
    const response = await fetch(
      'https://api.cloudinary.com/v1_1/YOUR_CLOUD_NAME/image/upload',
      { method: 'POST', body: formData }
    );
    
    const data = await response.json();
    setUploading(false);
    return data.secure_url;
  };

  const handleFileChange = async (e) => {
    const files = Array.from(e.target.files);
    const urls = await Promise.all(files.map(uploadImage));
    setGallery(prev => [...prev, ...urls]);
  };

  const removeImage = (index) => {
    if (confirm('Remove this image?')) {
      setGallery(prev => prev.filter((_, i) => i !== index));
    }
  };

  const saveGallery = async () => {
    setLoading(true);
    await fetch(`/api/staff/hotels/${hotelSlug}/hotel/settings/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gallery }),
    });
    setLoading(false);
    alert('Gallery saved!');
  };

  return (
    <div>
      <input
        type="file"
        multiple
        accept="image/*"
        onChange={handleFileChange}
        disabled={uploading}
      />
      
      <div className="gallery-grid">
        {gallery.map((url, i) => (
          <div key={i}>
            <img src={url} alt={`Gallery ${i}`} />
            <button onClick={() => removeImage(i)}>Remove</button>
          </div>
        ))}
      </div>
      
      <button onClick={saveGallery} disabled={loading}>
        {loading ? 'Saving...' : 'Save Gallery'}
      </button>
    </div>
  );
};
```

---

## Summary

✅ Backend supports `gallery` as JSONField array of URLs  
✅ Upload images to Cloudinary (direct widget or file upload)  
✅ Store Cloudinary URLs in gallery array  
✅ Display as grid with remove/reorder options  
✅ Save to backend via PATCH endpoint  
✅ Display on public page with lightbox viewer  

The gallery system is fully functional and ready for frontend implementation!
