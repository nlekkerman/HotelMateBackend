# Frontend Guide: Low Stock Analytics

## 🚨 QUICK REFERENCE - Read This First!

```javascript
// ✅ CORRECT - Low Stock Analytics
const currentStock = item.unopened_units_count;  // Whole numbers: 3 kegs, 50 bottles
const threshold = item.low_stock_threshold;       // Reorder level: 2, 10, 50, etc.
const isLowStock = currentStock < threshold;

// ❌ WRONG - Don't use these for low stock!
const wrong1 = item.total_stock_in_servings;      // This is for menu sales
const wrong2 = item.total_stock_in_physical_units; // This has decimals (2.5)
const wrong3 = item.current_full_units;            // This is raw stocktake data
```

**Three Fields, Three Purposes:**
- `unopened_units_count` → **Low Stock Analytics** (this guide)
- `total_stock_in_servings` → Menu/Sales Calculations
- `current_full_units/partial_units` → Stocktake Entry

---

## ⚠️ IMPORTANT: Use This Guide ONLY for Low Stock Analytics

**This guide is specifically for the low-stock analytics dashboard.**

For other features, use different fields:
- **Stocktake counting**: Use `current_full_units` and `current_partial_units`
- **Menu sales calculations**: Use `total_stock_in_servings`
- **Revenue analysis**: Use `total_stock_value`

**Do NOT mix these fields!** Low stock analytics requires special handling to show clean unit counts.

---

## Overview
The low-stock analytics endpoint uses **category-specific thresholds** and **unopened unit counts** for clean, whole-number displays suitable for purchasing decisions.

## ✅ Quick Implementation Checklist

**For Low Stock Analytics Dashboard, you MUST:**

1. ✅ Use `unopened_units_count` field (NOT `total_stock_in_servings`)
2. ✅ Use `low_stock_threshold` field for reorder levels
3. ✅ Display whole numbers only (no decimals)
4. ✅ Use `getUnitLabel()` helper to show correct units (kegs, bottles, boxes)
5. ✅ Compare `unopened_units_count` with `low_stock_threshold` for status
6. ✅ Implement period selector dropdown using `period_id` parameter
7. ✅ Display which period is being analyzed (show `period_name` from response)

**Example Analytics Display:**
```
Item: Guinness
Current Stock: 3 kegs          ← unopened_units_count
Threshold: 2 kegs              ← low_stock_threshold
Status: OK ✅
```

---

## API Endpoint

```
GET /stock_tracker/{hotelSlug}/items/low-stock/
```

### Optional Query Parameters
- `period_id` (integer): **Stock period ID to analyze** (optional)
  - If provided: analyzes closing stock from that period's snapshots
  - If omitted: analyzes current live stock
- `threshold` (integer): Override all category-specific thresholds with a single value

### Example Requests
```javascript
// Get CURRENT low stock items (live data)
const response = await fetch(`/stock_tracker/hotel-killarney/items/low-stock/`);

// Get low stock items for a SPECIFIC PERIOD (historical analysis)
const periodId = 42;
const response = await fetch(
  `/stock_tracker/hotel-killarney/items/low-stock/?period_id=${periodId}`
);

// Override threshold for a specific period
const response = await fetch(
  `/stock_tracker/hotel-killarney/items/low-stock/?period_id=${periodId}&threshold=100`
);
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
  "total_stock_in_physical_units": "2.50",
  "unopened_units_count": 2,
  "low_stock_threshold": "2.00",
  "unit_cost": "15.50",
  "menu_price": "5.00",
  "period_id": 42,
  "period_name": "October 2024"
}
```

### 🎯 Key Fields for Low Stock Analytics

