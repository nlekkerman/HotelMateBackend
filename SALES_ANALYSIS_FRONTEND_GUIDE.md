# 📊 Sales Analysis API - Frontend Implementation Guide

**Date:** November 11, 2025  
**Version:** 1.0  
**Purpose:** Combine stock item sales with cocktail sales for business intelligence and reporting

---

## 🎯 CRITICAL CONCEPTS

### **What This System Does:**

This API allows you to **analyze and display combined sales data** from two separate tracking systems:

1. **Stock Item Sales** (Beer, Wine, Spirits, etc.) - Tracked via Stocktakes
2. **Cocktail Sales** - Tracked separately via CocktailConsumption

### **⚠️ IMPORTANT: Separation of Concerns**

```
┌─────────────────────────────────────────────────────────────┐
│                   SYSTEM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────┘

STOCKTAKE SYSTEM (Inventory Tracking)
├─ Tracks: Stock items only (D, B, S, W, M categories)
├─ Calculates: Opening, Closing, Variance
├─ COGS: From Sale records (stock items only)
└─ ❌ NEVER includes cocktails in calculations

COCKTAIL TRACKING SYSTEM (Separate)
├─ Tracks: Cocktail ingredients and consumption
├─ Calculates: Ingredient usage, cocktail costs
├─ Revenue: From CocktailConsumption records
└─ ❌ NEVER affects stocktake inventory

SALES ANALYSIS API (This Guide)
├─ Purpose: Combine both for business intelligence
├─ Use Case: Total revenue, profit analysis, reports
├─ Method: Read-only combination of separate data
└─ ✅ Does NOT modify stocktakes or inventory
```

---

## 📋 KEY PRINCIPLES

### **1. Cocktails Are Separate**
- Cocktails use **different ingredients** (not stock items)
- Cocktails have **separate tracking** (CocktailConsumption model)
- Cocktails **NEVER affect** stocktake calculations
- Cocktails are **combined only for display/reporting**

### **2. This Is Analysis-Only**
- These endpoints **READ data** from both systems
- They **COMBINE** the data for reporting
- They **DO NOT WRITE** or modify anything
- Stocktake calculations remain **completely isolated**

### **3. Always Show The Breakdown**
- Always display **separate totals** (stock vs cocktails)
- Show **combined total** as additional info
- Let users see **where revenue comes from**
- Maintain **transparency** in reporting

---

## 🔌 API ENDPOINTS

### **1. Get Period Analysis (Basic)**

```
GET /api/stock/<hotel>/periods/<period_id>/
```

**What You Get:**
```json
{
  "id": 10,
  "period_name": "November 2025",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30",
  "stocktake": {
    "total_revenue": 125000.50,     // Stock items only
    "total_cogs": 42500.25,          // Stock items only
    "gross_profit_percentage": 66.00
  },
  // NEW: Cocktail data (separate)
  "cocktail_revenue": 18500.00,
  "cocktail_cost": 5200.00,
  "cocktail_quantity": 450,
  
  // NEW: Combined analysis (for display)
  "analysis_total_sales_combined": 143500.50,
  "analysis_total_cost_combined": 47700.25,
  "analysis_profit_combined": 95800.25
}
```

**How To Use:**
```javascript
const period = await fetch(`/api/stock/${hotel}/periods/${periodId}/`);

// Display separate totals
console.log('Stock Items Revenue:', period.stocktake.total_revenue);
console.log('Cocktail Revenue:', period.cocktail_revenue);

// Display combined total
console.log('TOTAL REVENUE:', period.analysis_total_sales_combined);

// Show breakdown
const stockPercentage = (
  (period.stocktake.total_revenue / period.analysis_total_sales_combined) * 100
).toFixed(2);
const cocktailPercentage = (
  (period.cocktail_revenue / period.analysis_total_sales_combined) * 100
).toFixed(2);

console.log(`Stock Items: ${stockPercentage}%`);
console.log(`Cocktails: ${cocktailPercentage}%`);
```

---

### **2. Get Sales By Category**

```
GET /api/stock/<hotel>/periods/<period_id>/category-breakdown/?include_cocktails=true
```

