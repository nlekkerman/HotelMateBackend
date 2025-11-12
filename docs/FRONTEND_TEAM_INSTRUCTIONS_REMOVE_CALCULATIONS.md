# 📢 FRONTEND TEAM INSTRUCTIONS - REMOVE CALCULATIONS

**Date:** November 12, 2025  
**Action Required:** Remove all frontend calculations and use backend values only  
**Priority:** HIGH

---

## 🚨 CRITICAL CHANGES REQUIRED

### STEP 1: Delete Calculation Functions

**Location:** `stocktakeCalculations.js` (or similar utility file)

**Delete these functions entirely:**

```javascript
// ❌ DELETE THIS ENTIRE FUNCTION
export function calculateExpectedQty(line) {
  const opening = parseFloat(line.opening_qty) || 0;
  const purchases = parseFloat(line.purchases) || 0;
  const waste = parseFloat(line.waste) || 0;
  return opening + purchases - waste;
}

// ❌ DELETE THIS ENTIRE FUNCTION
export function calculateCountedQty(line) {
  const fullUnits = parseFloat(line.counted_full_units) || 0;
  const partialUnits = parseFloat(line.counted_partial_units) || 0;
  const uom = parseFloat(line.item_uom || line.uom) || 1;
  
  if (line.category_code === 'B' || /* ... */) {
    return (fullUnits * uom) + partialUnits;
  } else {
    return (fullUnits * uom) + (partialUnits * uom);
  }
}

// ❌ DELETE THIS ENTIRE FUNCTION
export function calculateVariance(line) {
  const counted = calculateCountedQty(line);
  const expected = calculateExpectedQty(line);
  return counted - expected;
}

// ❌ DELETE THIS ENTIRE FUNCTION
export function calculateValues(line) {
  const counted = calculateCountedQty(line);
  const expected = calculateExpectedQty(line);
  const cost = parseFloat(line.valuation_cost) || 0;
  
  return {
    expected_value: expected * cost,
    counted_value: counted * cost,
    variance_value: (counted - expected) * cost
  };
}

// ❌ DELETE THIS ENTIRE FUNCTION
export function convertToDisplayUnits(servings, item) {
  const uom = parseFloat(item.item_uom || item.uom) || 1;
  const fullUnits = Math.floor(servings / uom);
  const partialUnits = servings % uom;
  // ... rounding logic ...
  return { full, partial };
}

// ❌ DELETE ALL OPTIMISTIC UPDATE FUNCTIONS
export function optimisticUpdateMovement(line, movementData) {
  // Don't calculate locally!
}

export function optimisticUpdateCount(line, fullUnits, partialUnits) {
  // Don't calculate locally!
}
```

---

### STEP 2: Update Display Components

**Before (WRONG):**
```javascript
// ❌ DON'T DO THIS
function StocktakeLine({ line }) {
  // Calculating on frontend
  const expected = calculateExpectedQty(line);
  const counted = calculateCountedQty(line);
  const variance = calculateVariance(line);
  const { expected_value, counted_value, variance_value } = calculateValues(line);
  
  return (
    <div>
      <span>Expected: {expected}</span>
      <span>Counted: {counted}</span>
      <span>Variance: {variance}</span>
      <span>Value: €{variance_value.toFixed(2)}</span>
    </div>
  );
}
```

**After (CORRECT):**
```javascript
// ✅ DO THIS - Just display backend values
function StocktakeLine({ line }) {
  return (
    <div>
      <span>Expected: {line.expected_display_full_units} cases, {line.expected_display_partial_units} bottles</span>
      <span>Counted: {line.counted_display_full_units} cases, {line.counted_display_partial_units} bottles</span>
      <span>Variance: {line.variance_display_full_units} cases, {line.variance_display_partial_units} bottles</span>
      <span>Value: €{parseFloat(line.variance_value).toFixed(2)}</span>
    </div>
  );
}
```

---

### STEP 3: Remove Optimistic Updates

**Before (WRONG):**
```javascript
// ❌ DON'T DO THIS
async function handleCountUpdate(lineId, fullUnits, partialUnits) {
  // Optimistically update UI before backend responds
  const optimisticLine = {
    ...line,
    counted_full_units: fullUnits,
    counted_partial_units: partialUnits,
    counted_qty: calculateCountedQty({ ...line, counted_full_units: fullUnits, counted_partial_units: partialUnits }),
    variance_qty: calculateVariance({ ...line, counted_full_units: fullUnits, counted_partial_units: partialUnits })
  };
  
  updateLineInState(lineId, optimisticLine); // ❌ Wrong!
  
  // Then send to backend
  await api.patch(`/stocktake-lines/${lineId}/`, {
    counted_full_units: fullUnits,
    counted_partial_units: partialUnits
  });
}
```

