# Frontend Syrup Display Issue - FIX REQUIRED

## Problem Summary

The frontend is displaying **incorrect variance values** for Syrups items:
- **Backend sends**: `-1.00` bottles variance
- **Frontend shows**: `-4.40` bottles variance ❌

## Root Cause

The frontend is using the **wrong fields** or **wrong calculations** to display bottle counts and servings for Syrup items.

## Backend Data Analysis

For item "Monin Chocolate Cookie LTR" (Syrup):

### What Backend Sends (100% CORRECT):
```json
{
  "counted_full_units": "3.50",
  "counted_partial_units": "0.00",
  "counted_qty": "3.5000",           // 3.50 BOTTLES
  "expected_qty": "4.5000",          // 4.50 BOTTLES
  "variance_qty": "-1.0000",         // -1.00 BOTTLES
  
  "counted_display_full_units": "3.50",
  "counted_display_partial_units": "0",
  "expected_display_full_units": "4.50",
  "expected_display_partial_units": "0",
  "variance_display_full_units": "-1.00",
  "variance_display_partial_units": "0",
  
  "valuation_cost": "9.3300",        // Cost per BOTTLE
  "expected_value": "41.98",         // 4.50 bottles × €9.33
  "counted_value": "32.66",          // 3.50 bottles × €9.33
  "variance_value": "-9.33"          // -1.00 bottles × €9.33
}
```

### What Frontend Shows (WRONG):
```
Opening: "4.50 bottles" ✓ (showing 4.50 servings) ❌
Expected: "4.50 bottles" ✓ (showing 4.50 servings) ❌
Counted: "3.50 bottles" ✓ BUT "Servings 0.10" ❌❌❌
Variance: "-4.40 bottles" ❌❌❌ (should be -1.00)
```

## The Issue

Looking at the frontend display, the "Servings" value shown is **0.10**, which is completely wrong. This suggests the frontend is:

1. **Incorrectly treating bottle counts as servings**
2. **Using wrong fields for display**
3. **Doing incorrect calculations with serving sizes**

### What's Happening:

For Syrups with UOM=1 (bottles as base unit):
- `counted_qty` = 3.50 **bottles**
- `expected_qty` = 4.50 **bottles**
- `variance_qty` = -1.00 **bottles**

But the frontend seems to be:
1. Using `counted_qty` (3.50) as if it's in servings
2. Dividing by something to get "0.10 servings" shown on screen
3. Using variance calculations that produce "-4.40" instead of "-1.00"

## What Frontend MUST Do

### ✅ CORRECT Approach (Use These Fields):

For **ALL** UOM=1 items (Spirits, Wine, Syrups, BIB, Bulk Juices):

```javascript
// DISPLAY BOTTLE COUNTS
const openingBottles = parseFloat(opening_display_full_units);  // 4.50
const countedBottles = parseFloat(counted_display_full_units);  // 3.50
const expectedBottles = parseFloat(expected_display_full_units); // 4.50

// DISPLAY VARIANCE
const varianceBottles = parseFloat(variance_display_full_units); // -1.00

// NOTE: partial_units will ALWAYS be "0" or "0.00" for UOM=1 items
// So you can ignore them or just add them (they're zero anyway)

// DISPLAY SERVINGS (for reference only)
// For Syrups: 1 bottle = 28 servings (700ml ÷ 25ml)
// For Spirits: 1 bottle = 20 servings (700ml ÷ 35ml)
// But DO NOT use serving calculations for variance!
```

### ❌ WRONG Approach (Don't Do This):

```javascript
// DON'T use counted_qty as servings!
const servings = obj.counted_qty;  // ❌ This is 3.50 BOTTLES, not servings!

// DON'T do calculations with serving sizes!
const bottles = servings / SERVING_SIZE;  // ❌ Wrong!

// DON'T use variance_qty with additional calculations!
const variance = obj.variance_qty * SOME_FACTOR;  // ❌ Wrong!
```

## Frontend Code Changes Needed

### 1. Fix Variance Display

