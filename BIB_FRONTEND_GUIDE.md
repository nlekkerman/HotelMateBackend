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

### Variance Display - IMPORTANT! 🎯

**BIB variance is ALREADY in BOXES (backend handles this automatically)**

```javascript
// Backend returns (for +2.5 box variance):
{
  "variance_display_full_units": "+2",      // ← Full boxes
  "variance_display_partial_units": "+0.5", // ← Fraction of box
  "variance_qty": 2.5,                       // ← Total boxes
  "variance_value": 427.90                   // ← Value: 2.5 × €171.16
}

// ✅ CORRECT Display (what user sees):
"+2 containers"    // Full boxes
"+0.5 serves"      // Box fraction (NOT drink servings!)
"+€427.90 ⚠️"
"(+2.50 boxes)"    // Total boxes (backend already did conversion!)

// 📊 Drink Servings Calculation (if needed for display):
// 1 box = 18L = 18,000ml
// Serving size = 36ml (from item.size_value)
// Servings per box = 18,000 ÷ 36 = 500 servings
// 2.5 boxes = 2.5 × 500 = 1,250 drink servings

// Backend Logic (you don't need to do this):
// For BIB: variance_qty is ALREADY in boxes
// _calculate_display_units() treats servings as boxes for BIB
// full = int(2.5) = 2
// partial = 2.5 - 2 = 0.5
```

**Key Points:**
1. ✅ Backend `variance_qty` for BIB = boxes (not drink servings)
2. ✅ Backend `_calculate_display_units()` splits boxes into full + partial
3. ✅ Display as boxes: "+2.50 boxes" (this is storage units, not drink servings!)
4. ✅ "servings" terminology = legacy label, actually means **box fraction** for BIB
5. ✅ No conversion needed - backend handles everything!

**Drink Servings Math (for reference):**
- 1 BIB box = 18 liters = 18,000ml
- Serving size = 36ml (from `item.size_value`)
- **Servings per box = 18,000ml ÷ 36ml = ~500 servings**
- 2.5 boxes = 2.5 × 500 = **1,250 drink servings**
- But variance shows "2.5 boxes", NOT "1,250 servings"!

**Why "servings" appears:**
- Other categories track servings (drinks sold)
- BIB reuses same UI components/labels
- For BIB: "servings" field = storage units (boxes)
- Frontend just displays what backend sends

---

## 💰 Value Display

**Important:** BIB values use `unit_cost` (box cost), NOT `cost_per_serving`

```javascript
// Example item from backend:
{
  "sku": "M25",
  "name": "Splash Cola 18LTR",
  "unit_cost": 171.16,  // ← Cost per 18L box
  "size_value": 36,     // ← Serving size in ml
  "counted_full_units": 2,
  "counted_partial_units": 0.50,
  "counted_value": 427.90  // = 2.5 × 171.16
}

// Calculate total servings available:
const totalBoxes = counted_full_units + counted_partial_units;  // 2.5
const servingsPerBox = 18000 / size_value;  // 18000ml ÷ 36ml = 500
const totalServings = totalBoxes * servingsPerBox;  // 2.5 × 500 = 1,250

// Display:
"Stock: 2.50 boxes"
"Available Servings: 1,250 servings (36ml)"
"Value: €427.90"
```

### Full Display Example

```tsx
function BIBStockDisplay({ line }) {
  const { counted_full_units, counted_partial_units, counted_value, item } = line;
  
  // Calculate totals
  const totalBoxes = counted_full_units + counted_partial_units;
  const servingsPerBox = 18000 / item.size_value;  // 500
  const totalServings = totalBoxes * servingsPerBox;  // 1,250
  
  return (
    <div className="stock-info">
      <div>📦 Stock: {totalBoxes.toFixed(2)} boxes</div>
      <div>🥤 Servings: {totalServings.toLocaleString()} × {item.size_value}ml</div>
      <div>💰 Value: €{counted_value}</div>
    </div>
  );
}

// Output:
// 📦 Stock: 2.50 boxes
// 🥤 Servings: 1,250 × 36ml
// 💰 Value: €427.90
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
6. ✅ **Variance in BOXES**: Display "+2.50 boxes" NOT "+2.50 servings"

---

## 📱 How to Display BIB Variance

### What Backend Sends (Example: +2.5 boxes variance)

```json
{
  "variance_display_full_units": "2",
  "variance_display_partial_units": "0.50",
  "variance_qty": 2.5000,
  "variance_value": 427.90
}
```

### Display Options

**Option 1: Keep existing UI labels (recommended)**
```tsx
// Your existing variance display component
<div className="variance">
  <div>{variance_display_full_units} containers</div>
  <div>{variance_display_partial_units} serves</div>
  <div>€{variance_value} ⚠️</div>
  <div>({variance_qty} servings)</div>  {/* This shows "2.50 servings" */}
</div>

// Result shows:
// 2 containers
// 0.50 serves
// €427.90 ⚠️
// (2.50 servings)  ← For BIB, this actually means boxes!
```

**Option 2: Change label for BIB only**
```tsx
// Conditionally change "servings" to "boxes" for BIB
<div className="variance">
  <div>{variance_display_full_units} containers</div>
  <div>{variance_display_partial_units} serves</div>
  <div>€{variance_value} ⚠️</div>
  <div>
    ({variance_qty} {item.subcategory === 'BIB' ? 'boxes' : 'servings'})
  </div>
