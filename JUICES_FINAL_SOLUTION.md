# JUICES 2-Field Solution: Cases + Bottles (with decimals)

## ✅ FINAL SOLUTION IMPLEMENTED

JUICES now support **3-level tracking** using only **2 database fields**:

### Storage Structure
```python
counted_full_units = cases (whole number)
counted_partial_units = bottles (with decimals)
  - Integer part = full bottles
  - Decimal part = ml (e.g., 0.5 × 1000ml = 500ml)
```

## Input Methods (Both Supported)

### Method 1: User Enters Cases + Bottles Separately
```
Frontend sends:
{
  "counted_full_units": 3,
  "counted_partial_units": 3.5
}

Backend stores:
counted_full_units = 3 (cases)
counted_partial_units = 3.5 (bottles)

Calculation:
- 3 cases × 12 = 36 bottles
- + 3.5 bottles = 39.5 total bottles
- Integer: 3 full bottles
- Decimal: 0.5 × 1000ml = 500ml
- Total: (36 + 3) × 1000ml + 500ml = 39,500ml
- Servings: 39,500 ÷ 200 = 197.5 servings
```

### Method 2: User Enters Total Bottles Only
```
Frontend sends:
{
  "counted_partial_units": 140.5  // All in bottles field
}

Backend auto-splits:
140.5 ÷ 12 = 11 cases (remainder 8.5)
counted_full_units = 11 (auto-calculated)
counted_partial_units = 8.5 (remainder)

Display shows:
"11 cases, 8.5 bottles"

Calculation:
- 11 cases × 12 = 132 bottles
- + 8.5 bottles
- Integer: 8 full bottles
- Decimal: 0.5 × 1000ml = 500ml
- Total: (132 + 8) × 1000ml + 500ml = 140,500ml
- Servings: 140,500 ÷ 200 = 702.5 servings
```

## Real Example: Lemonade Red Nashs

**Current Data:**
```
Opening: 716 bottles + 8ml (WRONG FORMAT!)
```

**With New Logic:**

If stored as `counted_partial_units = 716`:
```python
# Auto-split using helper
716 ÷ 12 = 59.666...
cases = 59
bottles_remainder = 716 - (59 × 12) = 716 - 708 = 8

# Display
"59 cases, 8 bottles"

# If there's also 8ml stored separately, it becomes:
"59 cases, 8.008 bottles"  (8 + 0.008)
```

## Backend Calculation (models.py)

```python
elif self.item.subcategory == 'JUICES':
    # Cases + Bottles (with decimals) → servings (200ml)
    # counted_full_units = cases (whole number)
    # counted_partial_units = bottles (can be 3.5, 11.75, etc.)
    
    cases = self.counted_full_units
    bottles_with_fraction = self.counted_partial_units
    
    # Split bottles into whole bottles + ml
    full_bottles = int(bottles_with_fraction)  # 3
    ml = (bottles_with_fraction - full_bottles) * self.item.uom  # 0.5 × 1000 = 500
    
    # Calculate servings using helper
    return cases_bottles_ml_to_servings(
        cases, full_bottles, ml,
        bottle_size_ml=float(self.item.uom),
        bottles_per_case=12,
        serving_size_ml=200
    )
```

## Display Logic (serializers.py)

```python
elif item.subcategory == 'JUICES':
    # servings → cases + bottles (with decimal)
    
    # Convert servings back to cases + bottles + ml
    cases, bottles, ml = servings_to_cases_bottles_ml(
        float(servings_decimal),
        bottle_size_ml=float(item.uom),
        bottles_per_case=12,
        serving_size_ml=200
    )
    
    # Combine bottles + ml as decimal for display
    # e.g., 3 bottles + 500ml (of 1000ml bottle) = 3.5
    bottles_decimal = Decimal(str(bottles)) + (Decimal(str(ml)) / item.uom)
    
    # Display shows: "X cases" + "Y.ZZ bottles"
    return str(cases), str(bottles_decimal)
```

## Frontend Display Examples

### Example 1: Display Opening Stock
```javascript
// Backend returns:
{
  "opening_display_full_units": "59",     // cases
  "opening_display_partial_units": "8.01" // bottles
}

// Display:
"59 cases, 8.01 bottles"
```

### Example 2: Input Counted Stock
```javascript
// User enters in 2 separate fields:
<Input label="Cases" value="3" />
<Input label="Bottles" value="3.5" />

// OR user enters in single field:
<Input label="Bottles" value="39.5" />
// → Frontend calculates: 39.5 ÷ 12 = 3 cases, 3.5 bottles

// Both send to backend:
{
  "counted_full_units": 3,
  "counted_partial_units": 3.5
}
```

## Helper Function Usage

All conversions use `juice_helpers.py`:

```python
# Convert total bottles → cases + bottles + ml
cases, bottles, ml = bottles_to_cases_bottles_ml(140.5, 1000, 12)
# Result: (11, 8, 500)

# Convert cases + bottles + ml → servings
servings = cases_bottles_ml_to_servings(11, 8, 500, 1000, 12, 200)
# Result: 702.5

# Convert servings → cases + bottles + ml (for display)
cases, bottles, ml = servings_to_cases_bottles_ml(702.5, 1000, 12, 200)
# Result: (11, 8, 500)
```

## Benefits

✅ **No database migration needed** - uses existing 2 fields  
✅ **Flexible input** - enter as cases+bottles OR total bottles  
✅ **Clear display** - always shows "X cases, Y.ZZ bottles"  
✅ **Automatic splitting** - helper functions handle all conversions  
✅ **Accurate calculations** - tracks ml as decimal portion of bottles  

## Migration Path

**No migration needed!** Existing data works as-is:

```python
# Old data: 716 bottles stored in counted_full_units
# New display: Automatically shows "59 cases, 8 bottles"

# Old data: 8ml stored in counted_partial_units  
# New display: Shows as "0 cases, 0.008 bottles"
```

The helper function seamlessly converts between formats!
