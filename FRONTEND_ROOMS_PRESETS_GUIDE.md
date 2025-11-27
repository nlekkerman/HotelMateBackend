# Frontend Guide: Using Rooms Section Presets

## Overview
This guide explains how to use the presets for styling the rooms section, including section layouts, room cards, and section headers.

---

## 🎨 Available Presets

### 1. **Rooms Section Layout Presets**
Control the overall layout of the rooms section.

| Preset Key | Name | Description | Config |
|------------|------|-------------|--------|
| `rooms_grid_3col` | Rooms Grid - 3 Columns | Classic 3-column grid (DEFAULT) | 3 columns, large gap |
| `rooms_grid_2col` | Rooms Grid - 2 Columns | Wider 2-column grid | 2 columns, large gap |
| `rooms_list` | Rooms List | Vertical list with image beside text | Image left, vertical layout |
| `rooms_carousel` | Rooms Carousel | Horizontal scrolling carousel | Carousel with dots |
| `rooms_luxury` | Luxury Display | Premium layout with large images | 2 columns, extra large gap, zoom effect |

---

### 2. **Room Card Presets**
Control individual room card styling.

| Preset Key | Name | Description | Features |
|------------|------|-------------|----------|
| `room_card_standard` | Standard Room Card | Classic card (DEFAULT) | 250px image, all details, lift effect |
| `room_card_compact` | Compact Room Card | Mobile-friendly compact | 200px image, minimal details, no badge |
| `room_card_luxury` | Luxury Room Card | Premium with large image | 350px image, border, shadow, zoom effect |
| `room_card_minimal` | Minimal Room Card | Clean minimal design | 300px image, no icons, text button |
| `room_card_horizontal` | Horizontal Room Card | Wide horizontal layout | Image 40% width, side-by-side layout |

---

### 3. **Section Header Presets**
Control section header styling (applies to all sections).

| Preset Key | Name | Description | Style |
|------------|------|-------------|-------|
| `header_centered` | Centered Header | Center-aligned (DEFAULT) | Large title, subtitle, centered |
| `header_left` | Left Aligned Header | Left-aligned header | Large title, subtitle, left |
| `header_with_divider` | Header with Divider | Centered with bottom line | Decorative divider below |
| `header_minimal` | Minimal Header | Simple title only | Medium size, no subtitle |
| `header_luxury` | Luxury Header | Elegant with decorative elements | Extra large, serif font, decorative divider |

---

## 📡 API Endpoints

### Get All Presets
```http
GET /api/public/presets/
```

**Response:**
```json
{
  "section": {
    "rooms": [
      {
        "key": "rooms_grid_3col",
        "name": "Rooms Grid - 3 Columns",
        "description": "Classic 3-column grid layout for room types",
        "is_default": true,
        "config": {
          "layout": "grid",
          "columns": 3,
          "gap": "large",
          "show_price": true,
          "show_amenities": true
        }
      }
    ]
  },
  "room_card": [
    {
      "key": "room_card_standard",
      "name": "Standard Room Card",
      "is_default": true,
      "config": {
        "image_height": "250px",
        "show_occupancy": true,
        "show_bed_setup": true,
        "show_description": true,
        "show_price": true,
        "show_badge": true,
        "button_style": "primary",
        "hover_effect": "lift"
      }
    }
  ],
  "section_header": [
    {
      "key": "header_centered",
      "name": "Centered Header",
      "is_default": true,
      "config": {
        "text_alignment": "center",
        "title_size": "large",
        "show_subtitle": true,
        "show_divider": false,
        "margin_bottom": "large"
      }
    }
  ]
}
```

### Get Presets by Type
```http
GET /api/public/presets/?target_type=room_card
GET /api/public/presets/?target_type=section_header
GET /api/public/presets/?target_type=section&section_type=rooms
```

---

## 💻 Frontend Implementation

### 1. Fetch Presets on App Load

```javascript
// services/presetsService.js
export const fetchPresets = async () => {
  const response = await fetch('/api/public/presets/');
  return await response.json();
};

// Store in context or state
const [presets, setPresets] = useState(null);

useEffect(() => {
  fetchPresets().then(setPresets);
}, []);
```

---

### 2. Rooms Section Component with Presets

