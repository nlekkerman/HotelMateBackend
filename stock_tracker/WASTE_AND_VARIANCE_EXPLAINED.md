# Understanding Waste Impact on Variance

## Quick Answer

**YES**, waste **DOES** impact variance, but **INDIRECTLY** through the expected quantity calculation.

## The Formula Chain

### 1. Expected Quantity Formula
```
expected_qty = opening_qty 
             + purchases 
             + transfers_in 
             - sales 
             - waste              ← Waste reduces expected!
             - transfers_out 
             + adjustments
```

### 2. Variance Formula
```
variance_qty = counted_qty - expected_qty
```

### 3. Counted Quantity
```
counted_qty = (counted_full_units × servings_per_unit) + counted_partial_units
```

## How Waste Affects Variance

Waste **reduces** the expected quantity, which **increases** the variance (makes it less negative or more positive).

### Example Scenario

**Initial State:**
```
Opening:  100 bottles
Purchases: 50 bottles
Sales:    120 bottles
Waste:     0 bottles (no waste recorded yet)
─────────────────────
Expected: 100 + 50 - 120 = 30 bottles
Counted:  25 bottles (actual physical count)
Variance: 25 - 30 = -5 bottles (shortage)
```

**After Recording Waste:**
```
Opening:  100 bottles
Purchases: 50 bottles
Sales:    120 bottles
Waste:     5 bottles ← NOW RECORDED!
─────────────────────
Expected: 100 + 50 - 120 - 5 = 25 bottles
Counted:  25 bottles (same physical count)
Variance: 25 - 25 = 0 bottles ✓ (Perfect match!)
```

## What Changed?

