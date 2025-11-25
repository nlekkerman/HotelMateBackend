# Frontend Guide: Public Page Builder API

## Overview

The Public Page Builder API allows Super Staff Admins to build hotel public pages from scratch or manage existing sections. It handles **blank hotels** gracefully - you get all the tools needed to build a page even when there are ZERO sections.

## Key Principle

**No more fighting empty states.** When a hotel has no sections:
- Backend returns `is_empty: true` + empty `sections: []` + full `presets` object
- Frontend shows a clean "empty canvas" UI with builder tools
- Staff can start building using presets or manual section creation

---

## Authentication

**Required:** Super Staff Admin only
- User must be authenticated
- User must have `Staff` profile with `access_level == 'super_staff_admin'`
- Staff must belong to the hotel being edited

**Permission:** `IsSuperStaffAdminForHotel`

---

## Endpoints

### 0. GET Hotel Status (Optional)

**Endpoint:** `GET /api/staff/hotel/{hotel_slug}/status/`

**Purpose:** Check hotel's current state before building

**Response:**
```json
{
  "hotel": {
    "id": 2,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney"
  },
  "branding": {
    "has_hero_image": false,
    "has_logo": false,
    "tagline": null
  },
  "public_page": {
    "section_count": 0,
    "is_empty": true
  },
  "ready_for_builder": true
}
```

### 1. GET Builder Data

**Endpoint:** `GET /api/staff/hotel/{hotel_slug}/public-page-builder/`

**Purpose:** Load builder interface data (blank or populated)

**Response:**
```json
{
  "hotel": {
    "id": 2,
    "slug": "hotel-killarney",
    "name": "Hotel Killarney",
    "city": "Killarney",
    "country": "Ireland",
    "tagline": "Your gateway to the Ring of Kerry",
    "booking_url": "https://booking.example.com"
  },
  "is_empty": true,
  "sections": [],
  "presets": {
    "element_types": [
      "hero",
      "text_block",
      "image_block",
      "gallery",
      "cards_list",
      "reviews_list",
      "rooms_list",
      "contact_block",
      "map_block",
      "footer_block"
    ],
    "section_presets": [
      {
        "key": "hero_default",
        "label": "Hero Section",
        "element_type": "hero",
        "element_defaults": {
          "title": "Welcome to Hotel Killarney",
          "subtitle": "Your perfect stay starts here",
          "body": "",
          "settings": {
            "primary_cta_label": "Book Now",
            "primary_cta_url": "https://booking.example.com"
          }
        }
      },
      {
        "key": "rooms_default",
        "label": "Rooms List",
        "element_type": "rooms_list",
        "element_defaults": {
          "title": "Our Rooms & Suites",
          "subtitle": "",
          "settings": {
            "show_price_from": true,
            "show_occupancy": true,
            "columns": 2
          }
        }
      }
      // ... more presets
    ]
  }
}
```

**When `is_empty: false`:** The `sections` array contains full section data:
```json
{
  "is_empty": false,
  "sections": [
    {
      "id": 1,
      "hotel": 2,
      "position": 0,
      "is_active": true,
      "name": "Hero",
      "element": {
        "id": 1,
        "element_type": "hero",
        "title": "Welcome to Hotel Killarney",
        "subtitle": "Your perfect stay starts here",
        "body": "",
        "image_url": "https://...",
        "settings": {
          "primary_cta_label": "Book Now",
          "primary_cta_url": "https://..."
        },
        "items": [],
        "created_at": "2025-11-25T10:00:00Z",
        "updated_at": "2025-11-25T10:00:00Z"
      },
      "created_at": "2025-11-25T10:00:00Z",
      "updated_at": "2025-11-25T10:00:00Z"
    }
  ]
}
```

---

### 2. POST Bootstrap Default Layout

**Endpoint:** `POST /api/staff/hotel/{hotel_slug}/public-page-builder/bootstrap-default/`

**Purpose:** Auto-create starter sections on a **blank hotel only**

**Conditions:**
- Hotel must have **ZERO sections**
- If hotel already has sections → `400 Bad Request`

**What it creates:**
1. Hero section
2. Rooms list section (auto-populated from `RoomType` model)
3. Highlights section (3 sample cards)
4. Gallery section (empty, ready for images)
5. Reviews section (empty, ready for reviews)
6. Contact section

**Response:** Same structure as GET endpoint, but with `is_empty: false` and populated `sections`

**Example:**
```json
{
  "message": "Successfully created 6 default sections",
  "sections_created": [
    "hero",
    "rooms_list",
    "highlights",
    "gallery",
    "reviews",
    "contact"
  ],
  "hotel": {
    "id": 2,
    "slug": "hotel-killarney",
    "name": "Hotel Killarney"
  },
  "is_empty": false,
  "sections": [/* full section data */]
}
```

---

## Frontend Implementation

### React Component Structure

