# ⚠️ VALIDATION RULES - Backend Already Has These!

## DO NOT DUPLICATE - These validations exist in `stock_serializers.py`

Backend already validates field limits in the `input_fields` method. Frontend should use these, not create new ones!

---

## MINERALS Validations (Backend)

### SOFT_DRINKS
```python
# Current backend validation (lines 695-698):
{
    'full': {'name': 'counted_full_units', 'label': 'Cases'},
    'partial': {'name': 'counted_partial_units', 'label': 'Bottles', 'max': 11}
}
```

**✅ Backend limits:** Bottles max = 11 (0-11 range)

**🔄 NEW: For total bottles input:**
```javascript
// Frontend auto-splits, no validation needed
// 145 bottles → 12 cases + 1 bottle (auto-calculated)
```

---

### SYRUPS
```python
# Current backend validation (lines 700-703):
{
    'full': {'name': 'counted_full_units', 'label': 'Bottles'},
    'partial': {'name': 'counted_partial_units', 'label': 'ml', 'max': 1000}
}
```

**❌ OUTDATED!** This is the OLD validation (2 separate fields: bottles + ml)

**✅ NEW IMPLEMENTATION:**
```python
# Should be updated to:
{
    'full': {'name': 'counted_full_units', 'label': None},  # Not used
    'partial': {'name': 'counted_partial_units', 'label': 'Total Bottles', 'step': 0.001}
}
# NO MAX - can be 10.5, 100.5, 1234.567, etc.
```

**Frontend validation for SYRUPS:**
```javascript
// Only validate it's a positive number
// NO maximum limit!
// Allow decimals: step="0.001"
value >= 0  // That's it!
```

---

### JUICES
```python
# Current backend validation (lines 705-708):
{
    'full': {'name': 'counted_full_units', 'label': 'Bottles'},
    'partial': {'name': 'counted_partial_units', 'label': 'ml', 'max': 1500}
}
```

**❌ OUTDATED!** This is also OLD validation

**✅ NEW IMPLEMENTATION:**
```python
# Should be updated to:
{
    'full': {'name': 'counted_full_units', 'label': 'Cases'},
    'partial': {'name': 'counted_partial_units', 'label': 'Bottles (decimal)', 'step': 0.001}
}
# NO MAX on bottles field - backend auto-splits
```

**Frontend validation for JUICES:**
```javascript
// If entering total bottles (e.g., 716.5):
// Auto-split to cases + bottles, no validation needed

// If entering cases + bottles separately:
// Bottles can have decimal: 8.5, 11.75, etc.
// NO maximum - any amount works
```

---

## Summary: What Frontend Should Do

### SYRUPS
```javascript
// ❌ DON'T validate max ml
// ❌ DON'T validate separate bottles/ml fields
// ✅ DO accept any positive decimal number

<Input 
  name="counted_partial_units"
  type="number"
  step="0.001"
  min="0"
  // NO max attribute!
/>
```

### SOFT_DRINKS
```javascript
// Option 1: Cases + Bottles
<Input name="counted_full_units" type="number" min="0" />
<Input name="counted_partial_units" type="number" min="0" max="11" />

// Option 2: Total Bottles (auto-split)
<Input 
  type="number" 
  min="0"
  onChange={(value) => {
    const cases = Math.floor(value / 12);
    const bottles = value % 12;
    setCountedFullUnits(cases);
    setCountedPartialUnits(bottles);
  }}
/>
// Auto-split ensures bottles stays 0-11 automatically
```

### JUICES
```javascript
// Cases field
<Input name="counted_full_units" type="number" min="0" />

// Bottles field (accepts decimals)
<Input 
  name="counted_partial_units" 
  type="number" 
  step="0.001"
  min="0"
  // NO max - backend handles any amount
/>
```

---

## Backend Updates Needed

Update `stock_serializers.py` line 700-708:

```python
elif obj.item.subcategory == 'SYRUPS':
    return {
        'full': None,  # Not used
        'partial': {
            'name': 'counted_partial_units', 
            'label': 'Total Bottles', 
            'step': 0.001
        }
    }

elif obj.item.subcategory == 'JUICES':
    return {
        'full': {
            'name': 'counted_full_units', 
            'label': 'Cases'
        },
        'partial': {
            'name': 'counted_partial_units', 
            'label': 'Bottles (decimal)', 
            'step': 0.001
        }
    }
```

---

## Key Points for Frontend

1. **SYRUPS:** NO max validation - accepts any positive decimal
2. **SOFT_DRINKS:** If using total bottles input, auto-split handles validation
3. **JUICES:** Bottles field accepts decimals, NO max limit
4. **Use backend's `input_fields` response** - don't duplicate validation logic
5. **The old max values (1000ml, 1500ml) are OBSOLETE** - remove them!
