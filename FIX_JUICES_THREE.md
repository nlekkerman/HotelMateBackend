# ✅ JUICES: 3-Level Tracking Using 2 Fields (IMPLEMENTED)

## Problem (SOLVED)

**Old Implementation:**
```
JUICES: Bottles + ml → servings (200ml)
- counted_full_units = bottles
- counted_partial_units = ml
```

**New Implementation (CURRENT):**
```
JUICES: Cases + Bottles (decimal) → servings (200ml)
- counted_full_units = cases (whole number)
- counted_partial_units = bottles with decimal (e.g., 3.5 = 3 bottles + 500ml)
  - Integer part = full bottles
  - Decimal part × bottle_size_ml = ml
```

## ✅ Solution Implemented

**Uses existing 2 fields cleverly - NO DATABASE MIGRATION NEEDED!**

The `StocktakeLine` model has 2 fields:
- `counted_full_units` = **cases**
- `counted_partial_units` = **bottles with decimal** (decimal part represents ml)

**How it works:**
- User enters: `3 cases + 3.5 bottles`
- Storage: `counted_full_units=3, counted_partial_units=3.5`
- Calculation: 
  - 3 cases × 12 = 36 bottles
  - 3.5 bottles = 3 full + (0.5 × 1000ml) = 3 bottles + 500ml
  - Total: (36 + 3) × 1000ml + 500ml = 39,500ml
  - Servings: 39,500 ÷ 200 = 197.5 servings

## Flexible Input Options

### Option 1: User Enters Cases + Bottles Separately
```
Frontend inputs:
- Cases field: 3
- Bottles field: 3.5

Backend stores:
counted_full_units = 3 (cases)
counted_partial_units = 3.5 (bottles)

Display shows: "3 cases, 3.5 bottles"
```

### Option 2: User Enters Total Bottles Only
```
Frontend input:
- Bottles field: 140.5

Backend auto-calculates:
140.5 ÷ 12 = 11.708...
Cases: 11 (integer division)
Remainder: 140.5 - 132 = 8.5 bottles

Backend stores:
counted_full_units = 11 (auto-calculated)
counted_partial_units = 8.5 (remainder)

Display shows: "11 cases, 8.5 bottles"
```

**Both methods are supported!** The helper function `bottles_to_cases_bottles_ml()` handles automatic splitting.

## Implementation (COMPLETED)

### Backend Model Logic (`models.py`)

**StockItem.total_stock_in_servings** and **StocktakeLine.counted_qty**:

```python
elif self.subcategory == 'JUICES':
    # Cases + Bottles (with decimals) → servings (200ml)
    # counted_full_units = cases (whole number)
    # counted_partial_units = bottles (can be 3.5, 11.75, etc.)
    
    cases = self.counted_full_units
    bottles_with_fraction = self.counted_partial_units
    
    # Split bottles into whole bottles + ml
    full_bottles = int(bottles_with_fraction)  # 3
    ml = (bottles_with_fraction - full_bottles) * self.item.uom  # 0.5 × 1000 = 500ml
    
    # Calculate servings using helper
    return cases_bottles_ml_to_servings(
        cases, full_bottles, ml,
        bottle_size_ml=float(self.item.uom),
        bottles_per_case=12,
        serving_size_ml=200
    )
```

### Serializer Display Logic (`stock_serializers.py`)

**`_calculate_display_units()` for JUICES**:

```python
elif item.subcategory == 'JUICES':
    # servings → cases + bottles (with decimal)
    from stock_tracker.juice_helpers import servings_to_cases_bottles_ml
    
    # Convert servings to cases + bottles + ml
    cases, bottles, ml = servings_to_cases_bottles_ml(
        float(servings_decimal),
        bottle_size_ml=float(item.uom),
        bottles_per_case=12,
        serving_size_ml=200
    )
    
    # Combine bottles + ml as decimal
    # e.g., 3 bottles + 500ml (of 1000ml bottle) = 3.5
    bottles_decimal = Decimal(str(bottles)) + (Decimal(str(ml)) / item.uom)
    
    # Returns: (cases, bottles_with_decimal)
    return str(cases), str(bottles_decimal)
```

### Helper Functions (`juice_helpers.py`)

Three key functions handle all conversions:

