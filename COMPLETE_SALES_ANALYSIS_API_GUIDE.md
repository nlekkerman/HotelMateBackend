# Complete Sales Analysis API - Frontend Implementation Guide

## 🎯 Overview

This guide explains how to use the **NEW Sales Analysis API** that combines stock item sales with cocktail sales for business intelligence reporting.

### What's New?

1. **Sales Analysis Endpoint** - `/api/stock/<hotel>/periods/<period_id>/sales-analysis/`
2. **Updated KPI Endpoint** - Now supports `?include_cocktails=true/false`
3. **Category Breakdown** - D, B, S, W, M + COCKTAILS as separate categories
4. **Isolation Tests** - Guarantees cocktails never affect stocktake calculations

---

## 🔑 Key Principle

> **"Separate in Database, Combined in Display, Never Mixed in Calculations"**

- **Stock items** tracked in `Sale` table → affects stocktake COGS
- **Cocktails** tracked in `CocktailConsumption` table → NEVER affects stocktake
- **Combined values** ONLY for reporting/display (dashboard charts, analytics)

---

## 📊 API Endpoints

### 1. Sales Analysis Endpoint (NEW)

**Endpoint:** `GET /api/stock/<hotel>/periods/<period_id>/sales-analysis/`

**Purpose:** Get comprehensive sales breakdown combining stock items + cocktails

**Query Parameters:**
- `include_cocktails` (boolean, default: `true`) - Include cocktail data
- `include_category_breakdown` (boolean, default: `true`) - Include D/B/S/W/M breakdown

**Response Structure:**

```json
{
  "period_id": 42,
  "period_name": "November 2025",
  "period_start": "2025-11-01",
  "period_end": "2025-11-30",
  "period_is_closed": true,
  
  "general_sales": {
    "revenue": 12500.50,
    "cost": 4200.20,
    "count": 350,
    "profit": 8300.30,
    "gp_percentage": 66.40
  },
  
  "cocktail_sales": {
    "revenue": 3200.00,
    "cost": 1100.00,
    "count": 120,
    "profit": 2100.00,
    "gp_percentage": 65.63
  },
  
  "combined_sales": {
    "total_revenue": 15700.50,
    "total_cost": 5300.20,
    "total_count": 470,
    "profit": 10400.30,
    "gp_percentage": 66.24
  },
  
  "breakdown_percentages": {
    "stock_revenue_percentage": 79.61,
    "cocktail_revenue_percentage": 20.39,
    "stock_cost_percentage": 79.25,
    "cocktail_cost_percentage": 20.75
  },
  
  "category_breakdown": [
    {
      "category_code": "D",
      "category_name": "Draught",
      "revenue": 5200.00,
      "cost": 1800.00,
      "count": 180,
      "profit": 3400.00,
      "gp_percentage": 65.38
    },
    {
      "category_code": "B",
      "category_name": "Bottled",
      "revenue": 3100.00,
      "cost": 1050.00,
      "count": 95,
      "profit": 2050.00,
      "gp_percentage": 66.13
    },
    {
      "category_code": "S",
      "category_name": "Spirits",
      "revenue": 2800.50,
      "cost": 950.20,
      "count": 55,
      "profit": 1850.30,
      "gp_percentage": 66.07
    },
    {
      "category_code": "W",
      "category_name": "Wine",
      "revenue": 1200.00,
      "cost": 350.00,
      "count": 15,
      "profit": 850.00,
      "gp_percentage": 70.83
    },
    {
      "category_code": "M",
      "category_name": "Miscellaneous",
      "revenue": 200.00,
      "cost": 50.00,
      "count": 5,
      "profit": 150.00,
      "gp_percentage": 75.00
    },
    {
      "category_code": "COCKTAILS",
      "category_name": "Cocktails",
      "revenue": 3200.00,
      "cost": 1100.00,
      "count": 120,
      "profit": 2100.00,
      "gp_percentage": 65.63
    }
  ]
}
```

---

### 2. KPI Summary Endpoint (UPDATED)

**Endpoint:** `GET /api/stock/<hotel>/kpi-summary/?period_ids=1,2,3`

**NEW Query Parameter:**
- `include_cocktails` (boolean, default: `false`) - Add cocktail metrics