```jsx
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

function PublicPageBuilder() {
  const { hotelSlug } = useParams();
  const [builderData, setBuilderData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBuilderData();
  }, [hotelSlug]);

  const loadBuilderData = async () => {
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/public-page-builder/`,
      {
        headers: {
          'Authorization': `Bearer ${yourAuthToken}`
        }
      }
    );
    const data = await response.json();
    setBuilderData(data);
    setLoading(false);
  };

  const bootstrapDefault = async () => {
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/public-page-builder/bootstrap-default/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${yourAuthToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      setBuilderData(data);
    } else {
      const error = await response.json();
      alert(error.detail);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="builder-container">
      <h1>Public Page Builder - {builderData.hotel.name}</h1>
      
      {builderData.is_empty ? (
        <EmptyCanvas 
          hotel={builderData.hotel}
          presets={builderData.presets}
          onBootstrap={bootstrapDefault}
        />
      ) : (
        <BuilderInterface 
          hotel={builderData.hotel}
          sections={builderData.sections}
          presets={builderData.presets}
        />
      )}
    </div>
  );
}
```

### Empty Canvas UI

```jsx
function EmptyCanvas({ hotel, presets, onBootstrap }) {
  return (
    <div className="empty-canvas">
      <div className="empty-state">
        <h2>This hotel has no public page yet</h2>
        <p>Start building from scratch or use a template</p>
        
        <button 
          onClick={onBootstrap}
          className="btn-primary"
        >
          🎨 Start from Default Template
        </button>
        
        <div className="preset-grid">
          <h3>Or add sections manually:</h3>
          {presets.section_presets.map(preset => (
            <button
              key={preset.key}
              className="preset-card"
              onClick={() => addSectionFromPreset(preset)}
            >
              <strong>{preset.label}</strong>
              <span>{preset.element_type}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### Builder Interface (with sections)

```jsx
function BuilderInterface({ hotel, sections, presets }) {
  return (
    <div className="builder-interface">
      <aside className="builder-sidebar">
        <h3>Add Section</h3>
        {presets.section_presets.map(preset => (
          <button
            key={preset.key}
            onClick={() => addSection(preset)}
          >
            + {preset.label}
          </button>
        ))}
      </aside>
      
      <main className="builder-canvas">
        {sections.map(section => (
          <SectionCard
            key={section.id}
            section={section}
          />
        ))}
      </main>
    </div>
  );
}
```

---

## Creating Sections Manually

Use existing endpoints (already built):

### Create a new section:
```javascript
POST /api/staff/hotel/{hotel_slug}/public-sections/
{
  "hotel": hotelId,  // REQUIRED - ID of the hotel
  "position": 0,
  "name": "Hero",
  "is_active": true
}
```

### Create element for that section:
```javascript
POST /api/staff/hotel/{hotel_slug}/public-elements/
{
  "section": sectionId,  // REQUIRED - ID of the section created above
  "element_type": "hero",
  "title": "Welcome to Hotel Killarney",
  "subtitle": "Your perfect stay starts here",
  "body": "",
  "image_url": "",
  "settings": {
    "primary_cta_label": "Book Now",
    "primary_cta_url": "https://..."
  }
}
```

### Add items to elements (for cards, gallery, reviews):
```javascript
POST /api/staff/hotel/{hotel_slug}/public-element-items/
{
  "element": elementId,  // REQUIRED - ID of the element
  "title": "Family Friendly",
  "subtitle": "Perfect for all ages",
  "body": "Spacious rooms...",
  "image_url": "",
  "sort_order": 0,
  "is_active": true
}
```

---

## Using Presets

The `presets` object gives you ready-made configurations:

```javascript
const preset = presets.section_presets.find(p => p.key === 'hero_default');

// Use preset.element_defaults to pre-fill form:
{
  element_type: preset.element_type,
  title: preset.element_defaults.title,
  subtitle: preset.element_defaults.subtitle,
  settings: preset.element_defaults.settings
}
```

---

## Element Types Reference

| Type | Description | Has Items? |
|------|-------------|------------|
| `hero` | Hero banner with title, subtitle, CTA | No |
| `rooms_list` | Auto-populated from `RoomType` model | **No** (uses `rooms` field) |
| `cards_list` | Feature cards, highlights | **Yes** |
| `gallery` | Image gallery | **Yes** |
| `reviews_list` | Customer reviews/testimonials | **Yes** |
| `contact_block` | Contact info + map | No |
| `text_block` | Rich text content | No |
| `image_block` | Single image with caption | No |
| `map_block` | Embedded map | No |
| `footer_block` | Footer content | No |

---

## Flow Diagram

```
Staff opens builder
    ↓
GET /public-page-builder/
    ↓
is_empty = true?
    ↓ YES                           ↓ NO
Show empty canvas             Show existing sections
with presets                  with edit tools
    ↓                                ↓
User clicks                    User edits sections
"Start from Template"          using PATCH/DELETE
    ↓                                ↓
POST /bootstrap-default/       Sections update
    ↓                                ↓
Sections created              Builder refreshes
    ↓
Builder shows populated interface
```

---

## Important Notes

1. **No seeds needed** - Blank hotels are handled elegantly
2. **Presets are static** - They come from backend, not database
3. **`rooms_list` is special** - It auto-populates from `RoomType` model (no manual items)
4. **Authentication required** - Must be Super Staff Admin for the hotel
5. **Use existing CRUD** - For editing/deleting sections after creation

---

## Testing Endpoints

### Test with blank hotel:
```bash
GET /api/staff/hotel/hotel-killarney/public-page-builder/
# Should return is_empty: true
```

### Bootstrap it:
```bash
POST /api/staff/hotel/hotel-killarney/public-page-builder/bootstrap-default/
# Creates 6 default sections
```

### Try to bootstrap again:
```bash
POST /api/staff/hotel/hotel-killarney/public-page-builder/bootstrap-default/
# Should return 400: "Hotel already has X sections"
```

---

## Questions?

Contact backend team or check:
- **Models:** `hotel/models.py` (PublicSection, PublicElement, PublicElementItem)
- **Views:** `hotel/views.py` (PublicPageBuilderView, PublicPageBootstrapView)
- **Permissions:** `hotel/permissions.py` (IsSuperStaffAdminForHotel)
- **Serializers:** `hotel/serializers.py` (PublicSectionStaffSerializer)
