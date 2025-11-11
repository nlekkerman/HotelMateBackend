# Period Sales Analysis API Documentation

## Overview

The Period Sales Analysis endpoint provides comprehensive sales analytics for a specific stock period, combining both **stock item sales** (from the Sale model) and **cocktail sales** (from CocktailConsumption model) into a unified report.

This is a **read-only analytics endpoint** - it does not modify any data, only aggregates and presents it for business intelligence purposes.

---

## Endpoint

**GET** `/api/stock_tracker/<hotel_identifier>/sales/summary/`

**Parameters:**
- `hotel_identifier`: The hotel's slug or subdomain (e.g., `hotel-killarney`)

**Required Query Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)

---

## Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_cocktails` | boolean | `true` | Include cocktail sales in the analysis |
| `include_category_breakdown` | boolean | `true` | Include detailed breakdown by category |

---

## Response Structure

```json
{
  "period_id": 123,
  "period_name": "October 2025",
  "period_start": "2025-10-01",
  "period_end": "2025-10-31",
  "period_is_closed": true,
  
  "general_sales": {
    "revenue": 45678.50,
    "cost": 18234.25,
    "count": 1250,
    "profit": 27444.25,
    "gp_percentage": 60.08
  },
  
  "cocktail_sales": {
    "revenue": 12450.00,
    "cost": 3678.50,
    "count": 345,
    "profit": 8771.50,
    "gp_percentage": 70.46
  },
  
  "combined_sales": {
    "total_revenue": 58128.50,
    "total_cost": 21912.75,
    "total_count": 1595,
    "profit": 36215.75,
    "gp_percentage": 62.30
  },
  
  "breakdown_percentages": {
    "general_revenue_percent": 78.58,
    "cocktail_revenue_percent": 21.42,
    "general_profit_percent": 75.78,
    "cocktail_profit_percent": 24.22
  },
  
  "category_breakdown": [
    {
      "category": "D",
      "name": "Draught",
      "revenue": 18450.00,
      "cost": 7234.50,
      "profit": 11215.50,
      "gp_percentage": 60.79,
      "count": 450
    },
    {
      "category": "B",
      "name": "Bottled",
      "revenue": 15678.50,
      "cost": 6123.75,
      "profit": 9554.75,
      "gp_percentage": 60.94,
      "count": 567
    },
    {
      "category": "COCKTAILS",
      "name": "Cocktails",
      "revenue": 12450.00,
      "cost": 3678.50,
      "profit": 8771.50,
      "gp_percentage": 70.46,
      "count": 345
    }
  ]
}
```

---

## Response Fields Explained

### Period Information
- `period_id`: Unique identifier for the stock period
- `period_name`: Human-readable period name (e.g., "October 2025")
- `period_start`: Start date of the period (YYYY-MM-DD)
- `period_end`: End date of the period (YYYY-MM-DD)
- `period_is_closed`: Whether the period has been closed/finalized

### General Sales (Stock Items)
Data from the **Sale** model - traditional stock item sales:
- `revenue`: Total sales revenue
- `cost`: Total cost of goods sold (COGS)
- `count`: Number of sale records
- `profit`: Gross profit (revenue - cost)
- `gp_percentage`: Gross profit percentage

### Cocktail Sales
Data from the **CocktailConsumption** model - cocktails made and sold:
- Same structure as general_sales
- Only included when `include_cocktails=true`

### Combined Sales
Aggregated totals combining both stock items and cocktails:
- `total_revenue`: Sum of all revenue
- `total_cost`: Sum of all costs
- `total_count`: Total number of transactions
- `profit`: Total gross profit
- `gp_percentage`: Overall GP%

### Breakdown Percentages
Shows the contribution of each sales type to totals:
- `general_revenue_percent`: % of revenue from stock items
- `cocktail_revenue_percent`: % of revenue from cocktails
- `general_profit_percent`: % of profit from stock items
- `cocktail_profit_percent`: % of profit from cocktails

### Category Breakdown
Detailed breakdown by product category:
- **Stock categories**: D (Draught), B (Bottled), S (Spirits), W (Wine), M (Minerals)
- **Cocktails**: Grouped as "COCKTAILS" category
- Each category shows revenue, cost, profit, GP%, and transaction count

