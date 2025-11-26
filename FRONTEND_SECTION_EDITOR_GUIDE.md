# Frontend Section Editor Integration Guide

## Overview

This guide explains how to integrate the section-based page editor into your React frontend. It covers the API endpoints, payloads, and expected responses for building a visual page editor.

---

## Base URL Structure

All staff endpoints follow this pattern:
```
/api/staff/hotel/<hotel_slug>/<resource>/
```

For example:
```
/api/staff/hotel/hotel-killarney/public-sections/
```

---

## 1. Creating a New Section

### Endpoint
```
POST /api/staff/hotel/<hotel_slug>/sections/create/
```

### Headers
```javascript
{
  'Authorization': 'Token <your-token>',
  'Content-Type': 'application/json'
}
```

### Payload Examples

#### Create Hero Section
```json
{
  "section_type": "hero",
  "name": "Main Hero",
  "position": 0
}
```

#### Create Gallery Section
```json
{
  "section_type": "gallery",
  "name": "Hotel Gallery",
  "position": 1
}
```

#### Create List/Cards Section
```json
{
  "section_type": "list",
  "name": "Special Offers",
  "position": 2
}
```

#### Create News Section
```json
{
  "section_type": "news",
  "name": "Latest Updates",
  "position": 3
}
```

### Response Example (Hero Section)
```json
{
  "message": "Hero section created successfully",
  "section": {
    "id": 42,
    "hotel": 2,
    "position": 0,
    "is_active": true,
    "name": "Main Hero",
    "section_type": "hero",
    "hero_data": {
      "id": 15,
      "section": 42,
      "hero_title": "Update your hero title here",
      "hero_text": "Update your hero description text here.",
      "hero_image_url": "https://res.cloudinary.com/demo/image/upload/v1/sample.jpg",
      "hero_logo_url": "https://res.cloudinary.com/demo/image/upload/v1/logo_sample.jpg",
      "created_at": "2025-11-26T01:23:10.196775Z",
      "updated_at": "2025-11-26T01:23:10.196786Z"
    },
    "galleries": [],
    "lists": [],
    "news_items": [],
    "created_at": "2025-11-26T01:23:10.196775Z",
    "updated_at": "2025-11-26T01:23:10.196786Z"
  }
}
```

### Response Example (Gallery Section)
```json
{
  "message": "Gallery section created successfully",
  "section": {
    "id": 43,
    "hotel": 2,
    "position": 1,
    "is_active": true,
    "name": "Hotel Gallery",
    "section_type": "gallery",
    "hero_data": null,
    "galleries": [
      {
        "id": 8,
        "section": 43,
        "name": "Gallery 1",
        "sort_order": 0,
        "image_count": 0,
        "images": []
      }
    ],
    "lists": [],
    "news_items": []
  }
}
```

---

## 2. Fetching All Sections

### Endpoint
```
GET /api/staff/hotel/<hotel_slug>/public-sections/
```

### Response
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 42,
      "hotel": 2,
      "position": 0,
      "is_active": true,
      "name": "Main Hero",
      "section_type": "hero",
      "hero_data": { /* hero section data */ },
      "galleries": [],
      "lists": [],
      "news_items": []
    },
    {
      "id": 43,
      "hotel": 2,
      "position": 1,
      "is_active": true,
      "name": "Hotel Gallery",
      "section_type": "gallery",
      "hero_data": null,
      "galleries": [
        {
          "id": 8,
          "name": "Gallery 1",
          "images": []
        }
      ],
      "lists": [],
      "news_items": []
    }
  ]
}
```

---

## 3. Hero Section Operations

### Update Hero Text

**Endpoint:** `PATCH /api/staff/hotel/<hotel_slug>/hero-sections/<hero_id>/`

**Payload:**
```json
{
  "hero_title": "Welcome to Grand Hotel",
  "hero_text": "Experience luxury and comfort in the heart of the city"
}
```

### Upload Hero Background Image

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/hero-sections/<hero_id>/upload-hero-image/`

**Content-Type:** `multipart/form-data`

**FormData:**
```javascript
const formData = new FormData();
formData.append('image', imageFile); // File object from input
```

**Example with Axios:**
```javascript
const uploadHeroImage = async (heroId, imageFile) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  const response = await axios.post(
    `/api/staff/hotel/hotel-killarney/hero-sections/${heroId}/upload-hero-image/`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Token ${token}`
      }
    }
  );
  
  return response.data;
};
```

### Upload Hero Logo

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/hero-sections/<hero_id>/upload-logo/`

**Same as hero image upload** - use `multipart/form-data` with `image` field.

---

## 4. Gallery Section Operations

