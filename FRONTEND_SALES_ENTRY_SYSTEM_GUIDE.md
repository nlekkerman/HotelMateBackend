# 🛒 Sales Entry System - Frontend Implementation Guide

**Purpose:** Allow staff to manually enter sales data for stock items independently of stocktakes, with the option to link to a stocktake period later.

**Date:** November 10, 2025

---

## 📋 OVERVIEW

### **What This System Does:**
1. ✅ Fetch ALL active stock items from the database (live items, not snapshots)
2. ✅ Allow manual entry of quantities sold for each item
3. ✅ Auto-calculate revenue and COGS based on item prices/costs
4. ✅ Sum up totals for the entire sales session
5. ✅ Save sales records to the database **independently**
6. ✅ **OPTIONAL:** Link/merge sales with a stocktake period **on demand** (user choice)
7. ❌ **NOT included:** Cocktails (separate system)

### **Why Not Use Stocktake Snapshots?**
- Stocktake snapshots are **frozen at a specific date** (end of period)
- Sales entry needs **current, live item data** (current prices, current items)
- Sales can be entered **independently** and saved separately
- **Link to stocktake ONLY when you want to merge** for reporting
- Flexibility to enter sales without completing a full stocktake

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    SALES ENTRY FLOW                         │
└─────────────────────────────────────────────────────────────┘

Step 1: Fetch Live Stock Items
├─ GET /api/stock/<hotel>/items/
└─ Returns ALL active stock items with current prices

Step 2: Manual Entry (Frontend)
├─ User enters quantities sold for each item
├─ Frontend calculates totals in real-time
└─ Displays: revenue, COGS, GP% per item

Step 3: Save Sales Records
├─ POST /api/stock/<hotel>/sales/bulk-create/
├─ Creates Sale records for each item
├─ Can save WITHOUT stocktake (standalone sales)
└─ OR provide stocktake ID to link/merge

