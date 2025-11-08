# FRONTEND API GUIDE - Stock Tracker Input System

## Overview
The backend is ready! It uses the **THREE-FIELD INPUT** system for stock takes:
1. **full_units** - Whole containers (kegs, cases, bottles)
2. **partial_units** - Fractional amounts or loose servings  
3. **sales_quantity** (optional) - Sales tracking

The backend automatically calculates everything based on **category-specific rules**.

---

## How Backend Calculates by Category

### BEERS (Draught D & Bottled B) → PINTS/BOTTLES
**Storage:**
- `full_units` = kegs or cases
- `partial_units` = loose pints or bottles (already servings)

**Backend Calculation:**
```
Value = (full_units × unit_cost) + (partial_units × cost_per_serving)
```

**Example - Heineken Keg 50L:**
```json
{
  "item": 1,
  "period": 1,
  "closing_full_units": 6,      // 6 kegs
  "closing_partial_units": 39.75  // 39.75 loose pints
}
```
Backend calculates:
- Full value: 6 kegs × €150 = €900
- Partial value: 39.75 pints × €2.50 = €99.38
- **Total: €999.38**

---

### SPIRITS (S) → SHOTS
**Storage:**
- `full_units` = full bottles
- `partial_units` = fractional bottles (0.70 = 70% of a bottle)

**Backend Calculation:**
```
Value = (full_units × unit_cost) + (partial_units × unit_cost)
```

**Example - Jameson 70cl:**
```json
{
  "item": 10,
  "period": 1,
  "closing_full_units": 2,     // 2 full bottles
  "closing_partial_units": 0.70  // 70% of a bottle
}
```
Backend calculates:
- Full value: 2 bottles × €15 = €30
- Partial value: 0.70 bottles × €15 = €10.50
- **Total: €40.50**

---

### WINES (W) → BOTTLES (with decimals)
**Storage:**
- `full_units` = full bottles
- `partial_units` = fractional bottles (0.80 = 80% of a bottle)

**Backend Calculation:**
```
Value = (full_units × unit_cost) + (partial_units × unit_cost)
```

**Example - Merlot 75cl:**
```json
{
  "item": 20,
  "period": 1,
  "closing_full_units": 10,    // 10 full bottles
  "closing_partial_units": 0.80  // 80% of a bottle
}
```
Backend calculates:
- Full value: 10 bottles × €12 = €120
- Partial value: 0.80 bottles × €12 = €9.60
- **Total: €129.60**
- *Display as: 10.80 bottles*

---

### MINERALS/SYRUPS (M) → VARIES
**Storage:**
- `full_units` = cases or bags-in-box
- `partial_units` = loose serves

**Backend Calculation:**
```
Value = (full_units × unit_cost) + (partial_units × cost_per_serving)
```

Same logic as Beers.

---

## API Endpoints for Frontend

### 1. Get Stock Items (with category info)
**GET** `/api/stock-tracker/{hotel_identifier}/items/`**

**Response:**
```json
[
  {
    "id": 1,
    "sku": "D001",
    "name": "Heineken Keg 50L",
    "category_code": "D",
    "category_name": "Draught Beer",
    "size": "50Lt",
    "uom": 88,  // 88 pints per keg
    "unit_cost": "150.0000",
    "cost_per_serving": "2.5000",
    "current_full_units": "6.00",
    "current_partial_units": "39.7500"
  }
]
```

**Frontend uses:**
- `category_code` to determine input behavior (B/D vs S/W)
- `uom` to show "servings per unit" info
- Current values as defaults

---

### 2. Create Stock Period
**POST** `/api/stock-tracker/{hotel_identifier}/periods/`

**Request:**
```json
{
  "period_type": "MONTHLY",
  "start_date": "2024-11-01",
  "end_date": "2024-11-30",
  "year": 2024,
  "month": 11,
  "period_name": "November 2024"
}
```

