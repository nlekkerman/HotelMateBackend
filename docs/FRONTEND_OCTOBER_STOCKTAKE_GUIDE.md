# Frontend Guide: October 2025 Stocktake

## Overview
This guide shows frontend developers how to fetch and display the October 2025 stocktake data that was created with 244 stock items for Hotel Killarney.

---

## Quick Reference

**Hotel ID**: `2` (Hotel Killarney)  
**Period ID**: `3` (October 2025: 2025-10-01 to 2025-10-31)  
**Stocktake ID**: `2` (DRAFT status, 244 lines)  
**Base URL**: `/api/hotels/2/stock/`

---

## API Endpoints

### 1. Get Stocktake Details

```http
GET /api/hotels/2/stock/stocktakes/2/
```

**Response**:
```json
{
  "id": 2,
  "hotel": 2,
  "period_start": "2025-10-01",
  "period_end": "2025-10-31",
  "status": "DRAFT",
  "created_at": "2025-11-07T...",
  "approved_at": null,
  "approved_by": null,
  "notes": "",
  "is_locked": false
}
```

**JavaScript Example**:
```javascript
async function getStocktake() {
  const response = await fetch('/api/hotels/2/stock/stocktakes/2/');
  const stocktake = await response.json();
  
  console.log('Period:', stocktake.period_start, 'to', stocktake.period_end);
  console.log('Status:', stocktake.status);
  console.log('Locked:', stocktake.is_locked);
  
  return stocktake;
}
```

---

### 2. Get All Stocktake Lines (244 Items)

```http
GET /api/hotels/2/stock/stocktake-lines/?stocktake=2
```

**Response** (array of 244 items):
```json
[
  {
    "id": 1,
    "stocktake": 2,
    "item": 1,
    "item_sku": "B0070",
    "item_name": "Budweiser 33cl",
    "category_code": "B",
    "category_name": "Bottled Beer",
    "opening_qty": "145.0000",
    "purchases": "0.0000",
    "sales": "0.0000",
    "waste": "0.0000",
    "transfers_in": "0.0000",
    "transfers_out": "0.0000",
    "adjustments": "0.0000",
    "counted_full_units": null,
    "counted_partial_units": null,
    "counted_qty": "0.0000",
    "expected_qty": "145.0000",
    "variance_qty": "-145.0000",
    "valuation_cost": "0.9792",
    "expected_value": "141.98",
    "counted_value": "0.00",
    "variance_value": "-141.98"
  },
  // ... 243 more items
]
```

**JavaScript Example**:
```javascript
async function getAllStocktakeLines() {
  const response = await fetch('/api/hotels/2/stock/stocktake-lines/?stocktake=2');
  const lines = await response.json();
  
  console.log('Total lines:', lines.length); // 244
  
  return lines;
}
```

---

### 3. Get Lines by Category

```http
GET /api/hotels/2/stock/stocktake-lines/?stocktake=2&category=B
GET /api/hotels/2/stock/stocktake-lines/?stocktake=2&category=S
GET /api/hotels/2/stock/stocktake-lines/?stocktake=2&category=D
GET /api/hotels/2/stock/stocktake-lines/?stocktake=2&category=W
GET /api/hotels/2/stock/stocktake-lines/?stocktake=2&category=M
```

**Categories**:
- **B**: Bottled Beer
- **S**: Spirits
- **D**: Draught Beer
- **W**: Wine
- **M**: Minerals & Syrups

**JavaScript Example**:
```javascript
async function getLinesByCategory(categoryCode) {
  const url = `/api/hotels/2/stock/stocktake-lines/?stocktake=2&category=${categoryCode}`;
  const response = await fetch(url);
  const lines = await response.json();
  
  console.log(`${categoryCode} items:`, lines.length);
  
  return lines;
}

// Get all bottled beer lines
const beerLines = await getLinesByCategory('B');

// Get all spirits lines
const spiritsLines = await getLinesByCategory('S');
```

---

### 4. Get Category Totals (Summary)

