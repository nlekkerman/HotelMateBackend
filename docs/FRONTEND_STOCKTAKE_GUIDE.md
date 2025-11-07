# Frontend Stocktake Guide - Hotel Killarney

## Quick Reference

**Hotel ID**: `2` (Hotel Killarney)  
**October Period ID**: `3` (Closed baseline period)  
**Total Items**: 244  
**Total Stock Value**: €59,504.23  
**Base URL**: `/api/hotels/2/stock/`

---

## 1. Fetch October 2025 Baseline (Closed Period)

This is your **historical baseline** - the closing stock from October 31st, 2025.

### Get Period Details

```http
GET /api/hotels/2/stock/periods/3/
```

**Response**:
```json
{
  "id": 3,
  "hotel": 2,
  "period_type": "MONTHLY",
  "period_name": "October 2025",
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  "year": 2025,
  "month": 10,
  "is_closed": true,
  "created_at": "2025-11-07T...",
  "closed_at": "2025-11-07T...",
  "notes": ""
}
```

**JavaScript Example**:
```javascript
async function getOctoberPeriod() {
  const response = await fetch('/api/hotels/2/stock/periods/3/');
  const period = await response.json();
  
  console.log('Period:', period.period_name);
  console.log('Status:', period.is_closed ? 'CLOSED' : 'OPEN');
  console.log('Dates:', period.start_date, 'to', period.end_date);
  
  return period;
}
```

---

## 2. Fetch October Snapshots (All 244 Items)

Snapshots = frozen stock levels from October 31st.

### Get All Snapshots

```http
GET /api/hotels/2/stock/periods/3/snapshots/
```

**Response** (244 items):
```json
[
  {
    "id": 1,
    "item": {
      "id": 1,
      "sku": "B0070",
      "name": "Budweiser 33cl",
      "category": "B",
      "size": "Doz",
      "uom": "12.0"
    },
    "closing_full_units": "0.00",
    "closing_partial_units": "113.00",
    "unit_cost": "11.75",
    "cost_per_serving": "0.9792",
    "closing_stock_value": "110.65",
    "menu_price": "5.50",
    "created_at": "2025-11-07T..."
  },
  {
    "id": 2,
    "item": {
      "id": 5,
      "sku": "S0045",
      "name": "Bacardi 1ltr",
      "category": "S",
      "size": "1 Lt",
      "uom": "28.2"
    },
    "closing_full_units": "5.00",
    "closing_partial_units": "0.85",
    "unit_cost": "24.82",
    "cost_per_serving": "0.88",
    "closing_stock_value": "145.20",
    "menu_price": "5.50",
    "created_at": "2025-11-07T..."
  }
  // ... 242 more items
]
```

**JavaScript Example**:
```javascript
async function getOctoberSnapshots() {
  const response = await fetch('/api/hotels/2/stock/periods/3/snapshots/');
  const snapshots = await response.json();
  
  console.log('Total items:', snapshots.length); // 244
  
  // Calculate total value
  const totalValue = snapshots.reduce((sum, snap) => {
    return sum + parseFloat(snap.closing_stock_value);
  }, 0);
  
  console.log('Total stock value:', `€${totalValue.toFixed(2)}`);
  
  return snapshots;
}
```

### Filter by Category

```http
GET /api/hotels/2/stock/periods/3/snapshots/?category=B
GET /api/hotels/2/stock/periods/3/snapshots/?category=S
GET /api/hotels/2/stock/periods/3/snapshots/?category=D
GET /api/hotels/2/stock/periods/3/snapshots/?category=W
GET /api/hotels/2/stock/periods/3/snapshots/?category=M
```

**JavaScript Example**:
```javascript
async function getOctoberByCategory(categoryCode) {
  const url = `/api/hotels/2/stock/periods/3/snapshots/?category=${categoryCode}`;
  const response = await fetch(url);
  const snapshots = await response.json();
  
  console.log(`${categoryCode} items:`, snapshots.length);
  
  return snapshots;
}

// Get Bottled Beer snapshots
const beerSnapshots = await getOctoberByCategory('B');

// Get Spirits snapshots
const spiritsSnapshots = await getOctoberByCategory('S');
```

---

## 3. Display October Stock (Cases + Bottles)

For "Doz" items, calculate display format from closing stock.

**Helper Function**:
```javascript
function formatOctoberStock(snapshot) {
  const item = snapshot.item;
  
  if (item.size && item.size.includes('Doz')) {
    // Bottled Beer - closing_partial_units = total bottles
    const totalBottles = parseFloat(snapshot.closing_partial_units);
    const cases = Math.floor(totalBottles / 12);
    const bottles = totalBottles % 12;
    
    if (cases > 0 && bottles > 0) {
      return `${cases} cases + ${bottles} bottles`;
    } else if (cases > 0) {
      return `${cases} cases`;
    } else {
      return `${bottles} bottles`;
    }
  } else {
    // Spirits, Wine, Draught, Minerals
    const full = parseFloat(snapshot.closing_full_units);
    const partial = parseFloat(snapshot.closing_partial_units);
    
    if (full > 0 && partial > 0) {
      return `${full} + ${partial.toFixed(2)}`;
    } else if (full > 0) {
      return `${full}`;
    } else {
      return `${partial.toFixed(2)}`;
    }
  }
}

// Example usage
const budweiser = {
  item: { sku: "B0070", name: "Budweiser 33cl", size: "Doz" },
  closing_full_units: "0.00",
  closing_partial_units: "113.00"
};

console.log(formatOctoberStock(budweiser));
// Output: "9 cases + 5 bottles"
```