| Field | **Use for Low Stock?** | Description |
|-------|:----------------------:|-------------|
| `unopened_units_count` | ✅ **YES** | Unopened units only - shows clean whole numbers (2 kegs, 50 bottles) |
| `low_stock_threshold` | ✅ **YES** | Reorder level in same units as unopened_units_count |
| `category_code` | ✅ **YES** | Group items by category (D, B, M, S, W) |
| `subcategory` | ✅ **YES** | Display Minerals subcategory badges |
| `total_stock_in_physical_units` | ❌ **NO** | Don't use - includes decimals (2.5 bottles) |
| `total_stock_in_servings` | ❌ **NO** | Don't use - this is for menu/sales, not ordering |
| `current_full_units` | ❌ **NO** | Don't use - this is for stocktake entry |
| `current_partial_units` | ❌ **NO** | Don't use - this is for stocktake entry |

---

## 📊 How `unopened_units_count` Works

This field intelligently handles partial units based on category type:

### Categories That IGNORE Partial (Opened Units):
Items that are opened/in-use - we only count full, unopened units:

| Category | What Partial Represents | Count for Analytics |
|----------|-------------------------|---------------------|
| **Draught (D)** | Pints in opened keg (e.g., 25 pints) | Full kegs only |
| **Spirits (S)** | Fraction of opened bottle (e.g., 0.5) | Full bottles only |
| **Wine (W)** | Fraction of opened bottle (e.g., 0.75) | Full bottles only |
| **Syrups** | Fraction of opened bottle (e.g., 0.5) | Full bottles only |
| **BIB** | Fraction of opened box (e.g., 0.5) | Full boxes only |
| **Bulk Juices** | Fraction of opened bottle (e.g., 0.25) | Full bottles only |

### Categories That INCLUDE Partial (Loose Unopened Units):
Items where partial means loose but still unopened:

| Category | What Partial Represents | Count for Analytics |
|----------|-------------------------|---------------------|
| **Bottled Beer (B)** | Loose bottles not in case (e.g., 8 bottles) | Cases + loose bottles |
| **Soft Drinks** | Loose bottles not in case (e.g., 10 bottles) | Cases + loose bottles |
| **Cordials** | Loose bottles not in case (e.g., 7 bottles) | Cases + loose bottles |
| **Juices** | Bottles with ml (e.g., 11.75 = 11 + 750ml) | Full bottles only (integer) |

### Real Examples:

```javascript
// Example 1: Draught Beer
// Storage: 3 kegs + 25 pints (opened keg)
{
  current_full_units: "3.00",
  current_partial_units: "25.00",
  unopened_units_count: 3  // ✅ Only 3 full kegs
}

// Example 2: Bottled Beer
// Storage: 4 cases + 8 loose bottles
{
  current_full_units: "4.00",
  current_partial_units: "8.00",
  unopened_units_count: 56  // ✅ (4×12) + 8 = 56 bottles
}

// Example 3: Spirits
// Storage: 5 bottles + 0.25 (opened bottle)
{
  current_full_units: "5.00",
  current_partial_units: "0.25",
  unopened_units_count: 5  // ✅ Only 5 full bottles
}

// Example 4: Wine
// Storage: 12 bottles + 0.5 (opened bottle)
{
  current_full_units: "12.00",
  current_partial_units: "0.50",
  unopened_units_count: 12  // ✅ Only 12 full bottles
}

// Example 5: Juices
// Storage: 2 cases + 11.75 bottles (11 bottles + 750ml)
{
  current_full_units: "2.00",
  current_partial_units: "11.75",
  unopened_units_count: 35  // ✅ (2×12) + 11 = 35 bottles
}
```

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

### 1. Period Selector Implementation

