# Frontend Guide: Dynamic Hotel Public Page Builder

## Overview

The backend provides a flexible, dynamic page builder system for hotel public pages. Each hotel can have multiple **sections** containing different types of **elements** (hero, gallery, rooms, features, etc.) with their associated **items**.

---

## API Endpoint

### GET `/api/public/hotel/{slug}/page/`

**Public endpoint** - No authentication required.

**Example:** `http://localhost:8000/api/public/hotel/hotel-killarney/page/`

**Response Structure:**
```json
{
  "hotel": {
    "id": 2,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney",
    "tagline": "Your Gateway to Ireland's Natural Beauty",
    "city": "Killarney",
    "country": "Ireland",
    "address_line_1": "College Street",
    "address_line_2": "",
    "postal_code": "V93 X2C4",
    "latitude": 52.058889,
    "longitude": -9.505556,
    "phone": "+353 64 663 1555",
    "email": "info@hotelkillarney.ie",
    "website_url": "https://www.hotelkillarney.ie",
    "booking_url": "https://www.hotelkillarney.ie/book",
    "hero_image": "http://res.cloudinary.com/.../hero.png",
    "logo": "http://res.cloudinary.com/.../logo.png",
    "short_description": "A modern family-friendly hotel...",
    "long_description": "Nestled in the heart of County Kerry...",
    "hotel_type": "FamilyHotel",
    "tags": ["Family", "Nature", "Spa"]
  },
  "sections": [
    {
      "id": 1,
      "position": 0,
      "name": "hero",
      "element": {
        "id": 1,
        "element_type": "hero",
        "title": "Welcome to Hotel Killarney",
        "subtitle": "Your perfect stay in the heart of Kerry",
        "body": "Enjoy comfortable rooms...",
        "image_url": "https://...",
        "settings": {
          "primary_cta_label": "Book Now",
          "primary_cta_url": "/booking",
          "align": "center"
        },
        "items": []
      }
    },
    // ... more sections
  ]
}
```

---

## Element Types & How to Display Them

### 1. **hero** - Hero Banner

**Purpose:** Large banner at top of page with CTA button.

**Fields Used:**
- `title` - Main heading
- `subtitle` - Subheading
- `body` - Description text
- `image_url` - Background image
- `settings.primary_cta_label` - Button text
- `settings.primary_cta_url` - Button link
- `settings.align` - Text alignment (center, left, right)

**Display:**
```jsx
<section className="hero" style={{ backgroundImage: `url(${element.image_url})` }}>
  <div className={`hero-content align-${element.settings.align}`}>
    <h1>{element.title}</h1>
    <h2>{element.subtitle}</h2>
    <p>{element.body}</p>
    <a href={element.settings.primary_cta_url} className="cta-button">
      {element.settings.primary_cta_label}
    </a>
  </div>
</section>
```

**Notes:**
- No `items` array for hero
- Always first section (position 0)
- `element.image_url` contains the hotel's hero image (same as `hotel.hero_image`)
- Image is automatically populated from hotel model when seeded

---

### 2. **rooms_list** - Room Types ⚠️ SPECIAL CASE

**Purpose:** Display available room types with pricing.

**Fields Used:**
- `title` - Section heading ("Our Rooms & Suites")
- `subtitle` - Section subheading
- `settings.show_price_from` - Show "from €X/night"
- `settings.show_occupancy` - Show max guests
- `settings.columns` - Grid columns (2 or 3)
- **`rooms`** - Array of room types (NOT `items`)

**⚠️ IMPORTANT:** This element uses `element.rooms` NOT `element.items`!

**Room Object Structure:**
```json
{
  "id": 5,
  "code": "DLX",
  "name": "Deluxe Suite",
  "short_description": "Spacious suite with...",
  "max_occupancy": 4,
  "bed_setup": "King Bed + Sofa Bed",
  "photo": "https://cloudinary.com/...",
  "starting_price_from": "199.00",
  "currency": "EUR",
  "booking_url": "/book/deluxe-suite",
  "availability_message": "High demand",
  "is_active": true
}
```