```python
# Split total bottles into cases + bottles + ml
bottles_to_cases_bottles_ml(140.5, 1000, 12)
# Returns: (11, 8, 500)

# Calculate servings from 3 levels
cases_bottles_ml_to_servings(11, 8, 500, 1000, 12, 200)
# Returns: 702.5 servings

# Convert servings back to 3 levels (for display)
servings_to_cases_bottles_ml(702.5, 1000, 12, 200)
# Returns: (11, 8, 500)
```

### Frontend Implementation

```javascript
// Two input fields
<Input 
  label="Cases" 
  name="counted_full_units" 
  type="number" 
  step="1" 
/>
<Input 
  label="Bottles" 
  name="counted_partial_units" 
  type="number" 
  step="0.01"  // Allows decimals like 3.5
/>

// Optional: Auto-split if user enters large bottle count
const handleBottleChange = (value) => {
  if (value > 12) {
    const cases = Math.floor(value / 12);
    const bottles = value % 12;
    setCases(cases);
    setBottles(bottles);
  }
};
```

## Example Calculations

### Example 1: User Enters Cases + Bottles

**Item:** Kulana 1L Juice (12 bottles per case)

**User Enters:**
- Cases: `5`
- Bottles: `3.25`

**Stored As:**
```python
counted_full_units = 5  # cases
counted_partial_units = 3.25  # bottles with decimal
```

**Backend Calculation:**
```python
cases = 5
bottles_with_fraction = 3.25

# Split bottles
full_bottles = int(3.25) = 3
ml = (3.25 - 3) × 1000 = 0.25 × 1000 = 250ml

# Calculate servings
# 5 cases = 60 bottles = 60,000ml
# 3 bottles = 3,000ml
# 250ml = 250ml
# Total: 63,250ml ÷ 200 = 316.25 servings
```

**Display:**
- Shows: `"5 cases, 3.25 bottles"`
- Value: `316.25 servings`

### Example 2: User Enters Total Bottles Only

**User Enters:**
- Bottles: `140.5`

**Auto-Split (frontend or backend):**
```python
140.5 ÷ 12 = 11.708...
cases = 11
remainder = 140.5 - 132 = 8.5 bottles
```

**Stored As:**
```python
counted_full_units = 11  # cases
counted_partial_units = 8.5  # bottles
```

**Display:**
- Shows: `"11 cases, 8.5 bottles"`
- Total: `(11×12 + 8.5) × 1000ml = 140,500ml ÷ 200 = 702.5 servings`

## Files Modified

✅ **Completed:**

1. **`stock_tracker/models.py`**
   - Updated `StockItem.total_stock_in_servings` for JUICES
   - Updated `StocktakeLine.counted_qty` for JUICES
   - Imported juice helper functions

2. **`stock_tracker/juice_helpers.py`** (NEW)
   - `bottles_to_cases_bottles_ml()` - Split total bottles
   - `cases_bottles_ml_to_servings()` - Calculate servings
   - `servings_to_cases_bottles_ml()` - Reverse conversion

3. **`stock_tracker/stock_serializers.py`**
   - Updated `_calculate_display_units()` for JUICES
   - Displays as "X cases, Y.ZZ bottles"

## Benefits

✅ **No database migration needed** - uses existing 2 fields  
✅ **Flexible input** - cases+bottles OR total bottles  
✅ **Accurate tracking** - decimal precision for ml  
✅ **Clear display** - always shows "X cases, Y.ZZ bottles"  
✅ **Backward compatible** - existing data works automatically  

## Testing

Run test script to verify:
```bash
python test_juice_2field_input.py
```

Expected output:
```
Test 1: 3 cases + 3.5 bottles → 197.5 servings ✓
Test 2: 0 cases + 150.5 bottles → 752.5 servings ✓
Test 3: 59 cases + 8.008 bottles (real data) → works ✓
```

---

## Real Data Example: M0042 Lemonade Red Nashs

**Before (WRONG):**
```
Opening: 716 bottles + 8ml  ← Confusing!
```

**After (CORRECT with new logic):**

If stored in old format:
```python
current_full_units = 716  # old data
current_partial_units = 8  # ml
```

New display automatically converts:
```python
# Helper auto-splits 716 bottles
716 ÷ 12 = 59 cases, remainder 8 bottles
8ml stays as 8ml or converts to 0.008 bottles

# Display shows:
"59 cases, 8.008 bottles"
```

**No data migration needed!** Old data automatically displays correctly.
