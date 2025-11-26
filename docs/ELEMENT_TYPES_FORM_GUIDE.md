# Element Types - Form Building Guide

## Overview
Each section has ONE element. The element type determines what fields to show in the edit form.

---

## Element Structure

```javascript
{
  id: 1,
  section: 15,  // FK to section
  element_type: "hero",
  title: "Welcome",
  subtitle: "Your perfect stay",
  body: "Long text content",
  image_url: "https://...",
  settings: {},  // JSON object for type-specific config
  items: [],     // Array of items (for cards, gallery, reviews)
  created_at: "...",
  updated_at: "..."
}
```

---

## 1. Hero (`element_type: "hero"`)

**Use Case**: Main banner section with large image, heading, and CTA buttons

**Form Fields**:
```javascript
{
  title: "text",           // Main heading
  subtitle: "text",        // Subheading
  image_url: "url",        // Background image
  settings: {
    logo_url: "url",                    // Optional hotel logo overlay
    primary_cta_label: "text",          // Button 1 text
    primary_cta_url: "url",             // Button 1 link
    secondary_cta_label: "text",        // Button 2 text (optional)
    secondary_cta_url: "url",           // Button 2 link (optional)
    text_position: "center|left|right", // Text alignment
    overlay_opacity: "0-100"            // Dark overlay %
  }
}
```

**Edit Form**:
- Text input: Title
- Text input: Subtitle
- Image upload: Background Image
- Image upload: Logo (optional)
- Text input: Primary Button Label
- URL input: Primary Button URL
- Text input: Secondary Button Label (optional)
- URL input: Secondary Button URL (optional)
- Select: Text Position (center, left, right)
- Slider: Overlay Opacity (0-100)

---

## 2. Text Block (`element_type: "text_block"`)

**Use Case**: Simple text section with heading and body

**Form Fields**:
```javascript
{
  title: "text",     // Heading
  body: "richtext",  // Main content (supports markdown/html)
  settings: {
    text_align: "left|center|right",
    max_width: "normal|wide|full"
  }
}
```

**Edit Form**:
- Text input: Title
- Rich text editor: Body
- Select: Text Alignment
- Select: Max Width

---

## 3. Image Block (`element_type: "image_block"`)

**Use Case**: Single image with optional caption

**Form Fields**:
```javascript
{
  image_url: "url",  // Main image
  title: "text",     // Caption/alt text
  settings: {
    size: "small|medium|large|full",
    caption_position: "below|overlay"
  }
}
```

**Edit Form**:
- Image upload: Image
- Text input: Caption
- Select: Size
- Select: Caption Position

---

## 4. Gallery (`element_type: "gallery"`)

**Use Case**: Multiple images in grid/carousel

**Form Fields**:
```javascript
{
  title: "text",  // Section heading
  settings: {
    layout: "grid|carousel|masonry",
    columns: 2|3|4,
    show_captions: true|false
  },
  items: [
    {
      image_url: "url",
      title: "caption",
      sort_order: 0
    }
  ]
}
```

**Edit Form**:
- Text input: Section Title
- Select: Layout (grid, carousel, masonry)
- Number input: Columns (2-4)
- Checkbox: Show Captions
- **Items Manager**:
  - Add Item button
  - For each item:
    - Image upload
    - Text input: Caption
    - Drag to reorder
    - Delete button

**Item Creation**:
```javascript
POST /api/staff/hotel/{slug}/public-element-items/
{
  element: elementId,
  image_url: "https://...",
  title: "Beach view at sunset",
  sort_order: 0,
  is_active: true
}
```

---

## 5. Cards List (`element_type: "cards_list"`)

**Use Case**: Feature cards, services, amenities

**Form Fields**:
```javascript
{
  title: "text",
  subtitle: "text",
  settings: {
    columns: 2|3|4,
    card_style: "bordered|shadow|flat"
  },
  items: [
    {
      title: "Card title",
      subtitle: "Card subtitle",
      body: "Description",
      image_url: "url or icon",
      badge: "Featured",
      cta_label: "Learn More",
      cta_url: "https://...",
      sort_order: 0
    }
  ]
}
```

**Edit Form**:
- Text input: Section Title
- Text input: Section Subtitle
- Select: Columns
- Select: Card Style
- **Items Manager**:
  - Add Card button
  - For each card:
    - Text input: Title
    - Text input: Subtitle
    - Textarea: Body
    - Image upload OR Icon picker
    - Text input: Badge (optional)
    - Text input: CTA Label
    - URL input: CTA URL
    - Drag to reorder
    - Delete button

