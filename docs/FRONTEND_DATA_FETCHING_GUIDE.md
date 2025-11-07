# Frontend Data Fetching Guide - Stock Tracker

## Overview
This guide explains **HOW to fetch data** from the backend API for all stock tracker features. Each section shows the API endpoint, required parameters, and complete response structure.

---

## 1. Getting Stocktake Period with All Items

### When to Use
- When displaying the stocktake entry screen
- When staff needs to enter/edit bottle counts
- When loading a specific period's data

### API Call
```javascript
GET /api/stock/{hotel_id}/periods/{period_id}/
```

### Parameters
- `{hotel_id}` - Your hotel's ID (e.g., 1)
- `{period_id}` - The period you want to load (e.g., 2 for November 2024)

### Complete Response
```javascript
{
  "id": 2,
  "hotel": 1,
  "month": "November",
  "year": 2024,
  "status": "open",  // or "closed"
  "created_at": "2024-11-01T00:00:00Z",
  "updated_at": "2024-11-07T10:30:00Z",
  
  // Array of ALL items in this stocktake
  "snapshots": [
    {
      "id": 501,
      
      // ═══ ITEM INFO (Master Data) ═══
      "item": {
        "id": 25,
        "sku": "JAME001",
        "name": "Jameson Irish Whiskey",
        "category": "S",
        "category_display": "Spirits",
        "size": 700,
        "uom": "ml",
        "unit_cost": 15.00,
        "menu_price": 4.50,
        "bottle_price": null
      },
      
      // ═══ STOCKTAKE DATA (Staff Enters) ═══
      "full_units": 17,           // Staff counted 17 full bottles
      "partial_units": 0.3,       // Staff counted 0.3 partial bottle
      "total_quantity": 17.3,     // Auto-calculated: 17 + 0.3
      
      // ═══ CALCULATED VALUES ═══
      "total_value": 259.50,      // 17.3 × €15.00 (cost value)
      "gp_percentage": 70.0,      // Gross profit %
      "markup_percentage": 200.0, // Markup %
      "pour_cost_percentage": 30.0 // Pour cost %
    },
    
    {
      "id": 502,
      "item": {
        "id": 26,
        "sku": "SMIR001",
        "name": "Smirnoff Vodka",
        "category": "S",
        "category_display": "Spirits",
        "size": 700,
        "uom": "ml",
        "unit_cost": 12.50,
        "menu_price": 4.00,
        "bottle_price": null
      },
      "full_units": 8,
      "partial_units": 0.75,
      "total_quantity": 8.75,
      "total_value": 109.38,
      "gp_percentage": 68.8,
      "markup_percentage": 220.0,
      "pour_cost_percentage": 31.3
    }
    // ... 242 more items
  ]
}
```

### How to Use This Data

#### Get All Items for Display
```javascript
const response = await fetch(`/api/stock/${hotelId}/periods/${periodId}/`);
const data = await response.json();

// Loop through all items
data.snapshots.forEach(snapshot => {
  console.log(`Item: ${snapshot.item.name}`);
  console.log(`Category: ${snapshot.item.category_display}`);
  console.log(`Unit Cost: €${snapshot.item.unit_cost}`);
  console.log(`Menu Price: €${snapshot.item.menu_price}`);
  console.log(`Counted: ${snapshot.full_units} full + ${snapshot.partial_units} partial`);
  console.log(`Total Value: €${snapshot.total_value}`);
});
```

#### Filter by Category
```javascript
// Get only Spirits
const spirits = data.snapshots.filter(s => s.item.category === 'S');

// Get only Beers
const beers = data.snapshots.filter(s => s.item.category === 'B');
```

#### Update a Count (Staff Entry)
```javascript
// When staff enters new count for an item
const updateCount = async (snapshotId, fullUnits, partialUnits) => {
  const response = await fetch(`/api/stock/${hotelId}/snapshots/${snapshotId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      full_units: fullUnits,
      partial_units: partialUnits
    })
  });
  return await response.json();
};

