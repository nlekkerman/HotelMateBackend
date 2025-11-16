# 📝 Input Methods - Final Implementation

## SYRUPS - Single Decimal Input (Two Fields Storage)

**User enters:** `10.5` bottles (single input)  

**Frontend must split and send TWO fields:**
```javascript
// User types: 10.5
const bottlesInput = 10.5;

// Split into whole + decimal
const fullBottles = Math.floor(bottlesInput);     // 10
const fractional = bottlesInput - fullBottles;     // 0.5

// Send to backend:
current_full_units = 10        // whole bottles
current_partial_units = 0.5    // decimal fraction ONLY
```

**Backend stores:**
```python
current_full_units = 10      # whole bottles
current_partial_units = 0.5  # decimal part (0.5, NOT 10.5!)
```

**Backend calculates:**
```python
total_ml = (10 × 1000) + (0.5 × 1000) = 10,500ml
servings = 10,500 ÷ 35 = 300 servings
```

**Display:** `"10.50"` (combine full + partial for display)

**How to display:**
```javascript
// Backend returns:
counted_full_units: 10
counted_partial_units: 0.50

// Frontend displays as single decimal:
const displayValue = counted_full_units + counted_partial_units;
// Shows: "10.50"

// Or format as: "10.50 bottles"
```

**Examples:**
| User Enters | full_units | partial_units | Total ml | Servings |
|-------------|-----------|---------------|----------|----------|
| `10.50` | 10 | 0.50 | 10,500 | 300 |
| `100.75` | 100 | 0.75 | 100,750 | 2,878.57 |
| `0.50` | 0 | 0.50 | 500 | 14.29 |
| `10.00` | 10 | 0.00 | 10,000 | 285.71 |

**Frontend Implementation:**
```javascript
<Input 
  label="Bottles" 
  type="number" 
  step="0.01"
  placeholder="e.g., 10.5"
  onChange={(value) => {
    // Split the decimal input (2 decimal places)
    const full = Math.floor(value);
    const partial = parseFloat((value - full).toFixed(2));
    
    // Set both fields
    setCurrentFullUnits(full);        // 10
    setCurrentPartialUnits(partial);  // 0.5 or 0.75
  }}
/>

// When sending to backend:
{
  current_full_units: 10,      // whole number
  current_partial_units: 0.50  // decimal fraction (2 decimals max)
}
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

| Category | Input Method | Storage | Display Format |
|----------|-------------|---------|----------------|
| **SYRUPS** | `10.50` (single) | `full=10, partial=0.50` | `"10.50"` (combine both) |
| **SOFT_DRINKS** | Cases+Bottles OR Total | `full=12, partial=1` | `"12 cases, 1 bottle"` |
| **JUICES** | Cases+Bottles OR Total | `full=59, partial=8.50` | `"59 cases, 8.50 bottles"` |
| **CORDIALS** | Cases + Bottles | `full=4, partial=7` | `"4 cases, 7 bottles"` |
| **BIB** | Boxes + Liters | `full=2, partial=5.50` | `"2 boxes, 5.50 liters"` |
| **DRAUGHT** | Kegs + Pints | `full=3, partial=12` | `"3 kegs, 12 pints"` |
| **BOTTLED** | Cases + Bottles | `full=8, partial=10` | `"8 cases, 10 bottles"` |
| **SPIRITS** | Bottles + Fractional | `full=5, partial=0.75` | `"5.00 + 0.75"` or `"5.75 bottles"` |
| **WINE** | Bottles + Fractional | `full=12, partial=0.50` | `"12.00 + 0.50"` or `"12.50 bottles"` |

---

## How to Display Values (Frontend)

### SYRUPS - Combine Both Fields
```javascript
// Backend sends:
{ counted_full_units: 10, counted_partial_units: 0.50 }

// Display as single number:
const displayValue = counted_full_units + counted_partial_units;
// Result: 10.50

// Format: "10.50" or "10.50 bottles"
```

### SOFT_DRINKS, CORDIALS, BOTTLED - Show Separately
```javascript
// Backend sends:
{ counted_full_units: 12, counted_partial_units: 1 }

// Display: "12 cases, 1 bottle"
```

### JUICES - Show Cases + Decimal Bottles
```javascript
// Backend sends:
{ counted_full_units: 59, counted_partial_units: 8.50 }

// Display: "59 cases, 8.50 bottles"
```

### SPIRITS, WINE - Two Options
```javascript
// Backend sends:
{ counted_full_units: 5, counted_partial_units: 0.75 }

// Option 1: Combined
const total = counted_full_units + counted_partial_units;
// Display: "5.75 bottles"

// Option 2: Separate (like Django admin)
// Display: "5.00 + 0.75"
```

### BIB - Show Separately
```javascript
// Backend sends:
{ counted_full_units: 2, counted_partial_units: 5.50 }

// Display: "2 boxes, 5.50 liters"
```

---

## Key Features

✅ **SYRUPS:** One input field, frontend splits into `full_units` (whole) + `partial_units` (decimal)  
✅ **SOFT_DRINKS:** Flexible - accepts total bottles and auto-converts to cases  
✅ **Display:** Always shows breakdown when user enters total  
✅ **Backend:** Handles both input methods automatically  
✅ **No database changes:** Uses existing 2 fields (`full_units` + `partial_units`)  
⚠️ **IMPORTANT:** For SYRUPS, frontend MUST split `10.5` → `full=10, partial=0.5` before sending

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
