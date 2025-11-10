# Frontend Sales Entry Integration Guide

## Overview
This guide explains how to integrate sales data entry into the frontend stocktake interface. The backend is fully prepared with all necessary endpoints - you just need to add the UI components.

---

## Architecture Summary

### 📊 Data Flow
```
Physical Count (Stocktake) ──┬─→ Variance Calculation
                             │   (Physical vs Expected)
                             │
Sales Data Entry ────────────┴─→ Profitability Metrics
                                 (GP%, Pour Cost%)
```

### ✅ Key Points
1. **Sales NOT in variance** - Variance shows physical loss/gain only (theft, waste, errors)
2. **Sales for profitability** - Used to calculate GP%, Pour Cost%, Revenue
3. **Three entry methods** - Itemized sales, line-level manual, period-level manual
4. **Flexible priority** - Backend uses 3-tier fallback system

---

## Backend Endpoints (Already Built) ✅

### Base URL Pattern
```
/api/stock-tracker/{hotel_identifier}/sales/
```

### 1. List Sales (GET)
**Endpoint:** `GET /api/stock-tracker/{hotel}/sales/`

**Query Parameters:**
- `stocktake={id}` - Filter by stocktake
- `item={id}` - Filter by item
- `category={code}` - Filter by category (D, B, S, W, M)
- `start_date={YYYY-MM-DD}` - Filter by date range
- `end_date={YYYY-MM-DD}` - Filter by date range

**Example Request:**
```javascript
// Get all sales for a specific stocktake
GET /api/stock-tracker/myhotel/sales/?stocktake=5

// Get sales for specific item in stocktake
GET /api/stock-tracker/myhotel/sales/?stocktake=5&item=123
```

**Response:**
```json
[
  {
    "id": 1,
    "stocktake": 5,
    "stocktake_period": "2024-11-01 to 2024-11-30",
    "item": 123,
    "item_sku": "D001",
    "item_name": "Guinness Draught 50L Keg",
    "category_code": "D",
    "category_name": "Draught Beer",
    "quantity": "350.0000",
    "unit_cost": "0.2214",
    "unit_price": "7.00",
    "total_cost": "77.49",
    "total_revenue": "2450.00",
    "gross_profit": "2372.51",
    "gross_profit_percentage": "96.84",
    "pour_cost_percentage": "3.16",
    "sale_date": "2024-11-10",
    "notes": "",
    "created_by": 1,
    "created_by_name": "John Manager",
    "created_at": "2024-11-10T14:30:00Z",
    "updated_at": "2024-11-10T14:30:00Z"
  }
]
```

---

### 2. Create Sale (POST)
**Endpoint:** `POST /api/stock-tracker/{hotel}/sales/`

**Request Body:**
```json
{
  "stocktake": 5,
  "item": 123,
  "quantity": "350.0000",
  "unit_cost": "0.2214",
  "unit_price": "7.00",
  "sale_date": "2024-11-10",
  "notes": "Weekend sales"
}
```

**Required Fields:**
- `stocktake` - Stocktake ID
- `item` - Item ID
- `quantity` - Quantity sold (in servings: pints, bottles, shots, glasses)
- `unit_cost` - Cost per serving at time of sale
- `sale_date` - Date of sale (YYYY-MM-DD)

**Optional Fields:**
- `unit_price` - Selling price per serving (for revenue calculation)
- `notes` - Additional notes

**Auto-calculated:**
- `total_cost` = quantity × unit_cost
- `total_revenue` = quantity × unit_price
- `gross_profit` = total_revenue - total_cost
- `gross_profit_percentage` = (gross_profit / total_revenue) × 100
- `pour_cost_percentage` = (total_cost / total_revenue) × 100
- `created_by` - Set from authenticated user

**Response:** Same as GET (single sale object)

---

### 3. Update Sale (PUT/PATCH)
**Endpoint:** `PUT /api/stock-tracker/{hotel}/sales/{id}/`

**Request Body:** Same as POST (all or partial fields)

---

### 4. Delete Sale (DELETE)
**Endpoint:** `DELETE /api/stock-tracker/{hotel}/sales/{id}/`

**Response:** `204 No Content`

---

### 5. Sales Summary (GET)
**Endpoint:** `GET /api/stock-tracker/{hotel}/sales/summary/?stocktake={id}`

