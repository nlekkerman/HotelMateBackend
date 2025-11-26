# Section-Based Page Editor API Documentation

## Overview

This API provides a complete section-based page editor for public hotel websites with four section types:
- **Hero**: Pre-populated with placeholder text and images
- **Gallery**: Multiple gallery containers with Cloudinary images
- **List/Cards**: Multiple list containers with cards (offers, rooms, facilities, etc.)
- **News**: News items with ordered content blocks (text/image with positioning)

All image uploads use the existing Cloudinary integration from the maintenance app.

## Permissions

- **Super Admin Only**: All section management endpoints require `IsSuperStaffAdminForHotel` permission
- **Guest/Public**: Can only view the rendered page (no edit controls)

---

## Section Management

### 1. Create Section (with Auto-Initialization)

Creates a new section and automatically initializes the appropriate data structure.

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/sections/create/`

**Body**:
```json
{
  "section_type": "hero" | "gallery" | "list" | "news",
  "name": "Optional section name",
  "position": 0
}
```

**Behavior by Type**:
- **hero**: Creates `HeroSection` with placeholder text ("Update your hero title here", etc.)
- **gallery**: Creates one empty `GalleryContainer` named "Gallery 1"
- **list**: Creates one empty `ListContainer`
- **news**: Creates empty section (news items added explicitly later)

**Response**:
```json
{
  "message": "Hero section created successfully",
  "section": {
    "id": 1,
    "hotel": 1,
    "position": 0,
    "is_active": true,
    "name": "Hero Section",
    "section_type": "hero",
    "hero_data": {
      "id": 1,
      "hero_title": "Update your hero title here",
      "hero_text": "Update your hero description text here.",
      "hero_image_url": null,
      "hero_logo_url": null
    }
  }
}
```

### 2. List All Sections

**Endpoint**: `GET /api/staff/hotel/<hotel_slug>/public-sections/`

Returns all sections for the hotel with nested data.

### 3. Update Section

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/public-sections/<id>/`

**Body**:
```json
{
  "name": "Updated name",
  "position": 1,
  "is_active": true
}
```

### 4. Delete Section

**Endpoint**: `DELETE /api/staff/hotel/<hotel_slug>/public-sections/<id>/`

---

## Hero Section

Hero sections are **pre-populated** with placeholder text and empty image fields.

### Update Hero Data

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/hero-sections/<id>/`

**Body**:
```json
{
  "hero_title": "Welcome to Our Hotel",
  "hero_text": "Experience luxury and comfort"
}
```

### Upload Hero Image

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/hero-sections/<id>/upload-hero-image/`

**Body** (multipart/form-data):
- `image`: Image file

### Upload Hero Logo

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/hero-sections/<id>/upload-logo/`

**Body** (multipart/form-data):
- `image`: Image file

---

## Gallery Section

Gallery sections can have **multiple gallery containers**, each containing multiple images.

### Create Gallery Container

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/gallery-containers/`

**Body**:
```json
{
  "section": 1,
  "name": "Pool Area",
  "sort_order": 0
}
```

### List Gallery Containers

**Endpoint**: `GET /api/staff/hotel/<hotel_slug>/gallery-containers/?section=<section_id>`

### Update Gallery Container

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/gallery-containers/<id>/`

### Delete Gallery Container

**Endpoint**: `DELETE /api/staff/hotel/<hotel_slug>/gallery-containers/<id>/`

### Add Images to Gallery (Bulk Upload)

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/gallery-images/bulk-upload/`

**Body** (multipart/form-data):
- `gallery`: Gallery container ID
- `images`: Array of image files (max 20)

**Response**:
```json
{
  "message": "5 image(s) uploaded successfully",
  "images": [
    {
      "id": 1,
      "gallery": 1,
      "image_url": "https://res.cloudinary.com/...",
      "caption": "",
      "sort_order": 0
    }
  ]
}
```

### Update Gallery Image

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/gallery-images/<id>/`

**Body**:
```json
{
  "caption": "Beautiful pool view",
  "alt_text": "Hotel pool",
  "sort_order": 1
}
```

### Delete Gallery Image

**Endpoint**: `DELETE /api/staff/hotel/<hotel_slug>/gallery-images/<id>/`

---

## List/Card Section

List sections can have **multiple list containers**, each containing multiple cards.

### Create List Container

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/list-containers/`

**Body**:
```json
{
  "section": 2,
  "title": "Special Offers",
  "sort_order": 0
}
```

### List Containers

**Endpoint**: `GET /api/staff/hotel/<hotel_slug>/list-containers/?section=<section_id>`

### Create Card

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/cards/`

**Body**:
```json
{
  "list_container": 1,
  "title": "Summer Special",
  "subtitle": "20% Off",
  "description": "Book now and save 20% on your stay",
  "sort_order": 0
}
```

### Upload Card Image

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/cards/<id>/upload-image/`

**Body** (multipart/form-data):
- `image`: Image file

### Update Card

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/cards/<id>/`

### Delete Card

**Endpoint**: `DELETE /api/staff/hotel/<hotel_slug>/cards/<id>/`

---

## News Section

News sections contain **news items** with ordered **content blocks** (text or image).

### Create News Item

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/news-items/`

**Body**:
```json
{
  "section": 3,
  "title": "Grand Opening Announcement",
  "date": "2025-12-01",
  "summary": "We're excited to announce our grand opening",
  "sort_order": 0
}
```

### List News Items

**Endpoint**: `GET /api/staff/hotel/<hotel_slug>/news-items/?section=<section_id>`