```javascript
// Fetch stock periods for dropdown
async function fetchStockPeriods(hotelSlug) {
  const response = await fetch(`/stock_tracker/${hotelSlug}/periods/`);
  const periods = await response.json();
  return periods;
}

// Fetch low stock items with optional period selection
async function fetchLowStock(hotelSlug, periodId = null) {
  let url = `/stock_tracker/${hotelSlug}/items/low-stock/`;
  
  if (periodId) {
    url += `?period_id=${periodId}`;
  }
  
  const response = await fetch(url);
  const items = await response.json();
  
  return items;
}

// React/Vue component example
function LowStockAnalytics({ hotelSlug }) {
  const [periods, setPeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [lowStockItems, setLowStockItems] = useState([]);
  
  useEffect(() => {
    // Load periods on mount
    fetchStockPeriods(hotelSlug).then(setPeriods);
  }, [hotelSlug]);
  
  useEffect(() => {
    // Load low stock when period changes
    fetchLowStock(hotelSlug, selectedPeriod).then(setLowStockItems);
  }, [hotelSlug, selectedPeriod]);
  
  return (
    <div className="low-stock-analytics">
      <div className="period-selector">
        <label>Analyze Period:</label>
        <select 
          value={selectedPeriod || ''} 
          onChange={(e) => setSelectedPeriod(e.target.value || null)}
        >
          <option value="">Current Stock</option>
          {periods.map(period => (
            <option key={period.id} value={period.id}>
              {period.period_name}
            </option>
          ))}
        </select>
      </div>
      
      <div className="low-stock-list">
        {lowStockItems.map(item => (
          <div key={item.id} className="low-stock-item">
            <span>{item.name}</span>
            <span>{item.unopened_units_count} {getUnitLabel(item)}</span>
            <span className="period-badge">{item.period_name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 2. Basic Low Stock Display

```javascript
// Simple fetch without period selector
async function fetchCurrentLowStock(hotelSlug) {
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
              {item.unopened_units_count}
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
                    {item.unopened_units_count}
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
  const current = item.unopened_units_count;
  const threshold = parseFloat(item.low_stock_threshold);
  const percentage = (current / threshold) * 100;
  
  if (percentage < 50) return { level: 'critical', color: 'red' };
  if (percentage < 100) return { level: 'low', color: 'orange' };
  return { level: 'ok', color: 'green' };
}

function StockIndicator({ item }) {
  const { level, color } = getStockLevel(item);
  const current = item.unopened_units_count;
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
        {current} / {threshold.toFixed(0)} {getUnitLabel(item)}
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
        const current = item.unopened_units_count;
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
                    {item.unopened_units_count} {getUnitLabel(item)}
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

### 3. **Use Unopened Units for Analytics Display**
`unopened_units_count` shows only full/unopened units (no partials) and can be directly compared with `low_stock_threshold`. This gives clean whole numbers for analytics dashboards.

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
  const aPercent = a.unopened_units_count / parseFloat(a.low_stock_threshold);
  const bPercent = b.unopened_units_count / parseFloat(b.low_stock_threshold);
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

## 🎯 Final Summary: LOW STOCK ANALYTICS ONLY

### What This Guide Is For:
✅ **Low stock analytics dashboard ONLY**  
✅ **Purchasing/ordering decisions**  
✅ **Showing which items need reordering**  

### What This Guide Is NOT For:
❌ Stocktake data entry  
❌ Menu/sales calculations  
❌ Revenue analysis  
❌ Inventory valuation  

---

## Key Implementation Rules

### ✅ DO:
- Use `unopened_units_count` for current stock display
- Use `low_stock_threshold` for reorder levels
- Show whole numbers only (no decimals)
- Use category-specific unit labels (kegs, bottles, boxes)
- Compare unopened units with threshold for status

### ❌ DON'T:
- Use `total_stock_in_servings` (wrong units for ordering)
- Use `total_stock_in_physical_units` (has decimals)
- Use `current_full_units` or `current_partial_units` (raw stocktake data)
- Mix fields from different purposes
- Show decimal values in analytics (2.5 kegs ❌ → 2 kegs ✅)

---

## Technical Summary

✅ **Backend automatically applies category-specific thresholds**  
✅ **Each item includes `unopened_units_count` and `low_stock_threshold`**  
✅ **Units are consistent and whole numbers**  
✅ **Partial units handled intelligently per category**  
✅ **Hotel isolation automatic (no cross-hotel data leaks)**  

**Questions?** Check the examples above or test with:
```bash
curl http://localhost:8000/stock_tracker/hotel-killarney/items/low-stock/
```
