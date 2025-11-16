# 📝 Input Methods - Final Implementation

## SYRUPS - Single Decimal Field

⚠️ **IMPORTANT:** For SYRUPS, `current_partial_units` stores the **TOTAL bottles** (not just partial)!

**User enters:** `100.5` bottles (any amount)  
**Backend stores:**
```python
current_full_units = 0  # ALWAYS 0 (not used for SYRUPS)
current_partial_units = 100.5  # TOTAL BOTTLES (full + partial combined)
```

**Backend internally splits for calculation:**
- `100` bottles (integer part)
- `500ml` (0.5 × 1000ml = decimal part)
- Total: `100,500ml ÷ 35ml = 2,871.43 servings`

**Display:** `"100.5 bottles"` = 2,871.43 servings

**Examples:**
- `10.5` → 10 bottles + 500ml
- `100.5` → 100 bottles + 500ml
- `0.5` → 0 bottles + 500ml
- `1234.567` → 1234 bottles + 567ml

**Frontend:**
```javascript
<Input 
  label="Total Bottles" 
  name="current_partial_units"  // Stores TOTAL, not just partial!
  type="number" 
  step="0.001"
  placeholder="e.g., 10.5 or 100.5"
/>
// Note: current_full_units should be 0 for SYRUPS
```

---

## SOFT_DRINKS - Flexible Input (Two Options)

### Option 1: Enter Cases + Bottles Separately
**User enters:**
- Cases: `12`
- Bottles: `1`

**Backend stores:**
```python
current_full_units = 12
current_partial_units = 1
```

**Display:** `"12 cases, 1 bottle"` = 145 bottles

---

### Option 2: Enter Total Bottles → Auto-Calculate Cases
**User enters:** `145` bottles (total)

**Frontend/Backend auto-splits:**
```python
from stock_tracker.juice_helpers import bottles_to_cases_and_bottles

cases, bottles = bottles_to_cases_and_bottles(145, 12)
# Returns: (12, 1)
```

**Backend stores:**
```python
current_full_units = 12  # auto-calculated
current_partial_units = 1  # remainder
```

**Display:** `"12 cases, 1 bottle"` = 145 bottles

**Frontend:**
```javascript
// Option A: Two separate fields
<Input label="Cases" name="counted_full_units" type="number" />
<Input label="Bottles" name="counted_partial_units" type="number" />

// Option B: Single field with auto-split
<Input 
  label="Total Bottles" 
  type="number"
  onChange={(value) => {
    const cases = Math.floor(value / 12);
    const bottles = value % 12;
    setCountedFullUnits(cases);
    setCountedPartialUnits(bottles);
    
    // Show calculated breakdown
    setDisplay(`${cases} cases, ${bottles} bottles`);
  }}
/>
<div>Calculated: {display}</div>
```

---

## JUICES - Already Implemented

**User enters:** `716.5` bottles (or cases + bottles separately)

**Backend stores:**
```python
current_full_units = 59  # cases (auto-calculated)
current_partial_units = 8.5  # bottles with decimal
```

**Display:** `"59 cases, 8.5 bottles"` = 3,580.04 servings

---

## Summary Table

| Category | Input Method | Field Usage | Display |
|----------|-------------|-------------|---------|
| **SYRUPS** | Decimal only: `100.5` | `full_units=0, partial_units=100.5` (TOTAL) | `"100.5 bottles"` |
| **SOFT_DRINKS** | Cases+Bottles OR Total Bottles | `"12 cases, 1 bottle"` (calculated) |
| **JUICES** | Cases+Bottles OR Total Bottles | `"59 cases, 8.5 bottles"` (calculated) |
| **CORDIALS** | Cases + Bottles (separate) | `"4 cases, 7 bottles"` |
| **BIB** | Boxes + Liters (separate) | `"2 boxes, 5.5 liters"` |
| **DRAUGHT** | Kegs + Pints (separate) | `"3 kegs, 12 pints"` |
| **BOTTLED** | Cases + Bottles (separate) | `"8 cases, 10 bottles"` |
| **SPIRITS** | Bottles + Fractional (separate) | `"5.75 bottles"` |
| **WINE** | Bottles + Fractional (separate) | `"12.5 bottles"` |

---

## Key Features

✅ **SYRUPS:** One decimal field stores TOTAL bottles in `partial_units` (100.5, 10.5, etc.)  
✅ **SOFT_DRINKS:** Flexible - accepts total bottles and auto-converts to cases  
✅ **Display:** Always shows breakdown when user enters total  
✅ **Backend:** Handles both input methods automatically  
✅ **No database changes:** Uses existing 2 fields (`full_units` + `partial_units`)  
⚠️ **Field naming quirk:** For SYRUPS, `partial_units` holds the TOTAL value (not just partial)

---

## Implementation Status

✅ **Backend Logic:** Complete for SYRUPS, JUICES  
✅ **Helper Function:** `bottles_to_cases_and_bottles()` available  
⏳ **Frontend:** Needs UI to show calculated breakdown when total entered  

---

## Example: SOFT_DRINKS Display

**Scenario:** User enters `145` total bottles

**Frontend shows:**
```
Input: 145 bottles

Calculated Breakdown:
📦 12 cases
🍾 1 bottle

Total: 145 bottles (145 servings)
```

**Stored in database:**
```python
counted_full_units = 12
counted_partial_units = 1
```