**Display:**
```jsx
<section className="rooms-section">
  <h2>{element.title}</h2>
  <h3>{element.subtitle}</h3>
  
  <div className={`rooms-grid cols-${element.settings.columns}`}>
    {element.rooms.map(room => (
      <div key={room.id} className="room-card">
        <img src={room.photo} alt={room.name} />
        <h4>{room.name}</h4>
        <p>{room.short_description}</p>
        
        {element.settings.show_occupancy && (
          <span>👥 Up to {room.max_occupancy} guests</span>
        )}
        
        {element.settings.show_price_from && (
          <p className="price">From €{room.starting_price_from}/night</p>
        )}
        
        <a href={room.booking_url} className="book-button">Book Now</a>
      </div>
    ))}
  </div>
</section>
```

---

### 3. **cards_list** - Feature Cards / Highlights

**Purpose:** Grid of feature cards (amenities, highlights, USPs).

**Fields Used:**
- `title` - Section heading
- `subtitle` - Section subheading
- `settings.columns` - Number of columns (2, 3, or 4)
- `items[]` - Array of feature cards

**Item Structure:**
```json
{
  "id": 1,
  "title": "Family Friendly",
  "subtitle": "Perfect for all ages",
  "body": "Spacious family rooms, kids' activities...",
  "badge": "Families",
  "image_url": "",
  "meta": { "icon": "family" }
}
```

**Display:**
```jsx
<section className="features">
  <h2>{element.title}</h2>
  <h3>{element.subtitle}</h3>
  
  <div className={`cards-grid cols-${element.settings.columns}`}>
    {element.items.map(item => (
      <div key={item.id} className="feature-card">
        {item.badge && <span className="badge">{item.badge}</span>}
        {item.meta.icon && <Icon name={item.meta.icon} />}
        <h4>{item.title}</h4>
        <h5>{item.subtitle}</h5>
        <p>{item.body}</p>
      </div>
    ))}
  </div>
</section>
```

---

### 4. **gallery** - Photo Gallery

**Purpose:** Image gallery grid.

**Fields Used:**
- `title` - Section heading
- `settings.layout` - "grid" or "carousel"
- `items[]` - Array of images

**Item Structure:**
```json
{
  "id": 1,
  "title": "Lobby",
  "image_url": "https://via.placeholder.com/800x500?text=Lobby",
  "sort_order": 0
}
```

**Display:**
```jsx
<section className="gallery">
  <h2>{element.title}</h2>
  
  {element.settings.layout === 'grid' ? (
    <div className="gallery-grid">
      {element.items.map(item => (
        <div key={item.id} className="gallery-item">
          <img src={item.image_url} alt={item.title} />
          <div className="caption">{item.title}</div>
        </div>
      ))}
    </div>
  ) : (
    <Carousel>
      {element.items.map(item => (
        <img key={item.id} src={item.image_url} alt={item.title} />
      ))}
    </Carousel>
  )}
</section>
```

---

### 5. **reviews_list** - Customer Reviews

**Purpose:** Display guest testimonials.

**Fields Used:**
- `title` - Section heading
- `items[]` - Array of reviews

**Item Structure:**
```json
{
  "id": 1,
  "title": "Amazing family break",
  "subtitle": "Sarah, Dublin",
  "body": "We loved our stay – staff were friendly...",
  "badge": "5★",
  "meta": {
    "rating": 5.0,
    "source": "Google"
  }
}
```

**Display:**
```jsx
<section className="reviews">
  <h2>{element.title}</h2>
  
  <div className="reviews-list">
    {element.items.map(item => (
      <div key={item.id} className="review-card">
        <div className="rating">{item.badge}</div>
        <h4>{item.title}</h4>
        <p className="reviewer">{item.subtitle}</p>
        <p className="review-text">{item.body}</p>
        <span className="source">via {item.meta.source}</span>
      </div>
    ))}
  </div>
</section>
```

---

### 6. **contact_block** - Contact Information

**Purpose:** Display contact details and map.

**Fields Used:**
- `title` - Section heading
- `body` - Introduction text
- `settings.show_phone` - Display phone
- `settings.show_email` - Display email
- `settings.show_address` - Display address

