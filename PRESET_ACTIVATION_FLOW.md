# How Frontend Gets Numbers and Applies Presets

## 1. Backend Sends Numbers in API Response

When frontend calls `/api/public/hotel/killarney/page/`, backend returns:

```json
{
  "hotel": {
    "id": 1,
    "name": "Killarney Hotel"
  },
  "sections": [
    {
      "id": 10,
      "position": 1,
      "name": "Hero",
      "style_variant": 3,  // ← NUMBER HERE
      "hero_data": {
        "id": 5,
        "hero_title": "Welcome to Killarney",
        "hero_text": "Your perfect getaway",
        "hero_image_url": "https://...",
        "style_variant": 3  // ← ALSO HERE
      }
    },
    {
      "id": 11,
      "position": 2,
      "name": "Gallery",
      "style_variant": 2,  // ← NUMBER HERE
      "galleries": [
        {
          "id": 8,
          "name": "Main Gallery",
          "style_variant": 2,  // ← ALSO HERE
          "images": [...]
        }
      ]
    },
    {
      "id": 12,
      "position": 3,
      "name": "Rooms",
      "style_variant": 1,  // ← NUMBER HERE
      "lists": [
        {
          "id": 3,
          "title": "Our Rooms",
          "style_variant": 1,  // ← ALSO HERE
          "cards": [
            {
              "id": 15,
              "title": "Deluxe Room",
              "style_preset": {
                "id": 20,
                "key": "card_price_badge",
                "name": "Card with Price Badge"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 2. Frontend Receives Data and Maps Numbers

### Step 1: Fetch the page data
```typescript
// pages/HotelPublicPage.tsx
const [pageData, setPageData] = useState(null);

useEffect(() => {
  fetch(`/api/public/hotel/${slug}/page/`)
    .then(res => res.json())
    .then(data => setPageData(data));
}, [slug]);
```

### Step 2: Loop through sections and render based on type
```typescript
// pages/HotelPublicPage.tsx
return (
  <div className="hotel-page">
    <h1>{pageData.hotel.name}</h1>
    
    {pageData.sections.map(section => {
      // Check what data exists to determine section type
      if (section.hero_data) {
        return <HeroSection key={section.id} section={section} />;
      }
      if (section.galleries) {
        return <GallerySection key={section.id} section={section} />;
      }
      if (section.lists) {
        return <ListSection key={section.id} section={section} />;
      }
      if (section.news_items) {
        return <NewsSection key={section.id} section={section} />;
      }
      return null;
    })}
  </div>
);
```

---

## 3. Each Section Component Maps Number to Preset Component

### Hero Section Example
```typescript
// components/sections/HeroSection.tsx
import HeroPreset1 from './presets/HeroPreset1';
import HeroPreset2 from './presets/HeroPreset2';
import HeroPreset3 from './presets/HeroPreset3';
import HeroPreset4 from './presets/HeroPreset4';
import HeroPreset5 from './presets/HeroPreset5';

const HERO_PRESETS = {
  1: HeroPreset1,  // Classic centered
  2: HeroPreset2,  // Split layout
  3: HeroPreset3,  // Full background
  4: HeroPreset4,  // Minimal
  5: HeroPreset5,  // Floating card
};

export function HeroSection({ section }) {
  const heroData = section.hero_data;
  
  // Get the number from API
  const variantNumber = heroData.style_variant; // 3
  
  // Map number to component
  const PresetComponent = HERO_PRESETS[variantNumber] || HERO_PRESETS[1];
  
  // Render that component
  return <PresetComponent data={heroData} />;
}
```

### Gallery Section Example
```typescript
// components/sections/GallerySection.tsx
import GalleryPreset1 from './presets/GalleryPreset1'; // Grid
import GalleryPreset2 from './presets/GalleryPreset2'; // Masonry
import GalleryPreset3 from './presets/GalleryPreset3'; // Slider
import GalleryPreset4 from './presets/GalleryPreset4'; // Collage
import GalleryPreset5 from './presets/GalleryPreset5'; // Tiled

const GALLERY_PRESETS = {
  1: GalleryPreset1,
  2: GalleryPreset2,
  3: GalleryPreset3,
  4: GalleryPreset4,
  5: GalleryPreset5,
};