// Usage
await updateCount(501, 17, 0.3);  // Update Jameson to 17.3 bottles
```

---

## 2. Getting Item Detail with Expected Stock & Variance

### When to Use
- When user clicks "View Details" on an item
- To show expected vs actual comparison
- To display variance analysis and stock movements

### API Call
```javascript
GET /api/stock/{hotel_id}/items/{item_id}/stocktake-guidance/?current_period={period_id}
```

### Parameters
- `{hotel_id}` - Your hotel's ID
- `{item_id}` - The specific item (e.g., 25 for Jameson)
- `{period_id}` - Current period being counted (e.g., 2 for November)

### Complete Response
```javascript
{
  // ═══ ITEM MASTER INFO ═══
  "item": {
    "id": 25,
    "sku": "JAME001",
    "name": "Jameson Irish Whiskey",
    "category": "S",
    "category_display": "Spirits",
    "size": 700,
    "uom": "ml",
    "unit_cost": 15.00,
    "menu_price": 4.50,
    "bottle_price": null
  },
  
  // ═══ PREVIOUS STOCKTAKE (October 2024) ═══
  "previous_stocktake": {
    "period_id": 1,
    "period": "October 2024",
    "date": "2024-10-31",
    "full_units": 12,
    "partial_units": 0.45,
    "total_quantity": 12.45,
    "stock_value": 186.75,        // 12.45 × €15.00
    "gp_percentage": 70.0,
    "markup_percentage": 200.0,
    "pour_cost_percentage": 30.0
  },
  
  // ═══ STOCK MOVEMENTS (Nov 1 - Nov 30) ═══
  "movements": {
    "deliveries": 24.0,      // Total deliveries/purchases
    "sales": -18.0,          // Total sold/used (negative)
    "adjustments": 0.0,      // Manual adjustments
    "total_change": 6.0,     // Net: +24 - 18 = +6
    
    // Detailed movement history
    "details": [
      {
        "id": 101,
        "date": "2024-11-05",
        "type": "IN",         // "IN" or "OUT"
        "quantity": 24.0,
        "reference": "Delivery #1234",
        "notes": "Regular supplier delivery"
      },
      {
        "id": 102,
        "date": "2024-11-15",
        "type": "OUT",
        "quantity": -18.0,
        "reference": "Sales",
        "notes": "Bar sales Nov 1-15"
      }
    ]
  },
  
  // ═══ EXPECTED STOCK (Calculated) ═══
  "expected_stock": {
    "calculated_quantity": 18.45,  // 12.45 (previous) + 6.0 (movements)
    "calculation": "12.45 + 24.0 - 18.0 = 18.45",
    "message": "Based on previous stock and movements, you should have 18.45 bottles"
  },
  
  // ═══ ACTUAL COUNT (What Staff Entered) ═══
  "actual_count": {
    "full_units": 17,
    "partial_units": 0.3,
    "total_quantity": 17.3
  },
  
  // ═══ VARIANCE ANALYSIS ═══
  "variance": {
    "difference": -1.15,              // 17.3 - 18.45 = -1.15
    "percentage": -6.2,               // (1.15 / 18.45) × 100
    "value_impact": -17.25,           // -1.15 × €15.00
    "status": "WARNING",              // "OK", "WARNING", or "CRITICAL"
    "message": "Missing 1.15 bottles (€17.25 value loss)"
  },
  
  // ═══ CURRENT STOCK VALUE (As Counted) ═══
  "current_value": {
    "cost_value": 259.50,           // 17.3 × €15.00
    "potential_sales": 1038.00,     // If all sold at menu price
    "potential_profit": 778.50,     // Sales - Cost
    "gp_percentage": 75.0           // (Profit / Sales) × 100
  }
}
```

### How to Use This Data

```javascript
// Fetch item detail
const getItemDetail = async (itemId, currentPeriodId) => {
  const response = await fetch(
    `/api/stock/${hotelId}/items/${itemId}/stocktake-guidance/?current_period=${currentPeriodId}`
  );
  return await response.json();
};

// Usage
const detail = await getItemDetail(25, 2);  // Jameson in November period