**Display:**
```jsx
<section className="contact">
  <h2>{element.title}</h2>
  <p>{element.body}</p>
  
  <div className="contact-info">
    {element.settings.show_phone && hotel.phone && (
      <div>📞 <a href={`tel:${hotel.phone}`}>{hotel.phone}</a></div>
    )}
    
    {element.settings.show_email && hotel.email && (
      <div>✉️ <a href={`mailto:${hotel.email}`}>{hotel.email}</a></div>
    )}
    
    {element.settings.show_address && (
      <div>
        📍 {hotel.address_line_1}<br />
        {hotel.address_line_2}<br />
        {hotel.city}, {hotel.postal_code}<br />
        {hotel.country}
      </div>
    )}
  </div>
  
  {hotel.latitude && hotel.longitude && (
    <Map lat={hotel.latitude} lng={hotel.longitude} />
  )}
</section>
```

**Notes:**
- No `items` array
- Contact data comes from main `hotel` object

---

## Complete React Example

```jsx
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

function HotelPublicPage() {
  const { slug } = useParams();
  const [pageData, setPageData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/public/hotel/${slug}/page/`)
      .then(res => res.json())
      .then(data => {
        setPageData(data);
        setLoading(false);
      });
  }, [slug]);

  if (loading) return <div>Loading...</div>;

  const renderElement = (section) => {
    const { element } = section;

    switch (element.element_type) {
      case 'hero':
        return <HeroSection element={element} />;
      
      case 'rooms_list':
        return <RoomsSection element={element} />;
      
      case 'cards_list':
        return <CardsSection element={element} />;
      
      case 'gallery':
        return <GallerySection element={element} />;
      
      case 'reviews_list':
        return <ReviewsSection element={element} />;
      
      case 'contact_block':
        return <ContactSection element={element} hotel={pageData.hotel} />;
      
      default:
        console.warn(`Unknown element type: ${element.element_type}`);
        return null;
    }
  };

  return (
    <div className="hotel-public-page">
      {pageData.sections.map(section => (
        <div key={section.id} data-section-id={section.id}>
          {renderElement(section)}
        </div>
      ))}
    </div>
  );
}

export default HotelPublicPage;
```

---

## Key Points for Frontend Developers

### ✅ DO:
1. **Loop through `sections` array** in order (already sorted by `position`)
2. **Check `element_type`** to determine which component to render
3. **For `rooms_list`:** Use `element.rooms` array (NOT `items`)
4. **For other types:** Use `element.items` array
5. **Respect `settings` object** for configuration (columns, layout, etc.)
6. **Use `section.id`** as React key, not array index

### ❌ DON'T:
1. Don't hardcode section order - it's dynamic
2. Don't assume all sections exist - check before rendering
3. Don't use `items` for `rooms_list` - it uses `rooms`
4. Don't ignore `is_active` - inactive sections won't be in API response
5. Don't skip error handling for missing images/data

---

## Testing with Hotel Killarney

**Test URL:** `http://localhost:8000/api/public/hotel/hotel-killarney/page/`

**Other Public Endpoints:**
- List all hotels: `http://localhost:8000/api/public/hotels/`
- Filter options: `http://localhost:8000/api/public/hotels/filters/`

**Seeded sections:**
1. Hero (position 0)
2. Rooms List (position 1) - Will show real room types from database
3. Highlights / Cards (position 2) - 3 feature cards
4. Gallery (position 3) - 3 placeholder images
5. Reviews (position 4) - 2 sample reviews
6. Contact (position 5)

**To reseed data:**
```bash
python manage.py seed_killarney_public_page
```

---

## Adding More Element Types (Future)

When backend adds new element types, frontend should:

1. Add new case in `switch` statement
2. Create corresponding component
3. Map item fields to UI elements
4. Check `settings` object for type-specific config

**Common element types to expect:**
- `hero` ✅ Implemented
- `rooms_list` ✅ Implemented
- `cards_list` ✅ Implemented
- `gallery` ✅ Implemented
- `reviews_list` ✅ Implemented
- `contact_block` ✅ Implemented
- `text_block` (future)
- `video_block` (future)
- `faq_list` (future)
- `amenities_list` (future)
- `location_map` (future)

---

## Questions?

Contact backend team or check:
- Models: `hotel/models.py` (PublicSection, PublicElement, PublicElementItem)
- View: `hotel/views.py` (HotelPublicPageView)
- Serializers: `hotel/serializers.py`