**Query Parameters:**
- `stocktake={id}` - **Required**

**Response:**
```json
{
  "stocktake_id": 5,
  "by_category": [
    {
      "item__category__code": "D",
      "item__category__name": "Draught Beer",
      "total_quantity": "1250.0000",
      "total_cost": "276.75",
      "total_revenue": "8750.00",
      "sale_count": 15
    },
    {
      "item__category__code": "B",
      "item__category__name": "Bottled Beer",
      "total_quantity": "450.0000",
      "total_cost": "675.00",
      "total_revenue": "1800.00",
      "sale_count": 8
    }
  ],
  "overall": {
    "total_quantity": "1700.0000",
    "total_cost": "951.75",
    "total_revenue": "10550.00",
    "sale_count": 23,
    "gross_profit": "9598.25",
    "gross_profit_percentage": "90.98"
  }
}
```

---

### 6. Bulk Create Sales (POST)
**Endpoint:** `POST /api/stock-tracker/{hotel}/sales/bulk_create/`

**Request Body:**
```json
{
  "sales": [
    {
      "stocktake": 5,
      "item": 123,
      "quantity": "350.0000",
      "unit_cost": "0.2214",
      "unit_price": "7.00",
      "sale_date": "2024-11-10"
    },
    {
      "stocktake": 5,
      "item": 124,
      "quantity": "200.0000",
      "unit_cost": "1.50",
      "unit_price": "4.00",
      "sale_date": "2024-11-10"
    }
  ]
}
```

**Response:**
```json
{
  "message": "All sales created successfully",
  "created_count": 2,
  "sales": [/* array of created sales */]
}
```

**Partial Success (207 Multi-Status):**
```json
{
  "message": "Some sales failed to create",
  "created_count": 1,
  "errors": [
    {
      "index": 1,
      "errors": {
        "quantity": ["This field is required"]
      }
    }
  ]
}
```

---

## Frontend Implementation

### 🎨 UI Components to Add

#### 1. Sales Entry Button on Stocktake Line

**Location:** Each stocktake line row (next to counted quantity input)

**Component Structure:**
```jsx
<StocktakeLine>
  {/* Existing fields: Opening, Purchases, Waste, Expected, Counted, Variance */}
  
  <div className="sales-section">
    <button 
      onClick={() => openSalesModal(line.item)}
      className="btn-sales"
    >
      📊 Enter Sales
    </button>
    
    {/* Display current sales total */}
    <div className="sales-summary">
      {line.sales_total && (
        <span>
          Sales: {line.sales_total.quantity} servings 
          (€{line.sales_total.revenue})
        </span>
      )}
    </div>
  </div>
</StocktakeLine>
```

---

#### 2. Sales Entry Modal

**Component:** `SalesEntryModal.jsx`

