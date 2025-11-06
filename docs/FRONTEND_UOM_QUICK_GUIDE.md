# Frontend UOM Display - Quick Guide

## TL;DR
The backend automatically calculates serving yields. Just display them based on product type!

---

## API Fields You'll Get

```typescript
interface StockItem {
  id: number;
  name: string;
  size: string;              // e.g., "30L", "70cl", "330ml"
  product_type: string;      // "Draught", "Spirit", "Beer", etc.
  uom: string;               // Units per case/keg
  
  // ⭐ AUTO-CALCULATED YIELDS (Read-only)
  pints_per_keg?: number;        // For Draught only
  half_pints_per_keg?: number;   // For Draught only
  shots_per_bottle?: number;     // For Spirits only
  servings_per_unit?: number;    // General serving count
}
```

---

## Display Logic by Product Type

### 🍺 Draught Beer (Kegs)

**You'll receive:**
```json
{
  "name": "Guinness Keg",
  "size": "30L",
  "product_type": "Draught",
  "pints_per_keg": "52.8",
  "half_pints_per_keg": "105.6"
}
```

**Display as:**
```
Guinness Keg 30L
Yield: 52.8 pints (105.6 half-pints)
```

**Keg Sizes (You have all three):**
- **20L** → 35.2 pints (70.4 half-pints) - Specialty/Low volume
- **30L** → 52.8 pints (105.6 half-pints) ⭐ **MOST COMMON (11 brands)**
- **50L** → 88.0 pints (176.0 half-pints) ⭐ **High volume (3 brands)**

**Important:** Each keg size = Separate SKU
- Example: "D0004" = Heineken 30L, "D0030" = Heineken 50L

---

### 🥃 Spirits & Liqueurs

**You'll receive:**
```json
{
  "name": "Smirnoff Vodka",
  "size": "70cl",
  "product_type": "Spirit",
  "shots_per_bottle": "28.0",
  "uom": "12.00"
}
```

**Display as:**
```
Smirnoff Vodka 70cl
Yield: 28 shots per bottle (25ml pour)
Case: 12 bottles
```

**Common Bottle Sizes:**
- 70cl (700ml) → 28 shots (25ml pour) or 20 shots (35ml pour)
- 1L (1000ml) → 40 shots (25ml pour) or 28 shots (35ml pour)

---

### 🍻 Bottled Beer

**You'll receive:**
```json
{
  "name": "Heineken Bottle",
  "size": "330ml",
  "product_type": "Beer",
  "uom": "24.00",
  "servings_per_unit": "1.00"
}
```

**Display as:**
```
Heineken Bottle 330ml
Case: 24 bottles
```

---

## UI Table Example

```tsx
function YieldDisplay({ item }: { item: StockItem }) {
  if (item.product_type === 'Draught') {
    return (
      <div>
        <strong>{item.pints_per_keg} pints</strong>
        <small>({item.half_pints_per_keg} half-pints)</small>
      </div>
    );
  }
  
  if (item.product_type === 'Spirit' || item.product_type === 'Liqueur') {
    return (
      <div>
        <strong>{item.shots_per_bottle} shots</strong>
        <small>per bottle</small>
      </div>
    );
  }
  
  if (item.product_type === 'Beer') {
    return (
      <div>
        <strong>{item.uom} bottles</strong>
        <small>per case</small>
      </div>
    );
  }
  
  return <span>{item.uom} units</span>;
}
```

**Renders as:**

| Item | Size | Type | Yield |
|------|------|------|-------|
| Guinness Keg | 30L | Draught | **52.8 pints** (105.6 half-pints) |
| Guinness Keg | 50L | Draught | **88.0 pints** (176.0 half-pints) |
| Smirnoff Vodka | 70cl | Spirit | **28 shots** per bottle |
| Heineken | 330ml | Beer | **24 bottles** per case |

---

## Form/Input Display

When users are adding/editing items:

