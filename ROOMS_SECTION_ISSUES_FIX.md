# 🚨 Rooms Section Issues & Fixes

## Issues Identified from Console Logs

### 1. **Preset Key Mismatch** ❌
- **Problem:** Section has `style_variant: 2` (numeric)
- **Expected:** String keys like `"rooms_grid_3col"`, `"rooms_grid_2col"`
- **Error:** `[usePreset] Preset key "2" not found. Falling back to default.`

### 2. **Price Field Mismatch** ❌
- **Problem:** Code looks for `starting_price_from`, `price`, `base_price`
- **Reality:** API returns `current_price: 129`, `original_price: 129`, `price_display: "€129"`
- **Result:** All rooms show fallback "EUR 89.00"

### 3. **Missing Default Presets** ❌
- **Problem:** No defaults found for `targetType="section"`, `sectionType="rooms"`
- **Error:** `[usePreset] No default preset found`

---

## 🔧 Fix Implementation

### Fix 1: Map Numeric Style Variants to Preset Keys

```javascript
// In RoomsSectionView.jsx - Add preset mapping
const getPresetKeyFromVariant = (variant) => {
  const presetMap = {
    1: 'rooms_grid_3col',     // Default 3-column grid
    2: 'rooms_grid_2col',     // 2-column grid
    3: 'rooms_list',          // List layout
    4: 'rooms_carousel',      // Carousel
    5: 'rooms_luxury'         // Luxury layout
  };
  return presetMap[variant] || 'rooms_grid_3col';
};

// Usage
const sectionPresetKey = getPresetKeyFromVariant(section.style_variant);
const sectionPreset = usePreset(sectionPresetKey, 'section', 'rooms');
```

### Fix 2: Use Correct Price Fields

```javascript
// Fix price extraction in room processing
const getLowestPrice = (rooms) => {
  if (!rooms || rooms.length === 0) return null;
  
  const prices = rooms
    .map(room => room.current_price) // Use current_price, not starting_price_from
    .filter(price => price != null && !isNaN(price));
  
  if (prices.length === 0) return null;
  return Math.min(...prices);
};

// In room type grouping
uniqueRoomTypes[room.room_type_name] = {
  name: room.room_type_name,
  code: room.room_type_code,
  starting_price: lowestPrice 
    ? `${room.currency} ${lowestPrice.toFixed(2)}` 
    : `${room.currency} ${room.current_price?.toFixed(2) || '0.00'}`, // Fallback to current_price
  photo: room.photo,
  short_description: room.short_description,
  max_occupancy: room.max_occupancy,
  bed_setup: room.bed_setup,
  booking_cta_url: room.booking_cta_url
};
```

### Fix 3: Add Preset Fallbacks

```javascript
// Add fallback configurations
const getDefaultSectionConfig = () => ({
  layout: 'grid',
  columns: 3,
  gap: 'large',
  show_price: true,
  show_amenities: true
});

const getDefaultHeaderConfig = () => ({
  text_alignment: 'center',
  title_size: 'large',
  show_subtitle: true,
  show_divider: false,
  margin_bottom: 'large'
});

const getDefaultCardConfig = () => ({
  image_height: '250px',
  show_occupancy: true,
  show_bed_setup: true,
  show_description: true,
  show_price: true,
  show_badge: true,
  button_style: 'primary',
  hover_effect: 'lift'
});
```

---

## 🎯 Complete Fixed Component Structure

```javascript
const RoomsSectionView = ({ section }) => {
  // 1. MAP NUMERIC VARIANT TO PRESET KEY
  const getPresetKeyFromVariant = (variant) => {
    const presetMap = {
      1: 'rooms_grid_3col',
      2: 'rooms_grid_2col', 
      3: 'rooms_list',
      4: 'rooms_carousel',
      5: 'rooms_luxury'
    };
    return presetMap[variant] || 'rooms_grid_3col';
  };

  // 2. GET PRESETS WITH FALLBACKS
  const sectionPresetKey = getPresetKeyFromVariant(section.style_variant);
  const sectionPreset = usePreset(sectionPresetKey, 'section', 'rooms');
  const headerPreset = usePreset('header_centered', 'section_header');
  const cardPreset = usePreset('room_card_standard', 'room_card');

  // 3. USE CORRECT PRICE FIELDS
  const processedRoomTypes = useMemo(() => {
    if (!section.rooms_data?.room_types) return [];

    const uniqueRoomTypes = {};

    section.rooms_data.room_types.forEach(room => {
      const roomTypeName = room.room_type_name;
      
      if (!uniqueRoomTypes[roomTypeName]) {
        // Use current_price instead of starting_price_from
        const price = room.current_price || 0;
        
        uniqueRoomTypes[roomTypeName] = {
          name: room.room_type_name,
          code: room.room_type_code,
          starting_price: `${room.currency} ${price.toFixed(2)}`, // Fixed!
          photo: room.photo,
          short_description: room.short_description,
          max_occupancy: room.max_occupancy,
          bed_setup: room.bed_setup,
          booking_cta_url: room.booking_cta_url
        };
      } else {
        // Update with lower price if found
        const existingPrice = parseFloat(uniqueRoomTypes[roomTypeName].starting_price.split(' ')[1]);
        const newPrice = room.current_price || 0;
        
        if (newPrice < existingPrice) {
          uniqueRoomTypes[roomTypeName].starting_price = `${room.currency} ${newPrice.toFixed(2)}`;
        }
      }
    });

    return Object.values(uniqueRoomTypes);
  }, [section.rooms_data?.room_types]);

  // 4. FALLBACK CONFIGS
  const sectionConfig = sectionPreset?.config || getDefaultSectionConfig();
  const headerConfig = headerPreset?.config || getDefaultHeaderConfig();
  const cardConfig = cardPreset?.config || getDefaultCardConfig();

  return (
    <section className="rooms-section">
      <SectionHeader 
        title={section.name}
        subtitle={section.rooms_data?.subtitle}
        config={headerConfig}
      />
      
      <RoomsLayout config={sectionConfig}>
        {processedRoomTypes.map(room => (
          <RoomCard 
            key={room.code}
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

## 🚀 Expected Results After Fix

- ✅ Preset "2" maps to "rooms_grid_2col" 
- ✅ Prices show actual values: €129, €120, €102, €96 instead of €89.00
- ✅ No more "Preset not found" errors
- ✅ Proper fallback configurations when presets missing
- ✅ Correct room type grouping with lowest prices

---

## 🧪 Testing Checklist

- [ ] Section style_variant 2 uses 2-column grid layout
- [ ] Room prices show real API values (€96-€129)
- [ ] No console errors about missing presets
- [ ] Header and card presets work correctly
- [ ] Fallback configs applied when presets unavailable