Step 4: View/Edit Sales
├─ GET /api/stock/<hotel>/stocktakes/<id>/sales/ (if linked)
├─ GET /api/stock/<hotel>/sales/?date=YYYY-MM-DD (standalone)
└─ Retrieve saved sales
```

---

## 🔌 API ENDPOINTS

### **1. Fetch Active Stock Items**

```
GET /api/stock/<hotel_identifier>/items/
```

**Purpose:** Get all active stock items for sales entry

**Query Parameters:**
- `active=true` - Only active items
- `available_on_menu=true` - Only items currently on menu
- `category=<code>` - Filter by category (D, B, S, W, M)

**Response:**
```json
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "sku": "D001",
      "name": "Guinness Keg",
      "category": {
        "code": "D",
        "name": "Draught Beer"
      },
      "size": "50Lt",
      "uom": 88,
      "unit_cost": 5.68,
      "cost_per_serving": 0.0645,
      "menu_price": 5.50,
      "menu_price_large": null,
      "bottle_price": null,
      "available_on_menu": true,
      "active": true,
      "current_full_units": 6,
      "current_partial_units": 23.5
    },
    {
      "id": 2,
      "sku": "B001",
      "name": "Heineken 330ml Doz",
      "category": {
        "code": "B",
        "name": "Bottled Beer"
      },
      "size": "Doz",
      "uom": 12,
      "unit_cost": 9.60,
      "cost_per_serving": 0.80,
      "menu_price": 4.50,
      "available_on_menu": true,
      "active": true,
      "current_full_units": 0,
      "current_partial_units": 145
    }
  ]
}
```

---

### **2. Bulk Create Sales Records**

```
POST /api/stock/<hotel_identifier>/sales/bulk-create/
```

**Purpose:** Save multiple sales entries at once

**Request Body (Option A - Standalone Sales):**
```json
{
  "sales": [
    {
      "item": 1,
      "quantity": 250.5,
      "sale_date": "2025-11-09"
    },
    {
      "item": 2,
      "quantity": 48,
      "sale_date": "2025-11-09"
    }
  ]
}
```

**Request Body (Option B - Link to Stocktake):**
```json
{
  "sales": [
    {
      "item": 1,
      "stocktake": 10,
      "quantity": 250.5,
      "sale_date": "2025-11-09"
    },
    {
      "item": 2,
      "stocktake": 10,
      "quantity": 48,
      "sale_date": "2025-11-09"
    }
  ]
}
```

**Notes:**
- `item` = StockItem ID (required)
- `stocktake` = Stocktake ID (OPTIONAL - only if you want to merge)
- `quantity` = servings sold (pints, bottles, shots, glasses)
- `sale_date` = date of sale
- `unit_cost` and `unit_price` are auto-fetched from StockItem
- `total_cost` and `total_revenue` are auto-calculated on save

**Response:**
```json
{
  "success": true,
  "created": 3,
  "sales": [
    {
      "id": 101,
      "item": {
        "id": 1,
        "sku": "D001",
        "name": "Guinness Keg"
      },
      "quantity": 250.5,
      "unit_cost": 0.0645,
      "unit_price": 5.50,
      "total_cost": 16.16,
      "total_revenue": 1377.75,
      "gross_profit": 1361.59,
      "gross_profit_percentage": 98.83,
      "sale_date": "2025-11-09"
    }
  ],
  "totals": {
    "total_revenue": 5432.50,
    "total_cogs": 387.25,
    "gross_profit": 5045.25,
    "gp_percentage": 92.87
  }
}
```

---

### **3. Get Sales for a Stocktake**

```
GET /api/stock/<hotel_identifier>/stocktakes/<stocktake_id>/sales/
```

**Purpose:** Retrieve all sales records for a stocktake period

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 101,
      "item": {
        "id": 1,
        "sku": "D001",
        "name": "Guinness Keg",
        "category": "D"
      },
      "quantity": 250.5,
      "unit_cost": 0.0645,
      "unit_price": 5.50,
      "total_cost": 16.16,
      "total_revenue": 1377.75,
      "gross_profit": 1361.59,
      "gross_profit_percentage": 98.83,
      "pour_cost_percentage": 1.17,
      "sale_date": "2025-11-09",
      "created_at": "2025-11-10T10:30:00Z"
    }
  ],
  "summary": {
    "total_items": 3,
    "total_quantity": 311.25,
    "total_revenue": 5432.50,
    "total_cogs": 387.25,
    "gross_profit": 5045.25,
    "gp_percentage": 92.87,
    "pour_cost_percentage": 7.13
  }
}
```

---

### **4. Update Individual Sale**

```
PATCH /api/stock/<hotel_identifier>/stocktakes/<stocktake_id>/sales/<sale_id>/
```

**Request Body:**
```json
{
  "quantity": 260.0,
  "sale_date": "2025-11-09"
}
```

**Response:**
```json
{
  "id": 101,
  "quantity": 260.0,
  "total_cost": 16.77,
  "total_revenue": 1430.00,
  "gross_profit": 1413.23,
  "message": "Sale updated successfully"
}
```

---

### **5. Delete Sale**

```
DELETE /api/stock/<hotel_identifier>/stocktakes/<stocktake_id>/sales/<sale_id>/
```

**Response:**
```json
{
  "success": true,
  "message": "Sale deleted successfully"
}
```

---

## 💻 FRONTEND IMPLEMENTATION

### **Step 1: Fetch Stock Items**

```javascript
// Fetch all active stock items
const fetchStockItems = async (hotelIdentifier) => {
  try {
    const response = await fetch(
      `/api/stock/${hotelIdentifier}/items/?active=true&available_on_menu=true`,
      {
        headers: {
          'Authorization': `Token ${authToken}`,
        }
      }
    );
    
    const data = await response.json();
    return data.results;
  } catch (error) {
    console.error('Error fetching stock items:', error);
    return [];
  }
};
```

