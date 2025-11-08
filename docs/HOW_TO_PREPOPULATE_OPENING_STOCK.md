# How to Prepopulate Opening Stock for New Period

## Quick Guide

When creating a new stock period (e.g., November 2025), you can automatically populate it with opening stock from the previous period's closing stock.

---

## Step-by-Step Instructions

### 1. Create the New Period

**Endpoint:** `POST /api/stock_tracker/{hotel_id}/periods/`

**Request Body:**
```json
{
  "period_type": "MONTHLY",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30"
}
```

**Response:**
```json
{
  "id": 10,
  "period_type": "MONTHLY",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30",
  "year": 2025,
  "month": 11,
  "period_name": "November 2025",
  "is_closed": false
}
```

**Note:** Year, month, and period_name are automatically generated from the dates!

---

### 2. Prepopulate Opening Stock

**Endpoint:** `POST /api/stock_tracker/{hotel_id}/periods/{period_id}/populate-opening-stock/`

**Example:**
```
POST /api/stock_tracker/1/periods/10/populate-opening-stock/
```

**No request body needed!**

**Response:**
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
    "id": 10,
    "period_name": "November 2025",
    "start_date": "2025-11-01"
  }
}
```

---

### 3. Verify the Snapshots Were Created

**Endpoint:** `GET /api/stock_tracker/{hotel_id}/periods/{period_id}/`

**Response:**
```json
{
  "id": 10,
  "period_name": "November 2025",
  "is_closed": false,
  "total_items": 254,
  "total_value": 26879.03,
  "snapshots": [
    {
      "id": 5001,
      "item": {
        "id": 250,
        "sku": "B0012",
        "name": "Cronins 0.0%"
      },
      "closing_full_units": "0.00",
      "closing_partial_units": "69.0000",
      "closing_stock_value": "81.65"
    },
    // ... 253 more items
  ]
}
```

---

## Frontend Code Example

```javascript
async function createAndPopulateNewPeriod(hotelId, year, month) {
  // Step 1: Create the period
  const createResponse = await fetch(
    `/api/stock_tracker/${hotelId}/periods/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        period_type: 'MONTHLY',
        start_date: `${year}-${month.toString().padStart(2, '0')}-01`,
        end_date: getLastDayOfMonth(year, month)
      })
    }
  );
  
  const newPeriod = await createResponse.json();
  console.log('Created period:', newPeriod.period_name);
  
  // Step 2: Populate opening stock
  const populateResponse = await fetch(
    `/api/stock_tracker/${hotelId}/periods/${newPeriod.id}/populate-opening-stock/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }
  );
  
  const result = await populateResponse.json();
  
  if (result.success) {
    console.log(`✅ Populated ${result.snapshots_created} items`);
    console.log(`Opening value: €${result.total_opening_value}`);
    return newPeriod;
  } else {
    console.error('❌ Error:', result.error);
    throw new Error(result.error);
  }
}

// Helper function
function getLastDayOfMonth(year, month) {
  const lastDay = new Date(year, month, 0).getDate();
  return `${year}-${month.toString().padStart(2, '0')}-${lastDay}`;
}

// Usage
createAndPopulateNewPeriod(1, 2025, 11);  // November 2025
```

---

## What Happens Behind the Scenes

1. **Finds Previous Period**: System looks for the last closed period
2. **Copies Closing Stock**: Takes all closing stock snapshots from previous period
3. **Includes Movements**: Adds any purchases/sales between periods
4. **Creates New Snapshots**: Generates snapshots for new period with opening balances
5. **Returns Summary**: Tells you how many items were created and total value

**Formula:**
```
Opening Stock = Previous Period Closing Stock + Movements Between Periods
```

---

## Common Errors

### ❌ "Period already has snapshots"

**Cause:** The period already has stock data.

**Solution:** Delete existing snapshots first, or use a different period.

---

### ❌ "Cannot populate a closed period"

**Cause:** Trying to populate a period that's already been finalized.

**Solution:** Only populate open/draft periods. Once closed, they shouldn't be modified.

---

### ❌ "Previous period is not closed"

**Cause:** The previous period (e.g., October) isn't closed yet.

**Solution:** Close the previous period first:
```javascript
// Close October before populating November
await fetch(`/api/stock_tracker/1/periods/7/`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ is_closed: true })
});
```

---

## After Prepopulation

Once prepopulated, staff can:

1. **View Opening Stock**: See what was left from last period
2. **Enter Actual Counts**: Update the snapshots with real counts
3. **Calculate Variance**: Compare actual vs opening
4. **Close Period**: Finalize when stocktake is complete

---

## Complete Workflow Example

```javascript
// 1. Create November 2025 period
const nov = await fetch('/api/stock_tracker/1/periods/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    period_type: 'MONTHLY',
    start_date: '2025-11-01',
    end_date: '2025-11-30'
  })
}).then(r => r.json());

// 2. Prepopulate with opening stock
await fetch(`/api/stock_tracker/1/periods/${nov.id}/populate-opening-stock/`, {
  method: 'POST'
}).then(r => r.json());

// 3. Get all items with opening stock
const period = await fetch(`/api/stock_tracker/1/periods/${nov.id}/`)
  .then(r => r.json());

// 4. Display to staff for counting
period.snapshots.forEach(snapshot => {
  console.log(
    `${snapshot.item.name}: ` +
    `Opening = ${snapshot.closing_full_units} full, ` +
    `${snapshot.closing_partial_units} partial`
  );
});

// 5. Staff updates actual counts (example for one item)
await fetch(`/api/stock_tracker/1/snapshots/${snapshot.id}/`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    closing_full_units: 5,    // Actual count
    closing_partial_units: 0.5  // Actual count
  })
});

// 6. Close period when done
await fetch(`/api/stock_tracker/1/periods/${nov.id}/`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ is_closed: true })
});
```

---

## Summary

✅ Create period with start/end dates  
✅ Call `/populate-opening-stock/` endpoint  
✅ System copies last period's closing stock  
✅ Staff updates with actual counts  
✅ Close period when complete  

**That's it!** Opening stock is automatically populated from the previous period.