```http
GET /api/hotels/2/stock/stocktakes/2/category_totals/
```

**Response**:
```json
[
  {
    "category": "B",
    "category_name": "Bottled Beer",
    "total_expected_value": 12500.00,
    "total_counted_value": 0.00,
    "total_variance_value": -12500.00,
    "item_count": 85
  },
  {
    "category": "S",
    "category_name": "Spirits",
    "total_expected_value": 15600.00,
    "total_counted_value": 0.00,
    "total_variance_value": -15600.00,
    "item_count": 95
  }
  // ... more categories
]
```

**JavaScript Example**:
```javascript
async function getCategoryTotals() {
  const response = await fetch('/api/hotels/2/stock/stocktakes/2/category_totals/');
  const totals = await response.json();
  
  totals.forEach(cat => {
    console.log(`${cat.category_name}:`);
    console.log(`  Items: ${cat.item_count}`);
    console.log(`  Expected Value: €${cat.total_expected_value}`);
    console.log(`  Variance: €${cat.total_variance_value}`);
  });
  
  return totals;
}
```

---

## Updating Stock Counts

### Update a Single Line

When staff physically counts an item, update the line:

```http
PATCH /api/hotels/2/stock/stocktake-lines/{line_id}/
Content-Type: application/json

{
  "counted_full_units": "7.00",
  "counted_partial_units": "0.05"
}
```

**JavaScript Example**:
```javascript
async function updateStockCount(lineId, fullUnits, partialUnits) {
  const response = await fetch(`/api/hotels/2/stock/stocktake-lines/${lineId}/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Token YOUR_AUTH_TOKEN'
    },
    body: JSON.stringify({
      counted_full_units: fullUnits.toString(),
      counted_partial_units: partialUnits.toString()
    })
  });
  
  const updatedLine = await response.json();
  
  console.log('Updated:', updatedLine.item_name);
  console.log('Counted Qty:', updatedLine.counted_qty);
  console.log('Expected Qty:', updatedLine.expected_qty);
  console.log('Variance:', updatedLine.variance_qty);
  
  return updatedLine;
}