### Create Additional Gallery Container

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/gallery-containers/`

**Payload:**
```json
{
  "section": 43,
  "name": "Dining Area",
  "sort_order": 1
}
```

### Bulk Upload Images to Gallery

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/gallery-images/bulk-upload/`

**Content-Type:** `multipart/form-data`

**FormData:**
```javascript
const formData = new FormData();
formData.append('gallery', galleryId); // Gallery container ID
imageFiles.forEach(file => {
  formData.append('images', file); // Multiple files
});
```

**Example:**
```javascript
const uploadGalleryImages = async (galleryId, imageFiles) => {
  const formData = new FormData();
  formData.append('gallery', galleryId);
  
  // Add up to 20 images
  imageFiles.forEach(file => {
    formData.append('images', file);
  });
  
  const response = await axios.post(
    `/api/staff/hotel/hotel-killarney/gallery-images/bulk-upload/`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Token ${token}`
      }
    }
  );
  
  return response.data;
};
```

**Response:**
```json
{
  "message": "5 image(s) uploaded successfully",
  "images": [
    {
      "id": 101,
      "gallery": 8,
      "image_url": "https://res.cloudinary.com/.../image1.jpg",
      "caption": "",
      "alt_text": "",
      "sort_order": 0
    }
  ]
}
```

### Update Gallery Image Metadata

**Endpoint:** `PATCH /api/staff/hotel/<hotel_slug>/gallery-images/<image_id>/`

**Payload:**
```json
{
  "caption": "Beautiful lobby view",
  "alt_text": "Hotel lobby with chandelier",
  "sort_order": 2
}
```

### Delete Gallery Image

**Endpoint:** `DELETE /api/staff/hotel/<hotel_slug>/gallery-images/<image_id>/`

---

## 5. List/Card Section Operations

### Create Card

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/cards/`

**Payload:**
```json
{
  "list_container": 12,
  "title": "Summer Special",
  "subtitle": "20% Off",
  "description": "Book now and save 20% on your summer stay",
  "sort_order": 0
}
```

### Upload Card Image

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/cards/<card_id>/upload-image/`

**Content-Type:** `multipart/form-data`

**FormData:**
```javascript
const formData = new FormData();
formData.append('image', imageFile);
```

### Update Card

**Endpoint:** `PATCH /api/staff/hotel/<hotel_slug>/cards/<card_id>/`

**Payload:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "sort_order": 1
}
```

### Delete Card

**Endpoint:** `DELETE /api/staff/hotel/<hotel_slug>/cards/<card_id>/`

---

## 6. News Section Operations

### Create News Item

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/news-items/`

**Payload:**
```json
{
  "section": 45,
  "title": "Grand Opening Announcement",
  "date": "2025-12-01",
  "summary": "We're excited to announce our grand opening",
  "sort_order": 0
}
```

### Add Text Block to News

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/content-blocks/`

**Payload:**
```json
{
  "news_item": 20,
  "block_type": "text",
  "body": "We are thrilled to announce our grand opening on December 1st. Join us for an unforgettable celebration!",
  "sort_order": 0
}
```

### Add Image Block to News

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/content-blocks/`

**Payload:**
```json
{
  "news_item": 20,
  "block_type": "image",
  "image_position": "full_width",
  "image_caption": "Opening day celebration",
  "sort_order": 1
}
```

**Image Position Options:**
- `"full_width"` - Full width image
- `"left"` - Image on left, text flows right
- `"right"` - Image on right, text flows left
- `"inline_grid"` - Multiple images in grid

### Upload Image for Image Block

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/content-blocks/<block_id>/upload-image/`

**Content-Type:** `multipart/form-data`

**FormData:**
```javascript
const formData = new FormData();
formData.append('image', imageFile);
```

---

## 7. Empty State Detection

When you receive section data, check for empty containers:

### Hero Section
```javascript
const isHeroEmpty = !section.hero_data?.hero_image_url && 
                    section.hero_data?.hero_title === "Update your hero title here";
```

### Gallery Section
```javascript
const hasNoImages = section.galleries.every(gallery => gallery.image_count === 0);
```

### List Section
```javascript
const hasNoCards = section.lists.every(list => list.card_count === 0);
```

### News Section
```javascript
const hasNoNews = section.news_items.length === 0;
```

### Empty State UI Examples

**Gallery Empty State:**
```jsx
{gallery.images.length === 0 && (
  <div className="empty-state">
    <p>No images in this gallery yet</p>
    <button onClick={() => handleAddImages(gallery.id)}>
      Add images to this gallery
    </button>
    <button onClick={() => handleCreateNewGallery(section.id)}>
      Create new gallery
    </button>
  </div>
)}
```

