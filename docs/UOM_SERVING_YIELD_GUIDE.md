# UOM & Serving Yield Logic Guide

## Overview
This guide explains the UOM (Units of Measure) and serving yield calculations for stock items in the Hotel Mate backend system.

## Key Concepts

### What is UOM?
**UOM** = Units of Measure per purchase unit
- For **cases**: Number of bottles/units per case (e.g., 12 bottles)
- For **kegs**: Number of pints per keg (e.g., 35.2 pints for 20L keg)
- For **spirits**: Number of shots per bottle (e.g., 20-28 shots)

### Base Unit System
All stock calculations use **base units**:
- Liquids: **ml** (milliliters)
- Solids: **g** (grams)
- Countable items: **pieces**

---

## Product Type Rules

### 1. Bottled Beer

**Purchase Unit:** Case (dozen)
**Sellable Unit:** Individual bottle

| Field | Example Value | Description |
|-------|---------------|-------------|
| `size` | "330ml" or "500ml" | Bottle size |
| `size_value` | 330 | Numeric size |
| `size_unit` | "ml" | Unit |
| `uom` | 12 or 24 | Bottles per case |
| `serving_size` | 330 | Full bottle serving |
| `servings_per_unit` | 1 | One bottle = one serving |

**Frontend Display:**
```
Heineken 330ml
UOM: 12 bottles/case
Yield: 1 per bottle
```

---

### 2. Spirits & Liqueurs

**Purchase Unit:** Bottle (70cl or 1L)
**Sellable Unit:** Shot/Pour

| Field | Example Value | Description |
|-------|---------------|-------------|
| `size` | "70cl" or "1L" | Bottle size |
| `size_value` | 70 or 100 | Numeric size |
| `size_unit` | "cl" or "L" | Unit |
| `uom` | 6 or 12 | Bottles per case (if buying by case) |
| `serving_size` | 25 or 35 | ml per shot |
| `shots_per_bottle` | 20-28 | Calculated shots |
| `servings_per_unit` | 20-28 | Same as shots |

**Shot Size Standards:**
- UK Standard: 25ml or 35ml
- Ireland Standard: 35.5ml
- Double: 50ml

**Calculations:**
```
70cl bottle = 700ml
Standard shot = 25ml
shots_per_bottle = 700 / 25 = 28 shots

If shot = 35ml:
shots_per_bottle = 700 / 35 = 20 shots
```

**Frontend Display:**
```
Smirnoff Vodka 70cl
UOM: 12 bottles/case
Yield: 28 shots per bottle (25ml pour)
```

---

### 3. Draught Beer (Kegs)

**Purchase Unit:** Keg (20L, 30L, 50L)
**Sellable Units:** Pint or Half-Pint

| Field | Example Value | Description |
|-------|---------------|-------------|
| `size` | "30L" or "50L" | Keg size |
| `size_value` | 30 or 50 | Numeric size |
| `size_unit` | "L" or "Lt" | Liters |
| `uom` | 52.8 or 88.0 | Pints per keg |
| `serving_size` | 568 | ml per pint (UK) |
| `pints_per_keg` | 52.8 or 88.0 | Calculated pints |
| `half_pints_per_keg` | 105.6 or 176.0 | Calculated half-pints |

**Pint Standards:**
- UK Imperial Pint: 568ml
- Half-Pint: 284ml

**Standard Keg Yields:**

| Keg Size | Liters | Pints | Half-Pints | Common Use | Your Stock |
|----------|--------|-------|------------|------------|------------|
| Small | **20L** | **35.2** | **70.4** | **Specialty beers** | **1 brand** |
| **Medium** | **30L** | **52.8** | **105.6** | **Most common** | **11 brands** ⭐ |
| **Large** | **50L** | **88.0** | **176.0** | **High-volume venues** | **3 brands** |

**Important:** Each keg size requires a **separate SKU/stock item**
- Example from your data:
  - `D0004` = Heineken 30L (30Lt, 52.8 pints)
  - `D0030` = Heineken 50L (50Lt, 88.0 pints)
  - `D2133` = Heineken 00% 20L (20Lt, 35.2 pints)

**Calculations:**
```
30L keg = 30,000ml
1 pint = 568ml
pints_per_keg = 30,000 / 568 = 52.8 pints
half_pints_per_keg = 52.8 × 2 = 105.6 half-pints
```

**Frontend Display:**
```
Guinness 30L Keg
UOM: 52.8 pints/keg
Yield: 52.8 pints (105.6 half-pints)
```

---

## API Response Fields

### StockItem Serializer Fields

```json
{
  "id": 1,
  "sku": "S0001",
  "name": "Smirnoff Vodka",
  "size": "70cl",
  "size_value": "70.00",
  "size_unit": "cl",
  "uom": "12.00",
  "product_type": "Spirit",
  "serving_size": "25.00",
  "serving_unit": "ml",
  
  // Calculated yields (read-only)
  "servings_per_unit": "28.00",
  "shots_per_bottle": "28.0",
  "pints_per_keg": null,
  "half_pints_per_keg": null
}
```

### Field Descriptions

