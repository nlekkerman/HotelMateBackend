# Frontend Guide: Low Stock Analytics

## Overview
The low-stock analytics endpoint now uses **category-specific thresholds** that account for the unit conversions (servings → bottles, etc.) implemented during the migration.

## API Endpoint

```
GET /stock_tracker/{hotelSlug}/items/low-stock/
```

### Optional Query Parameters
- `threshold` (integer): Override all category-specific thresholds with a single value

### Example Request
```javascript
// Get low stock items with default category-specific thresholds
const response = await fetch(`/stock_tracker/hotel-killarney/items/low-stock/`);

// Or override with custom threshold (50 for all categories)
const response = await fetch(`/stock_tracker/hotel-killarney/items/low-stock/?threshold=50`);
```

---

## Response Structure

Each low-stock item includes:

```json
{
  "id": 123,
  "sku": "VODKA-001",
  "name": "Smirnoff Vodka 70cl",
  "category": 5,
  "category_code": "S",
  "category_name": "Spirits",
  "subcategory": null,
  "uom": 28,
  "current_full_units": "2.00",
  "current_partial_units": "0.50",
  "total_stock_in_servings": "70.00",
  "low_stock_threshold": "56.00",
  "unit_cost": "15.50",
  "menu_price": "5.00"
}
```

### Key Fields for Frontend

| Field | Description | Frontend Use |
|-------|-------------|--------------|
| `total_stock_in_servings` | Current stock in servings/units | Display as "Current Stock" |
| `low_stock_threshold` | Category-specific threshold | Display as "Reorder Level" |
| `category_code` | Category code (D, B, M, S, W) | Group items by category |
| `subcategory` | Minerals subcategory (SYRUPS, JUICES, etc.) | Display subcategory badge |

---

## Category-Specific Thresholds

The backend automatically applies these thresholds **in physical ordering units**:

| Category | Code | Threshold | Unit | Notes |
|----------|------|-----------|------|-------|
| **Draught Beer** | D | 2 | kegs | Reorder when < 2 kegs |
| **Bottled Beer** | B | 50 | bottles | Reorder when < 50 bottles |
| **Soft Drinks** | M/SOFT_DRINKS | 50 | bottles | Reorder when < 50 bottles |
| **Syrups** | M/SYRUPS | 2 | bottles | Reorder when < 2 bottles |
| **Juices** | M/JUICES | 50 | bottles | Reorder when < 50 bottles |
| **Cordials** | M/CORDIALS | 20 | bottles | Reorder when < 20 bottles |
| **BIB** | M/BIB | 2 | boxes | Reorder when < 2 boxes |
| **Bulk Juices** | M/BULK_JUICES | 20 | bottles | Reorder when < 20 bottles |
| **Spirits** | S | 2 | bottles | Reorder when < 2 bottles |
| **Wine** | W | 10 | bottles | Reorder when < 10 bottles |

**Important:** All thresholds are in **physical units** you actually order (bottles, kegs, boxes), not servings!

---

## Frontend Implementation Examples

### 1. Basic Low Stock Display

```javascript
// Fetch low stock items
async function fetchLowStock(hotelSlug) {
  const response = await fetch(`/stock_tracker/${hotelSlug}/items/low-stock/`);
  const items = await response.json();
  
  return items;
}

// Display in table
function renderLowStockTable(items) {
  return (
    <table>
      <thead>
        <tr>
          <th>Item</th>
          <th>Category</th>
          <th>Current Stock</th>
          <th>Reorder Level</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {items.map(item => (
          <tr key={item.id}>
            <td>{item.name}</td>
            <td>
              {item.category_name}
              {item.subcategory && (
                <span className="badge">{item.subcategory}</span>
              )}
            </td>
            <td>
              {parseFloat(item.total_stock_in_servings).toFixed(2)}
              <span className="unit">{getUnitLabel(item)}</span>
            </td>
            <td>
              {parseFloat(item.low_stock_threshold).toFixed(0)}
              <span className="unit">{getUnitLabel(item)}</span>
            </td>
            <td>
              <span className="badge badge-warning">Low Stock</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### 2. Unit Labels Helper

```javascript
function getUnitLabel(item) {
  const category = item.category_code;
  const subcategory = item.subcategory;
  
  // Draught
  if (category === 'D') return 'pints';
  
  // Minerals subcategories
  if (category === 'M') {
    if (subcategory === 'SYRUPS') return 'servings';
    if (subcategory === 'JUICES') return 'servings';
    if (subcategory === 'BIB') return 'boxes';
    if (subcategory === 'BULK_JUICES') return 'bottles';
    if (subcategory === 'SOFT_DRINKS' || subcategory === 'CORDIALS') {
      return 'bottles';
    }
  }
  
  // Bottled Beer
  if (category === 'B') return 'bottles';
  
  // Spirits
  if (category === 'S') return 'shots';
  
  // Wine
  if (category === 'W') return 'glasses';
  
  return 'units';
}
```

### 3. Group by Category

```javascript
function groupByCategory(items) {
  const grouped = items.reduce((acc, item) => {
    const categoryKey = item.subcategory 
      ? `${item.category_name} - ${item.subcategory}` 
      : item.category_name;
    
    if (!acc[categoryKey]) {
      acc[categoryKey] = [];
    }
    acc[categoryKey].push(item);
    return acc;
  }, {});
  
  return grouped;
}