---

## 6. Reviews List (`element_type: "reviews_list"`)

**Use Case**: Customer testimonials

**Form Fields**:
```javascript
{
  title: "text",
  settings: {
    layout: "grid|carousel",
    show_ratings: true|false
  },
  items: [
    {
      title: "Customer Name",
      subtitle: "Location or date",
      body: "The review text",
      image_url: "Customer photo (optional)",
      badge: "5",  // Rating (1-5)
      sort_order: 0
    }
  ]
}
```

**Edit Form**:
- Text input: Section Title
- Select: Layout
- Checkbox: Show Ratings
- **Items Manager**:
  - Add Review button
  - For each review:
    - Text input: Customer Name
    - Text input: Location/Date
    - Textarea: Review Text
    - Image upload: Customer Photo (optional)
    - Star rating: Rating (1-5)
    - Drag to reorder
    - Delete button

---

## 7. Rooms List (`element_type: "rooms_list"`)

**Use Case**: Display hotel's room types (auto-fetched from RoomType model)

**Form Fields**:
```javascript
{
  title: "text",
  subtitle: "text",
  settings: {
    show_price_from: true|false,
    show_occupancy: true|false,
    show_amenities: true|false,
    columns: 2|3,
    sort_by: "price|name|capacity"
  }
}
```

**Edit Form**:
- Text input: Section Title
- Text input: Section Subtitle
- Checkbox: Show "From" Price
- Checkbox: Show Occupancy
- Checkbox: Show Amenities
- Select: Columns (2 or 3)
- Select: Sort By

**Note**: Room data is automatically fetched from the hotel's RoomType objects. No items needed.

---

## 8. Contact Block (`element_type: "contact_block"`)

**Use Case**: Contact information and form

**Form Fields**:
```javascript
{
  title: "text",
  body: "text",  // Optional intro text
  settings: {
    show_phone: true|false,
    show_email: true|false,
    show_address: true|false,
    show_form: true|false,
    phone_override: "custom phone",     // Optional custom phone
    email_override: "custom email",     // Optional custom email
    address_override: "custom address"  // Optional custom address
  }
}
```

**Edit Form**:
- Text input: Section Title
- Textarea: Intro Text
- Checkbox: Show Phone
- Checkbox: Show Email
- Checkbox: Show Address
- Checkbox: Show Contact Form
- Text input: Custom Phone (overrides hotel.phone)
- Text input: Custom Email (overrides hotel.email)
- Textarea: Custom Address (overrides hotel.address)

**Note**: Contact info pulls from Hotel model by default, but can be overridden.

---

## 9. Map Block (`element_type: "map_block"`)

**Use Case**: Embedded map showing hotel location

**Form Fields**:
```javascript
{
  title: "text",
  settings: {
    map_url: "url",  // Google Maps embed URL
    height: "400px|600px|800px",
    show_directions_link: true|false
  }
}
```

**Edit Form**:
- Text input: Section Title
- URL input: Map Embed URL
- Select: Map Height
- Checkbox: Show Directions Link

---

## 10. Footer Block (`element_type: "footer_block"`)

**Use Case**: Page footer with links and info

**Form Fields**:
```javascript
{
  body: "text",  // Copyright or footer text
  settings: {
    show_social_links: true|false,
    social_links: {
      facebook: "url",
      instagram: "url",
      twitter: "url"
    }
  },
  items: [
    {
      title: "Link text",
      cta_url: "url",
      sort_order: 0
    }
  ]
}
```

**Edit Form**:
- Textarea: Footer Text (copyright, etc.)
- Checkbox: Show Social Links
- URL inputs: Facebook, Instagram, Twitter
- **Items Manager** (Footer Links):
  - Add Link button
  - For each link:
    - Text input: Link Text
    - URL input: URL
    - Drag to reorder
    - Delete button

---

## Form Building Pattern

### 1. Detect Element Type
```javascript
const elementType = element.element_type;

function renderEditForm(element) {
  switch(elementType) {
    case 'hero':
      return <HeroForm element={element} onSave={handleSave} />;
    case 'text_block':
      return <TextBlockForm element={element} onSave={handleSave} />;
    case 'gallery':
      return <GalleryForm element={element} onSave={handleSave} />;
    // ... etc
  }
}
```

