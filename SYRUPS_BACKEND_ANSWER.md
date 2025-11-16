# SYRUPS Backend API - Simple Answer

## What Backend Sends (Opening Stock)

**Option C - Both fields with full values:**
```json
{
  "current_full_units": 15,
  "current_partial_units": 0.6
}
```

---

## What Frontend Should Do

### 1. Display Opening Stock
```javascript
// Combine both fields for display
const openingValue = current_full_units + current_partial_units;
// Shows: 15.6
```

### 2. User Updates Opening Stock (NEW WAY - Easiest!)
```javascript
// User enters: 1234
// Send to backend (NO SPLITTING NEEDED!):
{
  syrup_bottles_input: 1234
}
// Backend auto-splits to: full=1234, partial=0
```

### 3. User Enters Decimal (NEW WAY - Easiest!)
```javascript
// User enters: 10.5
// Send to backend (NO SPLITTING NEEDED!):
{
  syrup_bottles_input: 10.5
}
// Backend auto-splits to: full=10, partial=0.5
```

### 4. User Enters Whole Number (NEW WAY - Easiest!)
```javascript
// User enters: 199
// Send to backend (NO SPLITTING NEEDED!):
{
  syrup_bottles_input: 199
}
// Backend auto-splits to: full=199, partial=0
```

### 5. User Enters Only Decimal (NEW WAY - Easiest!)
```javascript
// User enters: 0.5
// Send to backend (NO SPLITTING NEEDED!):
{
  syrup_bottles_input: 0.5
}
// Backend auto-splits to: full=0, partial=0.5
```

---

## Complete Update Handler (SIMPLEST!)

```javascript
function handleSyrupInput(value) {
  // Just send the value as-is!
  return {
    syrup_bottles_input: value
  };
}

// Examples - ALL handled by backend:
handleSyrupInput(10.5)   // Backend splits → { full: 10, partial: 0.5 }
handleSyrupInput(199)    // Backend splits → { full: 199, partial: 0 }
handleSyrupInput(0.5)    // Backend splits → { full: 0, partial: 0.5 }
handleSyrupInput(1234.75) // Backend splits → { full: 1234, partial: 0.75 }
```

---

## DON'T Calculate ml or opening_qty!

❌ **WRONG:**
```javascript
opening_qty = (1234 × 1000) + 0  // DON'T DO THIS!
```

✅ **CORRECT:**
```javascript
// Just send the split values
{
  current_full_units: 1234,
  current_partial_units: 0
}
// Backend calculates everything else!
```

---

## Exact Payload Examples

### ✅ NEW: Single Field (Easiest!) - User enters 10.5
```javascript
// PATCH /api/stocktake-lines/{id}/
{
  "syrup_bottles_input": 10.5
}
// Backend auto-splits to: full=10, partial=0.5
```

### Update Counted Stock - User enters 199
```javascript
// PATCH /api/stocktake-lines/{id}/
{
  "syrup_bottles_input": 199
}
// Backend auto-splits to: full=199, partial=0
```

### Update Counted Stock - User enters 0.75
```javascript
// PATCH /api/stocktake-lines/{id}/
{
  "syrup_bottles_input": 0.75
}
// Backend auto-splits to: full=0, partial=0.75
```

### ⚠️ OLD WAY (Still works but not needed)
```javascript
// PATCH /api/stocktake-lines/{id}/
{
  "counted_full_units": 10,
  "counted_partial_units": 0.5
}
```

**That's it!** Backend calculates:
- `total_ml`
- `servings`
- `variance`
- Everything else

---

## Summary

**Backend sends:** `full_units` + `partial_units`  
**Frontend displays:** Combine them (`15 + 0.6 = 15.6`)  
**Frontend sends:** ✨ **JUST ONE FIELD:** `syrup_bottles_input: 10.5`  
**Backend auto-splits** into `full` + `partial`  
**DON'T:** Calculate ml, servings, opening_qty, or anything else!  

**Frontend does NO math - NO splitting needed!** Backend handles it! ✅
