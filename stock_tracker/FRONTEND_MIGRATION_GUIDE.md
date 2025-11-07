# Frontend Migration Guide - Stock Tracker Refactor

## 🔄 Overview of Changes

Your stock tracker backend has been completely refactored from category-specific models to a unified structure. This guide will help you update your frontend code.

---

## 📋 Table of Contents
1. [Breaking Changes](#breaking-changes)
2. [Data Model Changes](#data-model-changes)
3. [API Endpoint Changes](#api-endpoint-changes)
4. [Step-by-Step Migration](#step-by-step-migration)
5. [Code Examples](#code-examples)
6. [Testing Checklist](#testing-checklist)

---

## ⚠️ Breaking Changes

### 1. **Category Structure Changed**
**BEFORE:** Categories had `id`, `hotel`, `name`, `sort_order`
```javascript
// OLD
{
  id: 1,
  hotel: 1,
  name: "Draught Beer",
  sort_order: 1
}
```

**AFTER:** Categories use `code` as primary key, no hotel FK
```javascript
// NEW
{
  code: "D",
  name: "Draught Beer",
  item_count: 14
}
```

**Action Required:**
- Change category references from `category.id` → `category.code`
- Update category endpoint from `/categories/` → `/categories/` (now returns all 5 fixed categories)
- Remove any UI for creating/editing categories (they're now fixed: D, B, S, W, M)

---

### 2. **Stock Item Model Simplified**
**BEFORE:** Multiple fields for different product types
```javascript
// OLD StockItem
{
  id: 1,
  category: 1,  // FK to category ID
  sku: "D0005",
  name: "50 Guinness",
  description: "...",
  product_type: "BEER",
  subtype: "DRAUGHT",
  size: "50Lt",
  uom: 88.03,
  base_unit: "PINT",
  unit_cost: 179.00,
  cost_per_base: 2.03,
  case_cost: null,
  current_qty: 7.00,
  par_level: 5,
  bin: 1,
  vendor: "...",
  // ... many more fields
}
```

**AFTER:** Unified model with full/partial units
```javascript
// NEW StockItem
{
  id: 1,
  hotel: 1,
  sku: "D0005",
  name: "50 Guinness",
  category: "D",  // NOW: Direct code reference
  size: "50Lt",
  size_value: 50,
  size_unit: "L",
  uom: 88.03,
  unit_cost: 179.00,
  current_full_units: 7,      // NEW: Full kegs/cases/bottles
  current_partial_units: 0,   // NEW: Partial units (pints, individual bottles, etc.)
  menu_price: 5.50,
  // Calculated fields (read-only)
  total_units: 7.00,
  total_stock_value: 1253.00,
  cost_per_serving: 2.03,
  gross_profit_per_serving: 3.47,
  gp_percentage: 63.09,
  markup_percentage: 170.94,
  pour_cost_percentage: 36.91
}
```

**Action Required:**
- Replace `current_qty` with `current_full_units` + `current_partial_units`
- Remove references to: `description`, `product_type`, `subtype`, `tag`, `bin`, `vendor`, `country`, `region`, `par_level`, etc.
- Category is now a string code ("D", "B", "S", "W", "M") not an ID
- Use new calculated fields for profitability (they're read-only properties)

---

### 3. **Stock Movements Changed**
**BEFORE:**
```javascript
// OLD Movement
{
  id: 1,
  item: 123,
  movement_type: "PURCHASE",
  quantity: 10.5,  // Single quantity field
  unit_cost: 125.50,
  reference: "INV-123"
}
```

**AFTER:**
```javascript
// NEW Movement
{
  id: 1,
  hotel: 1,
  item: 123,
  item_sku: "D0005",
  item_name: "50 Guinness",
  movement_type: "PURCHASE",
  full_units: 10,        // NEW: Full units (kegs, cases, bottles)
  partial_units: 0.5,    // NEW: Partial units
  total_units: 10.5,     // NEW: Calculated total (read-only)
  unit_cost: 125.50,
  total_value: 1317.75,  // NEW: Calculated (read-only)
  reference: "INV-123",
  notes: "Weekly delivery",
  staff: 5,
  staff_name: "John Doe",
  timestamp: "2024-11-07T16:30:00Z"
}
```

**Action Required:**
- Replace `quantity` with `full_units` and `partial_units`
- Display `total_units` and `total_value` (read-only)
- Add UI for partial units based on category:
  - **Draught (D)**: Partial = pints remaining in keg
  - **Bottled (B)**: Partial = individual bottles from opened case
  - **Spirits (S)**: Partial = shots/servings from opened bottle
  - **Wine (W)**: Usually 0 (sold by bottle)
  - **Minerals (M)**: Partial = individual bottles from opened case

---

### 4. **New Models Added**

#### **StockPeriod** (NEW)
```javascript
{
  id: 1,
  hotel: 1,
  period_type: "MONTHLY",  // WEEKLY, MONTHLY, QUARTERLY, YEARLY, CUSTOM
  start_date: "2024-10-01",
  end_date: "2024-10-31",
  year: 2024,
  month: 10,
  quarter: null,
  week: null,
  period_name: "October 2024"  // Auto-generated
}
```

**Use Cases:**
- Track stock over time periods
- Compare month-to-month or week-to-week
- Generate period reports

---

#### **StockSnapshot** (NEW)
```javascript
{
  id: 1,
  hotel: 1,
  item: 123,
  item_sku: "D0005",
  item_name: "50 Guinness",
  category_code: "D",
  period: 1,
  period_name: "October 2024",
  closing_full_units: 7,
  closing_partial_units: 0,
  total_units: 7.00,
  unit_cost: 179.00,
  cost_per_serving: 2.03,
  closing_stock_value: 1253.00,
  created_at: "2024-11-01T00:00:00Z"
}
```

**Use Cases:**
- Historical stock levels at period end
- Month-over-month comparisons
- Stock valuation reports
- Trend analysis

---

#### **Location** (NEW - Optional)
```javascript
{
  id: 1,
  hotel: 1,
  name: "Main Bar",
  location_type: "BAR",  // BAR, CELLAR, STORAGE, KITCHEN, OTHER
  description: "Front bar area",
  is_active: true
}
```

**Use Cases:**
- Track stock by location
- Transfer stock between locations
- Multi-location inventory

---

## 🔗 API Endpoint Changes

### Category Endpoints
```diff
- GET /api/stock/{hotel}/categories/           ❌ Returns hotel-specific categories
+ GET /api/stock/{hotel}/categories/           ✅ Returns 5 fixed categories (D,B,S,W,M)

- POST /api/stock/{hotel}/categories/          ❌ Create new category
+ [REMOVED]                                    ✅ Categories are fixed, cannot create

- GET /api/stock/{hotel}/categories/{id}/      ❌ Get by numeric ID
+ GET /api/stock/{hotel}/categories/{code}/    ✅ Get by code (D, B, S, W, M)

+ GET /api/stock/{hotel}/categories/{code}/items/  ✅ NEW: Get all items in category
```

---

### Item Endpoints (Enhanced)
```diff
  GET /api/stock/{hotel}/items/                ✅ Still works (with new fields)
  POST /api/stock/{hotel}/items/               ✅ Still works (use new fields)
  
+ GET /api/stock/{hotel}/items/profitability/  ✅ NEW: Profitability analysis
+ GET /api/stock/{hotel}/items/low-stock/      ✅ NEW: Items with ≤2 units
+ GET /api/stock/{hotel}/items/{id}/history/   ✅ NEW: Item stock history
```

---

### NEW Endpoints
```javascript
// Periods
GET    /api/stock/{hotel}/periods/
POST   /api/stock/{hotel}/periods/
GET    /api/stock/{hotel}/periods/{id}/
GET    /api/stock/{hotel}/periods/{id}/snapshots/
GET    /api/stock/{hotel}/periods/compare/?period1={id}&period2={id}

// Snapshots (Read-only)
GET    /api/stock/{hotel}/snapshots/
GET    /api/stock/{hotel}/snapshots/{id}/

// Locations
GET    /api/stock/{hotel}/locations/
POST   /api/stock/{hotel}/locations/
GET    /api/stock/{hotel}/locations/{id}/
```

---

## 📝 Step-by-Step Migration

### Step 1: Update API Service Layer

#### Before (Old API calls):
```javascript
// OLD: Category API
export const getCategories = async (hotelId) => {
  const response = await api.get(`/stock/${hotelId}/categories/`);
  return response.data;
};

export const getItemsByCategory = async (hotelId, categoryId) => {
  const response = await api.get(`/stock/${hotelId}/items/?category=${categoryId}`);
  return response.data;
};
```

#### After (New API calls):
```javascript
// NEW: Category API
export const getCategories = async (hotelId) => {
  const response = await api.get(`/stock/${hotelId}/categories/`);
  // Returns: [{code: "D", name: "Draught Beer", item_count: 14}, ...]
  return response.data;
};

export const getCategoryItems = async (hotelId, categoryCode) => {
  const response = await api.get(`/stock/${hotelId}/categories/${categoryCode}/items/`);
  return response.data;
};

// OR filter items by category code
export const getItemsByCategory = async (hotelId, categoryCode) => {
  const response = await api.get(`/stock/${hotelId}/items/?category=${categoryCode}`);
  return response.data;
};
```

---

### Step 2: Update State Management

#### Before:
```javascript
// OLD: Redux/State structure
const stockState = {
  categories: [
    { id: 1, name: "Draught Beer", sort_order: 1 },
    { id: 2, name: "Bottled Beer", sort_order: 2 }
  ],
  items: [
    {
      id: 1,
      category: 1,  // FK to category ID
      sku: "D0005",
      current_qty: 7.00
    }
  ]
};
```

#### After:
```javascript
// NEW: Redux/State structure
const stockState = {
  categories: [
    { code: "D", name: "Draught Beer", item_count: 14 },
    { code: "B", name: "Bottled Beer", item_count: 21 }
  ],
  items: [
    {
      id: 1,
      category: "D",  // Direct code reference
      sku: "D0005",
      current_full_units: 7,
      current_partial_units: 0,
      total_units: 7.00
    }
  ],
  periods: [
    { id: 1, period_name: "October 2024", start_date: "2024-10-01" }
  ],
  snapshots: []
};
```

---

### Step 3: Update UI Components

#### Category Selector Component
```jsx
// BEFORE
const CategorySelector = ({ value, onChange }) => {
  const [categories, setCategories] = useState([]);
  
  useEffect(() => {
    fetchCategories().then(data => setCategories(data));
  }, []);
  
  return (
    <select value={value} onChange={(e) => onChange(parseInt(e.target.value))}>
      {categories.map(cat => (
        <option key={cat.id} value={cat.id}>
          {cat.name}
        </option>
      ))}
    </select>
  );
};

// AFTER
const CategorySelector = ({ value, onChange }) => {
  const categories = [
    { code: 'D', name: 'Draught Beer' },
    { code: 'B', name: 'Bottled Beer' },
    { code: 'S', name: 'Spirits' },
    { code: 'W', name: 'Wine' },
    { code: 'M', name: 'Minerals & Syrups' }
  ];
  
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {categories.map(cat => (
        <option key={cat.code} value={cat.code}>
          {cat.name}
        </option>
      ))}
    </select>
  );
};
```

---

#### Stock Item Form Component
```jsx
// BEFORE
const StockItemForm = ({ item, onSubmit }) => {
  const [formData, setFormData] = useState({
    sku: item?.sku || '',
    name: item?.name || '',
    category: item?.category || '',  // Category ID
    current_qty: item?.current_qty || 0,
    unit_cost: item?.unit_cost || 0
  });

  return (
    <form onSubmit={() => onSubmit(formData)}>
      <input 
        type="text" 
        value={formData.sku} 
        onChange={(e) => setFormData({...formData, sku: e.target.value})} 
      />
      <CategorySelector 
        value={formData.category} 
        onChange={(catId) => setFormData({...formData, category: catId})} 
      />
      <input 
        type="number" 
        value={formData.current_qty} 
        onChange={(e) => setFormData({...formData, current_qty: e.target.value})} 
      />
      {/* ... */}
    </form>
  );
};
```

```jsx
// AFTER
const StockItemForm = ({ item, onSubmit }) => {
  const [formData, setFormData] = useState({
    sku: item?.sku || '',
    name: item?.name || '',
    category: item?.category || 'D',  // Category CODE
    size: item?.size || '',
    size_value: item?.size_value || 0,
    size_unit: item?.size_unit || '',
    uom: item?.uom || 0,
    current_full_units: item?.current_full_units || 0,
    current_partial_units: item?.current_partial_units || 0,
    unit_cost: item?.unit_cost || 0,
    menu_price: item?.menu_price || 0
  });

  return (
    <form onSubmit={() => onSubmit(formData)}>
      <input 
        type="text" 
        value={formData.sku} 
        onChange={(e) => setFormData({...formData, sku: e.target.value})} 
        placeholder="SKU (e.g., D0005)"
      />
      
      <CategorySelector 
        value={formData.category} 
        onChange={(code) => setFormData({...formData, category: code})} 
      />
      
      <div className="stock-quantity">
        <label>Full Units (Kegs/Cases/Bottles)</label>
        <input 
          type="number" 
          step="1"
          value={formData.current_full_units} 
          onChange={(e) => setFormData({...formData, current_full_units: e.target.value})} 
        />
        
        <label>Partial Units (Pints/Individual Bottles)</label>
        <input 
          type="number" 
          step="0.01"
          value={formData.current_partial_units} 
          onChange={(e) => setFormData({...formData, current_partial_units: e.target.value})} 
        />
      </div>

      <div>
        <label>Size</label>
        <input 
          type="text" 
          value={formData.size} 
          onChange={(e) => setFormData({...formData, size: e.target.value})} 
          placeholder="e.g., 50Lt, 70cl, Doz"
        />
      </div>

      <div>
        <label>UOM (Units of Measure)</label>
        <input 
          type="number" 
          step="0.01"
          value={formData.uom} 
          onChange={(e) => setFormData({...formData, uom: e.target.value})} 
          placeholder="Pints per keg, shots per bottle, etc."
        />
      </div>
      
      {/* ... */}
    </form>
  );
};
```

---

#### Stock Display Component
```jsx
// BEFORE
const StockItemCard = ({ item }) => {
  return (
    <div className="stock-card">
      <h3>{item.name}</h3>
      <p>SKU: {item.sku}</p>
      <p>Current Stock: {item.current_qty} {item.base_unit}</p>
      <p>Value: €{item.current_qty * item.unit_cost}</p>
    </div>
  );
};

// AFTER
const StockItemCard = ({ item }) => {
  return (
    <div className="stock-card">
      <div className="card-header">
        <h3>{item.name}</h3>
        <span className="category-badge">{item.category_code}</span>
      </div>
      
      <p>SKU: {item.sku}</p>
      
      <div className="stock-quantity">
        <p>Full Units: {item.current_full_units}</p>
        <p>Partial Units: {item.current_partial_units}</p>
        <p><strong>Total: {item.total_units}</strong></p>
      </div>
      
      <div className="stock-value">
        <p>Unit Cost: €{item.unit_cost}</p>
        <p><strong>Total Value: €{item.total_stock_value}</strong></p>
      </div>
      
      {item.menu_price > 0 && (
        <div className="profitability">
          <p>Menu Price: €{item.menu_price}</p>
          <p>GP%: <span className="gp">{item.gp_percentage}%</span></p>
          <p>Pour Cost%: {item.pour_cost_percentage}%</p>
        </div>
      )}
    </div>
  );
};
```

---

### Step 4: Add New Features

#### Period Comparison Component (NEW)
```jsx
const PeriodComparison = ({ hotelId }) => {
  const [periods, setPeriods] = useState([]);
  const [period1, setPeriod1] = useState(null);
  const [period2, setPeriod2] = useState(null);
  const [comparison, setComparison] = useState(null);

  useEffect(() => {
    // Fetch available periods
    fetchPeriods(hotelId).then(data => setPeriods(data));
  }, [hotelId]);

  const handleCompare = async () => {
    if (!period1 || !period2) return;
    
    const response = await api.get(
      `/stock/${hotelId}/periods/compare/?period1=${period1}&period2=${period2}`
    );
    setComparison(response.data);
  };

  return (
    <div className="period-comparison">
      <h2>Period Comparison</h2>
      
      <div className="period-selectors">
        <select value={period1} onChange={(e) => setPeriod1(e.target.value)}>
          <option value="">Select Period 1</option>
          {periods.map(p => (
            <option key={p.id} value={p.id}>{p.period_name}</option>
          ))}
        </select>
        
        <select value={period2} onChange={(e) => setPeriod2(e.target.value)}>
          <option value="">Select Period 2</option>
          {periods.map(p => (
            <option key={p.id} value={p.id}>{p.period_name}</option>
          ))}
        </select>
        
        <button onClick={handleCompare}>Compare</button>
      </div>

      {comparison && (
        <div className="comparison-results">
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>{comparison.period1.period_name}</th>
                <th>{comparison.period2.period_name}</th>
                <th>Change</th>
                <th>%</th>
              </tr>
            </thead>
            <tbody>
              {comparison.comparison.map(item => (
                <tr key={item.item_id}>
                  <td>{item.name} ({item.sku})</td>
                  <td>€{item.period1.closing_stock}</td>
                  <td>€{item.period2.closing_stock}</td>
                  <td className={item.change.value >= 0 ? 'positive' : 'negative'}>
                    €{item.change.value}
                  </td>
                  <td>{item.change.percentage}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
```

---

#### Profitability Dashboard (NEW)
```jsx
const ProfitabilityDashboard = ({ hotelId }) => {
  const [items, setItems] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState('');

  useEffect(() => {
    fetchProfitability();
  }, [hotelId, categoryFilter]);

  const fetchProfitability = async () => {
    const url = categoryFilter 
      ? `/stock/${hotelId}/items/profitability/?category=${categoryFilter}`
      : `/stock/${hotelId}/items/profitability/`;
    
    const response = await api.get(url);
    setItems(response.data);
  };

  return (
    <div className="profitability-dashboard">
      <h2>Profitability Analysis</h2>
      
      <CategorySelector 
        value={categoryFilter} 
        onChange={setCategoryFilter}
        allowAll={true}
      />

      <div className="profit-table">
        <table>
          <thead>
            <tr>
              <th>SKU</th>
              <th>Name</th>
              <th>Category</th>
              <th>Unit Cost</th>
              <th>Menu Price</th>
              <th>Cost/Serving</th>
              <th>GP%</th>
              <th>Markup%</th>
              <th>Pour Cost%</th>
              <th>Stock Value</th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id}>
                <td>{item.sku}</td>
                <td>{item.name}</td>
                <td>{item.category}</td>
                <td>€{item.unit_cost}</td>
                <td>€{item.menu_price}</td>
                <td>€{item.cost_per_serving}</td>
                <td className={getGPClass(item.gp_percentage)}>
                  {item.gp_percentage}%
                </td>
                <td>{item.markup_percentage}%</td>
                <td>{item.pour_cost_percentage}%</td>
                <td>€{item.current_stock_value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const getGPClass = (gp) => {
  if (gp >= 70) return 'excellent';
  if (gp >= 60) return 'good';
  if (gp >= 50) return 'fair';
  return 'poor';
};
```

---

#### Low Stock Alert Component (NEW)
```jsx
const LowStockAlerts = ({ hotelId }) => {
  const [lowStockItems, setLowStockItems] = useState([]);

  useEffect(() => {
    fetchLowStock();
  }, [hotelId]);

  const fetchLowStock = async () => {
    const response = await api.get(`/stock/${hotelId}/items/low-stock/`);
    setLowStockItems(response.data);
  };

  if (lowStockItems.length === 0) {
    return <div className="no-alerts">✅ All items adequately stocked</div>;
  }

  return (
    <div className="low-stock-alerts">
      <h3>⚠️ Low Stock Alerts ({lowStockItems.length})</h3>
      
      <div className="alert-list">
        {lowStockItems.map(item => (
          <div key={item.id} className="alert-item">
            <div className="item-info">
              <strong>{item.name}</strong>
              <span className="sku">{item.sku}</span>
            </div>
            <div className="stock-level">
              <span className="quantity">{item.current_full_units} units</span>
              <span className="category-badge">{item.category_code}</span>
            </div>
            <button onClick={() => handleReorder(item)}>
              Reorder
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 🧪 Testing Checklist

### Phase 1: API Integration
- [ ] Test category fetching (should return 5 categories with codes)
- [ ] Test item fetching (verify new field structure)
- [ ] Test item creation with full_units and partial_units
- [ ] Test item update
- [ ] Test movement creation with full_units and partial_units

### Phase 2: Display Updates
- [ ] Category selector shows codes (D, B, S, W, M)
- [ ] Stock items display full_units + partial_units correctly
- [ ] Calculated fields (GP%, markup%, etc.) display correctly
- [ ] Stock value calculations are accurate

### Phase 3: New Features
- [ ] Period comparison works
- [ ] Profitability dashboard loads
- [ ] Low stock alerts appear
- [ ] Item history displays correctly

### Phase 4: Data Migration
- [ ] Old category IDs mapped to new codes
- [ ] Old current_qty split into full_units and partial_units
- [ ] All existing items have October 2024 snapshot

---

## 🔧 Common Issues & Solutions

### Issue 1: Categories showing undefined
**Problem:** Old code expects `category.id`, but new API returns `category.code`

**Solution:**
```javascript
// WRONG
items.filter(item => item.category === categoryId)

// CORRECT
items.filter(item => item.category === categoryCode)
```

---

### Issue 2: Stock quantity not displaying
**Problem:** Old code uses `item.current_qty`, which no longer exists

**Solution:**
```javascript
// WRONG
<p>Stock: {item.current_qty}</p>

// CORRECT
<p>Full Units: {item.current_full_units}</p>
<p>Partial: {item.current_partial_units}</p>
<p>Total: {item.total_units}</p>
```

---

### Issue 3: Movement creation fails
**Problem:** Sending `quantity` instead of `full_units` and `partial_units`

**Solution:**
```javascript
// WRONG
const movement = {
  item: itemId,
  movement_type: "PURCHASE",
  quantity: 10
};

// CORRECT
const movement = {
  item: itemId,
  movement_type: "PURCHASE",
  full_units: 10,
  partial_units: 0
};
```

---

### Issue 4: Category filter not working
**Problem:** Filtering by category ID instead of code

**Solution:**
```javascript
// WRONG
fetchItems(`/items/?category=${categoryId}`)

// CORRECT
fetchItems(`/items/?category=${categoryCode}`)  // Use "D", "B", "S", "W", "M"
```

---

## 📊 Data Mapping Reference

### Category ID → Code Mapping
If you need to migrate old data, use this mapping:

| Old Category Name | Old ID (varies) | New Code |
|------------------|-----------------|----------|
| Draught Beer     | ?               | D        |
| Bottled Beer     | ?               | B        |
| Spirits          | ?               | S        |
| Wine             | ?               | W        |
| Minerals & Syrups| ?               | M        |

### Field Mapping
| Old Field | New Field | Notes |
|-----------|-----------|-------|
| `current_qty` | `current_full_units` + `current_partial_units` | Split into two fields |
| `category` (ID) | `category` (code) | Now uses "D", "B", "S", "W", "M" |
| `cost_per_base` | `cost_per_serving` | Same concept, renamed |
| N/A | `total_units` | New calculated field |
| N/A | `total_stock_value` | New calculated field |
| N/A | `gp_percentage` | New calculated field |
| N/A | `markup_percentage` | New calculated field |
| N/A | `pour_cost_percentage` | New calculated field |

---

## 🎯 Quick Start Example

Here's a complete minimal example to get you started:

```javascript
// API service
const stockAPI = {
  getCategories: () => 
    api.get('/stock/hotel-killarney/categories/'),
  
  getItems: (categoryCode = '') => 
    api.get(`/stock/hotel-killarney/items/${categoryCode ? `?category=${categoryCode}` : ''}`),
  
  createItem: (itemData) => 
    api.post('/stock/hotel-killarney/items/', itemData),
  
  getProfitability: (categoryCode = '') =>
    api.get(`/stock/hotel-killarney/items/profitability/${categoryCode ? `?category=${categoryCode}` : ''}`),
  
  comparePeriods: (period1Id, period2Id) =>
    api.get(`/stock/hotel-killarney/periods/compare/?period1=${period1Id}&period2=${period2Id}`)
};

// Usage in component
const StockManagement = () => {
  const [items, setItems] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    stockAPI.getItems(selectedCategory)
      .then(response => setItems(response.data));
  }, [selectedCategory]);

  return (
    <div>
      <CategorySelector 
        value={selectedCategory} 
        onChange={setSelectedCategory} 
      />
      
      <div className="items-grid">
        {items.map(item => (
          <StockItemCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
};
```

---

## 📞 Need Help?

If you encounter issues during migration:
1. Check the `API_ENDPOINTS.md` for complete endpoint documentation
2. Verify your request payloads match the new structure
3. Check browser console for API error messages
4. Ensure category references use codes ("D", "B", etc.) not IDs

---

## ✅ Migration Complete Checklist

- [ ] Updated API service layer with new endpoints
- [ ] Updated state management for new data structure
- [ ] Replaced category IDs with codes throughout
- [ ] Updated forms to use full_units and partial_units
- [ ] Updated display components to show new fields
- [ ] Tested all CRUD operations
- [ ] Implemented period comparison feature
- [ ] Implemented profitability dashboard
- [ ] Implemented low stock alerts
- [ ] Verified all calculated fields display correctly
- [ ] Removed references to deprecated fields
- [ ] Tested with real October 2024 data

---

**Good luck with your migration! 🚀**