| Field | Without Waste | With Waste | Impact |
|-------|--------------|------------|---------|
| **Expected** | 30 | 25 | Decreased by 5 |
| **Counted** | 25 | 25 | No change (it's physical count) |
| **Variance** | -5 | 0 | Improved by 5 |

## Key Insights

### 1. Counted Qty is Independent
- `counted_full_units` and `counted_partial_units` are **user input**
- They represent **physical stock on hand**
- They are **NOT affected** by movements like waste, sales, or purchases
- You count what's physically there, period.

### 2. Expected Qty Changes with All Movements
Expected quantity changes based on:
- ✅ **Purchases** → Increase expected
- ✅ **Sales** → Decrease expected
- ✅ **Waste** → Decrease expected
- ✅ **Transfer In** → Increase expected
- ✅ **Transfer Out** → Decrease expected
- ✅ **Adjustments** → Increase or decrease expected

### 3. Variance is the Difference
- Variance shows how far off your expected calculation is from reality
- If you don't record waste, variance shows as shortage
- Recording waste adjusts expected to match reality

## Practical Examples

### Example 1: Broken Keg (Draught)

```
Before Recording Waste:
  Opening:  88 pints (1 keg)
  Purchases: 88 pints (1 keg delivered)
  Sales:    100 pints
  Waste:     0 pints ← Forgot to record broken keg!
  ─────────
  Expected: 88 + 88 - 100 = 76 pints
  Counted:  0 pints (keg broke, nothing left)
  Variance: 0 - 76 = -76 pints ⚠️ HUGE SHORTAGE!

After Recording Waste:
  Opening:  88 pints
  Purchases: 88 pints
  Sales:    100 pints
  Waste:    76 pints ← Recorded broken keg!
  ─────────
  Expected: 88 + 88 - 100 - 76 = 0 pints
  Counted:  0 pints
  Variance: 0 - 0 = 0 pints ✓ PERFECT!
```

### Example 2: Spoiled Wine Bottles

```
Before Recording Waste:
  Opening:  24 bottles (2 cases)
  Purchases: 12 bottles (1 case)
  Sales:    20 bottles
  Waste:     0 bottles ← 3 bottles corked/spoiled
  ─────────
  Expected: 24 + 12 - 20 = 16 bottles
  Counted:  13 bottles (3 were bad)
  Variance: 13 - 16 = -3 bottles ⚠️ Shortage

After Recording Waste:
  Opening:  24 bottles
  Purchases: 12 bottles
  Sales:    20 bottles
  Waste:     3 bottles ← Recorded spoiled bottles!
  ─────────
  Expected: 24 + 12 - 20 - 3 = 13 bottles
  Counted:  13 bottles
  Variance: 13 - 13 = 0 bottles ✓ MATCH!
```

### Example 3: Spillage (Spirits)

```
Before Recording Waste:
  Opening:  280 shots (4 bottles × 70 shots)
  Purchases: 210 shots (3 bottles)
  Sales:    400 shots
  Waste:     0 shots ← Dropped bottle = 70 shots lost
  ─────────
  Expected: 280 + 210 - 400 = 90 shots
  Counted:  20 shots (less than 1 bottle left)
  Variance: 20 - 90 = -70 shots ⚠️ SHORTAGE!

After Recording Waste:
  Opening:  280 shots
  Purchases: 210 shots
  Sales:    400 shots
  Waste:    70 shots ← Recorded dropped bottle!
  ─────────
  Expected: 280 + 210 - 400 - 70 = 20 shots
  Counted:  20 shots
  Variance: 20 - 20 = 0 shots ✓ MATCH!
```

## Why This Matters

### 1. Accurate Variance Reporting
- Without recording waste, variance looks like theft or loss
- Recording waste properly shows true operational efficiency
- Helps identify real problems vs. explained losses

### 2. Financial Accuracy
- Waste is a legitimate cost of business
- Should be tracked separately from theft/shrinkage
- Helps with cost control and pricing decisions

### 3. Audit Trail
- Each waste entry is documented with:
  - Quantity
  - Timestamp
  - Staff member who recorded it
  - Reference/notes (reason for waste)

## Common Waste Scenarios

### Bar/Restaurant Waste Types:
1. **Breakage** - Dropped bottles, broken kegs
2. **Spoilage** - Corked wine, flat beer, expired mixers
3. **Spillage** - Over-pouring, accidents
4. **Sampling** - Staff tastings, quality checks
5. **Comping** - Free drinks (sometimes tracked as waste)
6. **Line Cleaning** - Beer line flushes, draught maintenance

## How to Use in Your System

### Adding Waste from UI:

```javascript
// User clicks "Add Waste"
const handleAddWaste = async () => {
  const response = await fetch(
    `/api/stock_tracker/hotel/stocktake-lines/${lineId}/add-movement/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        movement_type: 'WASTE',
        quantity: 76,  // e.g., broken keg
        notes: 'Keg damaged during delivery'
      })
    }
  );
  
  const data = await response.json();
  // data.line.waste will now be updated
  // data.line.expected_qty will be recalculated
  // data.line.variance_qty will reflect the change
};
```

### Result:
- ✅ Waste movement created in database
- ✅ Line totals automatically recalculated
- ✅ Expected qty reduced by waste amount
- ✅ Variance adjusted to reflect reality
- ✅ Audit trail maintained

## Summary

| Factor | Affects Expected? | Affects Counted? | Affects Variance? |
|--------|------------------|------------------|-------------------|
| **Waste** | ✅ YES (reduces) | ❌ NO | ✅ YES (indirectly) |
| **Sales** | ✅ YES (reduces) | ❌ NO | ✅ YES (indirectly) |
| **Purchases** | ✅ YES (increases) | ❌ NO | ✅ YES (indirectly) |
| **counted_full_units** | ❌ NO | ✅ YES | ✅ YES (directly) |
| **counted_partial_units** | ❌ NO | ✅ YES | ✅ YES (directly) |

## Formula Breakdown

```python
# These affect EXPECTED (and thus variance):
expected_qty = (
    opening_qty +      # Starting point
    purchases +        # ↑ Increases expected
    transfers_in -     # ↑ Increases expected
    sales -            # ↓ Decreases expected
    waste -            # ↓ Decreases expected ← HERE!
    transfers_out +    # ↓ Decreases expected
    adjustments        # ↑↓ Increases or decreases
)

# These affect COUNTED (and thus variance):
counted_qty = (
    counted_full_units × servings_per_unit +
    counted_partial_units
)

# Variance is the difference:
variance_qty = counted_qty - expected_qty
```

## Bottom Line

**Waste DOES affect variance**, but in a specific way:
- It **reduces expected quantity**
- Which **changes the variance**
- But it does **NOT change counted quantity** (physical count is independent)
- Recording waste **explains discrepancies** and brings variance closer to zero

Think of it this way: If you waste something, you shouldn't expect to have it anymore! Waste tells the system "this stock is gone for a legitimate reason, don't count it as missing."