**Response:**
```json
{
  "id": 2,
  "period_name": "November 2024",
  "is_closed": false
}
```

---

### 3. Single Snapshot (Create/Update)
**POST** `/api/stock-tracker/{hotel_identifier}/snapshots/`
**PUT** `/api/stock-tracker/{hotel_identifier}/snapshots/{id}/`

**Request:**
```json
{
  "item": 1,
  "period": 2,
  "closing_full_units": 6,
  "closing_partial_units": 39.75,
  "sales_quantity": 200  // optional
}
```

**Response:**
```json
{
  "id": 1,
  "item": 1,
  "item_sku": "D001",
  "item_name": "Heineken Keg 50L",
  "category_code": "D",
  "period": 2,
  "closing_full_units": "6.00",
  "closing_partial_units": "39.7500",
  "closing_stock_value": "999.38",  // ✅ Backend calculated!
  "sales_quantity": "200.00",
  "unit_cost": "150.0000",
  "cost_per_serving": "2.5000"
}
```

---

### 4. Bulk Snapshots (Multiple Items at Once)
**POST** `/api/stock-tracker/{hotel_identifier}/periods/{period_id}/bulk-snapshots/`

**Request:**
```json
{
  "snapshots": [
    {
      "item_id": 1,
      "full_units": 6,
      "partial_units": 39.75,
      "sales_quantity": 200
    },
    {
      "item_id": 2,
      "full_units": 2,
      "partial_units": 0.70,
      "sales_quantity": 40
    },
    {
      "item_id": 3,
      "full_units": 10,
      "partial_units": 0.80
    }
  ]
}
```

**Response:**
```json
{
  "message": "Created/updated 3 snapshots",
  "snapshots": [
    {
      "id": 1,
      "item_sku": "D001",
      "closing_stock_value": "999.38"
    }
    // ... more
  ]
}
```

---

### 5. Get Period Summary (All Calculations Done)
**GET** `/api/stock-tracker/{hotel_identifier}/periods/{period_id}/summary/`

**Response:**
```json
{
  "period_id": 2,
  "period_name": "November 2024",
  "total_items": 254,
  "total_stock_value": 27306.58,  // ✅ Backend calculated!
  "total_sales_value": 15000.00,
  "categories": [
    {
      "category_code": "D",
      "category_name": "Draught Beer",
      "item_count": 25,
      "stock_value": 5311.62,  // ✅ Backend calculated!
      "sales_value": 2500.00
    }
    // ... more categories
  ]
}
```

---

### 6. Get Sales Calculations (Optional)
**GET** `/api/stock-tracker/{hotel_identifier}/periods/{period_id}/sales/`

**Query params:**
- `?category=D` - Filter by category
- `?item_id=1` - Single item

**Response:**
```json
{
  "D": {
    "category_code": "D",
    "total_sales_quantity": 500.00,
    "total_sales_value": 2750.00,  // ✅ Backend calculated!
    "items": [
      {
        "item_id": 1,
        "sku": "D001",
        "sales_quantity": 200.0,
        "menu_price": 5.50,
        "sales_value": 1100.00  // ✅ Backend calculated!
      }
    ]
  }
}
```

---

## Frontend Implementation Guide

### Step 1: Get Items and Show Input Form

```javascript
// Fetch items for the period
const items = await fetch(`/api/stock-tracker/${hotelIdentifier}/items/`);

// For each item, show THREE input fields:
items.forEach(item => {
  const inputFields = {
    full_units: {
      label: getCategoryLabel(item.category_code, 'full'),
      // D/B: "Kegs" or "Cases"
      // S/W: "Bottles"
      placeholder: item.current_full_units
    },
    partial_units: {
      label: getCategoryLabel(item.category_code, 'partial'),
      // D: "Loose Pints"
      // B: "Loose Bottles"
      // S/W: "Partial (0.70 = 70%)"
      placeholder: item.current_partial_units
    },
    sales_quantity: {
      label: "Sales (optional)",
      placeholder: "0"
    }
  };
});

function getCategoryLabel(category, type) {
  const labels = {
    'D': { full: 'Kegs', partial: 'Loose Pints' },
    'B': { full: 'Cases', partial: 'Loose Bottles' },
    'S': { full: 'Bottles', partial: 'Partial (0.70)' },
    'W': { full: 'Bottles', partial: 'Partial (0.80)' },
    'M': { full: 'Units', partial: 'Loose Serves' }
  };
  return labels[category][type];
}
```