console.log('Previous:', detail.previous_stocktake.total_quantity);
console.log('Deliveries:', detail.movements.deliveries);
console.log('Expected:', detail.expected_stock.calculated_quantity);
console.log('Actual:', detail.actual_count.total_quantity);
console.log('Variance:', detail.variance.difference, detail.variance.status);
```

---

## 3. Getting Period Summary (Totals & Comparison)

### When to Use
- After stocktake is finalized
- To show overall financial summary
- To compare with previous period

### API Call
```javascript
GET /api/stock/{hotel_id}/periods/{period_id}/summary/
```

### Parameters
- `{hotel_id}` - Your hotel's ID
- `{period_id}` - The period to summarize (e.g., 2 for November)

### Complete Response
```javascript
{
  // ═══ CURRENT PERIOD TOTALS ═══
  "current_period": {
    "id": 2,
    "month": "November",
    "year": 2024,
    "status": "closed",
    "finalized_date": "2024-11-30T23:59:59Z",
    
    // Overall totals
    "item_count": 244,
    "total_stock_value_cost": 12450.00,      // Sum of all (quantity × cost)
    "total_potential_sales": 41280.00,        // Sum of all (quantity × menu_price)
    "total_gross_profit": 28830.00,           // Sales - Cost
    "overall_gp_percentage": 69.8             // (Profit / Sales) × 100
  },
  
  // ═══ PREVIOUS PERIOD TOTALS ═══
  "previous_period": {
    "id": 1,
    "month": "October",
    "year": 2024,
    "status": "closed",
    "finalized_date": "2024-10-31T23:59:59Z",
    
    "item_count": 244,
    "total_stock_value_cost": 11200.00,
    "total_potential_sales": 38500.00,
    "total_gross_profit": 27300.00,
    "overall_gp_percentage": 70.9
  },
  
  // ═══ PERIOD COMPARISON ═══
  "comparison": {
    "stock_value_change": 1250.00,            // €12,450 - €11,200
    "stock_value_change_percent": 11.2,       // (1250 / 11200) × 100
    
    "sales_value_change": 2780.00,            // €41,280 - €38,500
    "sales_value_change_percent": 7.2,
    
    "profit_change": 1530.00,                 // €28,830 - €27,300
    "profit_change_percent": 5.6,
    
    "gp_change": -1.1,                        // 69.8% - 70.9%
    
    "trend": "stock_increased"                // or "stock_decreased", "stable"
  },
  
  // ═══ BREAKDOWN BY CATEGORY ═══
  "by_category": [
    {
      "category": "S",
      "category_name": "Spirits",
      "item_count": 89,
      
      // Current period values
      "current": {
        "stock_value": 5200.00,
        "sales_value": 18500.00,
        "gross_profit": 13300.00,
        "gp_percentage": 71.9
      },
      
      // Previous period values
      "previous": {
        "stock_value": 4800.00,
        "sales_value": 17100.00,
        "gross_profit": 12300.00,
        "gp_percentage": 69.6
      },
      
      // Category-specific comparison
      "change": {
        "stock_value_diff": 400.00,
        "stock_value_percent": 8.3,
        "gp_percentage_diff": 2.3
      }
    },
    {
      "category": "B",
      "category_name": "Beers",
      "item_count": 45,
      "current": {
        "stock_value": 3100.00,
        "sales_value": 8200.00,
        "gross_profit": 5100.00,
        "gp_percentage": 62.2
      },
      "previous": {
        "stock_value": 2900.00,
        "sales_value": 7800.00,
        "gross_profit": 4900.00,
        "gp_percentage": 63.7
      },
      "change": {
        "stock_value_diff": 200.00,
        "stock_value_percent": 6.9,
        "gp_percentage_diff": -1.5
      }
    },
    {
      "category": "W",
      "category_name": "Wines",
      "item_count": 67,
      "current": {
        "stock_value": 2800.00,
        "sales_value": 10100.00,
        "gross_profit": 7300.00,
        "gp_percentage": 72.3
      },
      "previous": {
        "stock_value": 2600.00,
        "sales_value": 9400.00,
        "gross_profit": 6800.00,
        "gp_percentage": 71.5
      },
      "change": {
        "stock_value_diff": 200.00,
        "stock_value_percent": 7.7,
        "gp_percentage_diff": 0.8
      }
    },
    {
      "category": "D",
      "category_name": "Draught",
      "item_count": 15,
      "current": {
        "stock_value": 1150.00,
        "sales_value": 3800.00,
        "gross_profit": 2650.00,
        "gp_percentage": 69.7
      },
      "previous": {
        "stock_value": 1100.00,
        "sales_value": 3600.00,
        "gross_profit": 2500.00,
        "gp_percentage": 70.2
      },
      "change": {
        "stock_value_diff": 50.00,
        "stock_value_percent": 4.5,
        "gp_percentage_diff": -0.5
      }
    },
    {
      "category": "M",
      "category_name": "Mixers",
      "item_count": 28,
      "current": {
        "stock_value": 200.00,
        "sales_value": 680.00,
        "gross_profit": 480.00,
        "gp_percentage": 70.6
      },
      "previous": {
        "stock_value": 180.00,
        "sales_value": 600.00,
        "gross_profit": 420.00,
        "gp_percentage": 69.4
      },
      "change": {
        "stock_value_diff": 20.00,
        "stock_value_percent": 11.1,
        "gp_percentage_diff": 1.2
      }
    }
  ],
  
  // ═══ VARIANCE SUMMARY ═══
  "variance_summary": {
    "critical_count": 3,      // Items with >15% variance
    "warning_count": 8,       // Items with 5-15% variance
    "ok_count": 233,          // Items with <5% variance
    "total_items": 244,
    
    // List of critical items
    "critical_items": [
      {
        "item_id": 45,
        "item_name": "Heineken Beer",
        "expected": 50.0,
        "actual": 35.0,
        "variance": -15.0,
        "variance_percent": -30.0
      }
      // ... 2 more
    ]
  }
}
```

### How to Use This Data

```javascript
// Fetch period summary
const getSummary = async (periodId) => {
  const response = await fetch(`/api/stock/${hotelId}/periods/${periodId}/summary/`);
  return await response.json();
};