---

## 4. React Component Examples

### Display October Baseline Table

```jsx
import { useState, useEffect } from 'react';

function OctoberBaseline() {
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOctoberData();
  }, []);

  const fetchOctoberData = async () => {
    try {
      const response = await fetch('/api/hotels/2/stock/periods/3/snapshots/');
      const data = await response.json();
      setSnapshots(data);
    } catch (error) {
      console.error('Error fetching October data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatStock = (snapshot) => {
    const item = snapshot.item;
    const totalBottles = parseFloat(snapshot.closing_partial_units);
    
    if (item.size?.includes('Doz')) {
      const cases = Math.floor(totalBottles / 12);
      const bottles = totalBottles % 12;
      return `${cases} cases + ${bottles} bottles`;
    }
    
    const full = parseFloat(snapshot.closing_full_units);
    const partial = parseFloat(snapshot.closing_partial_units);
    return full > 0 ? `${full} + ${partial.toFixed(2)}` : `${partial.toFixed(2)}`;
  };

  if (loading) return <div>Loading October baseline...</div>;

  const totalValue = snapshots.reduce((sum, s) => sum + parseFloat(s.closing_stock_value), 0);

  return (
    <div className="october-baseline">
      <h2>October 2025 Baseline</h2>
      <p>Closed Period - Total Value: €{totalValue.toFixed(2)}</p>
      
      <table>
        <thead>
          <tr>
            <th>SKU</th>
            <th>Name</th>
            <th>Category</th>
            <th>Closing Stock</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {snapshots.map(snapshot => (
            <tr key={snapshot.id}>
              <td>{snapshot.item.sku}</td>
              <td>{snapshot.item.name}</td>
              <td>{snapshot.item.category}</td>
              <td>{formatStock(snapshot)}</td>
              <td>€{parseFloat(snapshot.closing_stock_value).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Category Breakdown

```jsx
function OctoberCategoryBreakdown() {
  const [breakdown, setBreakdown] = useState([]);

  useEffect(() => {
    fetchCategoryBreakdown();
  }, []);

  const fetchCategoryBreakdown = async () => {
    const categories = ['D', 'B', 'S', 'W', 'M'];
    const categoryNames = {
      'D': 'Draught Beer',
      'B': 'Bottled Beer',
      'S': 'Spirits',
      'W': 'Wine',
      'M': 'Minerals & Syrups'
    };
    
    const results = await Promise.all(
      categories.map(async (cat) => {
        const response = await fetch(
          `/api/hotels/2/stock/periods/3/snapshots/?category=${cat}`
        );
        const data = await response.json();
        
        const totalValue = data.reduce((sum, item) => {
          return sum + parseFloat(item.closing_stock_value);
        }, 0);
        
        return {
          code: cat,
          name: categoryNames[cat],
          itemCount: data.length,
          totalValue: totalValue
        };
      })
    );
    
    setBreakdown(results);
  };

  const grandTotal = breakdown.reduce((sum, cat) => sum + cat.totalValue, 0);

  return (
    <div className="category-breakdown">
      <h3>October 2025 - By Category</h3>
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Items</th>
            <th>Total Value</th>
            <th>% of Total</th>
          </tr>
        </thead>
        <tbody>
          {breakdown.map(cat => (
            <tr key={cat.code}>
              <td>{cat.name}</td>
              <td>{cat.itemCount}</td>
              <td>€{cat.totalValue.toFixed(2)}</td>
              <td>{((cat.totalValue / grandTotal) * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td><strong>Total</strong></td>
            <td><strong>244</strong></td>
            <td><strong>€{grandTotal.toFixed(2)}</strong></td>
            <td><strong>100%</strong></td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
```

---

## 5. Using October as Opening Stock for November

When creating a **November stocktake**, October's closing stock becomes the opening stock.

### Concept

```
October Closing Stock (Snapshot) → November Opening Stock (Stocktake Line)
```

### Example Flow

1. **Create November Stocktake**:
```http
POST /api/hotels/2/stock/stocktakes/
{
  "period_start": "2025-11-01",
  "period_end": "2025-11-30",
  "notes": "November 2025 stocktake"
}
```

2. **Populate Lines** (backend automatically uses October snapshots):
```http
POST /api/hotels/2/stock/stocktakes/{id}/populate/
```

3. **Backend Logic** (this happens automatically):
```
For each item:
  opening_qty = October snapshot closing_partial_units
  expected_qty = opening_qty + purchases - sales - waste
```

4. **Fetch November Lines**:
```http
GET /api/hotels/2/stock/stocktake-lines/?stocktake={id}
```

**Response shows October as opening**:
```json
{
  "id": 1,
  "item": { "sku": "B0070", "name": "Budweiser 33cl" },
  "opening_qty": "113.00",  // ← From October snapshot!
  "purchases": "0.00",
  "sales": "0.00",
  "waste": "0.00",
  "expected_qty": "113.00",
  "counted_full_units": null,
  "counted_partial_units": null
}
```

---

## 6. Complete Dashboard Example

```jsx
function StockDashboard() {
  const [octoberData, setOctoberData] = useState(null);
  const [currentStock, setCurrentStock] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    // Fetch October baseline
    const octoberResponse = await fetch('/api/hotels/2/stock/periods/3/snapshots/');
    const october = await octoberResponse.json();
    setOctoberData(october);

    // Fetch current stock
    const stockResponse = await fetch('/api/hotels/2/stock/items/');
    const current = await stockResponse.json();
    setCurrentStock(current);
  };

  const octoberValue = octoberData?.reduce((sum, s) => 
    sum + parseFloat(s.closing_stock_value), 0
  ) || 0;

  const currentValue = currentStock.reduce((sum, item) => 
    sum + parseFloat(item.total_stock_value), 0
  );

  const variance = currentValue - octoberValue;
  const variancePercent = ((variance / octoberValue) * 100).toFixed(1);

  return (
    <div className="dashboard">
      <div className="summary-cards">
        <div className="card">
          <h3>October 2025 Baseline</h3>
          <p className="value">€{octoberValue.toFixed(2)}</p>
          <p className="subtitle">Closing Stock (31 Oct)</p>
        </div>
        
        <div className="card">
          <h3>Current Stock</h3>
          <p className="value">€{currentValue.toFixed(2)}</p>
          <p className="subtitle">As of today</p>
        </div>
        
        <div className="card">
          <h3>Change</h3>
          <p className={`value ${variance >= 0 ? 'positive' : 'negative'}`}>
            {variance >= 0 ? '+' : ''}€{variance.toFixed(2)}
          </p>
          <p className="subtitle">{variancePercent}%</p>
        </div>
      </div>
    </div>
  );
}
```

---

## 7. Key Points

### ✅ What October Snapshots Contain
- **Frozen data from October 31st, 2025**
- 244 items with exact closing stock
- Frozen costs and prices from that date
- Total value: €59,504.23

### ✅ How to Use October Data
- **Historical reference**: Show what stock you had
- **Opening stock**: For November stocktakes
- **Comparison**: Compare current stock vs October
- **Trends**: Track month-over-month changes

### ✅ Important Notes
- October period is **CLOSED** - data cannot be edited
- Snapshots are **frozen** - they don't change when current stock changes
- For "Doz" items: `closing_partial_units` = total bottles (calculate cases in frontend)
- All other categories: `closing_full_units` + `closing_partial_units`

---

## 8. API Summary

| Endpoint | Purpose |
|----------|---------|
| `GET /api/hotels/2/stock/periods/3/` | Get October period details |
| `GET /api/hotels/2/stock/periods/3/snapshots/` | Get all 244 October snapshots |
| `GET /api/hotels/2/stock/periods/3/snapshots/?category=B` | Filter by category |
| `GET /api/hotels/2/stock/items/` | Get current stock (for comparison) |

---

## 9. Example: Compare October vs Current

```javascript
async function compareOctoberVsCurrent() {
  // Fetch October baseline
  const octoberRes = await fetch('/api/hotels/2/stock/periods/3/snapshots/');
  const october = await octoberRes.json();

  // Fetch current stock
  const currentRes = await fetch('/api/hotels/2/stock/items/');
  const current = await currentRes.json();

  // Create comparison
  const comparison = october.map(snapshot => {
    const currentItem = current.find(item => item.sku === snapshot.item.sku);
    
    if (!currentItem) return null;

    const octoberQty = parseFloat(snapshot.closing_partial_units);
    const currentQty = parseFloat(currentItem.current_partial_units);
    const change = currentQty - octoberQty;
    const changePercent = ((change / octoberQty) * 100).toFixed(1);

    return {
      sku: snapshot.item.sku,
      name: snapshot.item.name,
      category: snapshot.item.category,
      octoberStock: octoberQty,
      currentStock: currentQty,
      change: change,
      changePercent: changePercent
    };
  }).filter(Boolean);

  // Find biggest changes
  const biggestIncreases = comparison
    .sort((a, b) => b.change - a.change)
    .slice(0, 10);

  const biggestDecreases = comparison
    .sort((a, b) => a.change - b.change)
    .slice(0, 10);

  console.log('Biggest Increases:', biggestIncreases);
  console.log('Biggest Decreases:', biggestDecreases);

  return comparison;
}
```

---

## Ready to Use!

October 2025 baseline is set up and ready for the frontend to fetch and display! 🎉