---

### **Step 2: Build Sales Entry Form**

```javascript
// Component state
const [stockItems, setStockItems] = useState([]);
const [salesData, setSalesData] = useState({});
const [totals, setTotals] = useState({
  revenue: 0,
  cogs: 0,
  profit: 0,
  gp: 0
});

// Load items on mount
useEffect(() => {
  const loadItems = async () => {
    const items = await fetchStockItems(hotelIdentifier);
    setStockItems(items);
    
    // Initialize sales data
    const initialData = {};
    items.forEach(item => {
      initialData[item.id] = {
        quantity: 0,
        revenue: 0,
        cogs: 0,
        profit: 0
      };
    });
    setSalesData(initialData);
  };
  
  loadItems();
}, [hotelIdentifier]);

// Handle quantity change
const handleQuantityChange = (itemId, quantity) => {
  const item = stockItems.find(i => i.id === itemId);
  const qty = parseFloat(quantity) || 0;
  
  const revenue = qty * item.menu_price;
  const cogs = qty * item.cost_per_serving;
  const profit = revenue - cogs;
  
  setSalesData(prev => ({
    ...prev,
    [itemId]: { quantity: qty, revenue, cogs, profit }
  }));
  
  // Recalculate totals
  calculateTotals();
};

// Calculate totals
const calculateTotals = () => {
  let totalRevenue = 0;
  let totalCogs = 0;
  
  Object.values(salesData).forEach(sale => {
    totalRevenue += sale.revenue;
    totalCogs += sale.cogs;
  });
  
  const profit = totalRevenue - totalCogs;
  const gp = totalRevenue > 0 ? ((profit / totalRevenue) * 100).toFixed(2) : 0;
  
  setTotals({
    revenue: totalRevenue.toFixed(2),
    cogs: totalCogs.toFixed(2),
    profit: profit.toFixed(2),
    gp: gp
  });
};
```

---

### **Step 3: Render Sales Entry Table**

```jsx
<div className="sales-entry-container">
  <h2>Sales Entry</h2>
  
  {/* Filter by category */}
  <select onChange={(e) => filterByCategory(e.target.value)}>
    <option value="">All Categories</option>
    <option value="D">Draught Beer</option>
    <option value="B">Bottled Beer</option>
    <option value="S">Spirits</option>
    <option value="W">Wine</option>
    <option value="M">Minerals</option>
  </select>
  
  <table className="sales-entry-table">
    <thead>
      <tr>
        <th>SKU</th>
        <th>Item Name</th>
        <th>Category</th>
        <th>Menu Price</th>
        <th>Cost/Serving</th>
        <th>Qty Sold</th>
        <th>Revenue</th>
        <th>COGS</th>
        <th>Profit</th>
        <th>GP%</th>
      </tr>
    </thead>
    <tbody>
      {stockItems.map(item => (
        <tr key={item.id}>
          <td>{item.sku}</td>
          <td>{item.name}</td>
          <td>{item.category.name}</td>
          <td>€{item.menu_price}</td>
          <td>€{item.cost_per_serving}</td>
          <td>
            <input
              type="number"
              step="0.25"
              min="0"
              value={salesData[item.id]?.quantity || 0}
              onChange={(e) => handleQuantityChange(item.id, e.target.value)}
              placeholder="0"
            />
          </td>
          <td>€{salesData[item.id]?.revenue.toFixed(2) || '0.00'}</td>
          <td>€{salesData[item.id]?.cogs.toFixed(2) || '0.00'}</td>
          <td>€{salesData[item.id]?.profit.toFixed(2) || '0.00'}</td>
          <td>
            {salesData[item.id]?.revenue > 0 
              ? ((salesData[item.id].profit / salesData[item.id].revenue) * 100).toFixed(2) 
              : '0.00'}%
          </td>
        </tr>
      ))}
    </tbody>
    <tfoot>
      <tr className="totals-row">
        <td colSpan="6"><strong>TOTALS</strong></td>
        <td><strong>€{totals.revenue}</strong></td>
        <td><strong>€{totals.cogs}</strong></td>
        <td><strong>€{totals.profit}</strong></td>
        <td><strong>{totals.gp}%</strong></td>
      </tr>
    </tfoot>
  </table>
  
  {/* Action buttons */}
  <div className="actions">
    <button onClick={() => saveSales(false)} className="btn-primary">
      Save Sales (Standalone)
    </button>
    <button onClick={() => saveSales(true)} className="btn-success">
      Save & Link to Stocktake
    </button>
    <button onClick={resetForm} className="btn-secondary">
      Reset
    </button>
  </div>
  
  {/* Info message */}
  <div className="info">
    <p>💡 <strong>Standalone:</strong> Save sales independently (can link later)</p>
    <p>🔗 <strong>Link to Stocktake:</strong> Merge sales with stocktake immediately</p>
  </div>
</div>
```