// Usage
const summary = await getSummary(2);  // November summary

console.log('Current Total Value:', summary.current_period.total_stock_value_cost);
console.log('Previous Total Value:', summary.previous_period.total_stock_value_cost);
console.log('Change:', summary.comparison.stock_value_change_percent + '%');

// Display by category
summary.by_category.forEach(cat => {
  console.log(`${cat.category_name}: ${cat.current.gp_percentage}% GP`);
  console.log(`  Change: ${cat.change.gp_percentage_diff}%`);
});
```

---

## 4. Comparing Two Periods Side-by-Side

### When to Use
- To analyze trends over time
- To compare any two months
- To identify top performers and concerns

### API Call
```javascript
GET /api/stock/{hotel_id}/periods/compare/?period1={id1}&period2={id2}
```

### Parameters
- `{hotel_id}` - Your hotel's ID
- `period1` - First period ID (e.g., 1 for October)
- `period2` - Second period ID (e.g., 2 for November)

### Complete Response
```javascript
{
  // ═══ PERIOD 1 DATA ═══
  "period1": {
    "id": 1,
    "month": "October",
    "year": 2024,
    "status": "closed",
    
    "totals": {
      "stock_value": 11200.00,
      "sales_value": 38500.00,
      "gross_profit": 27300.00,
      "gp_percentage": 70.9,
      "item_count": 244
    }
  },
  
  // ═══ PERIOD 2 DATA ═══
  "period2": {
    "id": 2,
    "month": "November",
    "year": 2024,
    "status": "closed",
    
    "totals": {
      "stock_value": 12450.00,
      "sales_value": 41280.00,
      "gross_profit": 28830.00,
      "gp_percentage": 69.8,
      "item_count": 244
    }
  },
  
  // ═══ OVERALL CHANGES ═══
  "changes": {
    "stock_value_diff": 1250.00,
    "stock_value_percent": 11.2,
    "sales_value_diff": 2780.00,
    "sales_value_percent": 7.2,
    "profit_diff": 1530.00,
    "profit_percent": 5.6,
    "gp_percent": -1.1
  },
  
  // ═══ TOP PERFORMERS (GP% Improved) ═══
  "top_improvers": [
    {
      "item_id": 25,
      "item_name": "Jameson Irish Whiskey",
      "category": "Spirits",
      "period1_gp": 70.0,
      "period2_gp": 75.0,
      "improvement": 5.0,
      "period1_quantity": 12.45,
      "period2_quantity": 17.3
    },
    {
      "item_id": 26,
      "item_name": "Smirnoff Vodka",
      "category": "Spirits",
      "period1_gp": 68.0,
      "period2_gp": 72.5,
      "improvement": 4.5,
      "period1_quantity": 10.0,
      "period2_quantity": 8.75
    },
    {
      "item_id": 45,
      "item_name": "Grey Goose Vodka",
      "category": "Spirits",
      "period1_gp": 71.0,
      "period2_gp": 74.0,
      "improvement": 3.0,
      "period1_quantity": 5.5,
      "period2_quantity": 6.2
    }
  ],
  
  // ═══ CONCERNS (GP% Decreased) ═══
  "concerns": [
    {
      "item_id": 89,
      "item_name": "Heineken Beer",
      "category": "Beers",
      "period1_gp": 45.0,
      "period2_gp": 38.0,
      "decline": -7.0,
      "severity": "CRITICAL",    // "WARNING" or "CRITICAL"
      "period1_quantity": 50.0,
      "period2_quantity": 35.0
    },
    {
      "item_id": 92,
      "item_name": "Corona Beer",
      "category": "Beers",
      "period1_gp": 42.0,
      "period2_gp": 37.0,
      "decline": -5.0,
      "severity": "WARNING",
      "period1_quantity": 40.0,
      "period2_quantity": 30.0
    }
  ],
  
  // ═══ CATEGORY COMPARISON ═══
  "by_category": [
    {
      "category": "S",
      "category_name": "Spirits",
      "period1": {
        "stock_value": 4800.00,
        "gp_percentage": 69.6
      },
      "period2": {
        "stock_value": 5200.00,
        "gp_percentage": 71.9
      },
      "change": {
        "stock_value_percent": 8.3,
        "gp_percentage_diff": 2.3
      }
    }
    // ... other categories
  ]
}
```

### How to Use This Data

```javascript
// Compare October vs November
const compare = async (period1Id, period2Id) => {
  const response = await fetch(
    `/api/stock/${hotelId}/periods/compare/?period1=${period1Id}&period2=${period2Id}`
  );
  return await response.json();
};

