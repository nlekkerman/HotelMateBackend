# Stock Period Auto-Population Feature

## Overview

When creating a new stocktake period, the system now automatically populates opening stock from the previous closed period's closing stock, plus any movements between periods.

---

## ✅ What Was Implemented

### 1. **Auto-Calculate Year/Month from Dates**

**Problem:** Periods were being created with wrong year (2024 instead of 2025) because frontend could send mismatched year/date values.

**Solution:** Made period identifiers read-only and auto-calculated from dates.

**Changes:**
- `year`, `month`, `quarter`, `week` are now **read-only** in serializers
- Added `save()` method to `StockPeriod` model that:
  - Extracts `year` from `start_date`
  - Extracts `month` from `start_date` for MONTHLY periods
  - Auto-generates `period_name` (e.g., "November 2025")

**Example:**
```javascript
// Frontend only sends dates
POST /api/stock_tracker/1/periods/
{
  "period_type": "MONTHLY",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30"
}

// Backend automatically sets:
// year: 2025
// month: 11
// period_name: "November 2025"
```

---

### 2. **Populate Opening Stock from Previous Period**

**Formula:**
```
Opening Stock = Last Closed Period's Closing Stock + Movements Between Periods
```

**New API Endpoint:**
```
POST /api/stock_tracker/{hotel_id}/periods/{period_id}/populate-opening-stock/
```

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
    "id": 9,
    "period_name": "November 2024",
    "start_date": "2024-11-01"
  }
}
```

---

### 3. **Enable Snapshot Updates During Stocktake**

**Changed:** `StockSnapshotViewSet` from `ReadOnlyModelViewSet` to full `ModelViewSet`

**Now supports:**
- `POST /api/stock_tracker/{hotel_id}/snapshots/` - Create new snapshot
- `PATCH /api/stock_tracker/{hotel_id}/snapshots/{id}/` - Update counts
- `PUT /api/stock_tracker/{hotel_id}/snapshots/{id}/` - Replace snapshot
- `DELETE /api/stock_tracker/{hotel_id}/snapshots/{id}/` - Delete snapshot

---

## 📋 Frontend Workflow

### Step 1: Create New Period

```javascript
// Create November 2025 period (year auto-detected from dates)
const response = await fetch('/api/stock_tracker/1/periods/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    period_type: 'MONTHLY',
    start_date: '2025-11-01',
    end_date: '2025-11-30'
    // NO need to send: year, month, period_name - auto-calculated!
  })
});

const newPeriod = await response.json();
// newPeriod.year = 2025 (auto)
// newPeriod.month = 11 (auto)
// newPeriod.period_name = "November 2025" (auto)
```

### Step 2: Populate Opening Stock

```javascript
// Initialize snapshots from October's closing stock
const populateResponse = await fetch(
  `/api/stock_tracker/1/periods/${newPeriod.id}/populate-opening-stock/`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }
);

const result = await populateResponse.json();
console.log(`Created ${result.snapshots_created} snapshots`);
console.log(`Opening value: €${result.total_opening_value}`);
```

### Step 3: Display Stocktake Entry

```javascript
// Fetch period with all pre-populated snapshots
const periodResponse = await fetch(
  `/api/stock_tracker/1/periods/${newPeriod.id}/`
);
const periodData = await periodResponse.json();

// Each snapshot has opening stock from last period
periodData.snapshots.forEach(snapshot => {
  displayItem({
    id: snapshot.id,
    itemName: snapshot.item.name,
    
    // Pre-filled from October closing:
    openingFull: snapshot.closing_full_units,
    openingPartial: snapshot.closing_partial_units,
    openingValue: snapshot.closing_stock_value,
    
    // Staff enters actual counts:
    actualFull: null,  // Input field
    actualPartial: null  // Input field
  });
});
```

### Step 4: Update Actual Counts

```javascript
// When staff counts, update the snapshot
async function saveCount(snapshotId, actualFull, actualPartial) {
  await fetch(`/api/stock_tracker/1/snapshots/${snapshotId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      closing_full_units: actualFull,
      closing_partial_units: actualPartial
    })
  });
}
```

### Step 5: Close Period

```javascript
// When all items counted, close the period
await fetch(`/api/stock_tracker/1/periods/${newPeriod.id}/`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ is_closed: true })
});
```

---

## 🔧 Backend Implementation

### Files Modified:

1. **`stock_tracker/models.py`**
   - Added `save()` method to `StockPeriod` for auto-population

2. **`stock_tracker/stocktake_service.py`**
   - `populate_period_opening_stock(period)` - Main function
   - `_create_snapshots_from_current_stock(period)` - For first period
   - `_calculate_movements_between_periods()` - Handle purchases/sales

3. **`stock_tracker/views.py`**
   - Added `populate_opening_stock` action to `StockPeriodViewSet`
   - Changed `StockSnapshotViewSet` to `ModelViewSet`

4. **`stock_tracker/stock_serializers.py`**
   - Made `year`, `month`, `quarter`, `week` read-only

5. **`stock_tracker/urls.py`**
   - Added route for populate-opening-stock
   - Updated snapshot routes for POST/PATCH/PUT

---

## 🎯 Key Benefits

✅ **Year always correct** - Extracted from actual dates, not manual input  
✅ **Opening stock auto-populated** - From previous period's closing  
✅ **Movements included** - Purchases/sales between periods counted  
✅ **Snapshots editable** - Staff can update counts during stocktake  
✅ **Error handling** - Validates previous period is closed  

---

## 🧪 Testing

Test script: `test_populate_opening_stock.py`

**Result:**
```
✅ Found October 2024 period (ID: 7)
   Status: CLOSED
   Snapshots: 254
   Total Value: €27,306.58

✅ Created November 2024 period (ID: 9)

✅ SUCCESS!
   Snapshots Created: 254
   Total Opening Value: €26,879.03
   Previous Period: October 2024

✅ VERIFICATION: All items matched ✓
```

---

## ⚠️ Error Handling

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
  "error": "Previous period October 2024 is not closed. Close it first."
}
```

---

## 📝 Summary

**Before:**
- Frontend had to manually calculate year/month
- No automatic opening stock population
- Couldn't update snapshots during stocktake

**After:**
- Year/month auto-calculated from dates ✅
- Opening stock auto-populated from previous period ✅
- Snapshots fully editable during stocktake ✅
- One API call to initialize entire new period ✅