**Response Structure:**

```json
{
  "success": true,
  "data": {
    "stock_value_metrics": { ... },
    "profitability_metrics": { ... },
    "category_performance": { ... },
    "inventory_health": { ... },
    "period_comparison": { ... },
    "performance_score": { ... },
    "additional_metrics": { ... },
    
    // ONLY if include_cocktails=true
    "cocktail_sales_metrics": {
      "total_revenue": 3200.00,
      "total_cost": 1100.00,
      "total_profit": 2100.00,
      "gp_percentage": 65.63,
      "count": 120,
      "avg_price_per_cocktail": 26.67
    }
  },
  "meta": {
    "periods_analyzed": 3,
    "period_names": ["September 2025", "October 2025", "November 2025"],
    "date_range": {
      "from": "2025-09-01",
      "to": "2025-11-30"
    }
  }
}
```

**Important:** Cocktails are in a **SEPARATE section**, never mixed with stock KPIs.

---

## 🎨 Frontend Implementation Examples

### Example 1: Sales Dashboard with Combined View

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function SalesDashboard({ hotelSlug, periodId }) {
  const [salesData, setSalesData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [includeCocktails, setIncludeCocktails] = useState(true);

  useEffect(() => {
    const fetchSalesAnalysis = async () => {
      try {
        const response = await axios.get(
          `/api/stock/${hotelSlug}/periods/${periodId}/sales-analysis/`,
          {
            params: {
              include_cocktails: includeCocktails,
              include_category_breakdown: true
            }
          }
        );
        setSalesData(response.data);
      } catch (error) {
        console.error('Failed to fetch sales analysis:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSalesAnalysis();
  }, [hotelSlug, periodId, includeCocktails]);

  if (loading) return <div>Loading sales data...</div>;
  if (!salesData) return <div>No data available</div>;

  return (
    <div className="sales-dashboard">
      <h1>Sales Analysis - {salesData.period_name}</h1>
      
      {/* Toggle Cocktails */}
      <div className="controls">
        <label>
          <input
            type="checkbox"
            checked={includeCocktails}
            onChange={(e) => setIncludeCocktails(e.target.checked)}
          />
          Include Cocktails
        </label>
      </div>

      {/* Combined Totals */}
      <div className="totals-grid">
        <div className="metric-card">
          <h3>Total Revenue</h3>
          <p className="amount">
            €{salesData.combined_sales.total_revenue.toFixed(2)}
          </p>
        </div>
        
        <div className="metric-card">
          <h3>Total Cost</h3>
          <p className="amount">
            €{salesData.combined_sales.total_cost.toFixed(2)}
          </p>
        </div>
        
        <div className="metric-card">
          <h3>Gross Profit</h3>
          <p className="amount profit">
            €{salesData.combined_sales.profit.toFixed(2)}
          </p>
          <span className="percentage">
            {salesData.combined_sales.gp_percentage.toFixed(2)}% GP
          </span>
        </div>
        
        <div className="metric-card">
          <h3>Items Sold</h3>
          <p className="count">{salesData.combined_sales.total_count}</p>
        </div>
      </div>

      {/* Breakdown */}
      <div className="breakdown-section">
        <h2>Revenue Breakdown</h2>
        <div className="breakdown-chart">
          <div className="bar-segment stock" 
               style={{width: `${salesData.breakdown_percentages.stock_revenue_percentage}%`}}>
            <span>Stock Items</span>
            <span>{salesData.breakdown_percentages.stock_revenue_percentage.toFixed(1)}%</span>
          </div>
          <div className="bar-segment cocktails" 
               style={{width: `${salesData.breakdown_percentages.cocktail_revenue_percentage}%`}}>
            <span>Cocktails</span>
            <span>{salesData.breakdown_percentages.cocktail_revenue_percentage.toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Category Performance */}
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
            {salesData.category_breakdown.map(cat => (
              <tr key={cat.category_code} 
                  className={cat.category_code === 'COCKTAILS' ? 'cocktails-row' : ''}>
                <td>{cat.category_name}</td>
                <td>€{cat.revenue.toFixed(2)}</td>
                <td>€{cat.cost.toFixed(2)}</td>
                <td>€{cat.profit.toFixed(2)}</td>
                <td>{cat.gp_percentage.toFixed(2)}%</td>
                <td>{cat.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Stock vs Cocktails Detail */}
      <div className="detail-section">
        <div className="detail-card">
          <h3>Stock Item Sales</h3>
          <p>Revenue: €{salesData.general_sales.revenue.toFixed(2)}</p>
          <p>Cost: €{salesData.general_sales.cost.toFixed(2)}</p>
          <p>Profit: €{salesData.general_sales.profit.toFixed(2)}</p>
          <p>GP: {salesData.general_sales.gp_percentage.toFixed(2)}%</p>
          <p>Count: {salesData.general_sales.count}</p>
        </div>

        {includeCocktails && (
          <div className="detail-card">
            <h3>Cocktail Sales</h3>
            <p>Revenue: €{salesData.cocktail_sales.revenue.toFixed(2)}</p>
            <p>Cost: €{salesData.cocktail_sales.cost.toFixed(2)}</p>
            <p>Profit: €{salesData.cocktail_sales.profit.toFixed(2)}</p>
            <p>GP: {salesData.cocktail_sales.gp_percentage.toFixed(2)}%</p>
            <p>Count: {salesData.cocktail_sales.count}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default SalesDashboard;
```

---

### Example 2: Category Breakdown Chart

```jsx
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

function CategoryBreakdownChart({ categoryData }) {
  // Transform data for chart
  const chartData = categoryData.map(cat => ({
    name: cat.category_name,
    revenue: cat.revenue,
    cost: cat.cost,
    profit: cat.profit,
    // Highlight cocktails differently
    fill: cat.category_code === 'COCKTAILS' ? '#FF6B6B' : '#4ECDC4'
  }));

  return (
    <div className="category-chart">
      <h3>Revenue by Category</h3>
      <BarChart width={800} height={400} data={chartData}>
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip 
          formatter={(value) => `€${value.toFixed(2)}`}
        />
        <Legend />
        <Bar dataKey="revenue" fill="#4ECDC4" name="Revenue" />
        <Bar dataKey="cost" fill="#FF6B6B" name="Cost" />
        <Bar dataKey="profit" fill="#95E1D3" name="Profit" />
      </BarChart>
      
      {/* Note for cocktails */}
      <p className="chart-note">
        <strong>Note:</strong> Cocktails are shown separately for comparison.
        They do NOT affect stocktake calculations.
      </p>
    </div>
  );
}

export default CategoryBreakdownChart;
```

---

### Example 3: KPI Dashboard with Cocktail Toggle

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function KPIDashboard({ hotelSlug, periodIds }) {
  const [kpiData, setKpiData] = useState(null);
  const [includeCocktails, setIncludeCocktails] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchKPIs = async () => {
      try {
        const response = await axios.get(
          `/api/stock/${hotelSlug}/kpi-summary/`,
          {
            params: {
              period_ids: periodIds.join(','),
              include_cocktails: includeCocktails
            }
          }
        );
        setKpiData(response.data.data);
      } catch (error) {
        console.error('Failed to fetch KPIs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchKPIs();
  }, [hotelSlug, periodIds, includeCocktails]);

  if (loading) return <div>Loading KPIs...</div>;
  if (!kpiData) return <div>No data available</div>;

  return (
    <div className="kpi-dashboard">
      <h1>KPI Summary</h1>
      
      {/* Toggle */}
      <div className="controls">
        <label>
          <input
            type="checkbox"
            checked={includeCocktails}
            onChange={(e) => setIncludeCocktails(e.target.checked)}
          />
          Include Cocktail Metrics
        </label>
      </div>

      {/* Stock KPIs */}
      <div className="kpi-section">
        <h2>Stock Performance</h2>
        <div className="kpi-grid">
          <KPICard
            title="Stock Value"
            value={`€${kpiData.stock_value_metrics.current_value.toFixed(2)}`}
            trend={kpiData.stock_value_metrics.trend_percentage}
          />
          <KPICard
            title="GP%"
            value={`${kpiData.profitability_metrics.avg_gp_percentage.toFixed(2)}%`}
            trend={kpiData.profitability_metrics.gp_trend}
          />
          <KPICard
            title="Pour Cost%"
            value={`${kpiData.profitability_metrics.avg_pour_cost.toFixed(2)}%`}
            trend={kpiData.profitability_metrics.pour_cost_trend}
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
          <p className="info-note">
            ℹ️ Cocktail metrics are separate from stock inventory calculations
          </p>
        </div>
      )}
    </div>
  );
}

function KPICard({ title, value, trend, highlight }) {
  return (
    <div className={`kpi-card ${highlight ? 'highlight-' + highlight : ''}`}>
      <h3>{title}</h3>
      <p className="value">{value}</p>
      {trend !== undefined && (
        <span className={`trend ${trend >= 0 ? 'positive' : 'negative'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(2)}%
        </span>
      )}
    </div>
  );
}

export default KPIDashboard;
```

---

## ⚠️ Important Guidelines

### DO ✅

1. **Use combined values for display/reporting**
   - Dashboard charts
   - Executive summaries
   - Revenue reports
   - Profitability analysis

2. **Show cocktails as separate section**
   - Separate cards/charts
   - Different colors
   - Clear labels ("Cocktails", "Stock Items")

3. **Allow users to toggle cocktail visibility**
   - Use `?include_cocktails=true/false`
   - Give users control over what they see

4. **Use category breakdown for detailed analysis**
   - Show D, B, S, W, M + COCKTAILS
   - Each category separate
   - Clear visual distinction

### DON'T ❌

1. **Never mix cocktails with stock calculations**
   - Don't add cocktail costs to COGS
   - Don't include cocktail revenue in stocktake totals
   - Don't combine them in variance calculations

2. **Don't confuse analysis with inventory**
   - `analysis_*` properties = reporting only
   - Stocktake COGS = stock items only
   - Variance = stock items only

3. **Don't hide the separation**
   - Always label "Stock Items" vs "Cocktails"
   - Don't make it look like they're the same thing
   - Make the distinction clear in UI

---

## 📝 Quick Reference

### Endpoints

| Endpoint | Purpose | Cocktails Included? |
|----------|---------|---------------------|
| `/periods/<id>/sales-analysis/` | Combined sales analysis | Optional (default: true) |
| `/kpi-summary/` | KPI metrics | Optional (default: false) |
| `/stocktakes/<id>/` | Stocktake details | **NO** (stock only) |

### Query Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `include_cocktails` | `true`/`false` | varies | Include cocktail data |
| `include_category_breakdown` | `true`/`false` | `true` | Include D/B/S/W/M breakdown |
| `period_ids` | `1,2,3` | required | Comma-separated period IDs |

### Response Fields

**Stock Items Only:**
- `Stocktake.total_cogs`
- `Stocktake.total_revenue`
- `StocktakeLine` calculations
- Period variance

**Analysis/Reporting (Combined):**
- `StockPeriod.analysis_total_sales_combined`
- `StockPeriod.analysis_total_cost_combined`
- `StockPeriod.analysis_profit_combined`
- Sales analysis endpoint

---

## 🧪 Testing Checklist

Before deploying to production, verify:

- [ ] Sales analysis endpoint returns correct data
- [ ] KPI endpoint respects `include_cocktails` parameter
- [ ] Cocktails shown separately in UI
- [ ] Toggle works correctly
- [ ] Category breakdown includes all categories + COCKTAILS
- [ ] Charts/graphs clearly distinguish stock vs cocktails
- [ ] Error handling for missing data
- [ ] Loading states implemented
- [ ] Mobile responsive design
- [ ] Accessibility (ARIA labels, keyboard navigation)

---

## 🚀 Next Steps

1. **Implement the dashboard** using examples above
2. **Test with real data** to ensure accuracy
3. **Get user feedback** on clarity of stock vs cocktails
4. **Add export functionality** (PDF, Excel)
5. **Create trend analysis** across multiple periods

---

## 📞 Support

For questions or issues:
- Check isolation tests: `test_sales_cocktail_isolation.py`
- Review architecture docs: `SALES_ARCHITECTURE_DECISION.md`
- Check API reference: `SALES_ANALYSIS_FRONTEND_GUIDE.md`

**Remember:** Stock items and cocktails are tracked separately in the database and NEVER mixed in calculations. Combined values are for reporting/display only!
