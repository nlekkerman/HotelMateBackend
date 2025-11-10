# Frontend Analytics Implementation Guide

## Overview
This guide covers the implementation of stock analytics features including profitability analysis, low stock alerts, and period comparisons.

---

## 1. Profitability Analysis API

### Endpoint
```
GET /api/stock_tracker/{hotel_identifier}/items/profitability/
```

### Query Parameters
- `category` (optional): Filter by category code (D, B, S, W, M)

### Response Format
```json
[
  {
    "id": 123,
    "sku": "S0380",
    "name": "Jack Daniels",
    "category": "S",
    "unit_cost": 25.50,
    "menu_price": 5.50,
    "cost_per_serving": 1.27,
    "gross_profit": 4.23,
    "gross_profit_percentage": 76.91,
    "markup_percentage": 332.28,
    "pour_cost_percentage": 23.09,
    "current_stock_value": 1250.00
  }
]
```

### Important: Null Values
Some items may have `null` for certain metrics when they cannot be calculated:
- `markup_percentage`: null when cost_per_serving is 0
- `gross_profit_percentage`: null when menu_price is 0 or missing

**Frontend Handling:**
```javascript
// Display null values as "N/A"
const displayValue = (value) => {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return `${value.toFixed(2)}%`;
};

// Filter out nulls for calculations
const validItems = items.filter(item => 
  item.gross_profit_percentage !== null
);
const avgGP = validItems.reduce((sum, item) => 
  sum + item.gross_profit_percentage, 0
) / validItems.length;
```

---

## 2. Low Stock Alert API (UPDATED)

### Endpoint
```
GET /api/stock_tracker/{hotel_identifier}/items/low-stock/
```

### Query Parameters
- `threshold` (optional, default: 50): Minimum servings before alert

### What Changed
**Before:** Checked `current_full_units <= 2` (returned 155+ false positives)
**After:** Checks `total_stock_in_servings < threshold` (returns ~11-22 genuine alerts)

### Response Format
```json
[
  {
    "id": 456,
    "sku": "W0039",
    "name": "Alvier Chardonny",
    "category": "W",
    "current_full_units": 0.00,
    "current_partial_units": 11.44,
    "par_level": 30.00,
    "unit_cost": 6.75,
    "menu_price": 9.50,
    // ... other fields
  }
]
```

### Frontend Implementation

#### Display Low Stock Badge
```javascript
// Fetch low stock items
const response = await fetch(
  `/api/stock_tracker/${hotelId}/items/low-stock/?threshold=50`
);
const lowStockItems = await response.json();

// Show count badge
if (lowStockItems.length > 0) {
  showNotification(`⚠️ ${lowStockItems.length} items below par level`);
}

// Calculate severity
const critical = lowStockItems.filter(item => {
  const servings = calculateServings(item);
  return servings < 20;
});

const urgent = lowStockItems.filter(item => {
  const servings = calculateServings(item);
  const deficit = item.par_level - servings;
  return deficit > (item.par_level * 0.5); // More than 50% below par
});
```

#### Calculate Total Servings
```javascript
function calculateServings(item) {
  const category = item.category;
  const fullUnits = parseFloat(item.current_full_units || 0);
  const partialUnits = parseFloat(item.current_partial_units || 0);
  const uom = parseFloat(item.uom || 1);
  
  // Draught, BIB (LT), and Dozen: partial = servings
  if (category === 'D' || 
      (item.size && (item.size.includes('Doz') || item.size.includes('LT')))) {
    return (fullUnits * uom) + partialUnits;
  }
  
  // Others (Spirits, Wine): partial = fractional
  return (fullUnits * uom) + (partialUnits * uom);
}
```

#### Low Stock Alert Component
```jsx
function LowStockAlert() {
  const [lowStock, setLowStock] = useState([]);
  const [threshold, setThreshold] = useState(50);
  
  useEffect(() => {
    fetchLowStock();
  }, [threshold]);
  
  const fetchLowStock = async () => {
    const response = await fetch(
      `/api/stock_tracker/${hotelId}/items/low-stock/?threshold=${threshold}`
    );
    const data = await response.json();
    setLowStock(data);
  };
  
  if (lowStock.length === 0) {
    return (
      <div className="alert alert-success">
        ✓ All items are above par level
      </div>
    );
  }
  
  return (
    <div className="low-stock-panel">
      <h3>Low Stock Alert</h3>
      <p>{lowStock.length} items need restocking</p>
      
      <div className="threshold-selector">
        <label>Alert Threshold:</label>
        <select value={threshold} onChange={(e) => setThreshold(e.target.value)}>
          <option value="20">Critical (20 servings)</option>
          <option value="50">Default (50 servings)</option>
          <option value="100">Cautious (100 servings)</option>
        </select>
      </div>
      
      <table>
        <thead>
          <tr>
            <th>SKU</th>
            <th>Item</th>
            <th>Current</th>
            <th>Par Level</th>
            <th>Deficit</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {lowStock.map(item => {
            const servings = calculateServings(item);
            const deficit = item.par_level - servings;
            const severity = servings < 0 ? 'danger' :
                           servings < 20 ? 'critical' :
                           deficit > item.par_level * 0.5 ? 'urgent' : 'warning';
            
            return (
              <tr key={item.id} className={severity}>
                <td>{item.sku}</td>
                <td>{item.name}</td>
                <td>{servings.toFixed(1)}</td>
                <td>{item.par_level}</td>
                <td>{deficit.toFixed(1)}</td>
                <td>
                  {servings < 0 && '🚨 NEGATIVE STOCK'}
                  {servings >= 0 && servings < 20 && '⚠️ Critical'}
                  {servings >= 20 && servings < item.par_level && '📉 Low'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
```