</div>

// Result shows:
// 2 containers
// 0.50 serves
// €427.90 ⚠️
// (2.50 boxes)  ← More accurate for BIB!
```

**Option 3: Show drink servings in tooltip/additional info**
```tsx
// Display variance with drink servings calculation
function BIBVarianceDisplay({ line }) {
  const { variance_display_full_units, variance_display_partial_units, 
          variance_qty, variance_value, item } = line;
  
  // Calculate drink servings from boxes
  const servingSize = item.size_value;  // 36ml from backend
  const servingsPerBox = 18000 / servingSize;  // 18000ml ÷ 36ml = 500
  const totalDrinkServings = variance_qty * servingsPerBox;  // 2.5 × 500 = 1250
  
  return (
    <div className="variance">
      <div>{variance_display_full_units} containers</div>
      <div>{variance_display_partial_units} serves</div>
      <div>€{variance_value} ⚠️</div>
      <div>({variance_qty} boxes)</div>
      
      {/* Optional: Show drink servings as additional info */}
      <div className="drink-servings-info" style={{ fontSize: '0.85em', color: '#666' }}>
        = {totalDrinkServings.toLocaleString()} drink servings ({servingSize}ml each)
      </div>
      
      {/* OR as tooltip */}
      <div 
        title={`${variance_qty} boxes = ${totalDrinkServings.toLocaleString()} drink servings (${servingSize}ml)`}
      >
        ℹ️ Serving details
      </div>
    </div>
  );
}

// Example output:
// 2 containers
// 0.50 serves
// €427.90 ⚠️
// (2.50 boxes)
// = 1,250 drink servings (36ml each)  ← Additional info line
```

### Key Point: Don't Convert!

```javascript
// ❌ DON'T DO THIS:
const servingSize = 36;  // ml
const servingsPerBox = 18000 / servingSize;  // = 500 servings
const drinkServings = variance_qty * servingsPerBox;  // 2.5 × 500 = 1250
// Shows: "(1250 servings)" ← CONFUSING! Don't show drink servings!

// ✅ DO THIS:
const boxVariance = variance_qty;  // Already in boxes from backend
// Shows: "(2.50 boxes)" ← CLEAR!
```

**Math Breakdown:**
- 1 box = 18 liters = 18,000ml
- Serving size = 36ml (set in backend: `item.size_value`)
- Servings per box = 18,000ml ÷ 36ml = **500 servings**
- 2.5 boxes = 2.5 × 500 = **1,250 drink servings**
- **Primary display**: "2.5 boxes"
- **Optional display**: "+ 1,250 drink servings (36ml each)" as additional info

**Frontend Calculation:**
```javascript
// Get serving size from backend
const servingSize = item.size_value;  // 36 (ml)

// Calculate servings per box
const servingsPerBox = 18000 / servingSize;  // 18000 ÷ 36 = 500

// Calculate total drink servings from box variance
const drinkServings = variance_qty * servingsPerBox;  // 2.5 × 500 = 1250

// Format for display
const display = `${variance_qty} boxes = ${drinkServings.toLocaleString()} drink servings (${servingSize}ml)`;
// Result: "2.5 boxes = 1,250 drink servings (36ml)"
```

---

## ⚠️ CRITICAL: Backend Logic for BIB Display

**Backend automatically converts BIB to box display (no frontend work needed!)**

### How Backend Handles BIB Variance

```python
# In stock_serializers.py - _calculate_display_units():

elif item.subcategory == 'BIB':
    # BIB: Storage only (no serving conversion)
    # servings_decimal = total boxes (e.g., 2.5)
    full = int(servings_decimal)  # whole boxes → 2
    partial = servings_decimal - full  # fraction → 0.5
    return str(full), str(partial_rounded)
```

**What This Means:**
1. ✅ Backend receives `variance_qty = 2.5` (boxes, not servings)
2. ✅ Backend splits into `full = 2` and `partial = 0.5`
3. ✅ Frontend displays: "+2 containers / +0.5 serves / (+2.50 servings)"
4. ✅ "servings" label = boxes (reusing existing UI component)

### Why "Servings" Label Appears

```javascript
// Other categories (SOFT_DRINKS, JUICES):
variance_qty = 1250 → actual drink servings
display: "(+1250 servings)" → correct

// BIB category:
variance_qty = 2.5 → boxes (not drink servings!)
display: "(+2.50 servings)" → label reused, means boxes

// Backend difference:
SOFT_DRINKS: counted_qty = bottles → converted to servings
BIB: counted_qty = boxes → NO conversion (stays as boxes)
```

**Display Rules:**
- ✅ Accept that "servings" label means "boxes" for BIB
- ✅ OR change label dynamically: `{subcategory === 'BIB' ? 'boxes' : 'servings'}`
- ✅ Value is ALWAYS correct: uses box count × unit_cost
- ✅ No conversion math needed in frontend!

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