**Response:**
```json
{
  "stock_categories": {
    "D": {
      "name": "Draught Beer",
      "revenue": 45000.00,
      "cost": 15000.00,
      "profit": 30000.00,
      "count": 250
    },
    "B": {
      "name": "Bottled Beer",
      "revenue": 32000.00,
      "cost": 11500.00,
      "profit": 20500.00,
      "count": 180
    },
    "S": {
      "name": "Spirits",
      "revenue": 28000.50,
      "cost": 9500.25,
      "profit": 18500.25,
      "count": 150
    },
    "W": {
      "name": "Wine",
      "revenue": 15000.00,
      "cost": 5000.00,
      "profit": 10000.00,
      "count": 85
    },
    "M": {
      "name": "Minerals",
      "revenue": 5000.00,
      "cost": 1500.00,
      "profit": 3500.00,
      "count": 120
    }
  },
  "cocktails": {
    "name": "Cocktails",
    "revenue": 18500.00,
    "cost": 5200.00,
    "profit": 13300.00,
    "count": 450
  },
  "combined_total": 143500.50,
  "breakdown_percentages": {
    "D": 31.35,
    "B": 22.30,
    "S": 19.51,
    "W": 10.45,
    "M": 3.48,
    "COCKTAILS": 12.89
  }
}
```

**Frontend Display Example:**
```jsx
const CategoryBreakdown = ({ data }) => {
  return (
    <div className="category-breakdown">
      <h3>Sales by Category</h3>
      
      {/* Stock Categories */}
      <div className="stock-categories">
        <h4>Stock Items</h4>
        {Object.entries(data.stock_categories).map(([code, cat]) => (
          <div key={code} className="category-row">
            <span className="category-name">{cat.name}</span>
            <span className="revenue">€{cat.revenue.toFixed(2)}</span>
            <span className="percentage">
              {data.breakdown_percentages[code]}%
            </span>
            <div className="progress-bar">
              <div 
                className="fill" 
                style={{width: `${data.breakdown_percentages[code]}%`}}
              />
            </div>
          </div>
        ))}
      </div>
      
      {/* Cocktails (Separate Section) */}
      <div className="cocktails-section">
        <h4>Cocktails (Separate Tracking)</h4>
        <div className="category-row cocktail">
          <span className="category-name">{data.cocktails.name}</span>
          <span className="revenue">€{data.cocktails.revenue.toFixed(2)}</span>
          <span className="percentage">
            {data.breakdown_percentages.COCKTAILS}%
          </span>
          <div className="progress-bar cocktail">
            <div 
              className="fill" 
              style={{width: `${data.breakdown_percentages.COCKTAILS}%`}}
            />
          </div>
        </div>
      </div>
      
      {/* Combined Total */}
      <div className="total-row">
        <strong>TOTAL REVENUE:</strong>
        <strong>€{data.combined_total.toFixed(2)}</strong>
      </div>
    </div>
  );
};
```

---

### **3. Period Comparison (With Cocktails)**

```
GET /api/stock/<hotel>/periods/compare/?period1=9&period2=10&include_cocktails=true
```

**Response:**
```json
{
  "period1": {
    "period_name": "October 2025",
    "stock_revenue": 118000.00,
    "cocktail_revenue": 16500.00,
    "combined_revenue": 134500.00,
    "stock_cost": 40000.00,
    "cocktail_cost": 4800.00,
    "combined_cost": 44800.00,
    "profit": 89700.00,
    "gp_percentage": 66.70
  },
  "period2": {
    "period_name": "November 2025",
    "stock_revenue": 125000.50,
    "cocktail_revenue": 18500.00,
    "combined_revenue": 143500.50,
    "stock_cost": 42500.25,
    "cocktail_cost": 5200.00,
    "combined_cost": 47700.25,
    "profit": 95800.25,
    "gp_percentage": 66.77
  },
  "comparison": {
    "revenue_change": 9000.50,
    "revenue_change_percentage": 6.69,
    "cost_change": 2900.25,
    "profit_change": 6100.25,
    "trend": "increasing"
  },
  "breakdown": {
    "stock_items_change": 7000.50,
    "cocktails_change": 2000.00
  }
}
```