**After (CORRECT):**
```javascript
// ✅ DO THIS - Wait for backend/Pusher
async function handleCountUpdate(lineId, fullUnits, partialUnits) {
  // Just send to backend
  const response = await api.patch(`/stocktake-lines/${lineId}/`, {
    counted_full_units: fullUnits,
    counted_partial_units: partialUnits
  });
  
  // Update state with backend-calculated values
  updateLineInState(lineId, response.data);
  
  // Pusher will broadcast to other users automatically
}
```

---

### STEP 4: Setup Pusher Listener

**Add this to your stocktake page component:**

```javascript
import { useEffect, useState } from 'react';
import Pusher from 'pusher-js';

function StocktakePage({ stocktakeId, hotelId }) {
  const [lines, setLines] = useState([]);
  
  useEffect(() => {
    // Initialize Pusher
    const pusher = new Pusher(process.env.REACT_APP_PUSHER_KEY, {
      cluster: process.env.REACT_APP_PUSHER_CLUSTER,
      authEndpoint: '/api/pusher/auth'
    });
    
    // Subscribe to stocktake channel
    const channelName = `private-hotel-${hotelId}-stocktake-${stocktakeId}`;
    const channel = pusher.subscribe(channelName);
    
    // Listen for line updates
    channel.bind('line-counted-updated', (data) => {
      console.log('Received line update from Pusher:', data);
      
      // Update the line in state with ALL backend-calculated values
      setLines(prevLines => 
        prevLines.map(line => 
          line.id === data.line_id ? data.line : line
        )
      );
      
      // Refresh category totals if needed
      refreshCategoryTotals();
    });
    
    // Cleanup on unmount
    return () => {
      channel.unbind_all();
      channel.unsubscribe();
      pusher.disconnect();
    };
  }, [stocktakeId, hotelId]);
  
  return (
    <div>
      {lines.map(line => (
        <StocktakeLine key={line.id} line={line} />
      ))}
    </div>
  );
}
```

---

### STEP 5: Update API Response Handling

**Use ALL fields from backend response:**

```javascript
// ✅ Backend provides these calculated fields:
{
  // RAW QUANTITIES (servings)
  "opening_qty": "0.0000",
  "purchases": "12.4300",
  "waste": "1.0000",
  "expected_qty": "11.4300",      // ✅ Backend calculated
  "counted_qty": "14.0000",       // ✅ Backend calculated
  "variance_qty": "2.5700",       // ✅ Backend calculated
  
  // DISPLAY UNITS (already converted and rounded)
  "opening_display_full_units": "0",
  "opening_display_partial_units": "0",
  "expected_display_full_units": "0",
  "expected_display_partial_units": "11",
  "counted_display_full_units": "1",
  "counted_display_partial_units": "2",
  "variance_display_full_units": "0",
  "variance_display_partial_units": "3",
  
  // VALUES (euros)
  "expected_value": "13.53",      // ✅ Backend calculated
  "counted_value": "17.22",       // ✅ Backend calculated
  "variance_value": "3.69",       // ✅ Backend calculated
  
  // USER INPUT
  "counted_full_units": "1.00",
  "counted_partial_units": "2.00"
}
```

---

### STEP 6: Update Category Totals

**Before (WRONG):**
```javascript
// ❌ DON'T calculate category totals on frontend
function CategoryTotal({ lines, categoryCode }) {
  const categoryLines = lines.filter(l => l.category_code === categoryCode);
  
  const totalExpected = categoryLines.reduce((sum, line) => 
    sum + calculateExpectedQty(line), 0
  );
  
  const totalCounted = categoryLines.reduce((sum, line) => 
    sum + calculateCountedQty(line), 0
  );
  
  const totalVariance = totalCounted - totalExpected;
  
  return <div>Variance: {totalVariance}</div>;
}
```

**After (CORRECT):**
```javascript
// ✅ Fetch category totals from backend
async function CategoryTotal({ stocktakeId, categoryCode }) {
  const [totals, setTotals] = useState(null);
  
  useEffect(() => {
    // Backend calculates all category totals
    const fetchTotals = async () => {
      const response = await api.get(
        `/stocktakes/${stocktakeId}/category_totals/?category=${categoryCode}`
      );
      setTotals(response.data[categoryCode]);
    };
    
    fetchTotals();
  }, [stocktakeId, categoryCode]);
  
  if (!totals) return <div>Loading...</div>;
  
  return (
    <div>
      <span>Expected: €{parseFloat(totals.expected_value).toFixed(2)}</span>
      <span>Counted: €{parseFloat(totals.counted_value).toFixed(2)}</span>
      <span>Variance: €{parseFloat(totals.variance_value).toFixed(2)}</span>
    </div>
  );
}
```