// Example: Update Budweiser count to 9 cases + 5 bottles
await updateStockCount(1, 9, 5);
```

---

## Display Examples

### React Component: Stocktake Line Item

```jsx
function StocktakeLineItem({ line }) {
  const [fullUnits, setFullUnits] = useState(line.counted_full_units || '');
  const [partialUnits, setPartialUnits] = useState(line.counted_partial_units || '');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    
    try {
      const response = await fetch(`/api/hotels/2/stock/stocktake-lines/${line.id}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`
        },
        body: JSON.stringify({
          counted_full_units: fullUnits,
          counted_partial_units: partialUnits
        })
      });
      
      const updated = await response.json();
      
      // Refresh line data
      // ...
      
    } catch (error) {
      console.error('Error saving:', error);
    } finally {
      setSaving(false);
    }
  };

  // Format display based on category
  const getUnitLabel = () => {
    switch (line.category_code) {
      case 'B': return { full: 'Cases', partial: 'Bottles' };
      case 'D': return { full: 'Kegs', partial: 'Pints' };
      case 'S': return { full: 'Bottles', partial: 'Shots' };
      case 'W': return { full: 'Bottles', partial: 'Glasses' };
      default: return { full: 'Units', partial: 'Partial' };
    }
  };

  const labels = getUnitLabel();
  const variance = parseFloat(line.variance_qty);
  const varianceClass = variance > 0 ? 'surplus' : variance < 0 ? 'shortage' : 'exact';

  return (
    <div className="stocktake-line-item">
      <div className="item-info">
        <span className="sku">{line.item_sku}</span>
        <span className="name">{line.item_name}</span>
      </div>
      
      <div className="expected">
        <label>Expected:</label>
        <span>{parseFloat(line.expected_qty).toFixed(2)}</span>
      </div>
      
      <div className="count-inputs">
        <input
          type="number"
          step="1"
          placeholder={labels.full}
          value={fullUnits}
          onChange={(e) => setFullUnits(e.target.value)}
        />
        <input
          type="number"
          step="0.01"
          placeholder={labels.partial}
          value={partialUnits}
          onChange={(e) => setPartialUnits(e.target.value)}
        />
      </div>
      
      <div className={`variance ${varianceClass}`}>
        <label>Variance:</label>
        <span>{variance > 0 ? '+' : ''}{variance.toFixed(2)}</span>
        <span className="value">€{parseFloat(line.variance_value).toFixed(2)}</span>
      </div>
      
      <button onClick={handleSave} disabled={saving}>
        {saving ? 'Saving...' : 'Save'}
      </button>
    </div>
  );
}
```

---

### React Component: Category View

```jsx
function CategoryStocktake({ categoryCode }) {
  const [lines, setLines] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLines();
  }, [categoryCode]);

  const fetchLines = async () => {
    setLoading(true);
    
    const url = `/api/hotels/2/stock/stocktake-lines/?stocktake=2&category=${categoryCode}`;
    const response = await fetch(url);
    const data = await response.json();
    
    setLines(data);
    setLoading(false);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="category-stocktake">
      <h2>{lines[0]?.category_name || categoryCode}</h2>
      <div className="summary">
        <span>Total Items: {lines.length}</span>
      </div>
      
      <div className="lines-list">
        {lines.map(line => (
          <StocktakeLineItem key={line.id} line={line} />
        ))}
      </div>
    </div>
  );
}
```

---

### React Component: Category Tabs

```jsx
function StocktakeDashboard() {
  const [activeCategory, setActiveCategory] = useState('B');
  const [totals, setTotals] = useState([]);

  useEffect(() => {
    fetchCategoryTotals();
  }, []);

  const fetchCategoryTotals = async () => {
    const response = await fetch('/api/hotels/2/stock/stocktakes/2/category_totals/');
    const data = await response.json();
    setTotals(data);
  };

  return (
    <div className="stocktake-dashboard">
      <h1>October 2025 Stocktake</h1>
      
      <div className="category-tabs">
        {totals.map(cat => (
          <button
            key={cat.category}
            className={activeCategory === cat.category ? 'active' : ''}
            onClick={() => setActiveCategory(cat.category)}
          >
            {cat.category_name}
            <span className="count">{cat.item_count}</span>
            <span className={`variance ${cat.total_variance_value < 0 ? 'negative' : 'positive'}`}>
              €{cat.total_variance_value.toFixed(2)}
            </span>
          </button>
        ))}
      </div>
      
      <CategoryStocktake categoryCode={activeCategory} />
    </div>
  );
}
```

---

## Special Handling: "Doz" Items (Cases + Bottles)

For items with `size="Doz"` (Bottled Beer, some Minerals), the backend stores individual bottles but provides display helpers.

### Fetching Item Details with Display Helpers

```http
GET /api/hotels/2/stock/items/{item_id}/
```

**Response for B0070 Budweiser**:
```json
{
  "id": 1,
  "sku": "B0070",
  "name": "Budweiser 33cl",
  "size": "Doz",
  "uom": "12.0",
  "current_full_units": "0.00",
  "current_partial_units": "145.00",
  "display_full_units": "12.00",
  "display_partial_units": "1.00",
  "total_stock_in_servings": "145.00"
}
```

**Display Logic**:
```javascript
function formatStockDisplay(item) {
  if (item.size && item.size.includes('Doz')) {
    const cases = parseFloat(item.display_full_units);
    const bottles = parseFloat(item.display_partial_units);
    
    const parts = [];
    if (cases > 0) parts.push(`${cases} case${cases !== 1 ? 's' : ''}`);
    if (bottles > 0) parts.push(`${bottles} bottle${bottles !== 1 ? 's' : ''}`);
    
    return parts.join(' + ') || '0 bottles';
  }
  
  // For other items
  const full = parseFloat(item.current_full_units);
  const partial = parseFloat(item.current_partial_units);
  
  if (full > 0 && partial > 0) {
    return `${full} + ${partial.toFixed(2)}`;
  } else if (full > 0) {
    return `${full}`;
  } else {
    return `${partial.toFixed(2)}`;
  }
}

