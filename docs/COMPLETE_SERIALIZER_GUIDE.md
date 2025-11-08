# Complete Stock Period Serializer - Backend to Frontend

## Overview

The backend provides **ALL data pre-calculated** in a single API response. Frontend just displays the values - **NO calculations needed!**

---

## API Endpoint

```
GET /api/stock_tracker/{hotel_id}/periods/{period_id}/
```

---

## Complete Response Structure

```json
{
  "id": 9,
  "hotel": 2,
  "period_type": "MONTHLY",
  "period_name": "November 2025",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30",
  "year": 2024,
  "month": 11,
  "quarter": null,
  "week": null,
  "is_closed": false,
  
  "total_items": 254,
  "total_value": "26879.03",
  
  "snapshot_ids": [3801, 3802, 3803, ..., 4054],
  
  "stocktake_id": 4,
  "stocktake_status": "DRAFT",
  
  "snapshots": [
    {
      "id": 3802,
      "item": {
        "id": 245,
        "sku": "B0070",
        "name": "Budweiser 33cl",
        "category": "B",
        "category_display": "Bottled Beer",
        "size": "Doz",
        "unit_cost": "11.7500",
        "menu_price": "5.70"
      },
      
      "opening_full_units": "0.00",
      "opening_partial_units": "113.0000",
      "opening_stock_value": "110.65",
      "opening_display_full_units": "9",
      "opening_display_partial_units": "5",
      
      "closing_full_units": "0.00",
      "closing_partial_units": "113.0000",
      "closing_stock_value": "110.65",
      "closing_display_full_units": "9",
      "closing_display_partial_units": "5",
      
      "total_servings": "113.00",
      "display_full_units": "9.00",
      "display_partial_units": "5.0000",
      
      "unit_cost": "11.7500",
      "cost_per_serving": "0.9792",
      
      "gp_percentage": "82.82",
      "markup_percentage": "482.13",
      "pour_cost_percentage": "17.18"
    }
  ]
}
```

---

## Field Definitions

### Period Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Period ID (primary reference) |
| `hotel` | integer | Hotel ID |
| `period_type` | string | "MONTHLY", "WEEKLY", "QUARTERLY" |
| `period_name` | string | Auto-generated (e.g., "November 2025") |
| `start_date` | date | Period start date |
| `end_date` | date | Period end date |
| `year` | integer | Auto-calculated from start_date |
| `month` | integer | Month number (1-12) |
| `quarter` | integer/null | Quarter number (1-4) |
| `week` | integer/null | Week number |
| `is_closed` | boolean | Whether period is closed |
| `total_items` | integer | Count of snapshots |
| `total_value` | string | Total stock value (decimal) |
| `snapshot_ids` | array | List of all snapshot IDs |
| `stocktake_id` | integer/null | Related stocktake ID (if exists) |
| `stocktake_status` | string/null | "DRAFT" or "APPROVED" |

### Snapshot Level Fields

#### Item Information
| Field | Type | Description |
|-------|------|-------------|
| `item.id` | integer | Item ID |
| `item.sku` | string | Stock keeping unit code |
| `item.name` | string | Item name |
| `item.category` | string | Category code (B/D/S/W/M) |
| `item.category_display` | string | Full category name |
| `item.size` | string | Size/unit (e.g., "Doz", "70cl", "20Lt") |
| `item.unit_cost` | string | Cost per full unit (decimal) |
| `item.menu_price` | string/null | Menu selling price |

#### Opening Stock (from previous period)
| Field | Type | Description |
|-------|------|-------------|
| `opening_full_units` | string | Raw full units (database value) |
| `opening_partial_units` | string | Raw partial units (database value) |
| `opening_stock_value` | string | Opening stock value (€) |
| `opening_display_full_units` | string | **Display: cases/kegs/bottles** |
| `opening_display_partial_units` | string | **Display: bottles/pints/fractional** |

#### Closing Stock (counted at period end)
| Field | Type | Description |
|-------|------|-------------|
| `closing_full_units` | string | Raw full units (database value) |
| `closing_partial_units` | string | Raw partial units (database value) |
| `closing_stock_value` | string | Closing stock value (€) |
| `closing_display_full_units` | string | **Display: cases/kegs/bottles** |
| `closing_display_partial_units` | string | **Display: bottles/pints/fractional** |

