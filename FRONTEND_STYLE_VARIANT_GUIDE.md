# Frontend Implementation Guide: Style Variants (1-5 Preset System)

## Overview
The backend now supports a **style_variant** system (1-5) for all sections. Each section type can have 5 different visual styles, and you can apply them individually or globally.

---

## API Changes

### 1. **All Section Objects Now Include `style_variant`**

Every section-related object returned from the API now includes a `style_variant` field (1-5):

```typescript
interface PublicSection {
  id: number;
  position: number;
  name: string;
  style_variant: 1 | 2 | 3 | 4 | 5;  // ← NEW FIELD
  layout_preset: Preset | null;
  element: PublicElement;
}

interface HeroSection {
  id: number;
  hero_title: string;
  hero_text: string;
  hero_image_url: string;
  hero_logo_url: string;
  style_variant: 1 | 2 | 3 | 4 | 5;  // ← NEW FIELD
}

interface GalleryContainer {
  id: number;
  name: string;
  style_variant: 1 | 2 | 3 | 4 | 5;  // ← NEW FIELD
  images: GalleryImage[];
}

interface ListContainer {
  id: number;
  title: string;
  style_variant: 1 | 2 | 3 | 4 | 5;  // ← NEW FIELD
  cards: Card[];
}

interface NewsItem {
  id: number;
  title: string;
  date: string;
  summary: string;
  style_variant: 1 | 2 | 3 | 4 | 5;  // ← NEW FIELD
  content_blocks: ContentBlock[];
}
```

### 2. **New HotelPublicPage Object**

```typescript
interface HotelPublicPage {
  id: number;
  hotel: number;
  global_style_variant: 1 | 2 | 3 | 4 | 5 | null;  // ← Global preset
  created_at: string;
  updated_at: string;
}
```

### 3. **New Endpoint: Apply Global Style**

**Endpoint:** `POST /api/staff/hotel/<hotel_slug>/public-page/apply-page-style/`

**Request Body:**
```json
{
  "style_variant": 3
}
```

**Response:**
```json
{
  "message": "Applied style preset 3 to all sections",
  "public_page": {
    "id": 1,
    "hotel": 1,
    "global_style_variant": 3
  },
  "updated_sections_count": 5,
  "sections": [/* all updated sections */]
}
```

**What It Does:**
- Sets `global_style_variant` on the hotel's public page
- Updates ALL sections to use the same `style_variant`
- Updates ALL section-specific models (hero, galleries, lists, news)

---

## Frontend Implementation

### Step 1: Create Style Variant Components

For each section type, create 5 style variants:

```typescript
// Hero Variants
const HeroVariant1 = ({ data }) => (
  // Classic centered layout
);

const HeroVariant2 = ({ data }) => (
  // Split layout with image on left
);

const HeroVariant3 = ({ data }) => (
  // Full background image with overlay
);

const HeroVariant4 = ({ data }) => (
  // Minimal style
);

const HeroVariant5 = ({ data }) => (
  // Floating text layout
);
```

### Step 2: Create Style Variant Mapper

```typescript
// components/sections/HeroSection.tsx
import HeroVariant1 from './variants/HeroVariant1';
import HeroVariant2 from './variants/HeroVariant2';
import HeroVariant3 from './variants/HeroVariant3';
import HeroVariant4 from './variants/HeroVariant4';
import HeroVariant5 from './variants/HeroVariant5';

const HERO_VARIANTS = {
  1: HeroVariant1,
  2: HeroVariant2,
  3: HeroVariant3,
  4: HeroVariant4,
  5: HeroVariant5,
};

export function HeroSection({ section, heroData }) {
  const VariantComponent = HERO_VARIANTS[heroData.style_variant] || HeroVariant1;
  
  return <VariantComponent data={heroData} />;
}
```

### Step 3: Repeat for All Section Types

```typescript
// Gallery variants
const GALLERY_VARIANTS = {
  1: GalleryGrid,      // Grid layout
  2: GalleryMasonry,   // Masonry layout
  3: GallerySlider,    // Carousel slider
  4: GalleryCollage,   // Collage style
  5: GalleryTiled,     // Tiled pattern
};

// List variants
const LIST_VARIANTS = {
  1: List3Column,           // 3-column grid
  2: ListVertical,          // Vertical stack
  3: ListTwoColumnAlt,      // Alternating 2-column
  4: ListHorizontalScroll,  // Horizontal scroll
  5: ListTimeline,          // Timeline layout
};

// News variants
const NEWS_VARIANTS = {
  1: NewsSimple,     // Simple article layout
  2: NewsFeatured,   // Featured with large image
  3: NewsCompact,    // Compact list style
  4: NewsBanner,     // Banner-style header
  5: NewsHighlight,  // Highlighted boxes
};
```

### Step 4: Create Style Preset Selector UI

