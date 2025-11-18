# 🍷 WINE STOCKTAKE - Frontend Implementation Guide

## ✅ WHAT CHANGED

**Wine UOM has been fixed from glasses to bottles**

### Before (Incorrect)
- UOM = 5.0 (glasses per bottle)
- Calculation: 10.5 bottles × 5 = 52.5 glasses ❌
- **Problem:** Half a bottle was converted to 2.5 glasses!

### After (Correct)
- UOM = 1.0 (individual bottles)
- Calculation: 10.5 bottles × 1 = 10.5 bottles ✓
- **Fixed:** Half a bottle stays as 0.5 bottles!

---

## 📋 FRONTEND INPUT (No Changes Required)

The input format **remains the same** as Spirits:

```jsx
// Wine Input (Category W)
<FormGroup>
  <Label>Bottles</Label>
  <Input 
    type="number" 
    name="counted_full_units"
    step="1"
    min="0"
  />
</FormGroup>

<FormGroup>
  <Label>Fractional (0-0.99)</Label>
  <Input 
    type="number" 
    name="counted_partial_units"
    step="0.05"
    min="0"
    max="0.99"
  />
</FormGroup>
```

### User Enters
- Bottles: `10`
- Fractional: `0.50`

### Backend Receives
```json
{
  "counted_full_units": 10,
  "counted_partial_units": 0.50
}
```

---

## 📊 DISPLAY FORMAT (No Changes Required)

Wine displays **exactly like Spirits** - as bottles + fractional:

### Option 1: Combined Display (Recommended)
```jsx
const displayValue = (full, partial) => {
  const total = parseFloat(full) + parseFloat(partial);
  return `${total.toFixed(2)} bottles`;
};

// Shows: "10.50 bottles"
```

### Option 2: Separate Display
```jsx
const displayValue = (full, partial) => {
  return `${full} + ${partial.toFixed(2)}`;
};

// Shows: "10 + 0.50"
```

---

## 🎯 BACKEND CALCULATION

### Stocktake Line Calculation
```python
# Wine Category (W)
counted_qty = (counted_full_units × UOM) + (counted_partial_units × UOM)
counted_qty = (10 × 1.0) + (0.50 × 1.0)
counted_qty = 10.5 bottles  ✓
```

### Cost Calculation
```python
# unit_cost = cost per bottle
# counted_value = bottles × cost_per_bottle
counted_value = 10.5 × €10.25 = €107.63
```

---

## 📦 API RESPONSE STRUCTURE

### StocktakeLine for Wine Item
```json
{
  "id": 123,
  "item_sku": "W0018",
  "item_name": "Chateau Pascaud",
  "category_code": "W",
  "category_name": "Wine",
  "subcategory": null,
  
  "item_size": "75cl",
  "item_uom": "1.00",
  
  "counted_full_units": "10",
  "counted_partial_units": "0.50",
  "counted_qty": "10.5000",
  
  "counted_display_full_units": "10",
  "counted_display_partial_units": "0.50",
  
  "valuation_cost": "10.2500",
  "counted_value": "107.63",
  
  "input_fields": {
    "full": {
      "name": "counted_full_units",
      "label": "Bottles"
    },
    "partial": {
      "name": "counted_partial_units",
      "label": "Fractional (0-0.99)",
      "max": 0.99,
      "step": 0.05
    }
  }
}
```

---

## 🔄 COMPARISON WITH OTHER CATEGORIES

| Category | Storage Unit | UOM | Calculation | Display |
|----------|-------------|-----|-------------|---------|
| **Spirits** | Bottles + Fractional | 20 (shots) | 10.5 × 20 = 210 shots | "10.50 bottles" |
| **Wine** | Bottles + Fractional | 1 (bottles) | 10.5 × 1 = 10.5 bottles | "10.50 bottles" |
| **Draught** | Kegs + Pints | 88 (pints) | (2 × 88) + 26.5 = 202.5 pints | "2 kegs, 26.50 pints" |
| **Bottled** | Cases + Bottles | 12 (bottles) | (8 × 12) + 10 = 106 bottles | "8 cases, 10 bottles" |

---

## ✨ KEY DIFFERENCES: SPIRITS vs WINE

### Spirits (Category S)
```javascript
// UOM = 20 (shots per bottle)
// Input: 10 bottles + 0.5 fractional
// Calculation: (10 × 20) + (0.5 × 20) = 210 shots
// Display: "10.50 bottles"
// Meaning: 0.5 = half bottle = 10 shots
```

### Wine (Category W)
```javascript
// UOM = 1 (bottles)
// Input: 10 bottles + 0.5 fractional
// Calculation: (10 × 1) + (0.5 × 1) = 10.5 bottles
// Display: "10.50 bottles"
// Meaning: 0.5 = half bottle = 0.5 bottles
```

**Why Different?**
- **Spirits:** Sold by **shot** → UOM converts bottles to shots
- **Wine:** Tracked by **bottle** → UOM keeps as bottles (no conversion)