#### Deprecated Fields (use closing_display_* instead)
| Field | Type | Description |
|-------|------|-------------|
| `total_servings` | string | Total servings (use for calculations) |
| `display_full_units` | string | Same as closing_display_full_units |
| `display_partial_units` | string | Same as closing_display_partial_units |

#### Cost Information
| Field | Type | Description |
|-------|------|-------------|
| `unit_cost` | string | Cost per full unit (€) |
| `cost_per_serving` | string | Cost per serving (€) |

#### Profitability Metrics
| Field | Type | Description |
|-------|------|-------------|
| `gp_percentage` | string/null | Gross profit % |
| `markup_percentage` | string/null | Markup % |
| `pour_cost_percentage` | string/null | Pour cost % |

---

## Display Format by Category

### Bottled Beer (Category B, Size "Doz")
```json
{
  "opening_display_full_units": "9",
  "opening_display_partial_units": "5",
  "closing_display_full_units": "12",
  "closing_display_partial_units": "8"
}
```
**Display:** "12 cases + 8 bottles"
- Full units = **Cases (dozens)**
- Partial units = **Individual bottles (WHOLE NUMBERS, 0-11)**

### Draught Beer (Category D)
```json
{
  "opening_display_full_units": "1",
  "opening_display_partial_units": "4.68",
  "closing_display_full_units": "5",
  "closing_display_partial_units": "39.90"
}
```
**Display:** "5 kegs + 39.90 pints"
- Full units = **Kegs**
- Partial units = **Pints (2 DECIMALS)**

### Spirits (Category S)
```json
{
  "opening_display_full_units": "2",
  "opening_display_partial_units": "0.30",
  "closing_display_full_units": "3",
  "closing_display_partial_units": "0.25"
}
```
**Display:** "3 bottles + 0.25"
- Full units = **Bottles**
- Partial units = **Fractional bottle (2 DECIMALS)**

### Wine (Category W)
```json
{
  "opening_display_full_units": "5",
  "opening_display_partial_units": "0.75",
  "closing_display_full_units": "4",
  "closing_display_partial_units": "0.50"
}
```
**Display:** "4 bottles + 0.50"
- Full units = **Bottles**
- Partial units = **Fractional bottle (2 DECIMALS)**

### Mixers (Category M with "Doz")
```json
{
  "opening_display_full_units": "15",
  "opening_display_partial_units": "7",
  "closing_display_full_units": "11",
  "closing_display_partial_units": "5"
}
```
**Display:** "11 cases + 5 bottles"
- Full units = **Cases (dozens)**
- Partial units = **Individual bottles (WHOLE NUMBERS, 0-11)**

---

## Frontend Implementation

### Fetch Period Data

```javascript
async function loadPeriod(hotelId, periodId) {
  const response = await fetch(
    `/api/stock_tracker/${hotelId}/periods/${periodId}/`
  );
  const data = await response.json();
  return data;
}
```

### Display Opening Stock

```javascript
function displayOpeningStock(snapshot) {
  const { item, opening_display_full_units, opening_display_partial_units } = snapshot;
  
  // Determine unit labels based on category
  let fullLabel, partialLabel;
  
  if (item.category === 'B' || (item.category === 'M' && item.size === 'Doz')) {
    fullLabel = 'cases';
    partialLabel = 'bottles';
  } else if (item.category === 'D') {
    fullLabel = 'kegs';
    partialLabel = 'pints';
  } else {
    fullLabel = 'bottles';
    partialLabel = '';
  }
  
  return `${opening_display_full_units} ${fullLabel} + ${opening_display_partial_units} ${partialLabel}`;
}
```

### Display Closing Stock

```javascript
function displayClosingStock(snapshot) {
  const { item, closing_display_full_units, closing_display_partial_units } = snapshot;
  
  // Same logic as opening stock
  let fullLabel, partialLabel;
  
  if (item.category === 'B' || (item.category === 'M' && item.size === 'Doz')) {
    fullLabel = 'cases';
    partialLabel = 'bottles';
  } else if (item.category === 'D') {
    fullLabel = 'kegs';
    partialLabel = 'pints';
  } else {
    fullLabel = 'bottles';
    partialLabel = '';
  }
  
  return `${closing_display_full_units} ${fullLabel} + ${closing_display_partial_units} ${partialLabel}`;
}
```

### Complete React Component Example