// Usage
const comparison = await compare(1, 2);  // Oct vs Nov

console.log('Period 1 GP:', comparison.period1.totals.gp_percentage);
console.log('Period 2 GP:', comparison.period2.totals.gp_percentage);
console.log('Change:', comparison.changes.gp_percent);

// Show top improvers
comparison.top_improvers.forEach(item => {
  console.log(`${item.item_name}: ${item.period1_gp}% → ${item.period2_gp}%`);
});

// Show concerns
comparison.concerns.forEach(item => {
  console.log(`⚠️ ${item.item_name}: ${item.decline}% decline`);
});
```

---

## 5. Getting All Periods (List)

### When to Use
- To show period selector dropdown
- To list stocktake history
- To let user choose which period to view

### API Call
```javascript
GET /api/stock/{hotel_id}/periods/
```

### Complete Response
```javascript
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "hotel": 1,
      "month": "November",
      "year": 2024,
      "status": "open",
      "created_at": "2024-11-01T00:00:00Z",
      "updated_at": "2024-11-07T10:30:00Z",
      "snapshot_count": 244
    },
    {
      "id": 1,
      "hotel": 1,
      "month": "October",
      "year": 2024,
      "status": "closed",
      "created_at": "2024-10-01T00:00:00Z",
      "updated_at": "2024-10-31T23:59:59Z",
      "snapshot_count": 244
    }
    // ... more periods
  ]
}
```

### How to Use This Data

```javascript
// Get all periods
const getPeriods = async () => {
  const response = await fetch(`/api/stock/${hotelId}/periods/`);
  return await response.json();
};

