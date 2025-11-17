# Backend Changes - Stock Tracker System (November 2025)

## Summary
This document outlines critical changes made to the stock tracking system to fix period-based opening stock calculations and remove confusion between real-time inventory and period-based accounting.

---

## ⚠️ Breaking Changes

### 1. Removed Auto-Update of Current Stock Fields

**What Changed:**
- `StockItem.current_full_units` and `StockItem.current_partial_units` are **no longer automatically updated** when stock movements are created
- These fields still exist in the database but are **deprecated for auto-update purposes**
- They can still be manually updated when closing periods if needed for dashboard displays

**Why:**
- The system uses **period-based accounting**, not real-time inventory tracking
- Auto-updating these fields was causing conflicts with period snapshots
- Opening stock should flow from previous period's closing snapshot, not from live inventory

**Impact on Frontend:**
- ✅ **No breaking changes** - fields still exist, just not auto-updated
- If your frontend displays "current stock" from these fields, it may show stale data
- Consider using the latest period's closing snapshot instead

---

## 🐛 Critical Bug Fixes

### Bug Fix #1: Opening Stock Missing Full Units (Kegs/Cases)

**Problem:**
- Opening stock for draught beer showed "0 kegs + 20 pints" instead of "1 keg + 20 pints"
- Only partial units were being carried forward, full units were lost

**Root Cause:**
```python
# OLD (WRONG):
return previous_snapshot.closing_partial_units  # ❌ Only returns pints

# NEW (CORRECT):
return previous_snapshot.total_servings  # ✅ Returns (kegs × 50) + pints
```

**Fixed In:** `stock_tracker/stocktake_service.py`, line 94

**Impact:** Opening stock now correctly includes both full units (kegs/cases) and partial units (pints/bottles)

---

### Bug Fix #2: Categories Appearing with Fake Opening Stock

**Problem:**
- Categories with NO January closing stock were appearing in February stocktake with opening values
- Example: Only Draught Beer had January closing, but Spirits, Wine, etc. showed up in February

**Root Cause:**
```python
# OLD (WRONG) - OPTION 2 fallback:
if stocktake.period_start == first_period.start_date:
    return item.total_stock_in_servings  # ❌ Uses live inventory!

# NEW (CORRECT):
return Decimal('0')  # ✅ No snapshot = zero opening
```

**Fixed In:** `stock_tracker/stocktake_service.py`, lines 95-103 (removed OPTION 2 fallback)

**Impact:** 
- Opening stock now ONLY comes from previous period's closing snapshot
- If no snapshot exists, opening stock is zero (as it should be)
- Pure period-based tracking with no fallback to live inventory

---

### Bug Fix #3: StockMovement Auto-Updating Current Fields

**Problem:**
- Creating movements (purchases, waste, etc.) was automatically updating `current_partial_units`
- This caused confusion between real-time tracking and period-based tracking

**Root Cause:**
```python
# OLD (WRONG) in StockMovement.save():
if self.movement_type == 'PURCHASE':
    item.current_partial_units += self.quantity
elif self.movement_type == 'WASTE':
    item.current_partial_units -= self.quantity
# ... etc
item.save()  # ❌ Auto-updating "current" fields

# NEW (CORRECT):
super().save(*args, **kwargs)  # ✅ Just save the movement, don't touch item
```

**Fixed In:** `stock_tracker/models.py`, `StockMovement.save()` method (line ~1507)

**Impact:**
- Movements no longer auto-update item stock
- Period snapshots are the single source of truth
- No more conflict between live inventory and period accounting

---

## 📊 Data Flow - How It Works Now

### Correct Opening Stock Calculation Flow

```
Period 1 (January):
├─ Closing Snapshot Created: 1 keg + 20 pints (total_servings = 70)
└─ Saved in database

Period 2 (February):
├─ Stocktake Created (period_start = 2025-02-01)
├─ populate_stocktake() called
│  └─ For each item:
│     ├─ Look for previous snapshot (January closing)
│     ├─ If found: opening = snapshot.total_servings (70 pints)
│     ├─ If NOT found: opening = 0
│     └─ Create StocktakeLine with opening_qty = 70
└─ Frontend displays: "1 keg + 20 pints" opening
```

### Property: `total_servings`

This is the **critical property** that makes everything work:

```python
@property
def total_servings(self):
    """
    For Draught Beer: (kegs × 50 pints/keg) + partial_pints
    For Spirits: (cases × 12 bottles/case) + partial_bottles
    For Syrups: bottles_only (full + partial)
    """
    if self.item.category.code == "DRAUGHT_BEER":
        return (self.closing_full_units * self.item.uom) + self.closing_partial_units
    # ... similar for other categories
```

**Key Points:**
- ✅ `total_servings` includes BOTH full and partial units
- ✅ It's category-aware (handles kegs, cases, bottles, etc.)
- ✅ This is what flows into next period's opening stock

---

## 🔧 API Changes

### StockItem Serializer Changes

**Removed from auto-update:**
- `current_full_units` - Still exists, but not auto-updated
- `current_partial_units` - Still exists, but not auto-updated

**These fields are still serialized** (for backward compatibility) but should not be relied upon for real-time data.

**Recommended Alternative:**
```javascript
// Instead of using item.current_full_units:
const latestPeriod = getLatestClosedPeriod();
const snapshot = latestPeriod.snapshots.find(s => s.item_id === item.id);
const currentStock = snapshot ? snapshot.total_servings : 0;
```

