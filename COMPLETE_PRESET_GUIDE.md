# Complete Preset System Guide

## 📚 Table of Contents
1. [Overview](#overview)
2. [Backend Architecture](#backend-architecture)
3. [All Available Presets](#all-available-presets)
4. [API Documentation](#api-documentation)
5. [Frontend Implementation](#frontend-implementation)
6. [Staff Admin Integration](#staff-admin-integration)
7. [Creating Custom Presets](#creating-custom-presets)

---

## 🎯 Overview

The preset system provides reusable styling configurations for all public page elements. Staff can mix and match presets to create unique hotel pages without writing code.

**Preset Types:**
- Section Layouts (hero, gallery, list, news, footer, rooms)
- Card Styles
- Room Card Styles
- Image Styles
- News Block Styles
- Section Headers
- Page Themes

---

## 🏗️ Backend Architecture

### Preset Model
```python
# hotel/models.py
class Preset(models.Model):
    TARGET_TYPES = [
        ("section", "Section"),
        ("card", "Card"),
        ("image", "Image"),
        ("news_block", "News Block"),
        ("footer", "Footer"),
        ("page_theme", "Page Theme"),
        ("room_card", "Room Card"),
        ("section_header", "Section Header"),
    ]
    
    SECTION_TYPES = [
        ("hero", "Hero"),
        ("gallery", "Gallery"),
        ("list", "List"),
        ("news", "News"),
        ("footer", "Footer"),
        ("rooms", "Rooms"),
    ]
    
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES)
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES, null=True, blank=True)
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    config = models.JSONField(default=dict, blank=True)
```

### Database Storage
- **Total Presets:** 70+
- **Organized by:** target_type → section_type (if applicable)
- **Identification:** Unique `key` field (e.g., `hero_classic_centered`)
- **Configuration:** JSON `config` field with flexible schema

---

## 🎨 All Available Presets

### 1. HERO SECTION PRESETS (5)

| Key | Name | Description | Default | Config Highlights |
|-----|------|-------------|---------|-------------------|
| `hero_classic_centered` | Classic Centered Hero | Traditional centered hero | ✅ | centered, background image |
| `hero_split_image_left` | Split Layout - Image Left | Split with image on left | ❌ | split, image left |
| `hero_image_background` | Full Background Image | Full-width background with overlay | ❌ | fullwidth, overlay |
| `hero_minimal` | Minimal Hero | Clean minimal design | ❌ | minimal, no image |
| `hero_left_text_floating` | Floating Text Left | Floating text on background | ❌ | floating, text left |

**Config Schema:**
```json
{
  "layout": "centered|split|fullwidth|minimal|floating",
  "text_alignment": "center|left",
  "image_position": "background|left|none",
  "overlay": true|false
}
```

---

### 2. GALLERY SECTION PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `gallery_grid` | Grid Gallery | Equal-sized grid | ✅ | 3 columns, medium gap |
| `gallery_masonry` | Masonry Gallery | Pinterest-style masonry | ❌ | 3 columns, varying heights |
| `gallery_slider` | Slider Gallery | Horizontal carousel | ❌ | autoplay, dots |
| `gallery_collage` | Collage Gallery | Artistic featured layout | ❌ | 2 featured images |
| `gallery_tiled` | Tiled Gallery | Compact no-gap tiles | ❌ | 4 columns, no gaps |

**Config Schema:**
```json
{
  "layout": "grid|masonry|slider|collage|tiled",
  "columns": 2|3|4,
  "gap": "none|small|medium|large",
  "autoplay": true|false,
  "show_dots": true|false,
  "featured_count": 1|2
}
```

---

### 3. LIST SECTION PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `list_3_column` | 3-Column Grid | Three equal columns | ✅ | 3 columns, large gap |
| `list_vertical` | Vertical Stack | Single column stack | ❌ | 1 column, medium gap |
| `list_two_column_alt` | 2-Column Alternating | Alternating image positions | ❌ | 2 columns, alternating |
| `list_horizontal_scroll` | Horizontal Scroll | Scrollable horizontal | ❌ | horizontal, medium cards |
| `list_timeline` | Timeline Layout | Vertical timeline | ❌ | timeline with line |

**Config Schema:**
```json
{
  "layout": "grid|vertical|alternating|horizontal_scroll|timeline",
  "columns": 1|2|3,
  "gap": "small|medium|large",
  "card_width": "small|medium|large",
  "show_line": true|false
}
```

---

### 4. NEWS SECTION PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `news_grid` | News Grid | Grid layout | ✅ | 3 columns, show date |
| `news_featured` | Featured News | Large featured + smaller | ❌ | 1 featured article |
| `news_magazine` | Magazine Layout | Magazine-style varied sizes | ❌ | show excerpt |
| `news_list` | News List | Simple list view | ❌ | show thumbnail |
| `news_cards` | News Cards | Card-based with shadows | ❌ | 2 columns, show CTA |

**Config Schema:**
```json
{
  "layout": "grid|featured|magazine|list|cards",
  "columns": 2|3,
  "show_date": true|false,
  "show_excerpt": true|false,
  "show_thumbnail": true|false,
  "show_cta": true|false,
  "featured_count": 1
}
```

---

### 5. ROOMS SECTION PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `rooms_grid_3col` | Rooms Grid - 3 Columns | Classic 3-column grid | ✅ | 3 columns, large gap |
| `rooms_grid_2col` | Rooms Grid - 2 Columns | Wider 2-column grid | ❌ | 2 columns, large gap |
| `rooms_list` | Rooms List | Vertical list layout | ❌ | image left, list |
| `rooms_carousel` | Rooms Carousel | Horizontal scrolling | ❌ | carousel, dots |
| `rooms_luxury` | Luxury Display | Premium large images | ❌ | 2 columns, zoom effect |

**Config Schema:**
```json
{
  "layout": "grid|list|carousel|luxury",
  "columns": 2|3,
  "gap": "large|extra_large",
  "show_price": true|false,
  "show_amenities": true|false,
  "autoplay": true|false,
  "show_dots": true|false,
  "hover_effect": "lift|zoom"
}
```

---

### 6. FOOTER SECTION PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `footer_minimal` | Minimal Footer | Simple contact info | ✅ | 1 column, show social |
| `footer_three_column` | 3-Column Footer | Three-column links | ❌ | 3 columns |
| `footer_split` | Split Footer | Logo left, links right | ❌ | split, show logo |
| `footer_dark` | Dark Footer | Dark background | ❌ | dark theme |
| `footer_cta` | Footer with CTA | Prominent call-to-action | ❌ | show CTA |

**Config Schema:**
```json
{
  "layout": "minimal|three_column|split|dark|cta",
  "columns": 1|3,
  "show_social": true|false,
  "show_logo": true|false,
  "show_cta": true|false,
  "theme": "light|dark"
}
```

---

### 7. CARD STYLE PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `card_image_top` | Image on Top | Classic card | ✅ | image top, shadow |
| `card_text_only` | Text Only | No image | ❌ | centered, border |
| `card_with_icon` | With Icon | Icon-based | ❌ | icon top, centered |
| `card_price_badge` | With Price Badge | Price overlay | ❌ | badge top-right |
| `card_shadow_big` | Large Shadow | Prominent shadow | ❌ | large shadow, lift |

**Config Schema:**
```json
{
  "image_position": "top|none",
  "text_alignment": "left|center",
  "show_shadow": true|false,
  "shadow_size": "medium|large",
  "show_icon": true|false,
  "icon_position": "top",
  "show_badge": true|false,
  "badge_position": "top-right",
  "hover_effect": "lift",
  "border": true|false
}
```

---

### 8. ROOM CARD PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `room_card_standard` | Standard Room Card | Classic room card | ✅ | 250px image, all details, lift |
| `room_card_compact` | Compact Room Card | Mobile-friendly | ❌ | 200px image, minimal |
| `room_card_luxury` | Luxury Room Card | Premium large image | ❌ | 350px image, zoom, border |
| `room_card_minimal` | Minimal Room Card | Clean minimal | ❌ | 300px image, text button |
| `room_card_horizontal` | Horizontal Room Card | Wide horizontal | ❌ | image 40%, horizontal |

**Config Schema:**
```json
{
  "image_height": "200px|250px|300px|350px",
  "layout": "vertical|horizontal",
  "image_width": "40%",
  "show_occupancy": true|false,
  "show_bed_setup": true|false,
  "show_description": true|false,
  "show_price": true|false,
  "show_badge": true|false,
  "button_style": "primary|outline|text",
  "hover_effect": "lift|zoom|opacity|none",
  "border": true|false,
  "shadow": "medium|large"
}
```

---

### 9. IMAGE STYLE PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `img_rounded` | Rounded Corners | Rounded corners | ✅ | medium radius, zoom |
| `img_polaroid` | Polaroid Style | White border polaroid | ❌ | border, shadow |
| `img_circle` | Circular Image | Circle crop | ❌ | circle, 1:1 aspect |
| `img_shadowed` | With Shadow | Drop shadow | ❌ | medium shadow |
| `img_borderless` | No Border | Clean no styling | ❌ | no border, no shadow |

**Config Schema:**
```json
{
  "border_radius": "none|medium",
  "shape": "rectangle|circle",
  "aspect_ratio": "1:1|16:9",
  "hover_effect": "zoom",
  "border": true|false,
  "border_color": "white",
  "padding": "medium",
  "show_shadow": true|false,
  "shadow_size": "medium"
}
```

---

### 10. NEWS BLOCK PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `news_simple` | Simple Block | Clean simple | ✅ | medium padding, left |
| `news_featured` | Featured Block | Highlighted background | ❌ | background, border |
| `news_compact` | Compact Block | Dense spacing | ❌ | small padding, small font |
| `news_banner` | Banner Block | Full-width banner | ❌ | full width, background |
| `news_highlight` | Highlight Block | Colored background | ❌ | accent color |

**Config Schema:**
```json
{
  "padding": "small|medium|large",
  "text_alignment": "left|center",
  "background": true|false,
  "background_color": "white|accent",
  "border": true|false,
  "font_size": "small|medium",
  "width": "normal|full"
}
```

---

### 11. SECTION HEADER PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `header_centered` | Centered Header | Center-aligned | ✅ | large, centered, subtitle |
| `header_left` | Left Aligned Header | Left-aligned | ❌ | large, left, subtitle |
| `header_with_divider` | Header with Divider | Decorative line | ❌ | centered, divider |
| `header_minimal` | Minimal Header | Title only | ❌ | medium, no subtitle |
| `header_luxury` | Luxury Header | Elegant decorative | ❌ | extra large, serif, decorative |

**Config Schema:**
```json
{
  "text_alignment": "center|left",
  "title_size": "medium|large|extra_large",
  "show_subtitle": true|false,
  "show_divider": true|false,
  "divider_style": "solid|decorative",
  "font_style": "sans-serif|serif",
  "margin_bottom": "small|medium|large|extra_large"
}
```

---

### 12. PAGE THEME PRESETS (5)

| Key | Name | Description | Default | Config |
|-----|------|-------------|---------|--------|
| `theme_modern_gold` | Modern Gold | Luxury gold accents | ✅ | gold/dark blue, sans-serif |
| `theme_modern_blue` | Modern Blue | Clean modern blue | ❌ | blue/dark, sans-serif |
| `theme_minimal` | Minimal | Black & white | ❌ | black/white, serif |
| `theme_luxury_dark` | Luxury Dark | Dark elegant | ❌ | dark/gold, serif, dark mode |
| `theme_nature_forest` | Nature Forest | Earth tones | ❌ | green/brown, sans-serif |

**Config Schema:**
```json
{
  "primary_color": "#hex",
  "secondary_color": "#hex",
  "font_family": "sans-serif|serif",
  "mode": "light|dark"
}
```

---

## 📡 API Documentation

### 1. Get All Presets

```http
GET /api/public/presets/
```

**Response Structure:**
```json
{
  "section": {
    "hero": [...],
    "gallery": [...],
    "list": [...],
    "news": [...],
    "footer": [...],
    "rooms": [...]
  },
  "card": [...],
  "room_card": [...],
  "image": [...],
  "news_block": [...],
  "section_header": [...],
  "page_theme": [...]
}
```

**Example Response:**
```json
{
  "section": {
    "rooms": [
      {
        "id": 21,
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
        },
        "target_type": "section",
        "section_type": "rooms"
      }
    ]
  },
  "room_card": [
    {
      "id": 36,
      "key": "room_card_standard",
      "name": "Standard Room Card",
      "description": "Classic room card with image, details, and booking button",
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
      },
      "target_type": "room_card",
      "section_type": null
    }
  ]
}
```

---

### 2. Filter by Target Type

```http
GET /api/public/presets/?target_type=room_card
GET /api/public/presets/?target_type=section_header
GET /api/public/presets/?target_type=page_theme
```

---

### 3. Filter by Section Type

```http
GET /api/public/presets/?section_type=rooms
GET /api/public/presets/?section_type=hero
GET /api/public/presets/?target_type=section&section_type=gallery
```

---

### 4. Get Single Preset by Key

```http
GET /api/public/presets/{key}/
```

**Example:**
```http
GET /api/public/presets/rooms_grid_3col/
```

---

## 💻 Frontend Implementation

### 1. Preset Service

```javascript
// services/presetsService.js
class PresetsService {
  constructor() {
    this.presets = null;
    this.loading = false;
  }

  async fetchAll() {
    if (this.presets) return this.presets;
    
    this.loading = true;
    try {
      const response = await fetch('/api/public/presets/');
      this.presets = await response.json();
      return this.presets;
    } finally {
      this.loading = false;
    }
  }

  getPreset(key) {
    if (!this.presets) return null;
    
    // Search all preset categories
    for (const category of Object.values(this.presets)) {
      if (Array.isArray(category)) {
        const preset = category.find(p => p.key === key);
        if (preset) return preset;
      } else {
        // Section presets are nested
        for (const sectionPresets of Object.values(category)) {
          const preset = sectionPresets.find(p => p.key === key);
          if (preset) return preset;
        }
      }
    }
    return null;
  }

  getDefault(targetType, sectionType = null) {
    if (!this.presets) return null;
    
    if (sectionType && this.presets.section?.[sectionType]) {
      return this.presets.section[sectionType].find(p => p.is_default);
    }
    
    if (this.presets[targetType]) {
      return this.presets[targetType].find(p => p.is_default);
    }
    
    return null;
  }
}

export default new PresetsService();
```

---

### 2. React Context Provider

```jsx
// contexts/PresetsContext.jsx
import { createContext, useContext, useEffect, useState } from 'react';
import presetsService from '../services/presetsService';

const PresetsContext = createContext(null);

export const PresetsProvider = ({ children }) => {
  const [presets, setPresets] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    presetsService.fetchAll()
      .then(setPresets)
      .finally(() => setLoading(false));
  }, []);

  return (
    <PresetsContext.Provider value={{ presets, loading }}>
      {children}
    </PresetsContext.Provider>
  );
};

export const usePresets = () => {
  const context = useContext(PresetsContext);
  if (!context) {
    throw new Error('usePresets must be used within PresetsProvider');
  }
  return context;
};
```

---

### 3. Hook for Preset Selection

```javascript
// hooks/usePreset.js
import { useMemo } from 'react';
import { usePresets } from '../contexts/PresetsContext';

export const usePreset = (presetKey, targetType, sectionType = null) => {
  const { presets } = usePresets();

  return useMemo(() => {
    if (!presets) return null;

    // Try to find by key
    if (presetKey) {
      if (sectionType && presets.section?.[sectionType]) {
        const found = presets.section[sectionType].find(p => p.key === presetKey);
        if (found) return found;
      }
      
      if (presets[targetType]) {
        const found = presets[targetType].find(p => p.key === presetKey);
        if (found) return found;
      }
    }

    // Fallback to default
    if (sectionType && presets.section?.[sectionType]) {
      return presets.section[sectionType].find(p => p.is_default);
    }
    
    if (presets[targetType]) {
      return presets[targetType].find(p => p.is_default);
    }

    return null;
  }, [presets, presetKey, targetType, sectionType]);
};
```

---

### 4. Universal Section Component

```jsx
// components/UniversalSection.jsx
import { usePreset } from '../hooks/usePreset';
import HeroSection from './sections/HeroSection';
import GallerySection from './sections/GallerySection';
import ListSection from './sections/ListSection';
import NewsSection from './sections/NewsSection';
import RoomsSection from './sections/RoomsSection';
import FooterSection from './sections/FooterSection';

const SECTION_COMPONENTS = {
  hero: HeroSection,
  gallery: GallerySection,
  list: ListSection,
  news: NewsSection,
  rooms: RoomsSection,
  footer: FooterSection,
};

const UniversalSection = ({ section }) => {
  const sectionPreset = usePreset(
    section.style_variant,
    'section',
    section.section_type
  );

  const headerPreset = usePreset(
    section.header_style || 'header_centered',
    'section_header'
  );

  const SectionComponent = SECTION_COMPONENTS[section.section_type];
  
  if (!SectionComponent) {
    console.warn(`Unknown section type: ${section.section_type}`);
    return null;
  }

  return (
    <SectionComponent
      section={section}
      sectionPreset={sectionPreset}
      headerPreset={headerPreset}
    />
  );
};

export default UniversalSection;
```

---

### 5. Rooms Section with Presets

```jsx
// components/sections/RoomsSection.jsx
import { usePreset } from '../../hooks/usePreset';
import SectionHeader from '../SectionHeader';
import RoomCard from '../RoomCard';

const RoomsSection = ({ section, sectionPreset, headerPreset }) => {
  const cardPreset = usePreset(
    section.card_style || 'room_card_standard',
    'room_card'
  );

  const config = sectionPreset?.config || {};
  const { layout = 'grid', columns = 3, gap = 'large' } = config;

  const getLayoutClass = () => {
    switch (layout) {
      case 'grid':
        return `row row-cols-1 row-cols-md-${columns} g-${gap === 'large' ? '4' : '3'}`;
      case 'list':
        return 'd-flex flex-column gap-4';
      case 'carousel':
        return 'rooms-carousel';
      case 'luxury':
        return `row row-cols-1 row-cols-md-${columns} g-5`;
      default:
        return 'row row-cols-1 row-cols-md-3 g-4';
    }
  };

  return (
    <section className="rooms-section py-5">
      <div className="container">
        <SectionHeader
          title={section.name}
          subtitle={section.rooms_data?.subtitle}
          preset={headerPreset}
        />

        <div className={getLayoutClass()}>
          {section.rooms_data?.room_types?.map(room => (
            <RoomCard
              key={room.id}
              room={room}
              preset={cardPreset}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default RoomsSection;
```

---

### 6. Room Card Component

```jsx
// components/RoomCard.jsx
const RoomCard = ({ room, preset }) => {
  const config = preset?.config || {};
  const {
    image_height = '250px',
    layout = 'vertical',
    show_occupancy = true,
    show_bed_setup = true,
    show_description = true,
    show_price = true,
    show_badge = true,
    button_style = 'primary',
    hover_effect = 'lift',
  } = config;

  const cardClasses = `
    room-card card h-100 shadow-sm
    ${hover_effect ? `hover-${hover_effect}` : ''}
    ${layout === 'horizontal' ? 'flex-row' : ''}
  `;

  return (
    <div className="col">
      <div className={cardClasses}>
        <img
          src={room.photo}
          alt={room.name}
          className={layout === 'horizontal' ? 'card-img-left' : 'card-img-top'}
          style={{
            height: layout === 'horizontal' ? '100%' : image_height,
            width: layout === 'horizontal' ? '40%' : '100%',
            objectFit: 'cover',
          }}
        />

        <div className="card-body d-flex flex-column">
          <h5 className="card-title">{room.name}</h5>

          {(show_occupancy || show_bed_setup) && (
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
          )}

          {show_description && room.short_description && (
            <p className="card-text text-muted mb-3">
              {room.short_description}
            </p>
          )}

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

            <a
              href={room.booking_cta_url}
              className={`w-100 btn btn-${button_style}`}
            >
              <i className="bi bi-calendar-check me-2"></i>
              Book Now
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoomCard;
```

---

### 7. Section Header Component

```jsx
// components/SectionHeader.jsx
const SectionHeader = ({ title, subtitle, preset }) => {
  const config = preset?.config || {};
  const {
    text_alignment = 'center',
    title_size = 'large',
    show_subtitle = true,
    show_divider = false,
    divider_style = 'solid',
    font_style = 'sans-serif',
    margin_bottom = 'large',
  } = config;

  const titleSizeClass = {
    'medium': 'h2',
    'large': 'display-4',
    'extra_large': 'display-3',
  }[title_size] || 'h2';

  return (
    <div className={`section-header text-${text_alignment} mb-${margin_bottom === 'large' ? '5' : margin_bottom === 'medium' ? '4' : '3'}`}>
      <h2 className={`${titleSizeClass} ${font_style === 'serif' ? 'font-serif' : ''}`}>
        {title}
      </h2>
      
      {show_subtitle && subtitle && (
        <p className="section-subtitle text-muted mt-2">{subtitle}</p>
      )}
      
      {show_divider && (
        <hr className={`divider divider-${divider_style} ${text_alignment === 'center' ? 'mx-auto' : ''}`} />
      )}
    </div>
  );
};

export default SectionHeader;
```

---

## 🎛️ Staff Admin Integration

### 1. Section Settings API

```http
PATCH /api/staff/hotels/{slug}/hotel/staff/rooms-sections/{id}/
```

**Request Body:**
```json
{
  "style_variant": "rooms_grid_2col",
  "subtitle": "Discover our beautiful accommodations",
  "description": "Choose from our range of rooms and suites"
}
```

**Note:** To add header and card style selection, extend the `RoomsSection` model:

```python
# hotel/models.py - RoomsSection
class RoomsSection(models.Model):
    section = models.OneToOneField(...)
    subtitle = models.CharField(...)
    description = models.TextField(...)
    style_variant = models.CharField(...)  # Section layout preset
    
    # NEW FIELDS for granular control
    header_style = models.CharField(
        max_length=50,
        default='header_centered',
        help_text="Section header preset key"
    )
    card_style = models.CharField(
        max_length=50,
        default='room_card_standard',
        help_text="Room card preset key"
    )
```

---

### 2. Staff Preset Selector Component

```jsx
// staff/components/PresetSelector.jsx
const PresetSelector = ({ 
  presets, 
  currentKey, 
  onChange, 
  targetType, 
  sectionType = null 
}) => {
  const availablePresets = useMemo(() => {
    if (sectionType && presets?.section?.[sectionType]) {
      return presets.section[sectionType];
    }
    return presets?.[targetType] || [];
  }, [presets, targetType, sectionType]);

  return (
    <div className="preset-selector">
      <label className="form-label">Select Preset</label>
      <select 
        className="form-select"
        value={currentKey}
        onChange={(e) => onChange(e.target.value)}
      >
        {availablePresets.map(preset => (
          <option key={preset.key} value={preset.key}>
            {preset.name} {preset.is_default && '(Default)'}
          </option>
        ))}
      </select>
      
      {availablePresets.find(p => p.key === currentKey)?.description && (
        <small className="form-text text-muted">
          {availablePresets.find(p => p.key === currentKey).description}
        </small>
      )}
    </div>
  );
};
```

---

### 3. Staff Room Section Editor

```jsx
// staff/components/RoomsSectionEditor.jsx
const RoomsSectionEditor = ({ section, onUpdate }) => {
  const { presets } = usePresets();
  const [formData, setFormData] = useState({
    style_variant: section.style_variant || 'rooms_grid_3col',
    header_style: section.header_style || 'header_centered',
    card_style: section.card_style || 'room_card_standard',
    subtitle: section.subtitle || '',
    description: section.description || '',
  });

  const handleSave = async () => {
    await onUpdate(section.id, formData);
  };

  return (
    <div className="rooms-section-editor">
      <h4>Edit Rooms Section</h4>

      {/* Section Layout Preset */}
      <PresetSelector
        presets={presets}
        currentKey={formData.style_variant}
        onChange={(key) => setFormData({...formData, style_variant: key})}
        targetType="section"
        sectionType="rooms"
      />

      {/* Header Style Preset */}
      <PresetSelector
        presets={presets}
        currentKey={formData.header_style}
        onChange={(key) => setFormData({...formData, header_style: key})}
        targetType="section_header"
      />

      {/* Card Style Preset */}
      <PresetSelector
        presets={presets}
        currentKey={formData.card_style}
        onChange={(key) => setFormData({...formData, card_style: key})}
        targetType="room_card"
      />

      {/* Content Fields */}
      <div className="mb-3">
        <label>Subtitle</label>
        <input
          type="text"
          className="form-control"
          value={formData.subtitle}
          onChange={(e) => setFormData({...formData, subtitle: e.target.value})}
        />
      </div>

      <div className="mb-3">
        <label>Description</label>
        <textarea
          className="form-control"
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
        />
      </div>

      <button className="btn btn-primary" onClick={handleSave}>
        Save Changes
      </button>
    </div>
  );
};
```

---

## 🎨 CSS/SCSS Styling

```scss
// styles/presets.scss

// Hover Effects
.hover-lift {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  
  &:hover {
    transform: translateY(-8px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  }
}

.hover-zoom {
  overflow: hidden;
  
  img {
    transition: transform 0.3s ease;
  }
  
  &:hover img {
    transform: scale(1.1);
  }
}

.hover-opacity {
  transition: opacity 0.3s ease;
  
  &:hover {
    opacity: 0.9;
  }
}

// Section Headers
.section-header {
  .divider {
    width: 80px;
    height: 3px;
    border: none;
    background: var(--primary-color, #d4af37);
    margin-top: 1.5rem;
    
    &.divider-decorative {
      width: 120px;
      height: 4px;
      background: linear-gradient(
        90deg,
        transparent,
        var(--primary-color, #d4af37),
        transparent
      );
    }
  }
  
  &.text-center .divider {
    margin-left: auto;
    margin-right: auto;
  }
  
  .font-serif {
    font-family: 'Georgia', 'Times New Roman', serif;
  }
}

// Room Cards
.room-card {
  transition: all 0.3s ease;
  
  &.card-horizontal {
    flex-direction: row;
    
    .card-img-left {
      width: 40%;
      height: 100%;
      object-fit: cover;
    }
  }
}

// Rooms Carousel
.rooms-carousel {
  .carousel-item {
    padding: 0 15px;
  }
}

// Layout Gaps
.g-2 { gap: 0.5rem; }
.g-3 { gap: 1rem; }
.g-4 { gap: 1.5rem; }
.g-5 { gap: 3rem; }

// Spacing Utilities
.mb-small { margin-bottom: 1rem; }
.mb-medium { margin-bottom: 2rem; }
.mb-large { margin-bottom: 3rem; }
.mb-extra_large { margin-bottom: 4rem; }
```

---

## 🔧 Creating Custom Presets

### Via Django Admin

1. Access Django admin: `/admin/hotel/preset/`
2. Click "Add Preset"
3. Fill in fields:
   - **Target Type:** section, card, room_card, etc.
   - **Section Type:** (if target_type is "section")
   - **Key:** unique identifier (e.g., `rooms_grid_4col`)
   - **Name:** Display name
   - **Description:** Help text
   - **Is Default:** Only one per category
   - **Config:** JSON configuration

**Example Custom Preset:**
```json
{
  "target_type": "section",
  "section_type": "rooms",
  "key": "rooms_masonry",
  "name": "Rooms Masonry Layout",
  "description": "Pinterest-style masonry grid for rooms",
  "is_default": false,
  "config": {
    "layout": "masonry",
    "columns": 3,
    "gap": "small",
    "show_price": true,
    "show_amenities": true,
    "hover_effect": "zoom"
  }
}
```

---

### Via Management Command

```python
# management/commands/create_preset.py
from django.core.management.base import BaseCommand
from hotel.models import Preset

class Command(BaseCommand):
    def handle(self, *args, **options):
        Preset.objects.create(
            target_type='room_card',
            key='room_card_photo_focus',
            name='Photo Focus Card',
            description='Large photo with minimal text',
            is_default=False,
            config={
                'image_height': '400px',
                'show_occupancy': False,
                'show_bed_setup': False,
                'show_description': False,
                'show_price': True,
                'show_badge': False,
                'button_style': 'primary',
                'hover_effect': 'zoom',
            }
        )
```

---

## 📊 Preset Usage Analytics

Track which presets are most popular:

```python
# hotel/models.py
from django.db.models import Count

class PresetManager(models.Manager):
    def most_used(self, target_type=None):
        qs = self.get_queryset()
        if target_type:
            qs = qs.filter(target_type=target_type)
        
        # Count usage from PublicSection.style_variant
        # This is a simplified example
        return qs.annotate(
            usage_count=Count('publicsection__style_variant')
        ).order_by('-usage_count')

class Preset(models.Model):
    objects = PresetManager()
    # ... rest of model
```

---

## ✅ Summary

**Total Presets:** 70+
- 30 Section presets (5 types × 5-6 presets each)
- 5 Card presets
- 5 Room card presets
- 5 Image presets
- 5 News block presets
- 5 Section header presets
- 5 Page theme presets

**Key Benefits:**
- 🎨 Mix and match for unlimited combinations
- 🚀 No-code customization for staff
- 📱 Responsive designs built-in
- ♻️ Reusable across hotels
- 🔧 Easy to extend with new presets

**Frontend Integration:**
- Context provider for global access
- Custom hooks for preset selection
- Universal components with preset props
- Dynamic styling based on config
- Fallback to defaults

**Staff Admin:**
- Dropdown selectors for presets
- Live preview of changes
- Granular control (section + header + card)
- No frontend redeployment needed