---

### Step 2: Submit Data (Bulk)

```javascript
// Collect all inputs
const snapshots = items.map(item => ({
  item_id: item.id,
  full_units: parseFloat(fullInput.value) || 0,
  partial_units: parseFloat(partialInput.value) || 0,
  sales_quantity: parseFloat(salesInput.value) || null
}));

// Send to backend
const response = await fetch(
  `/api/stock-tracker/${hotelIdentifier}/periods/${periodId}/bulk-snapshots/`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ snapshots })
  }
);

const result = await response.json();
// result.snapshots contains calculated values!
```

---

### Step 3: Display Results

```javascript
// Get period summary with all calculations
const summary = await fetch(
  `/api/stock-tracker/${hotelIdentifier}/periods/${periodId}/summary/`
);

// Show totals (all calculated by backend!)
console.log('Total Stock Value:', summary.total_stock_value);
console.log('By Category:', summary.categories);
```

---

## Key Points for Frontend

✅ **Send RAW inputs** - Don't calculate anything!
- Just send: `full_units`, `partial_units`, `sales_quantity`
- Backend does ALL calculations

✅ **Category awareness** - UI adapts to category:
- **Beers (D/B)**: "Kegs/Cases + Loose Pints/Bottles"
- **Spirits/Wine (S/W)**: "Bottles + Partial (0.70)"
- Different labels, same backend logic

✅ **Sales are optional** - Can be skipped:
- Leave blank or send `null`
- Backend handles gracefully

✅ **Bulk operations** - Use for efficiency:
- Submit all items at once
- Backend processes in transaction

✅ **Backend returns calculated values**:
- `closing_stock_value` - Total value
- `total_sales_value` - Sales revenue
- No frontend math needed!

---

## Validation Rules

### Input Validation (Frontend)
- `full_units` ≥ 0
- `partial_units` ≥ 0
- For **Wines (W)**: `partial_units` should be < 1.0 (fractional)
- For **Spirits (S)**: `partial_units` should be < 1.0 (fractional)
- `sales_quantity` ≥ 0 or null

### Backend Handles
- ✅ Category-specific calculations
- ✅ Cost freezing (unit_cost, cost_per_serving)
- ✅ Value calculations
- ✅ Sales calculations (if menu_price exists)
- ✅ Period validation (can't update closed periods)

---

## Example Complete Flow

```javascript
// 1. Create period
const period = await createPeriod({
  period_name: "November 2024",
  start_date: "2024-11-01",
  end_date: "2024-11-30"
});

// 2. Get items
const items = await getItems();

// 3. User enters data in UI:
// - Heineken: 6 kegs, 39.75 pints
// - Jameson: 2 bottles, 0.70 partial
// - Merlot: 10 bottles, 0.80 partial

// 4. Submit to backend
await bulkCreateSnapshots(period.id, [
  { item_id: 1, full_units: 6, partial_units: 39.75 },
  { item_id: 10, full_units: 2, partial_units: 0.70 },
  { item_id: 20, full_units: 10, partial_units: 0.80 }
]);

// 5. Get calculated summary
const summary = await getPeriodSummary(period.id);
// Backend calculated: €27,306.58 total! ✅
```

---

## Summary

**Frontend sends:** 3 numbers per item (full, partial, sales)
**Backend calculates:** Everything else automatically!

No complex math in frontend - just collect inputs and display results! 🎉