---

## Example Requests

### 1. Full Analysis (Default)

Get complete sales analysis with all categories and cocktails:

```bash
GET /api/stock_tracker/hotel-killarney/sales/summary/?start_date=2025-10-01&end_date=2025-10-31
```

**JavaScript:**
```javascript
const response = await fetch(
  `/api/stock_tracker/hotel-killarney/sales/summary/?start_date=2025-10-01&end_date=2025-10-31`
);
const data = await response.json();

console.log('Total Revenue:', data.overall.total_revenue);
console.log('Sales by Category:', data.by_category);
```

---

### 2. Exclude Cocktails

Get only stock item sales (no cocktails):

```bash
GET /api/stock_tracker/hotel-killarney/periods/123/sales-analysis/?include_cocktails=false
```

**JavaScript:**
```javascript
const response = await fetch(
  `/api/stock_tracker/hotel-killarney/periods/123/sales-analysis/?include_cocktails=false`
);
const data = await response.json();

// cocktail_sales will be zero/empty
console.log('Stock Sales Only:', data.general_sales.revenue);
```

---

### 3. Summary Only (No Category Breakdown)

Get high-level totals without detailed category breakdown:

```bash
GET /api/stock_tracker/hotel-killarney/periods/123/sales-analysis/?include_category_breakdown=false
```

**JavaScript:**
```javascript
const response = await fetch(
  `/api/stock_tracker/hotel-killarney/periods/123/sales-analysis/?include_category_breakdown=false`
);
const data = await response.json();

// category_breakdown will be empty array
console.log('Total Profit:', data.combined_sales.profit);
```

---

### 4. Stock Items Only, No Details

Minimal response with just stock sales summary:

```bash
GET /api/stock_tracker/hotel-killarney/periods/123/sales-analysis/?include_cocktails=false&include_category_breakdown=false
```

---

## Frontend Integration Examples

### React Component

```javascript
import React, { useState, useEffect } from 'react';

function PeriodSalesAnalysis({ hotelIdentifier, periodId }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const response = await fetch(
          `/api/stock_tracker/${hotelIdentifier}/periods/${periodId}/sales-analysis/`
        );
        const data = await response.json();
        setAnalysis(data);
      } catch (error) {
        console.error('Error fetching sales analysis:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [hotelIdentifier, periodId]);

  if (loading) return <div>Loading...</div>;
  if (!analysis) return <div>No data available</div>;

  return (
    <div className="sales-analysis">
      <h2>{analysis.period_name}</h2>
      <p>Period: {analysis.period_start} to {analysis.period_end}</p>
      
      <div className="totals">
        <h3>Combined Sales</h3>
        <p>Revenue: €{analysis.combined_sales.total_revenue.toFixed(2)}</p>
        <p>Cost: €{analysis.combined_sales.total_cost.toFixed(2)}</p>
        <p>Profit: €{analysis.combined_sales.profit.toFixed(2)}</p>
        <p>GP%: {analysis.combined_sales.gp_percentage}%</p>
      </div>
      
      <div className="breakdown">
        <h3>Category Breakdown</h3>
        {analysis.category_breakdown.map(cat => (
          <div key={cat.category}>
            <h4>{cat.name}</h4>
            <p>Revenue: €{cat.revenue.toFixed(2)}</p>
            <p>Profit: €{cat.profit.toFixed(2)}</p>
            <p>GP%: {cat.gp_percentage}%</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PeriodSalesAnalysis;
```

---

### Axios with Error Handling

```javascript
import axios from 'axios';

const fetchPeriodAnalysis = async (hotelIdentifier, periodId, options = {}) => {
  try {
    const params = new URLSearchParams();
    
    if (options.includeCocktails !== undefined) {
      params.append('include_cocktails', options.includeCocktails);
    }
    if (options.includeCategoryBreakdown !== undefined) {
      params.append('include_category_breakdown', options.includeCategoryBreakdown);
    }
    
    const url = `/api/stock_tracker/${hotelIdentifier}/periods/${periodId}/sales-analysis/`;
    const response = await axios.get(`${url}?${params.toString()}`);
    
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('Error fetching period analysis:', error);
    return {
      success: false,
      error: error.response?.data || error.message
    };
  }
};

// Usage
const result = await fetchPeriodAnalysis('hotel-killarney', 123, {
  includeCocktails: true,
  includeCategoryBreakdown: true
});

if (result.success) {
  console.log('Analysis:', result.data);
} else {
  console.error('Error:', result.error);
}
```