// Example
const budweiser = {
  sku: "B0070",
  name: "Budweiser 33cl",
  size: "Doz",
  display_full_units: "12.00",
  display_partial_units: "1.00"
};

console.log(formatStockDisplay(budweiser));
// Output: "12 cases + 1 bottle"
```

---

## Approve Stocktake

Once all items are counted, approve the stocktake to lock it and create adjustments.

```http
POST /api/hotels/2/stock/stocktakes/2/approve/
Content-Type: application/json

{}
```

**Response**:
```json
{
  "message": "Stocktake approved",
  "adjustments_created": 23
}
```

**JavaScript Example**:
```javascript
async function approveStocktake() {
  const response = await fetch('/api/hotels/2/stock/stocktakes/2/approve/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${authToken}`
    },
    body: JSON.stringify({})
  });
  
  const result = await response.json();
  
  console.log('Approved!');
  console.log('Adjustments created:', result.adjustments_created);
  
  // Stocktake is now locked (status = APPROVED)
  // Stock levels have been adjusted based on variances
}
```

**What Happens on Approval**:
1. ✅ Stocktake status changes to `APPROVED`
2. ✅ Stocktake is locked (cannot edit)
3. ✅ For each line with variance ≠ 0:
   - Creates `ADJUSTMENT` StockMovement
   - Updates item's `current_partial_units`
4. ✅ Stock levels now match physical count

---

## Complete Workflow Example

```javascript
// 1. Fetch stocktake details
const stocktake = await fetch('/api/hotels/2/stock/stocktakes/2/')
  .then(r => r.json());

console.log('Period:', stocktake.period_start, 'to', stocktake.period_end);

// 2. Get all lines
const lines = await fetch('/api/hotels/2/stock/stocktake-lines/?stocktake=2')
  .then(r => r.json());

console.log('Total items to count:', lines.length); // 244

// 3. Get category summary
const totals = await fetch('/api/hotels/2/stock/stocktakes/2/category_totals/')
  .then(r => r.json());

totals.forEach(cat => {
  console.log(`${cat.category_name}: ${cat.item_count} items`);
});

// 4. Count specific item (e.g., Budweiser)
const budweiserLine = lines.find(l => l.item_sku === 'B0070');

// Staff counts: 10 cases + 3 bottles
await fetch(`/api/hotels/2/stock/stocktake-lines/${budweiserLine.id}/`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${authToken}`
  },
  body: JSON.stringify({
    counted_full_units: '10',
    counted_partial_units: '3'
  })
});

// 5. After all items counted, approve
await fetch('/api/hotels/2/stock/stocktakes/2/approve/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${authToken}`
  },
  body: JSON.stringify({})
});

console.log('✅ Stocktake approved and locked!');
```

---

## Data Validation

### Before Saving Counts

```javascript
function validateCount(fullUnits, partialUnits, categoryCode) {
  const errors = [];
  
  // Check non-negative
  if (fullUnits < 0 || partialUnits < 0) {
    errors.push('Values cannot be negative');
  }
  
  // Check partial units don't exceed full unit
  if (categoryCode === 'B' && partialUnits >= 12) {
    errors.push('Bottles cannot be ≥12. Use full cases instead.');
  }
  
  if (categoryCode === 'D' && partialUnits >= 100) {
    errors.push('Partial pints seem too high. Check your count.');
  }
  
  return errors;
}

// Usage
const errors = validateCount(10, 15, 'B');
if (errors.length > 0) {
  alert(errors.join('\n'));
  return;
}
```

---

## Variance Highlighting

```javascript
function getVarianceClass(varianceQty, varianceValue) {
  const qty = parseFloat(varianceQty);
  const value = parseFloat(varianceValue);
  
  // Exact match
  if (qty === 0) return 'exact';
  
  // Small variance (< €5)
  if (Math.abs(value) < 5) return 'minor';
  
  // Medium variance (€5-€20)
  if (Math.abs(value) < 20) return 'moderate';
  
  // Large variance (≥ €20)
  return 'critical';
}

