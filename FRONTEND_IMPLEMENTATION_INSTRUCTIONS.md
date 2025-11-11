# Frontend Implementation Instructions - Sales Analysis System

## 🎯 Quick Start Guide

This document explains **step-by-step** how to implement the new sales analysis features in your frontend application.

---

## 📋 Table of Contents

1. [Setup & Configuration](#1-setup--configuration)
2. [Display Individual Sales](#2-display-individual-sales)
3. [Create New Sales](#3-create-new-sales)
4. [Display Sales Analysis Dashboard](#4-display-sales-analysis-dashboard)
5. [Display Category Breakdown](#5-display-category-breakdown)
6. [Display KPI Dashboard with Cocktails](#6-display-kpi-dashboard-with-cocktails)
7. [Complete Component Examples](#7-complete-component-examples)

---

## 1. Setup & Configuration

### Prerequisites

```bash
# Install required packages
npm install axios recharts
# or
yarn add axios recharts
```

### API Base URL Configuration

```javascript
// src/config/api.js
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Helper to build API URLs
export const buildApiUrl = (hotelSlug, path) => {
  return `${API_BASE_URL}/api/stock/${hotelSlug}${path}`;
};

// Example usage:
// buildApiUrl('myhotel', '/periods/42/sales-analysis/')
// Returns: http://localhost:8000/api/stock/myhotel/periods/42/sales-analysis/
```

---

## 2. Display Individual Sales

### Step 2.1: Create Sales Service

```javascript
// src/services/salesService.js
import axios from 'axios';
import { buildApiUrl } from '../config/api';

export const salesService = {
  /**
   * Get all sales for a stocktake
   * @param {string} hotelSlug - Hotel identifier
   * @param {number} stocktakeId - Stocktake ID
   * @returns {Promise<Array>} Array of sales
   */
  async getSales(hotelSlug, stocktakeId) {
    const url = buildApiUrl(hotelSlug, '/sales/');
    const response = await axios.get(url, {
      params: { stocktake: stocktakeId }
    });
    return response.data;
  },

  /**
   * Get sales filtered by category
   * @param {string} hotelSlug - Hotel identifier
   * @param {number} stocktakeId - Stocktake ID
   * @param {string} categoryCode - D, B, S, W, or M
   * @returns {Promise<Array>} Filtered sales
   */
  async getSalesByCategory(hotelSlug, stocktakeId, categoryCode) {
    const url = buildApiUrl(hotelSlug, '/sales/');
    const response = await axios.get(url, {
      params: { 
        stocktake: stocktakeId,
        category: categoryCode
      }
    });
    return response.data;
  }
};
```

### Step 2.2: Create Sales List Component

```jsx
// src/components/Sales/SalesList.jsx
import React, { useState, useEffect } from 'react';
import { salesService } from '../../services/salesService';
import './SalesList.css';

function SalesList({ hotelSlug, stocktakeId }) {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Fetch sales
  useEffect(() => {
    const fetchSales = async () => {
      setLoading(true);
      setError(null);
      
      try {
        let data;
        if (selectedCategory === 'all') {
          data = await salesService.getSales(hotelSlug, stocktakeId);
        } else {
          data = await salesService.getSalesByCategory(
            hotelSlug, 
            stocktakeId, 
            selectedCategory
          );
        }
        setSales(data);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch sales:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSales();
  }, [hotelSlug, stocktakeId, selectedCategory]);

  // Calculate totals
  const totals = sales.reduce((acc, sale) => ({
    revenue: acc.revenue + parseFloat(sale.total_revenue || 0),
    cost: acc.cost + parseFloat(sale.total_cost || 0),
    profit: acc.profit + parseFloat(sale.gross_profit || 0),
    quantity: acc.quantity + parseFloat(sale.quantity || 0)
  }), { revenue: 0, cost: 0, profit: 0, quantity: 0 });

  if (loading) return <div className="loading">Loading sales...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="sales-list">
      <div className="sales-header">
        <h2>Sales Records</h2>
        
        {/* Category Filter */}
        <div className="filters">
          <label>Category:</label>
          <select 
            value={selectedCategory} 
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories</option>
            <option value="D">Draught</option>
            <option value="B">Bottled</option>
            <option value="S">Spirits</option>
            <option value="W">Wine</option>
            <option value="M">Miscellaneous</option>
          </select>
        </div>
      </div>

      <table className="sales-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Item</th>
            <th>Category</th>
            <th>Quantity</th>
            <th>Unit Price</th>
            <th>Revenue</th>
            <th>Cost</th>
            <th>Profit</th>
            <th>GP%</th>
          </tr>
        </thead>
        <tbody>
          {sales.map(sale => (
            <tr key={sale.id}>
              <td>{new Date(sale.sale_date).toLocaleDateString()}</td>
              <td>
                <strong>{sale.item_name}</strong>
                <br />
                <small>{sale.item_sku}</small>
              </td>
              <td>
                <span className={`category-badge ${sale.category_code}`}>
                  {sale.category_name}
                </span>
              </td>
              <td className="number">{parseFloat(sale.quantity).toFixed(0)}</td>
              <td className="number">€{parseFloat(sale.unit_price).toFixed(2)}</td>
              <td className="number">€{parseFloat(sale.total_revenue).toFixed(2)}</td>
              <td className="number">€{parseFloat(sale.total_cost).toFixed(2)}</td>
              <td className="number profit">€{parseFloat(sale.gross_profit).toFixed(2)}</td>
              <td className="number">{parseFloat(sale.gross_profit_percentage).toFixed(2)}%</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="totals-row">
            <th colSpan="3">Total</th>
            <th className="number">{totals.quantity.toFixed(0)}</th>
            <th>-</th>
            <th className="number">€{totals.revenue.toFixed(2)}</th>
            <th className="number">€{totals.cost.toFixed(2)}</th>
            <th className="number profit">€{totals.profit.toFixed(2)}</th>
            <th className="number">
              {totals.revenue > 0 
                ? ((totals.profit / totals.revenue) * 100).toFixed(2) 
                : 0}%
            </th>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

export default SalesList;
```

### Step 2.3: Add Styling

```css
/* src/components/Sales/SalesList.css */
.sales-list {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.sales-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.filters select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.sales-table {
  width: 100%;
  border-collapse: collapse;
}

.sales-table th,
.sales-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.sales-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.sales-table .number {
  text-align: right;
}

.sales-table .profit {
  color: #28a745;
  font-weight: 600;
}

.category-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.category-badge.D { background: #e3f2fd; color: #1976d2; }
.category-badge.B { background: #fff3e0; color: #f57c00; }
.category-badge.S { background: #fce4ec; color: #c2185b; }
.category-badge.W { background: #f3e5f5; color: #7b1fa2; }
.category-badge.M { background: #e0f2f1; color: #00796b; }

.totals-row {
  background: #f8f9fa;
  font-weight: 600;
}
```

---

## 3. Create New Sales

### Step 3.1: Create Sales Form Service

```javascript
// src/services/salesService.js (add to existing)
export const salesService = {
  // ... existing methods ...

  /**
   * Create multiple sales at once (bulk create)
   * @param {string} hotelSlug - Hotel identifier
   * @param {number} stocktakeId - Stocktake ID
   * @param {Array} salesData - Array of sale objects
   * @returns {Promise<Object>} Result with created count
   */
  async bulkCreateSales(hotelSlug, stocktakeId, salesData) {
    const url = buildApiUrl(hotelSlug, '/sales/bulk-create/');
    const response = await axios.post(url, {
      stocktake_id: stocktakeId,
      sales: salesData
    });
    return response.data;
  }
};
```

### Step 3.2: Create Sales Entry Form

```jsx
// src/components/Sales/SalesEntryForm.jsx
import React, { useState, useEffect } from 'react';
import { salesService } from '../../services/salesService';
import { stockItemsService } from '../../services/stockItemsService';
import './SalesEntryForm.css';

function SalesEntryForm({ hotelSlug, stocktakeId, onSalesCreated }) {
  const [stockItems, setStockItems] = useState([]);
  const [salesEntries, setSalesEntries] = useState([
    { item: '', quantity: '', sale_date: new Date().toISOString().split('T')[0] }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch stock items on mount
  useEffect(() => {
    const fetchStockItems = async () => {
      try {
        const items = await stockItemsService.getStockItems(hotelSlug);
        setStockItems(items);
      } catch (err) {
        console.error('Failed to fetch stock items:', err);
      }
    };
    fetchStockItems();
  }, [hotelSlug]);

  // Add new row
  const addRow = () => {
    setSalesEntries([
      ...salesEntries,
      { item: '', quantity: '', sale_date: new Date().toISOString().split('T')[0] }
    ]);
  };

  // Remove row
  const removeRow = (index) => {
    setSalesEntries(salesEntries.filter((_, i) => i !== index));
  };

  // Update row
  const updateRow = (index, field, value) => {
    const updated = [...salesEntries];
    updated[index][field] = value;
    setSalesEntries(updated);
  };

  // Submit sales
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Filter out empty rows
      const validSales = salesEntries.filter(
        entry => entry.item && entry.quantity
      );

      if (validSales.length === 0) {
        throw new Error('Please add at least one sale');
      }

      // Convert item to integer, quantity to number
      const salesData = validSales.map(entry => ({
        item: parseInt(entry.item),
        quantity: parseFloat(entry.quantity),
        sale_date: entry.sale_date
        // Note: unit_cost and unit_price are AUTO-POPULATED by backend
      }));

      const result = await salesService.bulkCreateSales(
        hotelSlug,
        stocktakeId,
        salesData
      );

      alert(`Successfully created ${result.created_count} sales!`);
      
      // Reset form
      setSalesEntries([
        { item: '', quantity: '', sale_date: new Date().toISOString().split('T')[0] }
      ]);

      // Callback to parent
      if (onSalesCreated) {
        onSalesCreated(result);
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      console.error('Failed to create sales:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sales-entry-form">
      <h3>Enter Sales</h3>
      
      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit}>
        <table className="entry-table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Quantity</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {salesEntries.map((entry, index) => (
              <tr key={index}>
                <td>
                  <select
                    value={entry.item}
                    onChange={(e) => updateRow(index, 'item', e.target.value)}
                    required
                  >
                    <option value="">Select item...</option>
                    {stockItems.map(item => (
                      <option key={item.id} value={item.id}>
                        {item.name} - {item.category_name} (€{item.menu_price})
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    value={entry.quantity}
                    onChange={(e) => updateRow(index, 'quantity', e.target.value)}
                    placeholder="Quantity"
                    min="0"
                    step="1"
                    required
                  />
                </td>
                <td>
                  <input
                    type="date"
                    value={entry.sale_date}
                    onChange={(e) => updateRow(index, 'sale_date', e.target.value)}
                    required
                  />
                </td>
                <td>
                  {salesEntries.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRow(index)}
                      className="btn-remove"
                    >
                      Remove
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="form-actions">
          <button type="button" onClick={addRow} className="btn-secondary">
            Add Another Row
          </button>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Saving...' : 'Save Sales'}
          </button>
        </div>
      </form>

      <div className="info-note">
        <strong>Note:</strong> Unit cost and price are automatically fetched from stock items.
        You only need to enter item and quantity.
      </div>
    </div>
  );
}

export default SalesEntryForm;
```

---

## 4. Display Sales Analysis Dashboard

### Step 4.1: Create Analysis Service

```javascript
// src/services/salesAnalysisService.js
import axios from 'axios';
import { buildApiUrl } from '../config/api';

export const salesAnalysisService = {
  /**
   * Get sales analysis for a period (Stock Items + Cocktails)
   * @param {string} hotelSlug - Hotel identifier
   * @param {number} periodId - Period ID
   * @param {boolean} includeCocktails - Include cocktail data
   * @param {boolean} includeCategoryBreakdown - Include category breakdown
   * @returns {Promise<Object>} Sales analysis data
   */
  async getSalesAnalysis(
    hotelSlug, 
    periodId, 
    includeCocktails = true, 
    includeCategoryBreakdown = true
  ) {
    const url = buildApiUrl(hotelSlug, `/periods/${periodId}/sales-analysis/`);
    const response = await axios.get(url, {
      params: {
        include_cocktails: includeCocktails,
        include_category_breakdown: includeCategoryBreakdown
      }
    });
    return response.data;
  }
};
```

### Step 4.2: Create Analysis Dashboard Component

```jsx
// src/components/Sales/SalesAnalysisDashboard.jsx
import React, { useState, useEffect } from 'react';
import { salesAnalysisService } from '../../services/salesAnalysisService';
import './SalesAnalysisDashboard.css';

function SalesAnalysisDashboard({ hotelSlug, periodId }) {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [includeCocktails, setIncludeCocktails] = useState(true);

  useEffect(() => {
    const fetchAnalysis = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await salesAnalysisService.getSalesAnalysis(
          hotelSlug,
          periodId,
          includeCocktails,
          true // always include category breakdown
        );
        setAnalysisData(data);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch sales analysis:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [hotelSlug, periodId, includeCocktails]);

  if (loading) return <div className="loading">Loading analysis...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!analysisData) return <div>No data available</div>;

  return (
    <div className="sales-analysis-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h1>Sales Analysis - {analysisData.period_name}</h1>
        <div className="period-info">
          {analysisData.period_start} to {analysisData.period_end}
          {analysisData.period_is_closed && (
            <span className="badge closed">Closed</span>
          )}
        </div>
      </div>

      {/* Toggle Cocktails */}
      <div className="controls">
        <label className="toggle-label">
          <input
            type="checkbox"
            checked={includeCocktails}
            onChange={(e) => setIncludeCocktails(e.target.checked)}
          />
          <span>Include Cocktails</span>
        </label>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="card">
          <h3>Total Revenue</h3>
          <p className="amount">
            €{analysisData.combined_sales.total_revenue.toFixed(2)}
          </p>
          <div className="breakdown">
            <span>Stock: €{analysisData.general_sales.revenue.toFixed(2)}</span>
            {includeCocktails && (
              <span>Cocktails: €{analysisData.cocktail_sales.revenue.toFixed(2)}</span>
            )}
          </div>
        </div>

        <div className="card">
          <h3>Total Cost</h3>
          <p className="amount">
            €{analysisData.combined_sales.total_cost.toFixed(2)}
          </p>
          <div className="breakdown">
            <span>Stock: €{analysisData.general_sales.cost.toFixed(2)}</span>
            {includeCocktails && (
              <span>Cocktails: €{analysisData.cocktail_sales.cost.toFixed(2)}</span>
            )}
          </div>
        </div>

        <div className="card">
          <h3>Gross Profit</h3>
          <p className="amount profit">
            €{analysisData.combined_sales.profit.toFixed(2)}
          </p>
          <div className="breakdown">
            <span className="percentage">
              {analysisData.combined_sales.gp_percentage.toFixed(2)}% GP
            </span>
          </div>
        </div>

        <div className="card">
          <h3>Items Sold</h3>
          <p className="count">
            {analysisData.combined_sales.total_count}
          </p>
          <div className="breakdown">
            <span>Stock: {analysisData.general_sales.count}</span>
            {includeCocktails && (
              <span>Cocktails: {analysisData.cocktail_sales.count}</span>
            )}
          </div>
        </div>
      </div>

      {/* Revenue Breakdown Bar */}
      <div className="breakdown-section">
        <h2>Revenue Breakdown</h2>
        <div className="breakdown-bar">
          <div 
            className="bar-segment stock"
            style={{
              width: `${analysisData.breakdown_percentages.stock_revenue_percentage}%`
            }}
          >
            <span className="label">Stock Items</span>
            <span className="percentage">
              {analysisData.breakdown_percentages.stock_revenue_percentage.toFixed(1)}%
            </span>
          </div>
          {includeCocktails && (
            <div 
              className="bar-segment cocktails"
              style={{
                width: `${analysisData.breakdown_percentages.cocktail_revenue_percentage}%`
              }}
            >
              <span className="label">Cocktails</span>
              <span className="percentage">
                {analysisData.breakdown_percentages.cocktail_revenue_percentage.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Category Performance Table */}
      <div className="category-section">
        <h2>Category Performance</h2>
        <table className="category-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Revenue</th>
              <th>Cost</th>
              <th>Profit</th>
              <th>GP%</th>
              <th>Count</th>
            </tr>
          </thead>
          <tbody>
            {analysisData.category_breakdown.map(cat => (
              <tr 
                key={cat.category_code}
                className={cat.category_code === 'COCKTAILS' ? 'cocktail-row' : ''}
              >
                <td>
                  <span className={`category-badge ${cat.category_code}`}>
                    {cat.category_name}
                  </span>
                </td>
                <td className="number">€{cat.revenue.toFixed(2)}</td>
                <td className="number">€{cat.cost.toFixed(2)}</td>
                <td className="number profit">€{cat.profit.toFixed(2)}</td>
                <td className="number">{cat.gp_percentage.toFixed(2)}%</td>
                <td className="number">{cat.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Stock vs Cocktails Detail */}
      <div className="detail-section">
        <div className="detail-card stock">
          <h3>Stock Item Sales</h3>
          <div className="detail-grid">
            <div className="detail-item">
              <label>Revenue:</label>
              <span>€{analysisData.general_sales.revenue.toFixed(2)}</span>
            </div>
            <div className="detail-item">
              <label>Cost:</label>
              <span>€{analysisData.general_sales.cost.toFixed(2)}</span>
            </div>
            <div className="detail-item">
              <label>Profit:</label>
              <span className="profit">€{analysisData.general_sales.profit.toFixed(2)}</span>
            </div>
            <div className="detail-item">
              <label>GP%:</label>
              <span>{analysisData.general_sales.gp_percentage.toFixed(2)}%</span>
            </div>
            <div className="detail-item">
              <label>Count:</label>
              <span>{analysisData.general_sales.count}</span>
            </div>
          </div>
        </div>

        {includeCocktails && (
          <div className="detail-card cocktails">
            <h3>Cocktail Sales</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <label>Revenue:</label>
                <span>€{analysisData.cocktail_sales.revenue.toFixed(2)}</span>
              </div>
              <div className="detail-item">
                <label>Cost:</label>
                <span>€{analysisData.cocktail_sales.cost.toFixed(2)}</span>
              </div>
              <div className="detail-item">
                <label>Profit:</label>
                <span className="profit">€{analysisData.cocktail_sales.profit.toFixed(2)}</span>
              </div>
              <div className="detail-item">
                <label>GP%:</label>
                <span>{analysisData.cocktail_sales.gp_percentage.toFixed(2)}%</span>
              </div>
              <div className="detail-item">
                <label>Count:</label>
                <span>{analysisData.cocktail_sales.count}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Important Note */}
      <div className="info-note">
        <strong>ℹ️ Important:</strong> Cocktail sales are tracked separately 
        and do NOT affect stock inventory calculations. Combined values shown 
        above are for reporting and business intelligence only.
      </div>
    </div>
  );
}

export default SalesAnalysisDashboard;
```

---

## 5. Display Category Breakdown

### Step 5.1: Create Category Chart Component

```jsx
// src/components/Sales/CategoryBreakdownChart.jsx
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './CategoryBreakdownChart.css';

function CategoryBreakdownChart({ categoryData }) {
  // Transform data for chart
  const chartData = categoryData.map(cat => ({
    name: cat.category_name,
    revenue: cat.revenue,
    cost: cat.cost,
    profit: cat.profit,
    // Add flag for cocktails
    isCocktail: cat.category_code === 'COCKTAILS'
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;
    const gp = data.revenue > 0 
      ? ((data.profit / data.revenue) * 100).toFixed(2) 
      : 0;

    return (
      <div className="custom-tooltip">
        <h4>{data.name}</h4>
        <p><strong>Revenue:</strong> €{data.revenue.toFixed(2)}</p>
        <p><strong>Cost:</strong> €{data.cost.toFixed(2)}</p>
        <p><strong>Profit:</strong> €{data.profit.toFixed(2)}</p>
        <p><strong>GP%:</strong> {gp}%</p>
      </div>
    );
  };

  return (
    <div className="category-breakdown-chart">
      <h3>Revenue by Category</h3>
      
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar dataKey="revenue" fill="#4ECDC4" name="Revenue" />
          <Bar dataKey="cost" fill="#FF6B6B" name="Cost" />
          <Bar dataKey="profit" fill="#95E1D3" name="Profit" />
        </BarChart>
      </ResponsiveContainer>

      <div className="chart-note">
        <strong>Note:</strong> Cocktails are shown separately for comparison.
        They do NOT affect stocktake calculations.
      </div>
    </div>
  );
}

export default CategoryBreakdownChart;
```

---

## 6. Display KPI Dashboard with Cocktails

### Step 6.1: Create KPI Service

```javascript
// src/services/kpiService.js
import axios from 'axios';
import { buildApiUrl } from '../config/api';

export const kpiService = {
  /**
   * Get KPI summary for periods
   * @param {string} hotelSlug - Hotel identifier
   * @param {Array<number>} periodIds - Array of period IDs
   * @param {boolean} includeCocktails - Include cocktail metrics
   * @returns {Promise<Object>} KPI data
   */
  async getKPISummary(hotelSlug, periodIds, includeCocktails = false) {
    const url = buildApiUrl(hotelSlug, '/kpi-summary/');
    const response = await axios.get(url, {
      params: {
        period_ids: periodIds.join(','),
        include_cocktails: includeCocktails
      }
    });
    return response.data;
  }
};
```

### Step 6.2: Create KPI Dashboard Component

```jsx
// src/components/KPI/KPIDashboard.jsx
import React, { useState, useEffect } from 'react';
import { kpiService } from '../../services/kpiService';
import './KPIDashboard.css';

function KPIDashboard({ hotelSlug, periodIds }) {
  const [kpiData, setKpiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [includeCocktails, setIncludeCocktails] = useState(false);

  useEffect(() => {
    const fetchKPIs = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await kpiService.getKPISummary(
          hotelSlug,
          periodIds,
          includeCocktails
        );
        setKpiData(data.data);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch KPIs:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchKPIs();
  }, [hotelSlug, periodIds, includeCocktails]);

  if (loading) return <div className="loading">Loading KPIs...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!kpiData) return <div>No data available</div>;

  return (
    <div className="kpi-dashboard">
      <h1>KPI Summary</h1>

      {/* Toggle */}
      <div className="controls">
        <label className="toggle-label">
          <input
            type="checkbox"
            checked={includeCocktails}
            onChange={(e) => setIncludeCocktails(e.target.checked)}
          />
          <span>Include Cocktail Metrics</span>
        </label>
      </div>

      {/* Stock KPIs */}
      <div className="kpi-section">
        <h2>Stock Performance</h2>
        <div className="kpi-grid">
          <KPICard
            title="Stock Value"
            value={`€${kpiData.stock_value_metrics?.current_value?.toFixed(2) || '0.00'}`}
            trend={kpiData.stock_value_metrics?.trend_percentage}
          />
          <KPICard
            title="Gross Profit %"
            value={`${kpiData.profitability_metrics?.avg_gp_percentage?.toFixed(2) || '0'}%`}
            trend={kpiData.profitability_metrics?.gp_trend}
          />
          <KPICard
            title="Pour Cost %"
            value={`${kpiData.profitability_metrics?.avg_pour_cost?.toFixed(2) || '0'}%`}
            trend={kpiData.profitability_metrics?.pour_cost_trend}
            inverse
          />
        </div>
      </div>

      {/* Cocktail KPIs (if enabled) */}
      {includeCocktails && kpiData.cocktail_sales_metrics && (
        <div className="kpi-section cocktails-section">
          <h2>Cocktail Performance</h2>
          <div className="kpi-grid">
            <KPICard
              title="Cocktail Revenue"
              value={`€${kpiData.cocktail_sales_metrics.total_revenue.toFixed(2)}`}
              highlight="cocktail"
            />
            <KPICard
              title="Cocktail GP%"
              value={`${kpiData.cocktail_sales_metrics.gp_percentage.toFixed(2)}%`}
              highlight="cocktail"
            />
            <KPICard
              title="Avg Price"
              value={`€${kpiData.cocktail_sales_metrics.avg_price_per_cocktail.toFixed(2)}`}
              highlight="cocktail"
            />
            <KPICard
              title="Cocktails Sold"
              value={kpiData.cocktail_sales_metrics.count}
              highlight="cocktail"
            />
          </div>
          <div className="info-note">
            ℹ️ Cocktail metrics are separate from stock inventory calculations
          </div>
        </div>
      )}
    </div>
  );
}

function KPICard({ title, value, trend, inverse = false, highlight = null }) {
  const getTrendClass = () => {
    if (trend === undefined || trend === null) return '';
    if (inverse) {
      return trend <= 0 ? 'positive' : 'negative';
    }
    return trend >= 0 ? 'positive' : 'negative';
  };

  return (
    <div className={`kpi-card ${highlight ? `highlight-${highlight}` : ''}`}>
      <h3>{title}</h3>
      <p className="value">{value}</p>
      {trend !== undefined && trend !== null && (
        <span className={`trend ${getTrendClass()}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(2)}%
        </span>
      )}
    </div>
  );
}

export default KPIDashboard;
```

---

## 7. Complete Component Examples

### Step 7.1: Main App Integration

```jsx
// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SalesList from './components/Sales/SalesList';
import SalesEntryForm from './components/Sales/SalesEntryForm';
import SalesAnalysisDashboard from './components/Sales/SalesAnalysisDashboard';
import KPIDashboard from './components/KPI/KPIDashboard';

function App() {
  // Get from context or props
  const hotelSlug = 'myhotel';
  const stocktakeId = 42;
  const periodId = 15;

  return (
    <Router>
      <Routes>
        {/* Sales List */}
        <Route 
          path="/sales" 
          element={
            <SalesList 
              hotelSlug={hotelSlug} 
              stocktakeId={stocktakeId} 
            />
          } 
        />

        {/* Sales Entry */}
        <Route 
          path="/sales/create" 
          element={
            <SalesEntryForm 
              hotelSlug={hotelSlug} 
              stocktakeId={stocktakeId}
              onSalesCreated={(result) => {
                console.log('Sales created:', result);
                // Navigate to sales list or refresh
              }}
            />
          } 
        />

        {/* Sales Analysis Dashboard */}
        <Route 
          path="/analysis" 
          element={
            <SalesAnalysisDashboard 
              hotelSlug={hotelSlug} 
              periodId={periodId} 
            />
          } 
        />

        {/* KPI Dashboard */}
        <Route 
          path="/kpi" 
          element={
            <KPIDashboard 
              hotelSlug={hotelSlug} 
              periodIds={[13, 14, 15]} 
            />
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;
```

---

## 🎯 Key Points Summary

### ✅ DO

1. **Use the new sales-analysis endpoint** for combined reporting
2. **Toggle cocktails** with `include_cocktails` parameter
3. **Show clear visual distinction** between stock items and cocktails
4. **Display category breakdowns** with COCKTAILS as separate
5. **Auto-populate prices** from stock items when creating sales

### ❌ DON'T

1. **Don't mix cocktails with stock calculations**
2. **Don't add cocktail costs to COGS**
3. **Don't include cocktails in stocktake variance**
4. **Don't hide the separation** - make it obvious in UI

---

## 📞 Need Help?

- **API Documentation:** `COMPLETE_SALES_ANALYSIS_API_GUIDE.md`
- **Backend Summary:** `IMPLEMENTATION_SUMMARY.md`
- **Tests:** `test_sales_cocktail_isolation.py`

**Remember:** Stock items and cocktails are tracked separately - combined only for reporting!