### 2. Update Element
```javascript
PATCH /api/staff/hotel/{slug}/public-elements/{id}/
{
  title: "Updated title",
  settings: { /* updated settings */ }
}
```

### 3. Manage Items (for gallery, cards, reviews, footer)
```javascript
// Create item
POST /api/staff/hotel/{slug}/public-element-items/
{
  element: elementId,
  title: "...",
  image_url: "...",
  sort_order: 0
}

// Update item
PATCH /api/staff/hotel/{slug}/public-element-items/{itemId}/
{
  title: "Updated"
}

// Delete item
DELETE /api/staff/hotel/{slug}/public-element-items/{itemId}/

// Reorder items (update sort_order for each)
PATCH /api/staff/hotel/{slug}/public-element-items/{itemId}/
{
  sort_order: 2
}
```

---

## Settings Field Structure

The `settings` field is a JSON object. Different element types use different keys:

**Hero**:
```json
{
  "logo_url": "string",
  "primary_cta_label": "string",
  "primary_cta_url": "string",
  "secondary_cta_label": "string",
  "secondary_cta_url": "string",
  "text_position": "center",
  "overlay_opacity": 50
}
```

**Gallery**:
```json
{
  "layout": "grid",
  "columns": 3,
  "show_captions": true
}
```

**Cards List**:
```json
{
  "columns": 3,
  "card_style": "shadow"
}
```

**Rooms List**:
```json
{
  "show_price_from": true,
  "show_occupancy": true,
  "show_amenities": false,
  "columns": 2,
  "sort_by": "price"
}
```

---

## Item Field Structure

Items are used by: `gallery`, `cards_list`, `reviews_list`, `footer_block`

**Full item schema**:
```json
{
  "id": 1,
  "element": 10,
  "title": "string",
  "subtitle": "string",
  "body": "text",
  "image_url": "url",
  "badge": "string",
  "cta_label": "string",
  "cta_url": "url",
  "sort_order": 0,
  "is_active": true,
  "meta": {},
  "created_at": "...",
  "updated_at": "..."
}
```

**Which fields each type uses**:

| Element Type | title | subtitle | body | image_url | badge | cta_label | cta_url |
|-------------|-------|----------|------|-----------|-------|-----------|---------|
| gallery | ✅ (caption) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| cards_list | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| reviews_list | ✅ (name) | ✅ (location) | ✅ (review) | ✅ (photo) | ✅ (rating) | ❌ | ❌ |
| footer_block | ✅ (link text) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (link url) |

---

## Frontend Component Example

```jsx
function ElementEditor({ element, onUpdate }) {
  const [formData, setFormData] = useState(element);
  
  const handleSubmit = async () => {
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/public-elements/${element.id}/`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      }
    );
    
    if (response.ok) {
      const updated = await response.json();
      onUpdate(updated);
    }
  };
  
  const renderFields = () => {
    switch(element.element_type) {
      case 'hero':
        return (
          <>
            <input 
              value={formData.title} 
              onChange={e => setFormData({...formData, title: e.target.value})}
              placeholder="Title"
            />
            <input 
              value={formData.subtitle} 
              onChange={e => setFormData({...formData, subtitle: e.target.value})}
              placeholder="Subtitle"
            />
            <ImageUpload 
              value={formData.image_url}
              onChange={url => setFormData({...formData, image_url: url})}
            />
            <input 
              value={formData.settings.primary_cta_label || ''} 
              onChange={e => setFormData({
                ...formData, 
                settings: {...formData.settings, primary_cta_label: e.target.value}
              })}
              placeholder="Button Label"
            />
          </>
        );
      
      case 'gallery':
        return (
          <>
            <input 
              value={formData.title} 
              onChange={e => setFormData({...formData, title: e.target.value})}
              placeholder="Section Title"
            />
            <ItemsManager 
              elementId={element.id}
              items={element.items}
              type="gallery"
            />
          </>
        );
      
      // ... more cases
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {renderFields()}
      <button type="submit">Save Changes</button>
    </form>
  );
}
```

---

## Summary

1. **Each section = 1 element**
2. **Element type determines form fields**
3. **Settings field = JSON config for that type**
4. **Items = repeating content (cards, images, reviews)**
5. **Update element** = PATCH element endpoint
6. **Manage items** = CRUD on items endpoint
7. **Reorder items** = update sort_order field
