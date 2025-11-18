"""
SNAPSHOT CREATION - SYSTEM DESIGN DOCUMENT
============================================

WHERE SNAPSHOTS ARE CREATED:
----------------------------
Location: stock_tracker/stocktake_service.py
Function: approve_stocktake() (lines 183-283)

WHEN:
-----
Snapshots are created/updated when a stocktake is APPROVED.
This happens when frontend calls the approve endpoint.

HOW IT WORKS:
-------------
1. Frontend submits stocktake with counted stock:
   - counted_full_units (e.g., cases, full bottles)
   - counted_partial_units (e.g., loose bottles, partial)

2. Frontend calls approve stocktake endpoint

3. Backend approve_stocktake() function:
   a) Finds matching StockPeriod by dates
   b) For EACH stocktake line (all categories):
      - Try to get existing snapshot
      - If exists: UPDATE closing values
      - If not: CREATE new snapshot
   c) Saves:
      - closing_full_units = line.counted_full_units
      - closing_partial_units = line.counted_partial_units
      - closing_stock_value = line.counted_value

4. These closing values become OPENING stock for next period

FRONTEND RESPONSIBILITY:
-----------------------
✅ Collect counted stock from user
✅ Submit stocktake lines with counted_full_units + counted_partial_units
✅ Call approve stocktake endpoint
❌ DO NOT manually create snapshots
❌ DO NOT manually calculate opening stock

IMPORTANT NOTES:
---------------
- Snapshots are created for ALL categories (D, B, S, W, M)
- Each stocktake line creates/updates ONE snapshot
- If period doesn't exist, NO snapshots created (check line 209)
- Next period's opening stock = this period's closing stock

CLOSING PERIOD:
--------------
When closing a period (separate from stocktake approval):
- Period is marked as closed (is_closed = True)
- Snapshots should already exist from stocktake approval
- Frontend just calls close period endpoint

TWO SEPARATE ACTIONS:
--------------------
1. Approve Stocktake → Creates/updates snapshots
2. Close Period → Marks period as closed

Both can happen independently!

CURRENT DATA ISSUE:
------------------
- Stocktake 37 (Feb 2025) is APPROVED
- Period 29 (Feb 2025) exists and is CLOSED
- BUT: Period 29 has 0 snapshots ❌

This means:
a) Period didn't exist when stocktake was approved, OR
b) approve_stocktake() failed silently, OR
c) Snapshots were deleted after creation

To fix: Re-approve the stocktake to regenerate snapshots.
"""

print(__doc__)