---

## 3. Par Levels (NEW FIELD)

### What is Par Level?
Par level is the **minimum number of servings** an item should have in stock before reordering.

### Default Par Levels by Category
- **Draught Beer (D):** 100 pints
- **Bottled Beer (B):** 60 bottles
- **Spirits (S):** 40 shots
- **Wine (W):** 30 glasses
- **Minerals (M):** 50 servings

### Updating Par Levels
```javascript
// Update an item's par level
await fetch(`/api/stock_tracker/${hotelId}/items/${itemId}/`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    par_level: 75.00  // New par level in servings
  })
});
```

### Par Level vs Threshold
- **Par Level:** Item-specific minimum (stored in database per item)
- **Threshold:** Global filter for API queries (not stored)

When `par_level` is set, use it for item-specific alerts:
```javascript
// Check if item is below its par level
const isBelowPar = calculateServings(item) < item.par_level;
```

---

## 4. Period Comparison Analytics

### Available Endpoints

#### Get Closed Periods
```
GET /api/stock_tracker/{hotel_identifier}/periods/?is_closed=true
```

Returns all closed periods available for analytics.

#### Trend Analysis
```
GET /api/stock_tracker/{hotel_identifier}/compare/trend-analysis/?periods=8,7,9
```

Returns multi-period trend data for line charts.

#### Category Comparison
```
GET /api/stock_tracker/{hotel_identifier}/compare/categories/?periods=8,7,9
```

Returns category-level aggregations for pie/bar charts.

### Example: Period IDs
Based on your current data:
- Period ID 8: September 2025
- Period ID 7: October 2025
- Period ID 9: November 2025

### Frontend Example
```javascript
// Fetch closed periods
const periodsResponse = await fetch(
  `/api/stock_tracker/${hotelId}/periods/?is_closed=true`
);
const periods = await periodsResponse.json();

// Build period selector
const periodIds = periods.map(p => p.id).join(',');

// Fetch trend data
const trendResponse = await fetch(
  `/api/stock_tracker/${hotelId}/compare/trend-analysis/?periods=${periodIds}`
);
const trendData = await trendResponse.json();
```

---

## 5. Negative Stock Items (Action Required)

### Current Issues
Two items have **negative stock** (sales exceeded stock + purchases):
- `S1205` (Luxardo Limoncello): -111 servings
- `S2159` (Tequila Bianca): -195 servings

### Frontend Alert
```jsx
function NegativeStockAlert({ items }) {
  const negativeItems = items.filter(item => 
    calculateServings(item) < 0
  );
  
  if (negativeItems.length === 0) return null;
  
  return (
    <div className="alert alert-danger">
      <h4>🚨 Negative Stock Detected</h4>
      <p>{negativeItems.length} items have negative inventory</p>
      <ul>
        {negativeItems.map(item => (
          <li key={item.id}>
            {item.sku} ({item.name}): 
            {calculateServings(item).toFixed(1)} servings
            <button onClick={() => investigateItem(item)}>
              Investigate
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 6. Testing Your Implementation

### Test Low Stock Alert
```bash
# Get low stock items (default threshold: 50)
curl http://localhost:8000/api/stock_tracker/hotel-killarney/items/low-stock/

# Expected: ~11-22 items

# With custom threshold
curl http://localhost:8000/api/stock_tracker/hotel-killarney/items/low-stock/?threshold=100

# Expected: ~52 items
```

### Test Profitability
```bash
curl http://localhost:8000/api/stock_tracker/hotel-killarney/items/profitability/

# Check for null values in response
# Verify gross_profit_percentage is sorted descending
```

### Test Period Comparison
```bash
# Get closed periods first
curl http://localhost:8000/api/stock_tracker/hotel-killarney/periods/?is_closed=true

# Use period IDs for trend analysis
curl "http://localhost:8000/api/stock_tracker/hotel-killarney/compare/trend-analysis/?periods=8,7,9"
```

---

## 7. Summary of Changes

### Fixed Issues
✅ Profitability API: Now handles `null` values safely (no more TypeError)
✅ Low Stock Logic: Changed from full_units check to servings check (22 real alerts vs 155 false positives)
✅ Par Levels: Added `par_level` field to all items with category-based defaults

### New Features
✅ Customizable low stock threshold via query parameter
✅ Per-item par levels for inventory management
✅ Proper null handling for unavailable metrics

### Data Available
✅ 3 closed periods (September, October, November 2025) with full financial data
✅ 254 items with sales, purchases, and waste history
✅ 11 items genuinely below par level (need restocking)
✅ 2 items with negative stock (require investigation)

---

## Need Help?
Contact backend team if you encounter:
- Unexpected null values in profitability data
- Low stock counts that don't match expectations
- Issues with period comparison endpoints
- Questions about calculating total servings