```jsx
import React, { useState, useEffect } from 'react';

const SalesEntryModal = ({ 
  isOpen, 
  onClose, 
  item, 
  stocktakeId, 
  hotelIdentifier 
}) => {
  const [formData, setFormData] = useState({
    quantity: '',
    unit_price: item.menu_price || '', // Pre-fill from item
    sale_date: new Date().toISOString().split('T')[0],
    notes: ''
  });
  
  const [existingSales, setExistingSales] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch existing sales for this item
  useEffect(() => {
    if (isOpen) {
      fetchExistingSales();
    }
  }, [isOpen, item.id, stocktakeId]);

  const fetchExistingSales = async () => {
    try {
      const response = await fetch(
        `/api/stock-tracker/${hotelIdentifier}/sales/?stocktake=${stocktakeId}&item=${item.id}`
      );
      const data = await response.json();
      setExistingSales(data);
    } catch (error) {
      console.error('Error fetching sales:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(
        `/api/stock-tracker/${hotelIdentifier}/sales/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            stocktake: stocktakeId,
            item: item.id,
            quantity: formData.quantity,
            unit_cost: item.cost_per_serving, // From item
            unit_price: formData.unit_price,
            sale_date: formData.sale_date,
            notes: formData.notes
          })
        }
      );

      if (response.ok) {
        // Success - refresh list and close
        await fetchExistingSales();
        setFormData({
          quantity: '',
          unit_price: item.menu_price || '',
          sale_date: new Date().toISOString().split('T')[0],
          notes: ''
        });
        onClose();
      } else {
        const error = await response.json();
        alert(`Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error creating sale:', error);
      alert('Failed to create sale');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (saleId) => {
    if (!confirm('Delete this sale record?')) return;

    try {
      const response = await fetch(
        `/api/stock-tracker/${hotelIdentifier}/sales/${saleId}/`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        }
      );

      if (response.ok) {
        await fetchExistingSales();
      }
    } catch (error) {
      console.error('Error deleting sale:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content sales-modal">
        <h2>Sales Entry: {item.name}</h2>
        <p className="item-details">
          SKU: {item.sku} | Category: {item.category_name}
        </p>

        {/* Existing Sales List */}
        <div className="existing-sales">
          <h3>Existing Sales</h3>
          {existingSales.length === 0 ? (
            <p className="empty-state">No sales recorded yet</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Quantity</th>
                  <th>Unit Price</th>
                  <th>Revenue</th>
                  <th>GP%</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {existingSales.map(sale => (
                  <tr key={sale.id}>
                    <td>{sale.sale_date}</td>
                    <td>{parseFloat(sale.quantity).toFixed(2)} {item.serving_unit}</td>
                    <td>€{parseFloat(sale.unit_price).toFixed(2)}</td>
                    <td>€{parseFloat(sale.total_revenue).toFixed(2)}</td>
                    <td>{parseFloat(sale.gross_profit_percentage).toFixed(1)}%</td>
                    <td>
                      <button 
                        onClick={() => handleDelete(sale.id)}
                        className="btn-delete"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="totals">
                  <td>Total:</td>
                  <td>
                    {existingSales.reduce((sum, s) => 
                      sum + parseFloat(s.quantity), 0
                    ).toFixed(2)}
                  </td>
                  <td>-</td>
                  <td>
                    €{existingSales.reduce((sum, s) => 
                      sum + parseFloat(s.total_revenue), 0
                    ).toFixed(2)}
                  </td>
                  <td>-</td>
                  <td>-</td>
                </tr>
              </tfoot>
            </table>
          )}
        </div>

        {/* New Sale Form */}
        <form onSubmit={handleSubmit} className="sale-form">
          <h3>Add New Sale</h3>
          
          <div className="form-group">
            <label>Quantity Sold *</label>
            <input
              type="number"
              step="0.01"
              value={formData.quantity}
              onChange={(e) => setFormData({...formData, quantity: e.target.value})}
              placeholder={`Servings (${item.serving_unit})`}
              required
            />
            <small>Enter quantity in {item.serving_unit} (pints, bottles, shots, glasses)</small>
          </div>

          <div className="form-group">
            <label>Unit Price</label>
            <input
              type="number"
              step="0.01"
              value={formData.unit_price}
              onChange={(e) => setFormData({...formData, unit_price: e.target.value})}
              placeholder="€0.00"
            />
            <small>Current menu price: €{item.menu_price || 'N/A'}</small>
          </div>

          <div className="form-group">
            <label>Sale Date *</label>
            <input
              type="date"
              value={formData.sale_date}
              onChange={(e) => setFormData({...formData, sale_date: e.target.value})}
              required
            />
          </div>

          <div className="form-group">
            <label>Notes (Optional)</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              placeholder="Additional notes..."
              rows="2"
            />
          </div>

          {/* Preview Calculation */}
          {formData.quantity && formData.unit_price && (
            <div className="calculation-preview">
              <h4>Preview:</h4>
              <p>Total Revenue: €{(parseFloat(formData.quantity) * parseFloat(formData.unit_price)).toFixed(2)}</p>
              <p>Total Cost: €{(parseFloat(formData.quantity) * parseFloat(item.cost_per_serving)).toFixed(2)}</p>
              <p>
                Gross Profit: €{(
                  (parseFloat(formData.quantity) * parseFloat(formData.unit_price)) - 
                  (parseFloat(formData.quantity) * parseFloat(item.cost_per_serving))
                ).toFixed(2)}
              </p>
            </div>
          )}

          <div className="modal-actions">
            <button 
              type="button" 
              onClick={onClose}
              className="btn-cancel"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn-submit"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Sale'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SalesEntryModal;
```

---

#### 3. Stocktake Summary with Sales

**Location:** Top of stocktake page

```jsx
const StocktakeSummary = ({ stocktakeId, hotelIdentifier }) => {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchSummary();
  }, [stocktakeId]);

  const fetchSummary = async () => {
    try {
      const response = await fetch(
        `/api/stock-tracker/${hotelIdentifier}/sales/summary/?stocktake=${stocktakeId}`
      );
      const data = await response.json();
      setSummary(data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  if (!summary) return <div>Loading...</div>;

  return (
    <div className="stocktake-summary">
      <h2>Sales Summary</h2>
      
      <div className="overall-metrics">
        <div className="metric">
          <span className="label">Total Revenue:</span>
          <span className="value">€{parseFloat(summary.overall.total_revenue || 0).toFixed(2)}</span>
        </div>
        <div className="metric">
          <span className="label">Total COGS:</span>
          <span className="value">€{parseFloat(summary.overall.total_cost || 0).toFixed(2)}</span>
        </div>
        <div className="metric">
          <span className="label">Gross Profit:</span>
          <span className="value">€{parseFloat(summary.overall.gross_profit || 0).toFixed(2)}</span>
        </div>
        <div className="metric">
          <span className="label">GP%:</span>
          <span className="value">{parseFloat(summary.overall.gross_profit_percentage || 0).toFixed(1)}%</span>
        </div>
        <div className="metric">
          <span className="label">Sales Records:</span>
          <span className="value">{summary.overall.sale_count}</span>
        </div>
      </div>

      <div className="category-breakdown">
        <h3>By Category</h3>
        <table>
          <thead>
            <tr>
              <th>Category</th>
              <th>Quantity Sold</th>
              <th>Revenue</th>
              <th>COGS</th>
              <th>Records</th>
            </tr>
          </thead>
          <tbody>
            {summary.by_category.map(cat => (
              <tr key={cat.item__category__code}>
                <td>{cat.item__category__name}</td>
                <td>{parseFloat(cat.total_quantity).toFixed(2)}</td>
                <td>€{parseFloat(cat.total_revenue || 0).toFixed(2)}</td>
                <td>€{parseFloat(cat.total_cost || 0).toFixed(2)}</td>
                <td>{cat.sale_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
```

---

## Data Fetching Strategy

### 1. Load Stocktake with Sales Data
```javascript
const fetchStocktakeWithSales = async (stocktakeId) => {
  try {
    // Fetch stocktake details
    const stocktakeResponse = await fetch(
      `/api/stock-tracker/${hotelIdentifier}/stocktakes/${stocktakeId}/`
    );
    const stocktake = await stocktakeResponse.json();

    // Fetch all sales for this stocktake
    const salesResponse = await fetch(
      `/api/stock-tracker/${hotelIdentifier}/sales/?stocktake=${stocktakeId}`
    );
    const sales = await salesResponse.json();

    // Group sales by item for easy lookup
    const salesByItem = sales.reduce((acc, sale) => {
      if (!acc[sale.item]) {
        acc[sale.item] = [];
      }
      acc[sale.item].push(sale);
      return acc;
    }, {});

    // Enhance stocktake lines with sales data
    const enhancedLines = stocktake.lines.map(line => ({
      ...line,
      sales: salesByItem[line.item] || [],
      sales_total: calculateSalesTotal(salesByItem[line.item] || [])
    }));

    return {
      ...stocktake,
      lines: enhancedLines
    };
  } catch (error) {
    console.error('Error fetching stocktake:', error);
    throw error;
  }
};

const calculateSalesTotal = (sales) => {
  if (sales.length === 0) return null;
  
  return {
    quantity: sales.reduce((sum, s) => sum + parseFloat(s.quantity), 0),
    revenue: sales.reduce((sum, s) => sum + parseFloat(s.total_revenue || 0), 0),
    cost: sales.reduce((sum, s) => sum + parseFloat(s.total_cost || 0), 0),
    count: sales.length
  };
};
```

---

## Manual Entry Alternative

For simpler deployments, you can skip itemized sales and use manual entry:

### Period-Level Manual Entry
```jsx
const PeriodManualSalesEntry = ({ periodId, hotelIdentifier }) => {
  const [period, setPeriod] = useState(null);
  const [manualSales, setManualSales] = useState('');
  const [manualPurchases, setManualPurchases] = useState('');

  const handleSave = async () => {
    try {
      const response = await fetch(
        `/api/stock-tracker/${hotelIdentifier}/periods/${periodId}/`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            manual_sales_amount: manualSales,
            manual_purchases_amount: manualPurchases
          })
        }
      );

      if (response.ok) {
        alert('Manual values saved successfully');
      }
    } catch (error) {
      console.error('Error saving manual values:', error);
    }
  };

  return (
    <div className="manual-entry-form">
      <h3>Manual Period Totals</h3>
      <p>Use this if you don't have itemized sales data</p>
      
      <div className="form-group">
        <label>Total Sales Revenue</label>
        <input
          type="number"
          step="0.01"
          value={manualSales}
          onChange={(e) => setManualSales(e.target.value)}
          placeholder="€0.00"
        />
      </div>

      <div className="form-group">
        <label>Total Purchase Costs (COGS)</label>
        <input
          type="number"
          step="0.01"
          value={manualPurchases}
          onChange={(e) => setManualPurchases(e.target.value)}
          placeholder="€0.00"
        />
      </div>

      <button onClick={handleSave} className="btn-save">
        Save Manual Totals
      </button>
    </div>
  );
};
```

---

## Testing Checklist

### ✅ Basic Functionality
- [ ] Sales entry modal opens from stocktake line
- [ ] Form validates required fields (quantity, sale_date)
- [ ] Unit price pre-fills from item.menu_price
- [ ] Sale creates successfully via POST endpoint
- [ ] Created sale appears in list immediately
- [ ] Sales summary calculates correctly
- [ ] Delete sale works and updates totals

### ✅ Data Accuracy
- [ ] Total revenue = quantity × unit_price
- [ ] Total cost = quantity × unit_cost
- [ ] GP% = ((revenue - cost) / revenue) × 100
- [ ] Pour cost% = (cost / revenue) × 100
- [ ] Stocktake profitability metrics update with sales

### ✅ Edge Cases
- [ ] Handle no sales (show empty state)
- [ ] Handle missing unit_price (revenue = null)
- [ ] Handle locked stocktakes (disable entry)
- [ ] Handle network errors gracefully
- [ ] Validate date is within stocktake period

---

## Styling Recommendations

```css
/* Sales Section on Stocktake Line */
.sales-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.btn-sales {
  padding: 0.5rem 1rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-sales:hover {
  background: #218838;
}

.sales-summary {
  font-size: 0.9rem;
  color: #6c757d;
}

/* Sales Modal */
.sales-modal {
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.existing-sales table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.existing-sales th,
.existing-sales td {
  padding: 0.5rem;
  border: 1px solid #dee2e6;
  text-align: left;
}

.existing-sales th {
  background: #f8f9fa;
  font-weight: 600;
}

.existing-sales tfoot {
  background: #e9ecef;
  font-weight: 600;
}

.calculation-preview {
  padding: 1rem;
  background: #e7f3ff;
  border-radius: 4px;
  margin: 1rem 0;
}

.calculation-preview h4 {
  margin: 0 0 0.5rem 0;
}

.calculation-preview p {
  margin: 0.25rem 0;
  font-weight: 500;
}
```

---

## Backend Priority System (For Reference)

The backend uses this priority for calculating revenue/COGS:

### Revenue Calculation Priority:
1. ✅ **Line-level manual** (`StocktakeLine.manual_sales_value`)
2. ✅ **Period-level manual** (`StockPeriod.manual_sales_amount`)
3. ✅ **Itemized sales** (Sum of `Sale.total_revenue`)

### COGS Calculation Priority:
1. ✅ **Period-level manual** (`StockPeriod.manual_purchases_amount`)
2. ✅ **Line-level manual** (`StocktakeLine.manual_purchases_value + manual_waste_value`)
3. ✅ **Itemized sales** (Sum of `Sale.total_cost`)

**This means:** If any manual values exist, they override itemized sales. This gives you flexibility for historical data or quick estimates.

---

## Questions?

If you need clarification on:
- API authentication
- Error handling patterns
- State management integration
- Pusher real-time updates for sales

Just ask! The backend is fully prepared and tested. You only need to build the UI components.