```jsx
import React, { useEffect, useState } from 'react';

function StockPeriodView({ hotelId, periodId }) {
  const [period, setPeriod] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchPeriod();
  }, [periodId]);
  
  const fetchPeriod = async () => {
    const data = await fetch(`/api/stock_tracker/${hotelId}/periods/${periodId}/`)
      .then(r => r.json());
    setPeriod(data);
    setLoading(false);
  };
  
  const getUnitLabels = (item) => {
    if (item.category === 'B' || (item.category === 'M' && item.size === 'Doz')) {
      return { full: 'cases', partial: 'bottles' };
    } else if (item.category === 'D') {
      return { full: 'kegs', partial: 'pints' };
    } else {
      return { full: 'bottles', partial: '' };
    }
  };
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      <h1>{period.period_name}</h1>
      <p>Period: {period.start_date} to {period.end_date}</p>
      <p>Status: {period.is_closed ? 'Closed' : 'Open'}</p>
      <p>Total Items: {period.total_items}</p>
      <p>Total Value: €{period.total_value}</p>
      
      {period.stocktake_id && (
        <p>Stocktake: #{period.stocktake_id} ({period.stocktake_status})</p>
      )}
      
      <table>
        <thead>
          <tr>
            <th>Item</th>
            <th>Category</th>
            <th>Opening Stock</th>
            <th>Closing Stock</th>
            <th>Value</th>
            <th>Cost/Serving</th>
          </tr>
        </thead>
        <tbody>
          {period.snapshots.map(snap => {
            const labels = getUnitLabels(snap.item);
            
            return (
              <tr key={snap.id}>
                <td>
                  {snap.item.name}
                  <br />
                  <small>{snap.item.sku}</small>
                </td>
                <td>{snap.item.category_display}</td>
                <td>
                  {snap.opening_display_full_units} {labels.full} + 
                  {snap.opening_display_partial_units} {labels.partial}
                </td>
                <td>
                  {snap.closing_display_full_units} {labels.full} + 
                  {snap.closing_display_partial_units} {labels.partial}
                </td>
                <td>€{snap.closing_stock_value}</td>
                <td>€{snap.cost_per_serving}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default StockPeriodView;
```

---

## Key Points for Frontend

### ✅ What Frontend Gets (Pre-calculated):
1. **Opening stock display values** - ready to show
2. **Closing stock display values** - ready to show
3. **Stock values** (€) - already calculated
4. **Costs** - unit_cost and cost_per_serving
5. **Profitability metrics** - GP%, markup%, pour cost%
6. **Proper rounding**:
   - Bottles = whole numbers (0-11)
   - Pints = 2 decimals
   - Fractional = 2 decimals

### ❌ What Frontend Does NOT Need to Do:
1. ❌ Convert bottles to cases
2. ❌ Convert pints to kegs
3. ❌ Calculate opening stock
4. ❌ Calculate stock values
5. ❌ Calculate costs
6. ❌ Round numbers
7. ❌ Know about UOM (unit of measure)
8. ❌ Understand conversion logic

### ✅ What Frontend Should Do:
1. ✅ Display the pre-calculated values
2. ✅ Add appropriate labels (cases/kegs/bottles/pints)
3. ✅ Collect user input during stocktake
4. ✅ Send user input back to backend

---

## Rounding Rules (Already Applied by Backend)

| Category | Full Units | Partial Units | Example |
|----------|-----------|---------------|---------|
| Bottled Beer (Doz) | Integer | **Whole number (0-11)** | "12 cases + 8 bottles" |
| Draught Beer | Integer | **2 decimals** | "5 kegs + 39.90 pints" |
| Spirits | Integer | **2 decimals** | "2 bottles + 0.30" |
| Wine | Integer | **2 decimals** | "3 bottles + 0.75" |
| Mixers (Doz) | Integer | **Whole number (0-11)** | "11 cases + 5 bottles" |

---

## Summary

**Backend calculates EVERYTHING. Frontend just displays!**

✅ Single API call returns complete period data  
✅ All display values pre-calculated  
✅ Proper rounding applied  
✅ Opening stock from previous period  
✅ Closing stock with display format  
✅ All costs and profitability metrics  
✅ Stocktake information included  

**Frontend only needs to:**
1. Fetch the data
2. Display the values
3. Add unit labels
4. Collect user input

**No calculations, no conversions, no rounding needed on frontend!** 🎉
