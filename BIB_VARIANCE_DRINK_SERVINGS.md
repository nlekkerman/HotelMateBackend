# 🎯 BIB Variance: Drink Servings Field

## 📋 Overview

**New Backend Field:** `variance_drink_servings`

This field is **ONLY for BIB items** and calculates the actual drink servings from box variance.

---

## 🔄 Why This Field Exists

### The Problem
- BIB `variance_qty` = boxes (e.g., 2.5 boxes)
- Other categories `variance_qty` = drink servings already
- Frontend needed to calculate: boxes × servings_per_box = drink servings
- This calculation belongs in backend, not frontend

### The Solution
Backend now sends `variance_drink_servings` for BIB items:
- ✅ Backend calculates drink servings automatically
- ✅ Frontend just displays the value
- ✅ Returns `null` for non-BIB items (no impact on other categories)

---

## 📊 API Response Example

### BIB Item (Splash Cola 18LTR)

```json
{
  "item_sku": "M25",
  "item_name": "Splash Cola 18LTR",
  "subcategory": "BIB",
  "size_value": 36,
  
  "variance_display_full_units": "2",
  "variance_display_partial_units": "0.50",
  "variance_qty": "2.5000",
  "variance_value": "427.90",
  "variance_drink_servings": "1250.00"  // ← NEW FIELD!
}
```

**Backend Calculation:**
```
variance_qty = 2.5 boxes
serving_size = 36ml (from item.size_value)
servings_per_box = 18,000ml ÷ 36ml = 500 servings
variance_drink_servings = 2.5 × 500 = 1,250 servings
```

### Non-BIB Item (Soft Drinks)

```json
{
  "item_sku": "M03",
  "item_name": "Coke Zero 200ML Bottles",
  "subcategory": "SOFT_DRINKS",
  
  "variance_qty": "24.0000",
  "variance_value": "12.00",
  "variance_drink_servings": null  // ← null for non-BIB
}
```

---

## 🎨 Frontend Implementation

### Display BIB Variance with Drink Servings

```tsx
function BIBVarianceDisplay({ line }) {
  const { 
    variance_display_full_units,
    variance_display_partial_units,
    variance_qty,
    variance_value,
    variance_drink_servings,  // NEW!
    item 
  } = line;
  
  return (
    <div className="variance-display">
      {/* Primary display: boxes */}
      <div className="variance-boxes">
        <span className="full">{variance_display_full_units} containers</span>
        <span className="partial">{variance_display_partial_units} serves</span>
        <span className="value">€{variance_value}</span>
        <span className="total">({variance_qty} boxes)</span>
      </div>
      
      {/* Additional info: drink servings (ONLY for BIB) */}
      {variance_drink_servings && (
        <div className="drink-servings-info">
          = {parseFloat(variance_drink_servings).toLocaleString()} 
          drink servings ({item.size_value}ml each)
        </div>
      )}
    </div>
  );
}
```

### Example Output

**Display for +2.5 box variance:**
```
2 containers
0.50 serves
€427.90 ⚠️
(2.50 boxes)
= 1,250 drink servings (36ml each)
```

---

## ✅ Display Options

### Option 1: Inline with Variance
```tsx
<div className="variance">
  <span>({variance_qty} boxes</span>
  {variance_drink_servings && (
    <span> = {parseFloat(variance_drink_servings).toLocaleString()} servings</span>
  )}
  <span>)</span>
</div>

// Output: "(2.50 boxes = 1,250 servings)"
```

### Option 2: Separate Line
```tsx
<div className="variance-details">
  <div>Box variance: {variance_qty} boxes</div>
  {variance_drink_servings && (
    <div className="drink-servings">
      Drink servings: {parseFloat(variance_drink_servings).toLocaleString()}
      ({item.size_value}ml each)
    </div>
  )}
</div>

// Output:
// Box variance: 2.50 boxes
// Drink servings: 1,250 (36ml each)
```

### Option 3: Tooltip/Hover
```tsx
<div 
  className="variance-qty"
  title={variance_drink_servings 
    ? `${variance_qty} boxes = ${parseFloat(variance_drink_servings).toLocaleString()} drink servings` 
    : undefined
  }
>
  ({variance_qty} boxes)
  {variance_drink_servings && <span className="info-icon">ℹ️</span>}
</div>

// Hover shows: "2.50 boxes = 1,250 drink servings"
```

