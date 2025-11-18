# Opening Stock Fix for All Categories

## Problem
Opening stock was only populating correctly for **Draught Beer (D)** and **Bottled Beer (B)**. Other categories like **Spirits (S)**, **Wine (W)**, and **Minerals (M)** were not getting opening stock from the previous period's closing stock.

## Root Cause
When a stocktake was approved, the system:
1. ✅ Created adjustment movements for variances
2. ❌ **DID NOT update StockSnapshot closing values**

This meant that when the next period was created, `_get_opening_balance()` couldn't find any closing stock from the previous period for non-beer categories.

## Solution Implemented
Modified `stock_tracker/stocktake_service.py` - `approve_stocktake()` function to:

### What Changed:
When approving a stocktake, the function now:
1. Creates adjustment movements (existing behavior - unchanged)
2. **NEW:** Updates StockSnapshot closing values with counted stock for ALL categories
3. **NEW:** Creates snapshots if they don't exist

### Code Changes:
```python
def approve_stocktake(stocktake, approved_by):
    # ... existing variance adjustments code ...
    
    # Get the corresponding StockPeriod
    try:
        period = StockPeriod.objects.get(
            hotel=stocktake.hotel,
            start_date=stocktake.period_start,
            end_date=stocktake.period_end
        )
    except StockPeriod.DoesNotExist:
        period = None

    for line in stocktake.lines.all():
        # ... create adjustment movements ...
        
        # NEW: Update snapshot with counted stock (for ALL categories)
        if period:
            try:
                snapshot = StockSnapshot.objects.get(
                    period=period,
                    item=line.item
                )
                # Update closing stock with counted values
                snapshot.closing_full_units = line.counted_full_units
                snapshot.closing_partial_units = line.counted_partial_units
                snapshot.closing_stock_value = line.counted_value
                snapshot.save()
                
            except StockSnapshot.DoesNotExist:
                # Create snapshot if it doesn't exist
                StockSnapshot.objects.create(
                    hotel=stocktake.hotel,
                    item=line.item,
                    period=period,
                    closing_full_units=line.counted_full_units,
                    closing_partial_units=line.counted_partial_units,
                    # ... other fields ...
                )
```

## How It Works Now

### Flow:
1. **October Period** - Stocktake is created and populated
2. **User counts stock** - Enters counted_full_units and counted_partial_units
3. **Stocktake approved** - System now:
   - Creates adjustment movements (existing)
   - **Updates StockSnapshot closing values with counted stock (NEW)**
4. **November Period** - Created later
5. **November Stocktake** - When populated:
   - `_get_opening_balance()` finds October's snapshots
   - Uses `total_servings` (calculated from closing_full + closing_partial)
   - **All categories now have opening stock!**

## Categories Affected (Now Fixed)

✅ **Draught Beer (D)** - Already worked, still works
✅ **Bottled Beer (B)** - Already worked, still works
✅ **Spirits (S)** - NOW WORKS!
✅ **Wine (W)** - NOW WORKS!
✅ **Minerals (M)** - NOW WORKS!
  - SOFT_DRINKS - NOW WORKS!
  - SYRUPS - NOW WORKS!
  - JUICES - NOW WORKS!
  - CORDIALS - NOW WORKS!
  - BIB - NOW WORKS!
  - BULK_JUICES - NOW WORKS!

## No Changes to Beer Logic

⚠️ **IMPORTANT:** The fix does NOT modify any beer-specific logic:
- Beer opening stock calculation unchanged
- Beer `total_servings` formula unchanged
- Beer display units logic unchanged
- Beer UOM handling unchanged

The fix simply **applies the same snapshot update logic** that was implicitly working for beers to ALL categories.

## Testing

Run the test script:
```bash
python test_opening_stock_fix.py
```

This will:
1. Check closing stock by category in the most recent period
2. Verify if next period has opening stock from previous closing
3. Show which categories have proper stock flow

## For Existing Data

If you have existing periods where opening stock is missing:

1. **Reopen the stocktake:**
   ```
   POST /api/stock_tracker/{hotel}/stocktakes/{id}/reopen/
   ```

2. **Re-approve it:**
   ```
   POST /api/stock_tracker/{hotel}/stocktakes/{id}/approve/
   ```

3. **Check next period's opening stock:**
   - Opening stock should now be populated from the updated snapshots

## Technical Details

### Files Modified:
- `stock_tracker/stocktake_service.py` - `approve_stocktake()` function

### Files NOT Modified (as requested):
- All beer-specific logic remains untouched
- `total_servings` calculation unchanged
- Display unit helpers unchanged
- Serializers unchanged

### Database Changes:
- No schema changes
- Existing data unaffected
- Future stocktake approvals will update snapshots automatically

## Summary

✅ Opening stock now populates for ALL categories when creating new periods
✅ Beer logic completely untouched
✅ Simple, clean fix at the approval point
✅ Backward compatible with existing code

