# 🚨 FRONTEND FIX REQUIRED: Syrups Display - Locked View

## Problem Summary

The **locked/closed stocktake view** shows syrups incorrectly - displaying `counted_full_units` and `counted_partial_units` on **TWO SEPARATE LINES** instead of combining them into a **SINGLE TOTAL**.

## What's Working vs What's Broken

### ✅ Active/Draft View (Working Correctly)
The input view in `getLineInputs()` function **correctly combines** the values:
```javascript
if (line.subcategory_name === 'SYRUPS') {
  const fullUnits = Number(line.counted_full_units || 0);  // 4
  const partialUnits = Number(line.counted_partial_units || 0);  // 0.5
  const combinedValue = fullUnits + partialUnits;  // 4.5
  
  return {
    fullUnits: combinedValue !== 0 ? combinedValue.toFixed(2) : '',  // Shows "4.50" ✅
    partialUnits: '',  // Hidden ✅
  };
}
```
**Result:** User sees single input field with "4.50 bottles" ✅

---

### ❌ Locked/Closed View (BROKEN)
The locked view in `renderLockedLineRow()` function shows values **separately**:

**Current code (lines ~869-895):**
```javascript
{labels.showFull === false ? (
  // SYRUPS: Show full + partial bottles separately (no "cases" label)
  <div className="d-flex flex-column align-items-center gap-1">
    <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#212529' }}>
      {line.counted_full_units !== null ? line.counted_full_units : '-'}
    </div>
    {/* ❌ DISPLAYS "4" ON FIRST LINE */}
    
    <div className="d-flex align-items-center gap-1">
      <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#212529' }}>
        {line.counted_partial_units !== null ? parseFloat(line.counted_partial_units).toFixed(2) : '-'}
      </div>
      <small className="text-muted">{labels.servingUnit}</small>
    </div>
    {/* ❌ DISPLAYS "0.50 bottles" ON SECOND LINE */}
  </div>
```

**Result:** User sees TWO separate lines showing "4" and "0.50 bottles" ❌

---

## The Fix

### File: `StocktakeLines.jsx`
### Function: `renderLockedLineRow()` 
### Lines: ~869-895

**Replace the entire SYRUPS display block with this:**

```javascript
{labels.showFull === false ? (
  // SYRUPS: Show combined bottles (full + partial)
  <div className="d-flex align-items-center gap-2 justify-content-center">
    <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#212529' }}>
      {line.counted_full_units !== null || line.counted_partial_units !== null 
        ? (parseFloat(line.counted_full_units || 0) + parseFloat(line.counted_partial_units || 0)).toFixed(2)
        : '-'}
    </div>
    <small className="text-muted">{labels.servingUnit}</small>
  </div>
```

**Result:** User sees single line showing "**4.50** bottles" ✅

---

## Why This Matters

**Before fix:**
```
Line 1:  4
Line 2:  0.50 bottles
```
User sees two separate values - confusing and doesn't match the input view.

**After fix:**
```
4.50 bottles
```
User sees one combined total - matches how they entered it, clear and consistent.

---

## Testing Checklist

After making the change, verify in a **LOCKED/CLOSED** stocktake:

- [ ] Syrups display shows **ONE LINE** with combined value (e.g., "4.50 bottles")
- [ ] NOT showing TWO LINES with separate values (4 and 0.50)
- [ ] Label "bottles" appears next to the combined value
- [ ] All syrups in the stocktake display correctly
- [ ] Display matches the input view format (both show combined total)

---

## Technical Details

**Backend stores:**
- `counted_full_units = 4` (whole bottles)
- `counted_partial_units = 0.5` (fractional bottles)

**Frontend should display:**
- Combined: `4 + 0.5 = 4.50 bottles`
- NOT separate: `4` and `0.50 bottles`

**Why separate in database?**
Backend needs both fields to properly calculate:
- Servings: `(full + partial) × bottle_size_ml ÷ 35ml`
- Cost: `(full + partial) × valuation_cost`

**Why combined in display?**
Users think in total bottles (4.5), not separate components (4 + 0.5)
