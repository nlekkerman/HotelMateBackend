# 📂 OPENING VALUES - Display Guide for Frontend

## What Are Opening Values?

**Opening values** = Stock on hand at the START of the stocktake period

**Fields from backend:**
- `current_full_units` - Full units (cases, bottles, kegs, boxes)
- `current_partial_units` - Partial units (bottles, ml, pints, liters, fractional)

---

## Display Formats by Category

### SYRUPS - Combine Both Fields
```javascript
// Backend sends:
{
  item_code: "M13",
  name: "Monin Coconut Syrup 700ML",
  current_full_units: 15,
  current_partial_units: 0.60
}

// Display as single decimal:
const opening = current_full_units + current_partial_units;
// Shows: "15.60 bottles"
```

**Format:** `"15.60 bottles"` or just `"15.60"`

---

### SOFT_DRINKS - Show Separately
```javascript
// Backend sends:
{
  item_code: "M2105",
  name: "Split Coke Diet",
  current_full_units: 12,
  current_partial_units: 2
}

// Display separately:
// Shows: "12 cases, 2 bottles"
```

**Format:** `"12 cases, 2 bottles"`

---

### JUICES - Show Cases + Decimal Bottles
```javascript
// Backend sends:
{
  item_code: "M11",
  name: "Kulana Litre Juices",
  current_full_units: 59,
  current_partial_units: 8.50
}

// Display:
// Shows: "59 cases, 8.50 bottles"
```

**Format:** `"59 cases, 8.50 bottles"`

---

### CORDIALS - Show Separately
```javascript
// Backend sends:
{
  item_code: "M15",
  name: "Rose's Lime Cordial",
  current_full_units: 4,
  current_partial_units: 7
}

// Display:
// Shows: "4 cases, 7 bottles"
```

**Format:** `"4 cases, 7 bottles"`

---

### BIB (Bag-in-Box) - Show Separately
```javascript
// Backend sends:
{
  item_code: "M23",
  name: "Splash White 18LTR",
  current_full_units: 2,
  current_partial_units: 5.80
}

// Display:
// Shows: "2 boxes, 5.80 liters"
```

**Format:** `"2 boxes, 5.80 liters"`

---

### SPIRITS - Two Display Options
```javascript
// Backend sends:
{
  item_code: "S002",
  name: "Gordans Pink Litre",
  current_full_units: 7,
  current_partial_units: 0.60
}

// Option 1: Separate (like Django admin)
// Shows: "7.00 + 0.60"

// Option 2: Combined
const total = current_full_units + current_partial_units;
// Shows: "7.60 bottles"
```

**Format:** `"7.00 + 0.60"` OR `"7.60 bottles"`

---

### WINE - Same as Spirits
```javascript
// Backend sends:
{
  item_code: "W001",
  name: "House Red Wine",
  current_full_units: 12,
  current_partial_units: 0.50
}

// Option 1: "12.00 + 0.50"
// Option 2: "12.50 bottles"
```

**Format:** `"12.00 + 0.50"` OR `"12.50 bottles"`

---

### DRAUGHT - Show Separately
```javascript
// Backend sends:
{
  item_code: "D001",
  name: "Guinness Keg",
  current_full_units: 3,
  current_partial_units: 12
}

// Display:
// Shows: "3 kegs, 12 pints"
```

**Format:** `"3 kegs, 12 pints"`

---

### BOTTLED BEER - Show Separately
```javascript
// Backend sends:
{
  item_code: "B001",
  name: "Heineken Bottle",
  current_full_units: 8,
  current_partial_units: 10
}

// Display:
// Shows: "8 cases, 10 bottles"
```

**Format:** `"8 cases, 10 bottles"`

---

## Summary Table

| Category | Display Format | Example |
|----------|----------------|---------|
| **SYRUPS** | `"{full + partial} bottles"` | `"15.60 bottles"` |
| **SOFT_DRINKS** | `"{full} cases, {partial} bottles"` | `"12 cases, 2 bottles"` |
| **JUICES** | `"{full} cases, {partial} bottles"` | `"59 cases, 8.50 bottles"` |
| **CORDIALS** | `"{full} cases, {partial} bottles"` | `"4 cases, 7 bottles"` |
| **BIB** | `"{full} boxes, {partial} liters"` | `"2 boxes, 5.80 liters"` |
| **DRAUGHT** | `"{full} kegs, {partial} pints"` | `"3 kegs, 12 pints"` |
| **BOTTLED** | `"{full} cases, {partial} bottles"` | `"8 cases, 10 bottles"` |
| **SPIRITS** | `"{full}.00 + {partial}"` OR combined | `"7.00 + 0.60"` or `"7.60"` |
| **WINE** | `"{full}.00 + {partial}"` OR combined | `"12.00 + 0.50"` or `"12.50"` |

---

## Frontend Helper Function

```javascript
function formatOpeningValue(item) {
  const { category, subcategory, current_full_units, current_partial_units } = item;
  
  // MINERALS
  if (category === 'M') {
    if (subcategory === 'SYRUPS') {
      const total = current_full_units + current_partial_units;
      return `${total.toFixed(2)} bottles`;
    }
    
    if (subcategory === 'SOFT_DRINKS' || subcategory === 'CORDIALS') {
      return `${current_full_units} cases, ${current_partial_units} bottles`;
    }
    
    if (subcategory === 'JUICES') {
      return `${current_full_units} cases, ${current_partial_units.toFixed(2)} bottles`;
    }
    
    if (subcategory === 'BIB') {
      return `${current_full_units} boxes, ${current_partial_units.toFixed(2)} liters`;
    }
  }
  
  // DRAUGHT
  if (category === 'D') {
    return `${current_full_units} kegs, ${current_partial_units} pints`;
  }
  
  // BOTTLED BEER
  if (category === 'B') {
    return `${current_full_units} cases, ${current_partial_units} bottles`;
  }
  
  // SPIRITS
  if (category === 'S') {
    // Option 1: Separate
    return `${current_full_units.toFixed(2)} + ${current_partial_units.toFixed(2)}`;
    
    // Option 2: Combined
    // const total = current_full_units + current_partial_units;
    // return `${total.toFixed(2)} bottles`;
  }
  
  // WINE
  if (category === 'W') {
    // Option 1: Separate
    return `${current_full_units.toFixed(2)} + ${current_partial_units.toFixed(2)}`;
    
    // Option 2: Combined
    // const total = current_full_units + current_partial_units;
    // return `${total.toFixed(2)} bottles`;
  }
  
  // Fallback
  return `${current_full_units} + ${current_partial_units}`;
}
```

---

## Example API Response

```json
{
  "item_code": "M13",
  "name": "Monin Coconut Syrup 700ML",
  "category": "M",
  "subcategory": "SYRUPS",
  "current_full_units": 15,
  "current_partial_units": 0.60,
  "total_stock_in_servings": 311.60
}
```

**Frontend displays:** `"Opening: 15.60 bottles"`

---

## Key Points

✅ **SYRUPS:** Always combine `full + partial` for display  
✅ **SOFT_DRINKS, CORDIALS, BOTTLED:** Show separately (cases + bottles)  
✅ **JUICES:** Show cases + decimal bottles (e.g., `8.50`)  
✅ **SPIRITS/WINE:** Can show separate (`7.00 + 0.60`) or combined (`7.60`)  
✅ **Use helper function** to handle all categories automatically  
✅ **Decimal precision:** 2 decimal places for fractional values
