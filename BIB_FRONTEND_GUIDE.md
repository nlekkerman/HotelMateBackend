# 📦 BIB (Bag-in-Box) - Frontend Implementation Guide

## 🎯 Key Difference from Other Categories

**BIB is STORAGE-ONLY valuation** (like SYRUPS)
- ❌ NO serving conversions
- ❌ NO liters/ml calculations  
- ❌ NO sales logic
- ✅ Simple: `(boxes + fraction) × box_cost`

---

## 📋 BIB Logic vs Other Categories

| Category | Full Units | Partial Units | Valuation |
|----------|-----------|---------------|-----------|
| **SYRUPS** | Bottles (whole) | Decimal (0.5) | `(full + partial) × unit_cost` ✅ |
| **BIB** | Boxes (whole) | Decimal (0.5) | `(full + partial) × unit_cost` ✅ |
| **SOFT_DRINKS** | Cases | Bottles (whole) | `servings × cost_per_serving` |
| **CORDIALS** | Cases | Bottles (whole) | Total bottles only |
| **JUICES** | Cases | Bottles.ml (3.5) | `servings × cost_per_serving` |

**BIB = Same as SYRUPS logic!**

---

## 🔧 Backend API Response

### `input_fields` for BIB

```json
{
  "input_fields": {
    "full": {
      "name": "counted_full_units",
      "label": "Boxes"
    },
    "partial": {
      "name": "counted_partial_units",
      "label": "Fraction",
      "max": 0.99,
      "step": 0.01
    }
  }
}
```

---

## 🎨 Frontend Implementation

### Input: TWO Fields (Boxes + Fraction)

```tsx
{item.subcategory === 'BIB' && (
  <>
    <div className="input-group">
      <label>Boxes</label>
      <input
        type="number"
        name="counted_full_units"
        min="0"
        step="1"
        value={countedFullUnits}
        onChange={(e) => setCountedFullUnits(parseInt(e.target.value) || 0)}
        placeholder="Full boxes (e.g., 2)"
      />
    </div>
    
    <div className="input-group">
      <label>Fraction</label>
      <input
        type="number"
        name="counted_partial_units"
        min="0"
        max="0.99"
        step="0.01"
        value={countedPartialUnits}
        onChange={(e) => {
          const val = parseFloat(e.target.value) || 0;
          if (val >= 0 && val < 1) {
            setCountedPartialUnits(val);
          }
        }}
        placeholder="Decimal (e.g., 0.5)"
      />
    </div>
    
    <small className="help-text">
      Enter whole boxes + decimal fraction (e.g., 2 boxes + 0.5 = 2.5 boxes total)
    </small>
  </>
)}
```

---

## 📤 Sending Data to Backend

### Update Payload

```json
{
  "counted_full_units": 2,
  "counted_partial_units": 0.5
}
```

**Backend calculates:**
- Total units: `2 + 0.5 = 2.5`
- Stock value: `2.5 × €171.16 = €427.90`

---

## 📊 Display Values

### Opening Stock Display

```javascript
// Backend returns:
{
  "opening_display_full_units": "2",
  "opening_display_partial_units": "0.50"
}

// Display format:
"2 boxes + 0.50 = 2.50 boxes"
// OR simpler:
"2.50 boxes"
```

### Counted Stock Display

```javascript
// Backend returns:
{
  "counted_display_full_units": "1",
  "counted_display_partial_units": "0.75"
}

// Display format:
"1.75 boxes"
// OR with breakdown:
"1 box + 0.75"
```

### Variance Display

```javascript
// Backend returns:
{
  "variance_display_full_units": "-0",
  "variance_display_partial_units": "-0.25"
}

// Display format:
"-0.25 boxes"
// OR with sign:
"Short 0.25 boxes"
```

---

## 💰 Value Display

**Important:** BIB values use `unit_cost` (box cost), NOT `cost_per_serving`

```javascript
// Example item:
{
  "sku": "M25",
  "name": "Splash Cola 18LTR",
  "unit_cost": 171.16,  // ← Cost per 18L box
  "counted_full_units": 2,
  "counted_partial_units": 0.50,
  "counted_value": 427.90  // = 2.5 × 171.16
}

// Display:
"Stock: 2.50 boxes"
"Value: €427.90"
```

---

## ✅ Examples

### Example 1: Full Boxes Only
```
User Input:
  Boxes: 2
  Fraction: 0.00
  
Backend Receives:
  counted_full_units: 2
  counted_partial_units: 0.00
  
Calculation:
  2.00 × €171.16 = €342.32
  
Display:
  "2 boxes = €342.32"
```