---

## 🚨 Frontend Action Items

### 1. Handle Duplicate Stocktake Error

**Error You're Seeing:**
```
IntegrityError: duplicate key value violates unique constraint 
"stock_tracker_stocktake_hotel_id_period_start_pe_7d16c4a2_uniq"
DETAIL: Key (hotel_id, period_start, period_end)=(2, 2025-02-01, 2025-02-28) already exists.
```

**Cause:** Trying to create a stocktake for a period that already has one

**Frontend Fix Needed:**
```javascript
// Before creating stocktake:
const existingStocktakes = await fetchStocktakes();
const duplicate = existingStocktakes.find(st => 
  st.period_start === newPeriodStart && 
  st.period_end === newPeriodEnd
);

if (duplicate) {
  // Show user-friendly error:
  alert(`A stocktake already exists for ${newPeriodStart} to ${newPeriodEnd}`);
  // OR navigate to existing stocktake:
  navigate(`/stocktakes/${duplicate.id}`);
  return;
}

// Safe to create new stocktake
await createStocktake({ period_start, period_end });
```

### 2. Update "Current Stock" Displays

**If you're showing "current stock" from `item.current_full_units`:**

```javascript
// OLD (may show stale data):
const currentStock = item.current_full_units;

// NEW (use latest snapshot):
const latestSnapshot = getLatestSnapshotForItem(item.id);
const currentStock = latestSnapshot?.closing_full_units || 0;
```

### 3. Test Opening Stock Flow

**Critical Test Case:**
1. Create Period 1 (January) with draught beer closing: 1 keg + 20 pints
2. Create Period 2 (February)
3. Call "Populate Stocktake" for February
4. **Expected:** February opening should show "1 keg + 20 pints" (70 total pints)
5. **Verify:** Other categories (Spirits, Wine, etc.) show zero opening if they had no January closing

---

## 📝 Database Schema Notes

### StockItem Model

**Fields Still Exist (Deprecated for Auto-Update):**
```python
current_full_units = models.DecimalField(...)  # Not auto-updated
current_partial_units = models.DecimalField(...)  # Not auto-updated
```

**These can be manually updated** when closing periods if you need them for dashboards, but they are not part of the core period-based accounting flow.

### StockSnapshot Model

**Critical Fields:**
```python
closing_full_units  # Kegs, cases, boxes, bottles (depending on category)
closing_partial_units  # Pints, bottles, liters, fractional (depending on category)

@property
def total_servings(self):  # This is what flows to next period's opening
    return (closing_full_units * item.uom) + closing_partial_units
```

### Stocktake Model

**Unique Constraint (Causes Duplicate Error):**
```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['hotel', 'period_start', 'period_end'],
            name='stock_tracker_stocktake_hotel_id_period_start_pe_7d16c4a2_uniq'
        )
    ]
```

**This prevents creating multiple stocktakes for the same period.**

---

## 🧪 Testing Recommendations

### Backend Tests (Already Done)

✅ Created 5 test periods (January-May 2025)
✅ Populated January with draught beer closing (1 keg + 20 pints each)
✅ Fixed opening stock to include full units (kegs)
✅ Removed fallback to live inventory
✅ Disabled auto-update of current_* fields

### Frontend Tests (TODO)

**Test 1: Duplicate Stocktake Prevention**
- Try creating stocktake for February twice
- Should show error or navigate to existing stocktake
- Should NOT crash with 500 error

**Test 2: Opening Stock Display**
- View February stocktake
- Draught beer should show "1 keg + 20 pints" opening
- Other categories should show zero (if no January closing)

**Test 3: Movement Creation**
- Create a purchase movement
- Verify `current_full_units` and `current_partial_units` are NOT updated
- Verify movement is saved correctly

**Test 4: Period Closing**
- Close a period with counted stock
- Verify closing snapshot is created
- Verify next period's opening stock matches this closing

---

## 🔗 Related Files

**Modified Backend Files:**
1. `stock_tracker/models.py` - StockMovement.save() method (removed auto-update)
2. `stock_tracker/stocktake_service.py` - _get_opening_balance() (fixed bugs #1 and #2)
3. `stock_tracker/stock_serializers.py` - StockItemSerializer (current_* fields deprecated)

**Frontend Files to Update:**
1. Stocktake creation component (duplicate prevention)
2. Current stock display components (use snapshots instead)
3. Period closing flow (verify opening/closing flow)

---

## 📞 Support

If you encounter issues with:
- Opening stock showing incorrect values
- Stocktakes failing to create
- Current stock fields showing stale data

**First Steps:**
1. Check that you're using `total_servings` from snapshots, not `current_*` fields
2. Verify stocktake uniqueness before creation
3. Confirm populate_stocktake endpoint is being called after stocktake creation

**Contact:** Backend team for period-based accounting questions

---

## 📅 Change Log

**Date:** November 17, 2025
**Version:** Backend v1.0 (Period-Based Tracking)

**Changes:**
- ✅ Fixed opening stock calculation to include full units
- ✅ Removed fallback to live inventory (pure period-based)
- ✅ Disabled auto-update of current_full_units/current_partial_units
- ✅ Cleaned up serializers and views
- ✅ Created frontend documentation

**Next Steps:**
- Frontend: Implement duplicate stocktake prevention
- Frontend: Update current stock displays to use snapshots
- Backend: Consider removing current_* fields entirely in future migration