export function GallerySection({ section }) {
  return (
    <div className="gallery-section">
      {section.galleries.map(gallery => {
        // Get the number from API
        const variantNumber = gallery.style_variant; // 2
        
        // Map number to component
        const PresetComponent = GALLERY_PRESETS[variantNumber] || GALLERY_PRESETS[1];
        
        // Render that component
        return (
          <PresetComponent 
            key={gallery.id}
            gallery={gallery}
          />
        );
      })}
    </div>
  );
}
```

### List/Cards Section Example
```typescript
// components/sections/ListSection.tsx
import ListPreset1 from './presets/ListPreset1'; // 3-column grid
import ListPreset2 from './presets/ListPreset2'; // Vertical stack
import ListPreset3 from './presets/ListPreset3'; // 2-column alternating
import ListPreset4 from './presets/ListPreset4'; // Horizontal scroll
import ListPreset5 from './presets/ListPreset5'; // Timeline

const LIST_PRESETS = {
  1: ListPreset1,
  2: ListPreset2,
  3: ListPreset3,
  4: ListPreset4,
  5: ListPreset5,
};

export function ListSection({ section }) {
  return (
    <div className="list-section">
      {section.lists.map(list => {
        // Get the number from API
        const variantNumber = list.style_variant; // 1
        
        // Map number to component
        const PresetComponent = LIST_PRESETS[variantNumber] || LIST_PRESETS[1];
        
        // Render that component
        return (
          <PresetComponent 
            key={list.id}
            list={list}
          />
        );
      })}
    </div>
  );
}
```

---

## 4. Preset Components Render Different HTML/CSS

### HeroPreset1.tsx (Classic Centered)
```typescript
export function HeroPreset1({ data }) {
  return (
    <section className="hero-preset-1">
      <div className="container">
        <div className="hero-content centered">
          <h1 className="hero-title">{data.hero_title}</h1>
          <p className="hero-text">{data.hero_text}</p>
        </div>
        {data.hero_image_url && (
          <img 
            src={data.hero_image_url} 
            alt={data.hero_title}
            className="hero-image"
          />
        )}
      </div>
    </section>
  );
}
```

### HeroPreset3.tsx (Full Background)
```typescript
export function HeroPreset3({ data }) {
  return (
    <section 
      className="hero-preset-3"
      style={{
        backgroundImage: `url(${data.hero_image_url})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center'
      }}
    >
      <div className="overlay"></div>
      <div className="hero-content">
        <h1 className="hero-title-large">{data.hero_title}</h1>
        <p className="hero-text-overlay">{data.hero_text}</p>
      </div>
    </section>
  );
}
```

---

## 5. Complete Flow Example

```
1. User visits: /hotels/killarney
   
2. Frontend fetches: GET /api/public/hotel/killarney/page/
   
3. Backend returns:
   {
     "sections": [
       {
         "hero_data": {
           "style_variant": 3,  // ← Backend sends number
           "hero_title": "Welcome",
           "hero_image_url": "..."
         }
       }
     ]
   }

4. Frontend receives style_variant: 3

5. Frontend maps: HERO_PRESETS[3] → HeroPreset3 component

6. Frontend renders: <HeroPreset3 data={heroData} />

7. User sees: Full background hero section with overlay
```

---

## 6. Admin Panel: Changing Presets

### Individual Section Update
```typescript
// Admin component
async function updateHeroPreset(heroId, newVariant) {
  await fetch(`/api/staff/hotel/killarney/hero-sections/${heroId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      style_variant: newVariant  // Send new number (1-5)
    })
  });
  
  // Refresh page to see changes
  window.location.reload();
}

// Usage
<button onClick={() => updateHeroPreset(5, 2)}>
  Change to Preset 2
</button>
```

### Global Page Preset
```typescript
// Admin component
async function applyGlobalPreset(variant) {
  await fetch(`/api/staff/hotel/killarney/public-page/apply-page-style/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      style_variant: variant  // Send number (1-5)
    })
  });
  
  // This updates ALL sections to use the same variant
  window.location.reload();
}

// Usage
<button onClick={() => applyGlobalPreset(3)}>
  Apply Preset 3 to Entire Page
</button>
```

---

## Summary

1. **Backend stores:** `style_variant: 3` (just a number)
2. **Frontend receives:** `style_variant: 3` in JSON
3. **Frontend maps:** `PRESETS[3] → PresetComponent3`
4. **Frontend renders:** `<PresetComponent3 data={...} />`
5. **User sees:** The visual design of preset 3

**The number is the bridge between backend and frontend. Backend doesn't know what "preset 3" looks like - frontend decides that!**