---

## Use Cases

### 1. Period Performance Dashboard

Display overall performance metrics for a closed period:

```javascript
const showPeriodPerformance = (analysis) => {
  const { combined_sales, breakdown_percentages } = analysis;
  
  return {
    totalRevenue: combined_sales.total_revenue,
    totalProfit: combined_sales.profit,
    gpPercentage: combined_sales.gp_percentage,
    stockContribution: breakdown_percentages.general_revenue_percent,
    cocktailContribution: breakdown_percentages.cocktail_revenue_percent
  };
};
```

---

### 2. Category Performance Comparison

Compare performance across different categories:

```javascript
const getCategoryPerformance = (analysis) => {
  return analysis.category_breakdown
    .sort((a, b) => b.revenue - a.revenue)
    .map(cat => ({
      category: cat.name,
      revenue: cat.revenue,
      profit: cat.profit,
      gpPercent: cat.gp_percentage
    }));
};
```

---

### 3. Stock vs Cocktail Analysis

Analyze the split between traditional sales and cocktails:

```javascript
const analyzeStockVsCocktails = (analysis) => {
  const { general_sales, cocktail_sales, breakdown_percentages } = analysis;
  
  return {
    stockSales: {
      revenue: general_sales.revenue,
      profit: general_sales.profit,
      gp: general_sales.gp_percentage,
      contribution: breakdown_percentages.general_revenue_percent
    },
    cocktailSales: {
      revenue: cocktail_sales.revenue,
      profit: cocktail_sales.profit,
      gp: cocktail_sales.gp_percentage,
      contribution: breakdown_percentages.cocktail_revenue_percent
    }
  };
};
```

---

### 4. Compare Multiple Periods

Fetch and compare multiple periods:

```javascript
const comparePeriodsAnalysis = async (hotelIdentifier, periodIds) => {
  const analyses = await Promise.all(
    periodIds.map(id => 
      fetch(`/api/stock_tracker/${hotelIdentifier}/periods/${id}/sales-analysis/`)
        .then(r => r.json())
    )
  );
  
  return analyses.map(a => ({
    period: a.period_name,
    revenue: a.combined_sales.total_revenue,
    profit: a.combined_sales.profit,
    gp: a.combined_sales.gp_percentage
  }));
};

// Usage
const comparison = await comparePeriodsAnalysis('hotel-killarney', [120, 121, 122]);
console.log(comparison);
```

---

## Important Notes

1. **Read-Only**: This endpoint does NOT modify any data - it only reads and aggregates

2. **Stocktake Matching**: Sales are matched to periods via stocktake. The endpoint finds the stocktake with matching `period_start` and `period_end` dates

3. **Standalone Sales**: Sales not linked to a stocktake are excluded from period analysis

4. **Cocktail Data**: Cocktail sales come from `CocktailConsumption` records within the period date range

5. **Performance**: For large datasets with many categories, consider setting `include_category_breakdown=false` for faster responses

6. **Closed Periods**: Works for both open and closed periods, but typically used for closed periods in reporting

7. **Zero Values**: If no sales exist for a period, all values will be 0.0 with appropriate structure maintained

---

## Error Responses

### 404 Not Found
Period doesn't exist:
```json
{
  "detail": "Not found."
}
```

### 400 Bad Request
Invalid period ID:
```json
{
  "error": "Invalid period ID"
}
```

---

## Related Endpoints

- **List Periods**: `GET /api/stock_tracker/<hotel>/periods/`
- **Period Details**: `GET /api/stock_tracker/<hotel>/periods/<id>/`
- **Sales List**: `GET /api/stock_tracker/<hotel>/sales/?stocktake=<id>`
- **Cocktail Sales Report**: `GET /api/stock_tracker/<hotel>/consumptions/sales-report/`

---

**Last Updated:** November 11, 2025
