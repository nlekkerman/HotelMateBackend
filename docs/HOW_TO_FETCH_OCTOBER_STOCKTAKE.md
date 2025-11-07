# How to Fetch October 2025 Stocktake via API

## 🎯 Quick Reference

**Base URL:** `http://127.0.0.1:8000/api/stock_tracker/`  
**Hotel Identifier:** `1` (or hotel ID)  
**Period ID:** `2` (October 2025)

---

## Step-by-Step Guide

### Step 1: Get All Periods (Find October 2025)

**Endpoint:**
```
GET http://127.0.0.1:8000/api/stock_tracker/2/periods/
```

**What to Look For:**
```javascript
{
  "results": [
    {
      "id": 2,                    // ← This is your period ID
      "period_type": "MONTHLY",
      "period_name": "October 2025",
      "year": 2025,
      "month": 10,               // ← October = 10
      "is_closed": true,         // ← Closed period
      "start_date": "2025-10-01",
      "end_date": "2025-10-31"
    }
  ]
}
```

**Frontend Code:**
```javascript
// Fetch all periods
const response = await fetch('http://127.0.0.1:8000/api/stock_tracker/1/periods/');
const data = await response.json();

// Find October 2025 (closed)
const octoberPeriod = data.results.find(p => 
  p.year === 2025 && 
  p.month === 10 && 
  p.is_closed === true
);

console.log('October Period ID:', octoberPeriod.id); // 2
```

---

### Step 2: Get Period Details with All Items

**Endpoint:**
```
GET http://127.0.0.1:8000/api/stock_tracker/1/periods/2/
```

**Response Structure:**
```javascript
{
  "id": 2,
  "period_type": "MONTHLY",
  "period_name": "October 2025",
  "year": 2025,
  "month": 10,
  "is_closed": true,
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  
  // ✅ THIS IS WHAT YOU NEED - 244 items with closing stock
  "snapshots": [
    {
      "id": 1,
      "item": {
        "id": 1,
        "sku": "B0012",
        "name": "Cronins 0.0%",
        "category": "B",
        "category_display": "Bottled Beer",
        "size": "330ml",
        "unit_cost": 1.18,
        "menu_price": 4.50
      },
      
      // Previous month closing stock (October 31, 2025)
      "closing_full_units": 0.00,
      "closing_partial_units": 16.00,
      "total_quantity": 16.00,
      "closing_stock_value": 18.93,
      
      // Profitability metrics
      "gp_percentage": 73.78,
      "markup_percentage": 281.36,
      "pour_cost_percentage": 26.22
    },
    {
      "id": 2,
      "item": {
        "id": 2,
        "sku": "B0070",
        "name": "Budweiser 33cl",
        "category": "B",
        "category_display": "Bottled Beer",
        "size": "330ml",
        "unit_cost": 0.98,
        "menu_price": 5.00
      },
      "closing_full_units": 0.00,
      "closing_partial_units": 145.00,
      "total_quantity": 145.00,
      "closing_stock_value": 141.98,
      "gp_percentage": 80.40,
      "markup_percentage": 410.20,
      "pour_cost_percentage": 19.60
    }
    // ... 242 more items
  ]
}
```

**Frontend Code:**
```javascript
// Get October period with all snapshots
const periodResponse = await fetch(
  `http://127.0.0.1:8000/api/stock_tracker/1/periods/${octoberPeriod.id}/`
);
const octoberData = await periodResponse.json();

console.log('Total Items:', octoberData.snapshots.length); // 244
console.log('First Item:', octoberData.snapshots[0].item.name);
console.log('Closing Stock:', octoberData.snapshots[0].closing_full_units);
```

---

### Step 3: Use October Data as "Previous Month" Reference

**When Creating November 2025 Stocktake:**

```javascript
// For each item, show October closing stock as reference
octoberData.snapshots.forEach(snapshot => {
  const item = snapshot.item;
  
  // Display to staff:
  console.log(`
    Item: ${item.name}
    SKU: ${item.sku}
    
    Previous Month (October):
    - Closing Stock: ${snapshot.closing_full_units} full + ${snapshot.closing_partial_units} partial
    - Value: €${snapshot.closing_stock_value}
    - GP%: ${snapshot.gp_percentage}%
    
    Current Month (November):
    - Full Units: [Staff enters here]
    - Partial Units: [Staff enters here]
  `);
});
```

---

## Complete URL Structure

### Project URLs (HotelMateBackend/urls.py)
```python
path('api/stock_tracker/', include('stock_tracker.urls'))
```

### Stock Tracker URLs (stock_tracker/urls.py)
```python
# All periods list
path('<str:hotel_identifier>/periods/', period_list, name='period-list')

# Single period detail with snapshots
path('<str:hotel_identifier>/periods/<int:pk>/', period_detail, name='period-detail')

# Period comparison
path('<str:hotel_identifier>/periods/compare/', period_compare, name='period-compare')
```

---

## Full URL Examples

```bash
# List all periods
GET http://127.0.0.1:8000/api/stock_tracker/1/periods/

# Get October 2025 period (ID: 2)
GET http://127.0.0.1:8000/api/stock_tracker/1/periods/2/

# Get all snapshots for October
GET http://127.0.0.1:8000/api/stock_tracker/1/periods/2/snapshots/

# Compare October vs November (when November created)
GET http://127.0.0.1:8000/api/stock_tracker/1/periods/compare/?period1=2&period2=3
```

---

## Testing in Browser/Postman

### Option 1: Browser
Open:
```
http://127.0.0.1:8000/api/stock_tracker/1/periods/2/
```

### Option 2: Postman
```
GET http://127.0.0.1:8000/api/stock_tracker/1/periods/2/
Headers:
  Content-Type: application/json
```

### Option 3: cURL
```bash
curl http://127.0.0.1:8000/api/stock_tracker/1/periods/2/
```

### Option 4: JavaScript Fetch
```javascript
fetch('http://127.0.0.1:8000/api/stock_tracker/1/periods/2/')
  .then(response => response.json())
  .then(data => {
    console.log('Period:', data.period_name);
    console.log('Total Items:', data.snapshots.length);
    console.log('Total Value:', data.snapshots.reduce((sum, s) => sum + parseFloat(s.closing_stock_value), 0));
  });
```

---

## Expected Data

**Period:** October 2025 (ID: 2)  
**Status:** Closed  
**Items:** 244  
**Total Value:** €26,945.86  

**Sample Items:**
- Cronins 0.0%: 16 bottles = €18.93
- Budweiser 33cl: 145 bottles = €141.98
- Bulmers 33cl: 82 bottles = €142.07
- Bulmers Pt Btl: 267 bottles = €614.10
- Coors 330ml: 139 bottles = €164.25

---

## What to Do With This Data

1. **Display as "Previous Month"** in November stocktake entry screen
2. **Calculate Expected Stock** (October closing + movements = expected November opening)
3. **Show Variance** (Expected vs Actual count)
4. **Compare GP%** (October GP% vs November GP%)
5. **Track Stock Changes** (Did stock increase/decrease?)

---

**✅ You now have everything you need to fetch and display October 2025 stocktake data!** 🎯