```tsx
<Form>
  <FormField label="Product Type">
    <Select name="product_type">
      <option value="Draught">Draught Beer (Keg)</option>
      <option value="Spirit">Spirit</option>
      <option value="Liqueur">Liqueur</option>
      <option value="Beer">Bottled Beer</option>
      <option value="Wine">Wine</option>
    </Select>
  </FormField>
  
  <FormField label="Size">
    <Input name="size" placeholder="30L, 70cl, 330ml" />
  </FormField>
  
  <FormField label="Serving Size">
    <Input 
      name="serving_size" 
      placeholder="568 (pint), 25 (shot), 330 (bottle)"
      helperText={getServingHelperText(productType)}
    />
  </FormField>
  
  {/* Show calculated yield preview */}
  {item.pints_per_keg && (
    <Alert type="info">
      This keg will yield {item.pints_per_keg} pints 
      or {item.half_pints_per_keg} half-pints
    </Alert>
  )}
</Form>

function getServingHelperText(type: string): string {
  switch(type) {
    case 'Draught':
      return 'Pint = 568ml, Half-pint = 284ml';
    case 'Spirit':
    case 'Liqueur':
      return 'Standard shot = 25ml or 35ml';
    case 'Beer':
      return 'Full bottle (e.g., 330ml)';
    default:
      return 'Size in ml';
  }
}
```

---

## Stocktake Counting Guide

### Draught (Kegs)
```
Full Kegs: 2
Partial (pints): 26.5

Display: "2 kegs + 26.5 pints"
```

### Spirits (Bottles)
```
Full Bottles: 5
Partial (shots): 15

Display: "5 bottles + 15 shots"
```

### Bottled Beer (Cases)
```
Full Cases: 3
Partial (bottles): 8

Display: "3 cases + 8 bottles"
```

---

## Quick Reference Cards

### 🍺 Draught Beer Card
```
┌─────────────────────────────┐
│ Guinness 30L Keg           │
├─────────────────────────────┤
│ Size: 30L                   │
│ Yield: 52.8 pints           │
│        105.6 half-pints     │
│ Cost per pint: €2.34        │
└─────────────────────────────┘
```

### 🥃 Spirit Card
```
┌─────────────────────────────┐
│ Smirnoff Vodka             │
├─────────────────────────────┤
│ Size: 70cl                  │
│ Yield: 28 shots (25ml)      │
│ Case: 12 bottles            │
│ Cost per shot: €0.47        │
└─────────────────────────────┘
```

### 🍻 Beer Card
```
┌─────────────────────────────┐
│ Heineken 330ml             │
├─────────────────────────────┤
│ Size: 330ml                 │
│ Case: 24 bottles            │
│ Cost per bottle: €1.14      │
└─────────────────────────────┘
```

---

## Important Notes

✅ **30L and 50L kegs are fully supported**
- 30L is the most common size
- 50L for high-volume venues
- System automatically calculates pints/half-pints

✅ **All yields are READ-ONLY**
- Calculated automatically by backend
- Update size/serving_size to recalculate
- No need to manually enter yields

✅ **Product types matter**
- `Draught` → Shows pints/half-pints
- `Spirit`/`Liqueur` → Shows shots
- `Beer` → Shows bottles per case

✅ **UOM is flexible**
- For kegs: Shows pints per keg
- For cases: Shows bottles per case
- For spirits: Can show bottles per case

---

## API Endpoints

```bash
# Get all items with yields
GET /api/stock-tracker/stock-items/

# Get single item with yields
GET /api/stock-tracker/stock-items/{id}/

# Update item (yields auto-recalculate)
PATCH /api/stock-tracker/stock-items/{id}/
{
  "size_value": 50,
  "size_unit": "L",
  "serving_size": 568
}
# Response will include updated pints_per_keg: 88.0
```

---

## Need More Help?

- Full technical details: `UOM_SERVING_YIELD_GUIDE.md`
- Model calculations: `stock_tracker/models.py`
- API fields: `stock_tracker/stock_serializers.py`

**Questions?** Contact the backend team! 🚀