---

## 🎯 VALIDATION (Keep This)

**Frontend should ONLY validate user input format:**

```javascript
// ✅ KEEP THIS - Validate before sending to backend
function validatePartialUnits(value, line) {
  const uom = parseFloat(line.item_uom);
  const category = line.category_code;
  const size = line.item_size || '';
  
  // Bottled Beer + Dozen Minerals: whole numbers only
  if (category === 'B' || (category === 'M' && size.includes('Doz'))) {
    if (!Number.isInteger(value)) {
      return 'Must be a whole number';
    }
    if (value < 0 || value >= uom) {
      return `Must be between 0 and ${uom - 1}`;
    }
  }
  // Draught, Spirits, Wine: max 2 decimals
  else {
    if (!/^\d+(\.\d{0,2})?$/.test(value.toString())) {
      return 'Max 2 decimal places';
    }
    if (value < 0 || value >= uom) {
      return `Must be between 0.00 and ${(uom - 0.01).toFixed(2)}`;
    }
  }
  
  return null; // Valid
}
```

---

## 📊 BEFORE & AFTER COMPARISON

### Display Opening Stock

**Before:**
```javascript
const { full, partial } = convertToDisplayUnits(line.opening_qty, line);
return <span>{full} cases, {partial} bottles</span>;
```

**After:**
```javascript
return <span>{line.opening_display_full_units} cases, {line.opening_display_partial_units} bottles</span>;
```

### Display Expected

**Before:**
```javascript
const expected = calculateExpectedQty(line);
const { full, partial } = convertToDisplayUnits(expected, line);
const value = expected * parseFloat(line.valuation_cost);
return <span>{full} cases, {partial} bottles (€{value.toFixed(2)})</span>;
```

**After:**
```javascript
return <span>{line.expected_display_full_units} cases, {line.expected_display_partial_units} bottles (€{parseFloat(line.expected_value).toFixed(2)})</span>;
```

### Display Variance

**Before:**
```javascript
const variance = calculateVariance(line);
const { full, partial } = convertToDisplayUnits(variance, line);
const value = variance * parseFloat(line.valuation_cost);
const color = value > 0 ? 'green' : value < 0 ? 'red' : 'grey';
return <span style={{color}}>{full} cases, {partial} bottles (€{value.toFixed(2)})</span>;
```

**After:**
```javascript
const value = parseFloat(line.variance_value);
const color = value > 0 ? 'green' : value < 0 ? 'red' : 'grey';
return <span style={{color}}>{line.variance_display_full_units} cases, {line.variance_display_partial_units} bottles (€{value.toFixed(2)})</span>;
```

---

## ✅ TESTING CHECKLIST

After making changes, verify:

- [ ] No calculation functions remain in frontend code
- [ ] All displays use backend fields (`_display_full_units`, `_display_partial_units`, `_value`)
- [ ] Pusher listener is connected and receiving updates
- [ ] When user A updates a count, user B sees the change immediately
- [ ] No optimistic updates - UI waits for backend/Pusher
- [ ] Category totals come from backend API, not frontend calculation
- [ ] Input validation still works (format checking before sending)
- [ ] Console shows no calculation-related errors
- [ ] Values match between what backend sends and what UI displays

---

## 📚 DOCUMENTATION REFERENCES

- **Complete API Reference:** `docs/BACKEND_API_COMPLETE_REFERENCE_FOR_FRONTEND.md`
- **Formula Reference:** `docs/STOCKTAKE_FORMULAS_QUICK_REFERENCE.md`
- **Original Display Variables:** `STOCKTAKE_DISPLAY_VARIABLES_BACKEND_REFERENCE.md`

---

## 🆘 SUPPORT

If you encounter issues:

1. **Check API response** - Does it include all calculated fields?
2. **Check Pusher connection** - Are you subscribed to the right channel?
3. **Check field names** - Use `expected_display_full_units`, not `expectedDisplayFullUnits`
4. **Check parsing** - All numeric values are strings, use `parseFloat()`

**Backend Developer Contact:** [Your contact info]

---

## 🎯 SUMMARY

### What to DELETE:
- `calculateExpectedQty()`
- `calculateCountedQty()`
- `calculateVariance()`
- `calculateValues()`
- `convertToDisplayUnits()`
- `optimisticUpdateMovement()`
- `optimisticUpdateCount()`

### What to KEEP:
- Input validation functions
- Display components (but using backend values)
- API call functions
- Pusher setup

### What to ADD:
- Pusher event listener for `line-counted-updated`
- Direct usage of backend fields in displays
- Category totals API calls

---

**END OF INSTRUCTIONS**