### Update News Item

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/news-items/<id>/`

### Delete News Item

**Endpoint**: `DELETE /api/staff/hotel/<hotel_slug>/news-items/<id>/`

### Add Text Block to News Item

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/content-blocks/`

**Body**:
```json
{
  "news_item": 1,
  "block_type": "text",
  "body": "We are thrilled to announce our grand opening...",
  "sort_order": 0
}
```

### Add Image Block to News Item

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/content-blocks/`

**Body**:
```json
{
  "news_item": 1,
  "block_type": "image",
  "image_position": "full_width" | "left" | "right" | "inline_grid",
  "image_caption": "Opening day celebration",
  "sort_order": 1
}
```

Then upload the image:

**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/content-blocks/<id>/upload-image/`

**Body** (multipart/form-data):
- `image`: Image file

### Update Content Block

**Endpoint**: `PATCH /api/staff/hotel/<hotel_slug>/content-blocks/<id>/`

### Delete Content Block

**Endpoint**: `DELETE /api/staff/hotel/<hotel_slug>/content-blocks/<id>/`

---

## Public/Guest View

### Get Hotel Page with All Sections

**Endpoint**: `GET /api/public/hotel/<slug>/page/`

**No authentication required**

Returns complete page structure with all active sections and their data.

**Response**:
```json
{
  "hotel": {
    "id": 1,
    "name": "Grand Hotel",
    "slug": "grand-hotel",
    "tagline": "Luxury in the heart of the city"
  },
  "sections": [
    {
      "id": 1,
      "position": 0,
      "name": "Hero Section",
      "section_type": "hero",
      "hero_data": {
        "hero_title": "Welcome to Grand Hotel",
        "hero_text": "Experience luxury...",
        "hero_image_url": "https://...",
        "hero_logo_url": "https://..."
      }
    },
    {
      "id": 2,
      "position": 1,
      "name": "Gallery",
      "section_type": "gallery",
      "galleries": [
        {
          "id": 1,
          "name": "Pool Area",
          "images": [
            {
              "id": 1,
              "image_url": "https://...",
              "caption": "Beautiful pool"
            }
          ]
        }
      ]
    }
  ]
}
```

---

## Cloudinary Integration

All image uploads use the **existing Cloudinary integration** from the maintenance app:

- Images are stored using `CloudinaryField` from `cloudinary.models`
- Upload handling reuses the same logic as `MaintenancePhoto` uploads
- No duplicate upload code - shared utility in `common/cloudinary_utils.py`

### Supported Image Types
- JPEG, PNG, WebP
- Max size: 10MB per image
- Bulk upload: Max 20 images at once

---

## Example Workflows

### Create a Complete Hero Section

1. Create section:
   ```
   POST /api/staff/hotel/grand-hotel/hotel/sections/create/
   { "section_type": "hero", "name": "Main Hero" }
   ```

2. Update text:
   ```
   PATCH /api/staff/hotel/grand-hotel/hero-sections/1/
   {
     "hero_title": "Welcome to Grand Hotel",
     "hero_text": "Your perfect getaway awaits"
   }
   ```

3. Upload images:
   ```
   POST /api/staff/hotel/grand-hotel/hero-sections/1/upload-hero-image/
   (multipart: image file)
   
   POST /api/staff/hotel/grand-hotel/hero-sections/1/upload-logo/
   (multipart: logo file)
   ```

### Create a Gallery with Multiple Images

1. Create section:
   ```
   POST /api/staff/hotel/grand-hotel/sections/create/
   { "section_type": "gallery", "name": "Hotel Gallery" }
   ```

2. Gallery container is auto-created, get its ID from response

3. Upload multiple images:
   ```
   POST /api/staff/hotel/grand-hotel/gallery-images/bulk-upload/
   (multipart: gallery=1, images=[file1, file2, file3])
   ```

4. Create additional gallery:
   ```
   POST /api/staff/hotel/grand-hotel/gallery-containers/
   { "section": 2, "name": "Dining Area", "sort_order": 1 }
   ```

### Create News with Text and Images

1. Create section:
   ```
   POST /api/staff/hotel/grand-hotel/sections/create/
   { "section_type": "news", "name": "Latest News" }
   ```

2. Create news item:
   ```
   POST /api/staff/hotel/grand-hotel/news-items/
   {
     "section": 3,
     "title": "New Spa Opening",
     "date": "2025-12-15",
     "summary": "Our luxury spa is now open"
   }
   ```

3. Add text block:
   ```
   POST /api/staff/hotel/grand-hotel/content-blocks/
   {
     "news_item": 1,
     "block_type": "text",
     "body": "We're excited to announce...",
     "sort_order": 0
   }
   ```

4. Add image block:
   ```
   POST /api/staff/hotel/grand-hotel/content-blocks/
   {
     "news_item": 1,
     "block_type": "image",
     "image_position": "full_width",
     "sort_order": 1
   }
   
   POST /api/staff/hotel/grand-hotel/content-blocks/2/upload-image/
   (multipart: image file)
   ```

---

## Empty State Behavior

Following the requirements:

- **Hero**: Pre-populated with placeholder text, empty images
- **Gallery**: One empty container created automatically, shows helper text "No images in this gallery yet" + buttons
- **List**: One empty container created automatically, shows helper text "No cards in this list yet" + buttons  
- **News**: Empty section, shows helper text "No news items yet" + button

Frontend should detect empty containers and show appropriate UI with "Add" buttons for super admins only.