// CSS classes
/*
.variance.exact { color: green; }
.variance.minor { color: orange; }
.variance.moderate { color: darkorange; }
.variance.critical { color: red; font-weight: bold; }
*/
```

---

## Progress Tracking

```javascript
function calculateProgress(lines) {
  const total = lines.length;
  const counted = lines.filter(line => 
    line.counted_full_units !== null || 
    line.counted_partial_units !== null
  ).length;
  
  const percentage = (counted / total * 100).toFixed(1);
  
  return {
    total,
    counted,
    remaining: total - counted,
    percentage
  };
}

// Usage
const progress = calculateProgress(lines);
console.log(`Progress: ${progress.counted}/${progress.total} (${progress.percentage}%)`);
```

---

## Error Handling

```javascript
async function updateCountWithErrorHandling(lineId, fullUnits, partialUnits) {
  try {
    const response = await fetch(`/api/hotels/2/stock/stocktake-lines/${lineId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${authToken}`
      },
      body: JSON.stringify({
        counted_full_units: fullUnits.toString(),
        counted_partial_units: partialUnits.toString()
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update count');
    }
    
    const updated = await response.json();
    return { success: true, data: updated };
    
  } catch (error) {
    console.error('Error updating count:', error);
    return { success: false, error: error.message };
  }
}

// Usage
const result = await updateCountWithErrorHandling(1, 10, 5);

if (result.success) {
  console.log('Updated successfully:', result.data);
} else {
  alert('Error: ' + result.error);
}
```

---

## Admin Panel Display

### Stock Items List View

The admin panel now displays stock in a user-friendly format:

**For "Doz" items (Bottled Beer, some Minerals)**:
- Shows: "12 cases + 1 bottle" instead of raw numbers
- Uses `display_full_units` and `display_partial_units` from the model

**For other items (Spirits, Wine, Draught)**:
- Shows: "7.00 + 0.05" (full units + partial units)

### Example Display

**B0070 Budweiser 33cl**:
- **Database**: `current_partial_units = 145.00` (total bottles)
- **Admin Display**: "12 cases + 1 bottle"
- **Calculation**: 145 ÷ 12 = 12 cases remainder 1 bottle
- **Total Servings**: 145.00 bottles
- **Total Value**: €141.98

### Stocktake Lines

When viewing stocktake lines in admin:
- "Counted" column shows: "10 cases + 3 bottles" for Doz items
- Makes it easier to verify physical counts
- Matches the format staff use when counting

---

## Summary

### Key Endpoints
1. **Get Stocktake**: `GET /api/hotels/2/stock/stocktakes/2/`
2. **Get All Lines**: `GET /api/hotels/2/stock/stocktake-lines/?stocktake=2`
3. **Get Category Lines**: `GET /api/hotels/2/stock/stocktake-lines/?stocktake=2&category=B`
4. **Update Count**: `PATCH /api/hotels/2/stock/stocktake-lines/{id}/`
5. **Category Totals**: `GET /api/hotels/2/stock/stocktakes/2/category_totals/`
6. **Approve**: `POST /api/hotels/2/stock/stocktakes/2/approve/`

### Important Notes
- ✅ Stocktake has **244 lines** (all active stock items)
- ✅ Opening quantities are already populated from stock snapshots
- ✅ Status is **DRAFT** (editable until approved)
- ✅ For "Doz" items, use `display_full_units` and `display_partial_units` for UI
- ✅ Backend handles all calculations automatically
- ✅ Approval locks stocktake and creates adjustment movements

### Best Practices
- Group items by category for easier counting
- Show progress indicator (counted/total)
- Highlight large variances for review
- Validate inputs before saving
- Save frequently (auto-save on input blur)
- Show expected vs counted comparison
- Allow filtering/searching by SKU or name