// Usage
const periods = await getPeriods();

// Create dropdown options
periods.results.forEach(period => {
  console.log(`${period.month} ${period.year} - ${period.status}`);
});

// Find the current open period
const openPeriod = periods.results.find(p => p.status === 'open');
console.log('Current period:', openPeriod.id);
```

---

## 6. Getting All Stock Items (Master List)

### When to Use
- To get all product information
- To create new stocktake periods
- To manage item master data

### API Call
```javascript
GET /api/stock/{hotel_id}/items/
```

### Query Parameters (Optional)
- `category=S` - Filter by category (S/B/W/D/M)
- `search=Jameson` - Search by name or SKU
- `ordering=name` - Sort by field (`name`, `-name`, `unit_cost`, etc.)

### Complete Response
```javascript
{
  "count": 244,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 25,
      "hotel": 1,
      "sku": "JAME001",
      "name": "Jameson Irish Whiskey",
      "category": "S",
      "category_display": "Spirits",
      "size": 700,
      "uom": "ml",
      "unit_cost": 15.00,
      "menu_price": 4.50,
      "bottle_price": null,
      "created_at": "2024-09-01T00:00:00Z",
      "updated_at": "2024-11-05T14:20:00Z"
    }
    // ... 243 more items
  ]
}
```

### How to Use This Data

```javascript
// Get all items
const getAllItems = async () => {
  const response = await fetch(`/api/stock/${hotelId}/items/`);
  return await response.json();
};

// Get filtered items
const getSpirits = async () => {
  const response = await fetch(`/api/stock/${hotelId}/items/?category=S`);
  return await response.json();
};

// Search items
const searchItems = async (query) => {
  const response = await fetch(`/api/stock/${hotelId}/items/?search=${query}`);
  return await response.json();
};

// Usage
const items = await getAllItems();
const spirits = await getSpirits();
const jamesonResults = await searchItems('Jameson');
```

---

## Summary: Quick Reference

| **What You Need** | **API Endpoint** | **Use For** |
|-------------------|------------------|-------------|
| All periods | `GET /periods/` | Period selector dropdown |
| Period with items | `GET /periods/{id}/` | Stocktake entry screen |
| Item detail + variance | `GET /items/{id}/stocktake-guidance/?current_period={id}` | Item detail modal |
| Period summary | `GET /periods/{id}/summary/` | Financial summary report |
| Compare periods | `GET /periods/compare/?period1={id1}&period2={id2}` | Trend analysis |
| All items | `GET /items/` | Item master list |
| Update count | `PATCH /snapshots/{id}/` | Save staff entry |

---

## Common Patterns

### Pattern 1: Loading Stocktake Entry Screen
```javascript
// 1. Get all periods to show dropdown
const periods = await fetch(`/api/stock/${hotelId}/periods/`).then(r => r.json());

// 2. Get current open period
const currentPeriod = periods.results.find(p => p.status === 'open');

// 3. Load all items for that period
const stocktake = await fetch(`/api/stock/${hotelId}/periods/${currentPeriod.id}/`).then(r => r.json());

// Now you have all data for entry screen
```

### Pattern 2: Showing Item Detail
```javascript
// User clicks item, you have item.id and current period.id
const itemId = 25;
const periodId = 2;

const detail = await fetch(
  `/api/stock/${hotelId}/items/${itemId}/stocktake-guidance/?current_period=${periodId}`
).then(r => r.json());

// Now show modal with all detail data
```

### Pattern 3: Finalizing Stocktake & Showing Summary
```javascript
// 1. Close the period
await fetch(`/api/stock/${hotelId}/periods/${periodId}/`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ status: 'closed' })
});

// 2. Get summary
const summary = await fetch(`/api/stock/${hotelId}/periods/${periodId}/summary/`)
  .then(r => r.json());

// Now show summary report
```

---

**That's everything! You now know HOW to fetch all the data you need.** 🎯