// Render grouped view
function renderGroupedLowStock(items) {
  const grouped = groupByCategory(items);
  
  return (
    <div className="low-stock-groups">
      {Object.entries(grouped).map(([category, categoryItems]) => (
        <div key={category} className="category-section">
          <h3>{category}</h3>
          <div className="items-count">{categoryItems.length} items</div>
          
          <ul className="item-list">
            {categoryItems.map(item => (
              <li key={item.id} className="low-stock-item">
                <div className="item-name">{item.name}</div>
                <div className="stock-info">
                  <span className="current">
                    {parseFloat(item.total_stock_in_servings).toFixed(2)}
                  </span>
                  <span className="separator">/</span>
                  <span className="threshold">
                    {parseFloat(item.low_stock_threshold).toFixed(0)}
                  </span>
                  <span className="unit">{getUnitLabel(item)}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
```

### 4. Stock Level Indicator

```javascript
function getStockLevel(item) {
  const current = parseFloat(item.total_stock_in_servings);
  const threshold = parseFloat(item.low_stock_threshold);
  const percentage = (current / threshold) * 100;
  
  if (percentage < 50) return { level: 'critical', color: 'red' };
  if (percentage < 100) return { level: 'low', color: 'orange' };
  return { level: 'ok', color: 'green' };
}

function StockIndicator({ item }) {
  const { level, color } = getStockLevel(item);
  const current = parseFloat(item.total_stock_in_servings);
  const threshold = parseFloat(item.low_stock_threshold);
  const percentage = Math.min((current / threshold) * 100, 100);
  
  return (
    <div className="stock-indicator">
      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{ 
            width: `${percentage}%`, 
            backgroundColor: color 
          }}
        />
      </div>
      <div className="stock-text">
        {current.toFixed(2)} / {threshold.toFixed(0)} {getUnitLabel(item)}
      </div>
      <span className={`badge badge-${level}`}>
        {level.toUpperCase()}
      </span>
    </div>
  );
}
```

### 5. Alert Dashboard Card

```javascript
function LowStockAlert({ hotelSlug }) {
  const [lowStockCount, setLowStockCount] = useState(0);
  const [criticalItems, setCriticalItems] = useState([]);
  
  useEffect(() => {
    async function loadLowStock() {
      const items = await fetchLowStock(hotelSlug);
      setLowStockCount(items.length);
      
      // Filter critical items (< 50% of threshold)
      const critical = items.filter(item => {
        const current = parseFloat(item.total_stock_in_servings);
        const threshold = parseFloat(item.low_stock_threshold);
        return (current / threshold) < 0.5;
      });
      setCriticalItems(critical);
    }
    
    loadLowStock();
  }, [hotelSlug]);
  
  return (
    <div className="alert-card">
      <div className="alert-header">
        <h3>Stock Alerts</h3>
        {criticalItems.length > 0 && (
          <span className="badge badge-critical">
            {criticalItems.length} Critical
          </span>
        )}
      </div>
      
      <div className="alert-body">
        <div className="stat">
          <div className="stat-value">{lowStockCount}</div>
          <div className="stat-label">Items Low in Stock</div>
        </div>
        
        {criticalItems.length > 0 && (
          <div className="critical-items">
            <h4>Critical Items</h4>
            <ul>
              {criticalItems.map(item => (
                <li key={item.id}>
                  <span className="item-name">{item.name}</span>
                  <span className="stock-level">
                    {parseFloat(item.total_stock_in_servings).toFixed(2)} {getUnitLabel(item)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        <button className="btn btn-primary" onClick={() => navigateToLowStock()}>
          View All Low Stock Items
        </button>
      </div>
    </div>
  );
}
```

---

## Important Notes

### 1. **No Manual Threshold Configuration Needed**
The backend automatically applies appropriate thresholds based on category and unit type. The frontend just displays the values.

### 2. **Display Units Correctly**
Always show the appropriate unit label (pints, bottles, shots, glasses, servings) based on category using the `getUnitLabel()` helper.

### 3. **Threshold is Already in Same Units as Current Stock**
Both `total_stock_in_servings` and `low_stock_threshold` are in the same units, so they can be directly compared.

### 4. **Override Threshold (Optional)**
If you want to let users temporarily override thresholds:
```javascript
const customThreshold = 100;
const items = await fetch(
  `/stock_tracker/${hotelSlug}/items/low-stock/?threshold=${customThreshold}`
);
```
Note: This overrides ALL category-specific thresholds with a single value.

### 5. **Sorting Recommendations**
Sort by urgency (lowest percentage first):
```javascript
const sortedItems = items.sort((a, b) => {
  const aPercent = parseFloat(a.total_stock_in_servings) / parseFloat(a.low_stock_threshold);
  const bPercent = parseFloat(b.total_stock_in_servings) / parseFloat(b.low_stock_threshold);
  return aPercent - bPercent;
});
```

---

## Example CSS

```css
.low-stock-groups {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.category-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.category-section h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.items-count {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.item-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.low-stock-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-bottom: 1px solid #eee;
}

.low-stock-item:last-child {
  border-bottom: none;
}

.stock-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.stock-info .current {
  font-weight: bold;
  color: #e74c3c;
}

.stock-info .threshold {
  color: #666;
}

.stock-info .unit {
  color: #999;
  font-size: 0.85rem;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-warning {
  background-color: #ffeaa7;
  color: #d63031;
}

.badge-critical {
  background-color: #d63031;
  color: white;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #eee;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease;
}
```

---

## Testing

Test the endpoint with:
```bash
# Get low stock items for hotel
curl http://localhost:8000/stock_tracker/hotel-killarney/items/low-stock/

# Override with custom threshold
curl http://localhost:8000/stock_tracker/hotel-killarney/items/low-stock/?threshold=100
```

---

## Summary

✅ **Backend automatically applies category-specific thresholds**  
✅ **Each item includes its threshold in the response**  
✅ **Units are consistent between current stock and threshold**  
✅ **Frontend just needs to display the data with correct unit labels**  
✅ **Hotel isolation is automatic (no cross-hotel data leaks)**