---

### **Step 4: Save Sales to Backend**

```javascript
const saveSales = async (linkToStocktake = false) => {
  // Filter out items with zero quantity
  const salesArray = Object.entries(salesData)
    .filter(([itemId, data]) => data.quantity > 0)
    .map(([itemId, data]) => {
      const saleData = {
        item: parseInt(itemId),
        quantity: data.quantity,
        sale_date: selectedDate // e.g., "2025-11-09"
      };
      
      // OPTIONAL: Only add stocktake if user wants to merge
      if (linkToStocktake && stocktakeId) {
        saleData.stocktake = stocktakeId;
      }
      
      return saleData;
    });
  
  if (salesArray.length === 0) {
    alert('No sales entered');
    return;
  }
  
  try {
    const response = await fetch(
      `/api/stock/${hotelIdentifier}/sales/bulk-create/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify({ sales: salesArray })
      }
    );
    
    const result = await response.json();
    
    if (result.success) {
      alert(`✅ ${result.created} sales saved successfully!`);
      console.log('Totals:', result.totals);
      
      // Optionally reset form or navigate away
      resetForm();
    } else {
      alert('Error saving sales');
    }
  } catch (error) {
    console.error('Error saving sales:', error);
    alert('Failed to save sales');
  }
};
```

---

## 🔗 LINKING TO STOCKTAKE (OPTIONAL)

### **Option A: Save Sales Independently (Default)**

Save sales without linking to any stocktake:

```javascript
// Save standalone sales
const response = await fetch(
  `/api/stock/${hotelIdentifier}/sales/bulk-create/`,
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${authToken}`,
    },
    body: JSON.stringify({
      sales: [
        { item: 1, quantity: 250, sale_date: "2025-11-09" },
        { item: 2, quantity: 48, sale_date: "2025-11-09" }
      ]
    })
  }
);

// Sales saved! Can be viewed/edited independently
// No stocktake needed
```

---

### **Option B: Link Sales to Stocktake (On Demand)**

Include `stocktake` field to merge with a stocktake:

```javascript
// Save and link to stocktake
const response = await fetch(
  `/api/stock/${hotelIdentifier}/sales/bulk-create/`,
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${authToken}`,
    },
    body: JSON.stringify({
      sales: [
        { item: 1, stocktake: 10, quantity: 250, sale_date: "2025-11-09" },
        { item: 2, stocktake: 10, quantity: 48, sale_date: "2025-11-09" }
      ]
    })
  }
);

