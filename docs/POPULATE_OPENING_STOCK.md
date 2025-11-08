# Populate Opening Stock for New Stock Periods

## Overview

When creating a new stock period (e.g., November 2024), the system can automatically populate opening stock from the last closed period's closing stock, plus any movements that occurred between periods.

**Formula:**
```
Opening Stock = Last Closed Period's Closing Stock + Movements Between Periods
```

## How It Works

### Backend Implementation

1. **Service Function**: `populate_period_opening_stock(period)` in `stocktake_service.py`
   - Gets the previous closed period using `period.get_previous_period()`
   - Retrieves all closing stock snapshots from the previous period
   - Calculates any movements between the two periods
   - Creates new snapshots for the new period with opening balances

2. **API Endpoint**: `POST /api/stock_tracker/{hotel_id}/periods/{period_id}/populate-opening-stock/`
   - Calls the service function to populate snapshots
   - Returns success with snapshot count and total value

3. **Snapshot Management**: `StockSnapshotViewSet` is now a full `ModelViewSet`
   - Allows POST/PATCH/PUT operations
   - Staff can create and update snapshots during stocktake entry

## Frontend Workflow

### Step 1: Create New Period

```javascript
// Create November 2025 period
const response = await fetch('/api/stock_tracker/1/periods/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    period_type: 'MONTHLY',
    year: 2025,  // Use current year
    month: 11,
    start_date: '2025-11-01',
    end_date: '2025-11-30'
  })
});

const newPeriod = await response.json();
console.log('Created period:', newPeriod.id);
```

### Step 2: Populate Opening Stock

```javascript
// Populate opening stock from October's closing stock
const populateResponse = await fetch(
  `/api/stock_tracker/1/periods/${newPeriod.id}/populate-opening-stock/`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }
);

const result = await populateResponse.json();

console.log('Snapshots created:', result.snapshots_created);
console.log('Total opening value:', result.total_opening_value);
console.log('Previous period:', result.previous_period.period_name);
```

**Example Response:**
```json
{
  "success": true,
  "message": "Created 254 snapshots with opening stock",
  "snapshots_created": 254,
  "total_opening_value": 26879.03,
  "previous_period": {
    "id": 7,
    "period_name": "October 2024",
    "end_date": "2024-10-31"
  },
  "period": {
    "id": 9,
    "period_name": "November 2024",
    "start_date": "2024-11-01"
  }
}
```

### Step 3: Display Stocktake Entry Screen

```javascript
// Fetch the period with all snapshots
const periodResponse = await fetch(`/api/stock_tracker/1/periods/${newPeriod.id}/`);
const periodData = await periodResponse.json();

// Display each item with opening stock for staff to update
periodData.snapshots.forEach(snapshot => {
  displayStocktakeItem({
    itemId: snapshot.item.id,
    itemName: snapshot.item.name,
    sku: snapshot.item.sku,
    
    // Opening stock (pre-filled from last period)
    openingFull: snapshot.closing_full_units,
    openingPartial: snapshot.closing_partial_units,
    openingValue: snapshot.closing_stock_value,
    
    // Staff will enter actual counts here
    actualFull: null,  // Input field
    actualPartial: null  // Input field
  });
});
```

### Step 4: Update Counts During Stocktake

```javascript
// When staff enters actual count, update the snapshot
async function updateStockCount(snapshotId, actualFull, actualPartial) {
  const response = await fetch(
    `/api/stock_tracker/1/snapshots/${snapshotId}/`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        closing_full_units: actualFull,
        closing_partial_units: actualPartial
        // closing_stock_value will be recalculated
      })
    }
  );
  
  return await response.json();
}
```

### Step 5: Close the Period

```javascript
// When all counts are done, close the period
await fetch(`/api/stock_tracker/1/periods/${newPeriod.id}/`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    is_closed: true
  })
});
```

## Error Handling

### Period Already Has Snapshots
```json
{
  "success": false,
  "error": "Period already has 254 snapshots. Delete them first to repopulate."
}
```

### Period Already Closed
```json
{
  "success": false,
  "error": "Cannot populate a closed period"
}
```

### Previous Period Not Closed
```json
{
  "success": false,
  "error": "Previous period October 2024 is not closed. Close it first before populating this period."
}
```

## Important Notes

1. **Year Selection**: Always use the **current year** (2025) when creating new periods
   - The system has historical data from 2024
   - New periods should be created for 2025

2. **First Period**: If there's no previous closed period, the system will use current stock levels from `StockItem.current_full_units` and `current_partial_units`

3. **Movements Between Periods**: If there are any stock movements (purchases, sales, waste) recorded between the end of the last period and the start of the new period, they will be included in the opening stock calculation

4. **Cost Updates**: Opening stock uses the **current** costs from `StockItem.unit_cost` and `cost_per_serving`, not the frozen costs from the previous period. This ensures valuation reflects current pricing.

## Testing

Run the test script:
```bash
python test_populate_opening_stock.py
```

This will:
1. Find the last closed period (October 2024)
2. Create a new November 2024 period
3. Populate it with opening stock
4. Verify the data matches

## Summary

✅ **Opening stock automatically populated** from previous period  
✅ **Snapshots can be updated** during stocktake entry  
✅ **Movements between periods** are included in calculations  
✅ **Error handling** for common issues  
✅ **Full API support** for frontend integration