### Example 2: Boxes + Fraction
```
User Input:
  Boxes: 1
  Fraction: 0.50
  
Backend Receives:
  counted_full_units: 1
  counted_partial_units: 0.50
  
Calculation:
  1.50 × €171.16 = €256.74
  
Display:
  "1.50 boxes = €256.74"
```

### Example 3: Fraction Only
```
User Input:
  Boxes: 0
  Fraction: 0.30
  
Backend Receives:
  counted_full_units: 0
  counted_partial_units: 0.30
  
Calculation:
  0.30 × €182.64 = €54.79
  
Display:
  "0.30 boxes = €54.79"
```

---

## 🚫 What NOT to Do

❌ **DON'T convert to liters:**
```javascript
// WRONG:
const liters = boxes * 18 + partialLiters;
```

❌ **DON'T calculate servings:**
```javascript
// WRONG:
const servings = totalLiters / 0.2;
```

❌ **DON'T use cost_per_serving:**
```javascript
// WRONG:
const value = servings * cost_per_serving;
```

✅ **DO use simple box calculation:**
```javascript
// CORRECT:
const totalBoxes = counted_full_units + counted_partial_units;
const value = totalBoxes * unit_cost;
```

---

## 🔄 Comparison: BIB vs SYRUPS

Both use the SAME logic pattern:

### SYRUPS
```javascript
Input: 10.5 bottles
Send: { full: 10, partial: 0.5 }
Value: 10.5 × unit_cost
Display: "10.50 bottles"
```

### BIB
```javascript
Input: 2.5 boxes
Send: { full: 2, partial: 0.5 }
Value: 2.5 × unit_cost
Display: "2.50 boxes"
```

**Same logic, different unit names!**

---

## 📝 Validation Rules

```javascript
// Full units (boxes)
- Type: Integer
- Min: 0
- No max

// Partial units (fraction)
- Type: Decimal
- Min: 0
- Max: 0.99
- Step: 0.01
- Format: 2 decimal places max
```

---

## 🎯 Key Points for Frontend Team

1. ✅ **Two input fields**: "Boxes" (integer) + "Fraction" (decimal 0-0.99)
2. ✅ **Send as-is**: No conversion needed, send directly to backend
3. ✅ **Display combined**: Show as single decimal "2.50 boxes"
4. ✅ **Use unit_cost**: For value calculations (NOT cost_per_serving)
5. ✅ **Like SYRUPS**: Same input/display pattern

---

## 🚀 Implementation Checklist

- [ ] Show two input fields for BIB: Boxes + Fraction
- [ ] Set step="0.01" for Fraction field
- [ ] Set max="0.99" for Fraction field
- [ ] Display combined value (e.g., "2.50 boxes")
- [ ] Send both fields separately to backend
- [ ] Show values using unit_cost
- [ ] Test with examples above

---

## 🔍 Testing Scenarios

Test these in your UI:

1. **2 full boxes** → Should show €342.32 (for M25)
2. **1.5 boxes** → Should show €256.74 (for M25)
3. **0.3 boxes** → Should show €54.79 (for M24)
4. **Variance** → Should show as boxes (e.g., "-0.25 boxes")

---

## ✅ Model & Serializer Status

### Backend Verification Results

**All BIB calculations working correctly:**

#### StockItem Properties
- ✅ `unit_cost`: Cost per 18L box (€171-€183)
- ✅ `size_value`: 36ml (500 servings per box)
- ✅ `cost_per_serving`: Calculated as `unit_cost / 500`

#### StocktakeLine Properties
- ✅ `counted_qty`: Returns `full_units + partial_units` (simple addition)
- ✅ `counted_value`: Uses `(full + partial) × unit_cost`
- ✅ `expected_value`: Uses `unit_cost` for BIB
- ✅ `opening_value`: Uses `unit_cost` for BIB

#### Serializer
- ✅ `input_fields`: Returns "Boxes" + "Fraction" (0-0.99)
- ✅ Display values: Simple decimal format

### Verified Examples
```
M23 - 20.06 boxes × €173.06 = €3,471.58 ✅
M24 - 12.64 boxes × €182.64 = €2,308.57 ✅
M25 - 18.16 boxes × €171.16 = €3,108.27 ✅
```

### GP Calculations
```
M23: 76.93% GP at €1.50 menu price ✅
M24: 75.65% GP at €1.50 menu price ✅
M25: 86.31% GP at €2.50 menu price ✅
```

**Backend is ready for frontend implementation!**

---

## 📞 Questions?

If the UI isn't showing correct values, check:
1. Are you sending both `counted_full_units` AND `counted_partial_units`?
2. Is partial a decimal between 0-0.99?
3. Are you displaying the combined total?
4. Is the backend returning `unit_cost` correctly?