**Current (WRONG):**
```javascript
// Somewhere in your code, you're probably doing:
const variance = Math.abs(Number(varianceDisplayFull) + Number(varianceDisplayPartial)).toFixed(2);
// This SHOULD work and give you 1.00, but you're getting 4.40...
```

**Check if you're using the wrong field:**
```javascript
// Are you using one of these by mistake?
obj.variance_qty                    // This is correct (-1.00 bottles)
obj.counted_qty - obj.expected_qty  // This also works (-1.00 bottles)

// But NOT:
obj.some_serving_based_calculation  // ❌
```

### 2. Fix Servings Display

**For Syrups:**
```javascript
// If you want to show servings for reference:
const SYRUP_SERVING_SIZE = 25;  // ml
const BOTTLE_SIZE = 700;         // ml (or 1000ml for LTR)

const servingsPerBottle = BOTTLE_SIZE / SYRUP_SERVING_SIZE;
const totalServings = countedBottles * servingsPerBottle;

// Example: 3.50 bottles × 28 servings/bottle = 98 servings
// NOT "0.10 servings" as shown on screen!
```

### 3. Fix Display Labels

**For UOM=1 items (Spirits, Wine, Syrups, BIB, Bulk Juices):**
- Show: "3.50 bottles" (not split into full + partial)
- Show: "-1.00 bottles" for variance (not "-4.40")
- Optional: Show calculated servings for reference

**For UOM>1 items (Draught, Bottled Beer, Soft Drinks):**
- Show: "2 cases + 8 bottles" (split display)
- Show: "+1 cases +10 bottles" for variance

## Testing Checklist

Test these scenarios in the frontend:

### Syrups (UOM=1):
- [ ] Opening: 4.50 bottles → Display "4.50 bottles" (not split)
- [ ] Counted: 3.50 bottles → Display "3.50 bottles" (not split)
- [ ] Variance: -1.00 bottles → Display "-1.00 bottles" (not "-4.40")
- [ ] Servings (optional): 98 servings (not "0.10")

### Spirits (UOM=1):
- [ ] Opening: 5.50 bottles → Display "5.50 bottles"
- [ ] Variance: +2.00 bottles → Display "+2.00 bottles"

### Bottled Beer (UOM=12):
- [ ] Opening: 22 bottles → Display "1 cases + 10 bottles"
- [ ] Variance: +10 bottles → Display "+0 cases +10 bottles"

## Backend Data Contract

The backend guarantees for **UOM=1 items**:

1. **All quantity fields are in BOTTLES:**
   - `counted_qty` = bottle count
   - `expected_qty` = bottle count
   - `variance_qty` = bottle count
   - `opening_qty` = bottle count

2. **All display fields show combined totals:**
   - `counted_display_full_units` = total bottles (e.g., "3.50")
   - `counted_display_partial_units` = "0" (always zero)
   - `variance_display_full_units` = variance in bottles (e.g., "-1.00")
   - `variance_display_partial_units` = "0" (always zero)

3. **Valuation is per bottle:**
   - `valuation_cost` = cost per bottle
   - `counted_value` = bottles × cost_per_bottle
   - `variance_value` = variance_bottles × cost_per_bottle

## Summary

**The backend is 100% correct.** The issue is in the frontend code that:
1. Uses wrong fields for display
2. Shows "Servings 0.10" when it should show "3.50 bottles"
3. Calculates variance as "-4.40" when backend sends "-1.00"

**Frontend fix:**
- Use `variance_display_full_units` directly
- Stop doing serving-based calculations for UOM=1 items
- Display bottle counts, not servings
- The formula `Math.abs(Number(varianceDisplayFull) + Number(varianceDisplayPartial))` SHOULD work if you're using the right fields!

## Questions to Ask Frontend Developer

1. Which field are you using for variance display?
2. Are you doing any calculations with serving sizes?
3. Where is the "0.10 servings" value coming from?
4. Can you console.log() the actual values you're receiving from the backend?

---

**Date**: 2025-01-19  
**Backend Version**: All fixes applied, tested, and verified correct  
**Issue**: Frontend display logic needs update