```jsx
// components/RoomsSection.jsx
import { useMemo } from 'react';

const RoomsSection = ({ section, presets }) => {
  // Get selected preset or default
  const layoutPreset = useMemo(() => {
    const presetKey = section.style_variant || 'rooms_grid_3col';
    return presets?.section?.rooms?.find(p => p.key === presetKey) 
           || presets?.section?.rooms?.find(p => p.is_default);
  }, [section.style_variant, presets]);

  // Get header preset
  const headerPreset = useMemo(() => {
    const key = section.header_style || 'header_centered';
    return presets?.section_header?.find(p => p.key === key)
           || presets?.section_header?.find(p => p.is_default);
  }, [section.header_style, presets]);

  // Get card preset
  const cardPreset = useMemo(() => {
    const key = section.card_style || 'room_card_standard';
    return presets?.room_card?.find(p => p.key === key)
           || presets?.room_card?.find(p => p.is_default);
  }, [section.card_style, presets]);

  // Apply layout config
  const layoutConfig = layoutPreset?.config || {};
  const headerConfig = headerPreset?.config || {};
  const cardConfig = cardPreset?.config || {};

  return (
    <section className="rooms-section">
      {/* Section Header */}
      <SectionHeader 
        title={section.name}
        subtitle={section.rooms_data?.subtitle}
        config={headerConfig}
      />

      {/* Rooms Grid/Layout */}
      <RoomsLayout 
        layout={layoutConfig.layout || 'grid'}
        columns={layoutConfig.columns || 3}
        gap={layoutConfig.gap || 'large'}
      >
        {section.rooms_data?.room_types?.map(room => (
          <RoomCard 
            key={room.id}
            room={room}
            config={cardConfig}
          />
        ))}
      </RoomsLayout>
    </section>
  );
};
```

---

### 3. Section Header Component

```jsx
// components/SectionHeader.jsx
const SectionHeader = ({ title, subtitle, config }) => {
  const {
    text_alignment = 'center',
    title_size = 'large',
    show_subtitle = true,
    show_divider = false,
    divider_style = 'solid',
    font_style = 'sans-serif',
    margin_bottom = 'large'
  } = config;

  const headerClasses = `
    section-header 
    text-${text_alignment} 
    mb-${margin_bottom}
    ${font_style === 'serif' ? 'font-serif' : ''}
  `;

  const titleClasses = `
    section-title 
    ${title_size === 'extra_large' ? 'display-3' : 
      title_size === 'large' ? 'display-4' : 'h2'}
  `;

  return (
    <div className={headerClasses}>
      <h2 className={titleClasses}>{title}</h2>
      {show_subtitle && subtitle && (
        <p className="section-subtitle text-muted">{subtitle}</p>
      )}
      {show_divider && (
        <hr className={`divider divider-${divider_style}`} />
      )}
    </div>
  );
};
```

---

### 4. Rooms Layout Component

```jsx
// components/RoomsLayout.jsx
const RoomsLayout = ({ layout, columns, gap, children }) => {
  const getLayoutClasses = () => {
    switch(layout) {
      case 'grid':
        return `row row-cols-1 row-cols-md-${columns} g-${gap === 'large' ? '4' : gap === 'medium' ? '3' : '2'}`;
      
      case 'list':
        return 'd-flex flex-column gap-4';
      
      case 'carousel':
        return 'carousel-container';
      
      case 'luxury':
        return `row row-cols-1 row-cols-md-${columns} g-5`;
      
      default:
        return `row row-cols-1 row-cols-md-${columns} g-4`;
    }
  };

  if (layout === 'carousel') {
    return (
      <div className="rooms-carousel">
        <Carousel>
          {children}
        </Carousel>
      </div>
    );
  }

  return (
    <div className={getLayoutClasses()}>
      {children}
    </div>
  );
};
```

---

### 5. Room Card Component