**Frontend Chart Example:**
```jsx
const PeriodComparison = ({ data }) => {
  return (
    <div className="comparison-chart">
      <h3>Period Comparison</h3>
      
      <div className="periods-side-by-side">
        {/* Period 1 */}
        <div className="period-column">
          <h4>{data.period1.period_name}</h4>
          <div className="metrics">
            <div className="metric">
              <label>Stock Items:</label>
              <span>€{data.period1.stock_revenue.toLocaleString()}</span>
            </div>
            <div className="metric cocktail">
              <label>Cocktails:</label>
              <span>€{data.period1.cocktail_revenue.toLocaleString()}</span>
            </div>
            <div className="metric total">
              <label>Total Revenue:</label>
              <strong>€{data.period1.combined_revenue.toLocaleString()}</strong>
            </div>
          </div>
        </div>
        
        {/* Arrow/Change Indicator */}
        <div className="change-indicator">
          <div className={`arrow ${data.comparison.trend}`}>
            {data.comparison.trend === 'increasing' ? '↗' : '↘'}
          </div>
          <div className="change-amount">
            {data.comparison.revenue_change >= 0 ? '+' : ''}
            €{data.comparison.revenue_change.toLocaleString()}
          </div>
          <div className="change-percentage">
            ({data.comparison.revenue_change_percentage}%)
          </div>
        </div>
        
        {/* Period 2 */}
        <div className="period-column">
          <h4>{data.period2.period_name}</h4>
          <div className="metrics">
            <div className="metric">
              <label>Stock Items:</label>
              <span>€{data.period2.stock_revenue.toLocaleString()}</span>
            </div>
            <div className="metric cocktail">
              <label>Cocktails:</label>
              <span>€{data.period2.cocktail_revenue.toLocaleString()}</span>
            </div>
            <div className="metric total">
              <label>Total Revenue:</label>
              <strong>€{data.period2.combined_revenue.toLocaleString()}</strong>
            </div>
          </div>
        </div>
      </div>
      
      {/* Breakdown */}
      <div className="breakdown-section">
        <h5>Revenue Change Breakdown:</h5>
        <div className="breakdown-item">
          <span>Stock Items:</span>
          <span className="positive">
            +€{data.breakdown.stock_items_change.toLocaleString()}
          </span>
        </div>
        <div className="breakdown-item">
          <span>Cocktails:</span>
          <span className="positive">
            +€{data.breakdown.cocktails_change.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
};
```

---

## 🎨 UI/UX RECOMMENDATIONS

### **1. Always Show Separate Totals First**
```
Stock Items:    €125,000  (87%)
Cocktails:      €18,500   (13%)
─────────────────────────────────
TOTAL:          €143,500
```

### **2. Use Visual Indicators**
- **Stock Items**: Blue/Green colors
- **Cocktails**: Orange/Purple colors (different from stock)
- **Combined**: Gray or neutral

### **3. Provide Context**
```
💡 Note: Cocktails are tracked separately from stock 
inventory. This combined view is for reporting only.
```

### **4. Allow Filtering**
```html
<select id="view-mode">
  <option value="separate">Show Separate (Default)</option>
  <option value="combined">Show Combined Total</option>
  <option value="both">Show Both</option>
</select>
```

---

## ⚠️ IMPORTANT WARNINGS

### **1. Don't Mix in Stocktake Views**
❌ **WRONG:**
```
Stocktake Total Revenue: €143,500  // Including cocktails
```

✅ **CORRECT:**
```
Stocktake Revenue: €125,000  (Stock Items Only)
Cocktail Revenue:  €18,500   (Separate Tracking)
─────────────────────────────────────────────────
Combined Total:    €143,500  (For Analysis)
```

### **2. Don't Use Combined Values for Inventory**
❌ **WRONG:**
```javascript
// DON'T use combined values for variance calculations
const variance = opening + purchases - combined_sales - closing;
```