---

## 💰 PRICING & SALES (Separate from Stocktake)

Wine items have **two prices** for sales reporting:

```json
{
  "item_sku": "W0018",
  "unit_cost": "10.25",      // Cost per bottle (stocktake)
  "bottle_price": "45.00",   // Selling price per bottle
  "menu_price": "12.50"      // Selling price per glass
}
```

### Stocktake Uses
- `unit_cost` = €10.25 per bottle
- UOM = 1.0 (bottles)
- Tracks inventory in **bottles**

### Sales Reporting Uses
- `bottle_price` = €45.00 (when sold by bottle)
- `menu_price` = €12.50 (when sold by glass)

**Important:** Stocktake tracks **bottles in inventory**, not glasses sold!

---

## 🎨 FRONTEND COMPONENT EXAMPLE

```jsx
const WineStocktakeInput = ({ item, onUpdate }) => {
  const [fullUnits, setFullUnits] = useState(item.counted_full_units || 0);
  const [partialUnits, setPartialUnits] = useState(item.counted_partial_units || 0);

  // Calculate total bottles for display
  const totalBottles = parseFloat(fullUnits) + parseFloat(partialUnits);

  const handleSubmit = () => {
    onUpdate({
      counted_full_units: fullUnits,
      counted_partial_units: partialUnits
    });
  };

  return (
    <div className="wine-stocktake-input">
      <h4>{item.item_name}</h4>
      <p className="text-muted">
        Size: {item.item_size} | Cost: €{item.valuation_cost}
      </p>

      <Row>
        <Col md={6}>
          <FormGroup>
            <Label>Bottles</Label>
            <Input
              type="number"
              value={fullUnits}
              onChange={(e) => setFullUnits(e.target.value)}
              min="0"
              step="1"
            />
          </FormGroup>
        </Col>
        <Col md={6}>
          <FormGroup>
            <Label>Fractional (0-0.99)</Label>
            <Input
              type="number"
              value={partialUnits}
              onChange={(e) => setPartialUnits(e.target.value)}
              min="0"
              max="0.99"
              step="0.05"
            />
          </FormGroup>
        </Col>
      </Row>

      <div className="display-summary">
        <strong>Total: {totalBottles.toFixed(2)} bottles</strong>
        <span className="text-muted ml-3">
          Value: €{(totalBottles * parseFloat(item.valuation_cost)).toFixed(2)}
        </span>
      </div>

      <Button color="primary" onClick={handleSubmit}>
        Update Count
      </Button>
    </div>
  );
};
```

---

## ✅ VALIDATION RULES

```javascript
const validateWineInput = (full, partial) => {
  const errors = [];

  // Full units must be non-negative integer
  if (full < 0 || !Number.isInteger(Number(full))) {
    errors.push("Bottles must be a non-negative whole number");
  }

  // Partial must be between 0 and 0.99
  if (partial < 0 || partial >= 1) {
    errors.push("Fractional must be between 0.00 and 0.99");
  }

  // At least one value must be greater than 0
  if (full === 0 && partial === 0) {
    errors.push("Total count must be greater than 0");
  }

  return errors;
};
```

---

## 📝 SUMMARY FOR FRONTEND DEVELOPERS

### What You Need to Know

1. **Input Format:** Same as Spirits (Bottles + Fractional 0-0.99)
2. **Display Format:** Same as Spirits (X.XX bottles)
3. **UOM:** Changed from 5.0 to 1.0 (internal - no UI change needed)
4. **Calculation:** Backend now calculates correctly (no frontend changes)

### What Changed in Backend Only

- ✅ Wine UOM: 5.0 → 1.0
- ✅ Calculation: Now uses bottles, not glasses
- ✅ Display: Already correct (shows bottles)

### What Stays the Same

- ✅ Input fields (Bottles + Fractional)
- ✅ Display format (X.XX bottles)
- ✅ Validation rules
- ✅ API structure
- ✅ User experience

**Result:** No frontend code changes required! The fix is backend-only.

---

## 🔍 TESTING CHECKLIST

- [ ] Create new stocktake
- [ ] Add wine item (e.g., "Chateau Pascaud")
- [ ] Enter: 10 bottles + 0.5 fractional
- [ ] Verify display shows: "10.50 bottles"
- [ ] Verify counted_qty in API: 10.5000
- [ ] Verify counted_value: bottles × unit_cost
- [ ] Check variance calculation works correctly
- [ ] Test with different quantities (5.25, 12.75, 0.50, etc.)

---

## 📞 SUPPORT

If you see any issues with wine calculations:

1. Check `item.uom` in API response - should be `1.00`
2. Check `counted_qty` matches input (10.5 bottles = 10.5 servings)
3. Check `counted_value` = bottles × unit_cost
4. Verify display shows bottles, not glasses

All 44 wine items have been updated with UOM = 1.0.