```jsx
// components/RoomCard.jsx
const RoomCard = ({ room, config }) => {
  const {
    image_height = '250px',
    show_occupancy = true,
    show_bed_setup = true,
    show_description = true,
    show_price = true,
    show_badge = true,
    button_style = 'primary',
    hover_effect = 'lift',
    layout = 'vertical'
  } = config;

  const cardClasses = `
    room-card 
    ${hover_effect ? `hover-${hover_effect}` : ''} 
    ${layout === 'horizontal' ? 'card-horizontal' : ''}
    h-100 shadow-sm card
  `;

  return (
    <div className="col">
      <div className={cardClasses}>
        {/* Room Image */}
        <img 
          src={room.photo} 
          alt={room.name}
          className="card-img-top"
          style={{ 
            height: image_height, 
            objectFit: 'cover',
            width: layout === 'horizontal' ? '40%' : '100%'
          }}
        />

        <div className="card-body d-flex flex-column">
          {/* Room Name */}
          <h5 className="card-title mb-3">{room.name}</h5>

          {/* Room Details */}
          <div className="mb-3">
            {show_occupancy && (
              <div className="d-flex align-items-center mb-2 text-muted">
                <i className="bi bi-people me-2"></i>
                <small>Up to {room.max_occupancy} guests</small>
              </div>
            )}
            {show_bed_setup && room.bed_setup && (
              <div className="d-flex align-items-center mb-2 text-muted">
                <i className="bi bi-moon me-2"></i>
                <small>{room.bed_setup}</small>
              </div>
            )}
          </div>

          {/* Description */}
          {show_description && room.short_description && (
            <p className="card-text text-muted mb-3">
              {room.short_description}
            </p>
          )}

          {/* Price & CTA */}
          <div className="mt-auto">
            {show_price && (
              <div className="d-flex justify-content-between align-items-center mb-3">
                <div>
                  <small className="text-muted d-block">From</small>
                  <h4 className="mb-0 text-primary">
                    {room.currency}{room.starting_price_from}
                    <small className="text-muted fs-6"> /night</small>
                  </h4>
                </div>
                {show_badge && room.availability_message && (
                  <span className="badge bg-warning text-dark">
                    {room.availability_message}
                  </span>
                )}
              </div>
            )}

            {/* Book Now Button */}
            <button 
              type="button"
              className={`w-100 btn btn-${button_style}`}
              onClick={() => window.location.href = room.booking_cta_url}
            >
              <i className="bi bi-calendar-check me-2"></i>
              Book Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
```

---

## 🎛️ Staff Admin: Selecting Presets

Staff can select presets via the settings API:

```javascript
// Update rooms section style
PATCH /api/staff/hotels/{slug}/hotel/staff/rooms-sections/{id}/

{
  "style_variant": "rooms_grid_2col",    // Section layout preset
  "header_style": "header_with_divider", // Header preset (custom field)
  "card_style": "room_card_luxury"       // Card preset (custom field)
}
```

**Note:** You'll need to add `header_style` and `card_style` fields to the `RoomsSection` model if you want staff to customize these separately. Otherwise, use the section-level `style_variant` for the layout only.

---

## 📝 CSS/SCSS for Hover Effects

```scss
// styles/rooms.scss

.room-card {
  transition: all 0.3s ease;

  &.hover-lift:hover {
    transform: translateY(-8px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  }

  &.hover-zoom:hover img {
    transform: scale(1.1);
  }

  &.hover-opacity:hover {
    opacity: 0.9;
  }

  img {
    transition: transform 0.3s ease;
  }
}

.section-header {
  &.text-center {
    text-align: center;
  }

  &.text-left {
    text-align: left;
  }

  .divider {
    width: 80px;
    height: 3px;
    margin: 1.5rem auto;
    border: none;
    background: var(--primary-color);

    &.divider-decorative {
      width: 120px;
      height: 4px;
      background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
    }
  }
}
```

---

## ✅ Summary

**Backend provides:**
- 5 section layout presets (grid 3col/2col, list, carousel, luxury)
- 5 room card presets (standard, compact, luxury, minimal, horizontal)
- 5 section header presets (centered, left, with divider, minimal, luxury)

**Frontend implementation:**
1. Fetch presets from `/api/public/presets/`
2. Match preset key from section data (e.g., `section.style_variant`)
3. Apply config values to components (columns, gaps, show/hide features)
4. Render dynamic layouts and styles based on preset config

**Staff can:**
- Select presets via admin panel
- Mix and match section layout + card style + header style
- Create unique combinations for different hotels