| Field | Type | Editable | Description |
|-------|------|----------|-------------|
| `size` | string | Yes | Display size (e.g., "70cl") |
| `size_value` | decimal | Yes | Numeric size (e.g., 70) |
| `size_unit` | string | Yes | Unit (ml, cl, L, Lt) |
| `uom` | decimal | Yes | Units per case/keg |
| `product_type` | string | Yes | Spirit, Beer, Draught, Wine, etc. |
| `serving_size` | decimal | Yes | ml per serving |
| `serving_unit` | string | Yes | Usually "ml" |
| `servings_per_unit` | decimal | **Read-only** | Auto-calculated servings |
| `shots_per_bottle` | decimal | **Read-only** | For spirits only |
| `pints_per_keg` | decimal | **Read-only** | For draught only |
| `half_pints_per_keg` | decimal | **Read-only** | For draught only |

---

## Frontend Implementation

### 1. Display Logic

```typescript
interface StockItem {
  id: number;
  name: string;
  size: string;
  product_type: string;
  uom: number;
  
  // Calculated yields
  servings_per_unit?: number;
  shots_per_bottle?: number;
  pints_per_keg?: number;
  half_pints_per_keg?: number;
}

function displayYield(item: StockItem): string {
  switch(item.product_type) {
    case 'Spirit':
    case 'Liqueur':
      return `${item.shots_per_bottle} shots per bottle`;
    
    case 'Draught':
      return `${item.pints_per_keg} pints (${item.half_pints_per_keg} half-pints)`;
    
    case 'Beer':
    case 'Bottled Beer':
      return `${item.uom} bottles per case`;
    
    default:
      return item.servings_per_unit 
        ? `${item.servings_per_unit} servings`
        : `${item.uom} units`;
  }
}
```

### 2. Example UI Table

```tsx
<Table>
  <thead>
    <tr>
      <th>Item</th>
      <th>Size</th>
      <th>Type</th>
      <th>UOM</th>
      <th>Yield</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Smirnoff Vodka</td>
      <td>70cl</td>
      <td>Spirit</td>
      <td>12 btl/case</td>
      <td>28 shots/bottle</td>
    </tr>
    <tr>
      <td>Guinness Keg</td>
      <td>30L</td>
      <td>Draught</td>
      <td>52.8 pints</td>
      <td>52.8 pints (105.6 half)</td>
    </tr>
    <tr>
      <td>Heineken Bottle</td>
      <td>330ml</td>
      <td>Beer</td>
      <td>24 btl/case</td>
      <td>1 per bottle</td>
    </tr>
  </tbody>
</Table>
```

### 3. Auto-Calculate on Form

```typescript
function calculateServings(item: Partial<StockItem>) {
  if (!item.size_value || !item.serving_size) return null;
  
  // Convert size to ml
  const sizeInMl = convertToMl(item.size_value, item.size_unit);
  
  // Calculate servings
  return Math.round((sizeInMl / item.serving_size) * 100) / 100;
}

function convertToMl(value: number, unit: string): number {
  const conversions = {
    'ml': 1,
    'cl': 10,
    'L': 1000,
    'Lt': 1000,
  };
  return value * (conversions[unit] || 1);
}
```

---

## Stocktake Considerations

### When Counting Stock

**Draught Beer:**
- Count full kegs + partial kegs in pints
- Example: `counted_full_units = 2, counted_partial_units = 26.5`
- Means: 2 full 30L kegs + 26.5 pints from an opened keg

**Spirits:**
- Count full bottles + partial bottle (in shots or ml)
- Example: `counted_full_units = 5, counted_partial_units = 15`
- Means: 5 full bottles + 15 shots (375ml) from opened bottle

**Bottled Beer:**
- Count full cases + individual bottles
- Example: `counted_full_units = 3, counted_partial_units = 8`
- Means: 3 full cases (36 bottles) + 8 loose bottles

### Conversion to Base Units

The system automatically converts mixed units:
```
counted_qty = (counted_full_units × UOM) + counted_partial_units
```

**Example - 30L Keg:**
- `uom = 52.8` pints per keg
- `counted_full_units = 2` kegs
- `counted_partial_units = 26.5` pints
- `counted_qty = (2 × 52.8) + 26.5 = 132.1 pints`
- Converted to ml: `132.1 × 568 = 75,032.8ml`

---

## Product Type Reference

| Product Type | UOM Meaning | Serving Unit | Yield Fields |
|--------------|-------------|--------------|--------------|
| Spirit | Bottles/case | Shot (25-35ml) | `shots_per_bottle` |
| Liqueur | Bottles/case | Shot (25ml) | `shots_per_bottle` |
| Draught | Pints/keg | Pint (568ml) | `pints_per_keg`, `half_pints_per_keg` |
| Beer | Bottles/case | Bottle | `servings_per_unit` |
| Wine | Bottles/case | Glass (125-175ml) | `servings_per_unit` |
| Soft Drink | Units/case | Serving | `servings_per_unit` |

---

## Summary for Frontend Developers

### Key Points:
1. **UOM is editable** - User sets this based on supplier packaging
2. **Yields are auto-calculated** - Backend computes servings based on size + serving_size
3. **Different displays per type**:
   - Spirits → shots per bottle
   - Draught → pints and half-pints per keg
   - Bottled → bottles per case
4. **Always show both** size and yield for clarity
5. **Base units (ml)** are used for all backend calculations
6. **Mixed unit counting** supported in stocktakes

### API Endpoints:
- `GET /api/stock-tracker/stock-items/` - Returns all calculated yields
- `PATCH /api/stock-tracker/stock-items/{id}/` - Update size/serving to recalculate yields

### Need Help?
- See `stock_tracker/models.py` for calculation formulas
- See `stock_tracker/stock_serializers.py` for API fields
- Contact backend team for custom yield calculations