// Sales saved AND linked to stocktake ID 10
// Stocktake totals automatically include these sales
```

---

### **Option C: Link Existing Sales Later**

Update standalone sales to link them to a stocktake:

```javascript
// Update sale to add stocktake link
await fetch(
  `/api/stock/${hotelIdentifier}/stocktakes/${stocktakeId}/sales/${saleId}/`,
  {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${authToken}`,
    },
    body: JSON.stringify({ stocktake: stocktakeId })
  }
);

// Sale now linked to stocktake
```

---

## 📊 MERGING WITH STOCKTAKE SNAPSHOTS

### **Scenario: Use Both Live Sales + Stocktake Snapshots**

If you want to use stocktake snapshots for **inventory verification** but live sales for **revenue**:

```javascript
// 1. Complete physical stocktake (creates snapshots)
const stocktake = await getStocktake(stocktakeId);
console.log('Closing stock:', stocktake.lines);

// 2. Enter sales manually using live items
await bulkCreateSales(stocktake.id, salesData);

// 3. View combined report
const report = {
  period: stocktake.period_name,
  inventory: {
    opening_value: calculateOpeningValue(stocktake.lines),
    closing_value: calculateClosingValue(stocktake.lines),
    purchases: calculatePurchases(stocktake.lines),
    waste: calculateWaste(stocktake.lines)
  },
  sales: {
    revenue: stocktake.total_revenue,
    cogs: stocktake.total_cogs,
    gp: stocktake.gross_profit_percentage
  }
};
```

---

## ⚠️ IMPORTANT NOTES

### **1. Sales vs Stocktake Snapshots**

| Feature | Live Items (Sales Entry) | Stocktake Snapshots |
|---------|-------------------------|---------------------|
| **Data Source** | Current `StockItem` table | Frozen `StockSnapshot` |
| **Prices** | Current menu prices | Frozen at period end |
| **Items** | All active items | Only items in stocktake |
| **Purpose** | Enter sales | Verify inventory |
| **Flexibility** | Can add/edit anytime | Locked when approved |

### **2. When to Use Each**

**Use Live Items (Sales Entry) when:**
- ✅ Entering daily/weekly sales
- ✅ Need current prices
- ✅ Want to enter sales without full stocktake
- ✅ Quick sales reporting

**Use Stocktake Snapshots when:**
- ✅ Doing full inventory count
- ✅ Need historical prices (as of period end)
- ✅ Calculating variances (expected vs actual)
- ✅ Period is closed/locked

### **3. Cocktails**

**Not included in this system.**  
Cocktails use `CocktailConsumption` model and are tracked separately.  
For now, focus on stock items only.

---

## 🎯 WORKFLOW EXAMPLE

### **Workflow A: Independent Sales Entry**

```
Day 1-30: Staff enter sales daily
├─ Fetch active items
├─ Enter quantities sold
├─ Save standalone (NO stocktake link)
└─ Repeat daily

End of Month: Decide to Merge
├─ Review standalone sales
├─ Create stocktake
├─ OPTIONAL: Link sales to stocktake
├─ Approve stocktake
└─ Generate reports
```

### **Workflow B: Direct Stocktake Integration**

```
End of Month: Create stocktake first
├─ Create stocktake draft
├─ Enter sales with stocktake ID
├─ Sales automatically merge
├─ Physical inventory count
├─ Approve stocktake
└─ Done
```

---

## 🔧 TROUBLESHOOTING

### **Q: What if item prices change during the month?**
A: Sales are saved with the price **at the time of sale**. The `unit_price` is frozen when the Sale record is created.

### **Q: Can I edit sales after saving?**
A: Yes, use the PATCH endpoint to update individual sales.

### **Q: What if I don't have a stocktake yet?**
A: No problem! Save sales as **standalone** (without stocktake field). You can link them to a stocktake later, or keep them independent for reporting.

### **Q: How do I handle returns/refunds?**
A: Enter negative quantities for returns. Example: `-5.0` for 5 returned items.

---

## 📝 NEXT STEPS

1. ✅ Implement sales entry form on frontend
2. ✅ Test bulk create endpoint
3. ✅ Add category filtering
4. ✅ Add search functionality
5. ✅ Implement edit/delete for individual sales
6. ⏭️ Add cocktails integration (future)

---

**END OF GUIDE**