---

## 🔍 When to Display

### Show drink servings IF:
- ✅ Item is BIB (`subcategory === 'BIB'`)
- ✅ `variance_drink_servings` is not null
- ✅ User wants to see actual serving impact

### Don't show drink servings IF:
- ❌ Non-BIB items (field will be null anyway)
- ❌ User only cares about storage (boxes)
- ❌ Display is too cluttered

---

## 📐 Formatting Examples

```javascript
// Parse and format
const servings = parseFloat(variance_drink_servings);

// With thousands separator
servings.toLocaleString()  // "1,250"

// With decimals
servings.toFixed(0)  // "1250"

// Conditional display
{variance_drink_servings && (
  <span>{parseFloat(variance_drink_servings).toLocaleString()} servings</span>
)}
```

---

## 🚫 What NOT to Do

### ❌ DON'T calculate drink servings yourself:
```javascript
// WRONG - backend already does this!
const servingsPerBox = 18000 / item.size_value;
const drinkServings = variance_qty * servingsPerBox;
```

### ✅ DO use the backend field:
```javascript
// CORRECT - just display what backend sends
const drinkServings = variance_drink_servings;
```

### ❌ DON'T show for non-BIB items:
```javascript
// WRONG - will be null for non-BIB
{variance_drink_servings && <span>{variance_drink_servings}</span>}
```

### ✅ DO check if it exists:
```javascript
// CORRECT - only shows for BIB
{variance_drink_servings && (
  <span>{parseFloat(variance_drink_servings).toLocaleString()}</span>
)}
```

---

## 🧪 Testing

### Test BIB Item (M25 - Splash Cola)
```
Expected response:
- variance_qty: "2.5000" (boxes)
- variance_drink_servings: "1250.00" (servings)
- Calculation: 2.5 boxes × 500 servings/box = 1,250
```

### Test Non-BIB Item (M03 - Soft Drinks)
```
Expected response:
- variance_qty: "24.0000" (already servings)
- variance_drink_servings: null
```

---

## 📊 Complete Example Component

```tsx
function VarianceDisplay({ line }) {
  const {
    item,
    variance_display_full_units,
    variance_display_partial_units,
    variance_qty,
    variance_value,
    variance_drink_servings
  } = line;
  
  // Parse values
  const varianceNum = parseFloat(variance_qty);
  const isPositive = varianceNum >= 0;
  const drinkServings = variance_drink_servings 
    ? parseFloat(variance_drink_servings) 
    : null;
  
  return (
    <div className={`variance ${isPositive ? 'surplus' : 'shortage'}`}>
      {/* Full/Partial display */}
      <div className="variance-units">
        <span className="full">
          {isPositive ? '+' : ''}{variance_display_full_units} containers
        </span>
        <span className="partial">
          {isPositive ? '+' : ''}{variance_display_partial_units} serves
        </span>
      </div>
      
      {/* Value */}
      <div className="variance-value">
        {isPositive ? '+' : ''}€{variance_value} 
        {!isPositive && ' ⚠️'}
      </div>
      
      {/* Total with drink servings */}
      <div className="variance-total">
        ({isPositive ? '+' : ''}{varianceNum.toFixed(2)} 
        {item.subcategory === 'BIB' ? ' boxes' : ' servings'})
        
        {drinkServings && (
          <div className="drink-servings-detail">
            = {drinkServings.toLocaleString()} drink servings 
            ({item.size_value}ml each)
          </div>
        )}
      </div>
    </div>
  );
}
```

**Example Output:**
```
+2 containers
+0.50 serves
+€427.90
(+2.50 boxes)
= 1,250 drink servings (36ml each)
```

---

## 🎯 Key Points

1. ✅ **BIB ONLY**: Field returns `null` for non-BIB items
2. ✅ **Backend calculates**: No frontend math needed
3. ✅ **Optional display**: Show if you want serving impact info
4. ✅ **Safe to use**: Won't break existing logic for other categories
5. ✅ **Easy formatting**: Just parse and display with toLocaleString()

---

## 📝 Summary

| Field | BIB Value | Other Categories |
|-------|-----------|------------------|
| `variance_qty` | Boxes (2.5) | Servings (24) |
| `variance_drink_servings` | Drink servings (1250.00) | `null` |

**Use case:** Show both storage variance (boxes) AND drink impact (servings) for BIB items.