✅ **CORRECT:**
```javascript
// Use stocktake values only for inventory
const variance = opening + purchases - stocktake.total_revenue - closing;
```

### **3. Label Everything Clearly**
Always make it obvious what data source you're displaying:
- "Stock Item Sales" or "Inventory Sales"
- "Cocktail Sales" (with note: "Separate tracking")
- "Combined Analysis Total" or "Total Revenue (Stock + Cocktails)"

---

## 📊 EXAMPLE DASHBOARD LAYOUT

```
┌─────────────────────────────────────────────────────────┐
│              November 2025 Sales Summary                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Stock Items (Inventory)          Cocktails (Separate)  │
│  ┌──────────────────────┐        ┌─────────────────┐  │
│  │ Revenue: €125,000    │        │ Revenue: €18,500│  │
│  │ COGS:    €42,500     │        │ Cost:    €5,200 │  │
│  │ GP:      66.0%       │        │ GP:      71.9%  │  │
│  └──────────────────────┘        └─────────────────┘  │
│                                                          │
│  ═══════════════════════════════════════════════════════ │
│  COMBINED ANALYSIS (Stock + Cocktails)                   │
│  Total Revenue:  €143,500                               │
│  Total Cost:     €47,700                                │
│  Total Profit:   €95,800                                │
│  GP%:            66.8%                                  │
│                                                          │
│  💡 Note: Combined total for reporting only.            │
│     Stocktake calculations use stock items only.        │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 QUICK START CODE

### **Fetch and Display Combined Analysis:**

```javascript
async function loadSalesAnalysis(hotelId, periodId) {
  try {
    const response = await fetch(
      `/api/stock/${hotelId}/periods/${periodId}/`,
      {
        headers: {
          'Authorization': `Token ${authToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const period = await response.json();
    
    // Extract data
    const stockRevenue = period.stocktake?.total_revenue || 0;
    const stockCost = period.stocktake?.total_cogs || 0;
    const cocktailRevenue = period.cocktail_revenue || 0;
    const cocktailCost = period.cocktail_cost || 0;
    
    // Calculate combined
    const combinedRevenue = stockRevenue + cocktailRevenue;
    const combinedCost = stockCost + cocktailCost;
    const combinedProfit = combinedRevenue - combinedCost;
    const combinedGP = (combinedProfit / combinedRevenue * 100).toFixed(2);
    
    // Calculate percentages
    const stockPercentage = (stockRevenue / combinedRevenue * 100).toFixed(1);
    const cocktailPercentage = (cocktailRevenue / combinedRevenue * 100).toFixed(1);
    
    // Display
    return {
      period_name: period.period_name,
      stock: {
        revenue: stockRevenue,
        cost: stockCost,
        percentage: stockPercentage
      },
      cocktails: {
        revenue: cocktailRevenue,
        cost: cocktailCost,
        percentage: cocktailPercentage
      },
      combined: {
        revenue: combinedRevenue,
        cost: combinedCost,
        profit: combinedProfit,
        gp: combinedGP
      }
    };
    
  } catch (error) {
    console.error('Error loading sales analysis:', error);
    throw error;
  }
}

// Usage
const analysis = await loadSalesAnalysis('hotel-killarney', 10);
console.log('Stock Revenue:', analysis.stock.revenue);
console.log('Cocktail Revenue:', analysis.cocktails.revenue);
console.log('TOTAL:', analysis.combined.revenue);
```

---

## 📝 SUMMARY

### **What You Can Do:**
✅ Display combined revenue totals for business reports  
✅ Show separate breakdown (stock vs cocktails)  
✅ Compare periods with combined analysis  
✅ Create charts showing revenue sources  
✅ Calculate overall profitability  

### **What You Can NOT Do:**
❌ Use combined values in stocktake variance calculations  
❌ Mix cocktails into inventory tracking  
❌ Display combined values as "Stocktake Total"  
❌ Use cocktail data for stock item COGS  
❌ Modify stocktake calculations with cocktail data  

### **Golden Rule:**
**"Separate in the database, combined in the display, never mixed in calculations."**

---

**END OF GUIDE**