**List Empty State:**
```jsx
{list.cards.length === 0 && (
  <div className="empty-state">
    <p>No cards in this list yet</p>
    <button onClick={() => handleAddCard(list.id)}>
      Add card
    </button>
    <button onClick={() => handleCreateNewList(section.id)}>
      Create new list
    </button>
  </div>
)}
```

---

## 8. Complete React Example

```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

const SectionEditor = ({ hotelSlug, token }) => {
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);

  const API_BASE = `/api/staff/hotel/${hotelSlug}`;
  
  const axiosConfig = {
    headers: { 'Authorization': `Token ${token}` }
  };

  // Fetch all sections
  const fetchSections = async () => {
    try {
      const response = await axios.get(
        `${API_BASE}/public-sections/`,
        axiosConfig
      );
      setSections(response.data.results);
    } catch (error) {
      console.error('Error fetching sections:', error);
    } finally {
      setLoading(false);
    }
  };

  // Create new section
  const createSection = async (sectionType, name) => {
    try {
      const response = await axios.post(
        `${API_BASE}/sections/create/`,
        {
          section_type: sectionType,
          name: name
        },
        axiosConfig
      );
      
      // Add new section to state
      setSections([...sections, response.data.section]);
      return response.data.section;
    } catch (error) {
      console.error('Error creating section:', error);
    }
  };

  // Update hero text
  const updateHeroText = async (heroId, title, text) => {
    try {
      const response = await axios.patch(
        `${API_BASE}/hero-sections/${heroId}/`,
        {
          hero_title: title,
          hero_text: text
        },
        axiosConfig
      );
      
      // Update state
      fetchSections();
      return response.data;
    } catch (error) {
      console.error('Error updating hero:', error);
    }
  };

  // Upload hero image
  const uploadHeroImage = async (heroId, imageFile) => {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    try {
      const response = await axios.post(
        `${API_BASE}/hero-sections/${heroId}/upload-hero-image/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Token ${token}`
          }
        }
      );
      
      fetchSections();
      return response.data;
    } catch (error) {
      console.error('Error uploading image:', error);
    }
  };

  // Bulk upload gallery images
  const uploadGalleryImages = async (galleryId, imageFiles) => {
    const formData = new FormData();
    formData.append('gallery', galleryId);
    
    imageFiles.forEach(file => {
      formData.append('images', file);
    });
    
    try {
      const response = await axios.post(
        `${API_BASE}/gallery-images/bulk-upload/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Token ${token}`
          }
        }
      );
      
      fetchSections();
      return response.data;
    } catch (error) {
      console.error('Error uploading images:', error);
    }
  };

  useEffect(() => {
    fetchSections();
  }, []);

  return (
    <div>
      <h2>Page Editor</h2>
      
      {/* Section Creation Buttons */}
      <div className="section-controls">
        <button onClick={() => createSection('hero', 'Main Hero')}>
          Add Hero Section
        </button>
        <button onClick={() => createSection('gallery', 'Gallery')}>
          Add Gallery Section
        </button>
        <button onClick={() => createSection('list', 'Offers')}>
          Add List Section
        </button>
        <button onClick={() => createSection('news', 'News')}>
          Add News Section
        </button>
      </div>

      {/* Render Sections */}
      {loading ? (
        <p>Loading sections...</p>
      ) : (
        <div className="sections-list">
          {sections.map(section => (
            <div key={section.id} className="section">
              <h3>{section.name} ({section.section_type})</h3>
              
              {/* Render based on section type */}
              {section.section_type === 'hero' && section.hero_data && (
                <div>
                  <input
                    value={section.hero_data.hero_title}
                    onChange={(e) => updateHeroText(
                      section.hero_data.id,
                      e.target.value,
                      section.hero_data.hero_text
                    )}
                  />
                  <input
                    type="file"
                    onChange={(e) => uploadHeroImage(
                      section.hero_data.id,
                      e.target.files[0]
                    )}
                  />
                </div>
              )}
              
              {/* Add more section type renderers here */}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SectionEditor;
```

---

## 9. Key Points

✅ **All sections auto-initialize** - Hero gets placeholders, Gallery/List get empty containers  
✅ **Use multipart/form-data** for all image uploads  
✅ **Hotel slug is in URL** - `/api/staff/hotel/<hotel_slug>/...`  
✅ **Token authentication** required for all endpoints  
✅ **Empty state detection** - Check counts and placeholder values  
✅ **Bulk operations** - Gallery supports uploading up to 20 images at once  
✅ **Ordering** - Use `sort_order` field to control display order  

---

## 10. Error Handling

All endpoints return standard REST error codes:

- `200 OK` - Successful GET/PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid payload
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource doesn't exist
- `500 Internal Server Error` - Server error

Handle errors gracefully in your frontend and show user-friendly messages.