```typescript
// Admin component for selecting presets
export function StylePresetSelector({ sectionId, currentVariant, onUpdate }) {
  const variants = [1, 2, 3, 4, 5];
  
  return (
    <div className="preset-selector">
      <h3>Style Preset</h3>
      <div className="preset-options">
        {variants.map(variant => (
          <button
            key={variant}
            className={currentVariant === variant ? 'active' : ''}
            onClick={() => onUpdate(variant)}
          >
            Preset {variant}
            <PreviewThumbnail variant={variant} />
          </button>
        ))}
      </div>
    </div>
  );
}
```

### Step 5: Implement Global Style Preset Button

```typescript
// Admin component for applying global style
export function GlobalStylePresetButton({ hotelSlug }) {
  const [selectedVariant, setSelectedVariant] = useState(1);
  
  const applyGlobalStyle = async () => {
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/public-page/apply-page-style/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ style_variant: selectedVariant })
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      alert(`Applied Preset ${selectedVariant} to ${data.updated_sections_count} sections`);
      // Refresh page data
    }
  };
  
  return (
    <div className="global-style-control">
      <h2>Apply Page-Wide Style</h2>
      <p>Select a style preset to apply to all sections at once</p>
      
      <div className="preset-grid">
        {[1, 2, 3, 4, 5].map(variant => (
          <button
            key={variant}
            className={selectedVariant === variant ? 'selected' : ''}
            onClick={() => setSelectedVariant(variant)}
          >
            <div className="preset-preview">
              {/* Show preview thumbnails */}
            </div>
            <span>Preset {variant}</span>
          </button>
        ))}
      </div>
      
      <button 
        className="apply-btn"
        onClick={applyGlobalStyle}
      >
        Apply to All Sections
      </button>
    </div>
  );
}
```

### Step 6: Update Individual Sections

When editing a single section, update its `style_variant`:

```typescript
async function updateSectionStyle(sectionId: number, variant: number) {
  await fetch(`/api/staff/hotel/${hotelSlug}/public-sections/${sectionId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ style_variant: variant })
  });
}

// For section-specific models
async function updateHeroStyle(heroId: number, variant: number) {
  await fetch(`/api/staff/hotel/${hotelSlug}/hero-sections/${heroId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ style_variant: variant })
  });
}
```

---

## Example: Complete Hero Section Implementation

```typescript
// variants/HeroVariant1.tsx - Classic Centered
export function HeroVariant1({ data }) {
  return (
    <section className="hero-variant-1">
      <div className="hero-content centered">
        <h1>{data.hero_title}</h1>
        <p>{data.hero_text}</p>
      </div>
      {data.hero_image_url && (
        <img src={data.hero_image_url} alt="Hero" />
      )}
    </section>
  );
}

// variants/HeroVariant2.tsx - Split Layout
export function HeroVariant2({ data }) {
  return (
    <section className="hero-variant-2">
      <div className="hero-grid">
        <div className="hero-image">
          <img src={data.hero_image_url} alt="Hero" />
        </div>
        <div className="hero-content">
          <h1>{data.hero_title}</h1>
          <p>{data.hero_text}</p>
        </div>
      </div>
    </section>
  );
}

// Main component
export function HeroSection({ heroData }) {
  const variants = {
    1: HeroVariant1,
    2: HeroVariant2,
    3: HeroVariant3,
    4: HeroVariant4,
    5: HeroVariant5,
  };
  
  const Component = variants[heroData.style_variant] || variants[1];
  
  return <Component data={heroData} />;
}
```

---

## CSS Strategy

Create modular CSS for each variant:

```css
/* hero-variant-1.css - Classic Centered */
.hero-variant-1 {
  text-align: center;
  padding: 80px 20px;
}

.hero-variant-1 .hero-content {
  max-width: 800px;
  margin: 0 auto;
}

/* hero-variant-2.css - Split Layout */
.hero-variant-2 .hero-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  align-items: center;
}

.hero-variant-2 .hero-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

---

## Quick Start Checklist

- [ ] Update TypeScript interfaces to include `style_variant`
- [ ] Create 5 variant components for each section type (Hero, Gallery, List, News)
- [ ] Create variant mapper objects
- [ ] Update section renderers to use variant mappers
- [ ] Build style preset selector UI
- [ ] Implement global style preset button
- [ ] Create CSS for all variants
- [ ] Test switching between variants
- [ ] Test applying global presets
- [ ] Add preview thumbnails for each preset

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/staff/hotel/<slug>/public-page/apply-page-style/` | POST | Apply global style to all sections |
| `/api/staff/hotel/<slug>/public-sections/<id>/` | PATCH | Update individual section style |
| `/api/staff/hotel/<slug>/hero-sections/<id>/` | PATCH | Update hero section style |
| `/api/staff/hotel/<slug>/gallery-containers/<id>/` | PATCH | Update gallery style |
| `/api/staff/hotel/<slug>/list-containers/<id>/` | PATCH | Update list style |
| `/api/staff/hotel/<slug>/news-items/<id>/` | PATCH | Update news item style |

---

## Notes

- `style_variant` defaults to `1` for all new sections
- `global_style_variant` can be `null` (no global preset set)
- When you apply a global preset, it overwrites all individual section styles
- Each section type can have completely different implementations for the same variant number
- Variant 1 = most common/default style, Variants 2-5 = alternative styles
