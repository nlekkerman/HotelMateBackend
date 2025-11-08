# Backend Report API Documentation

## Overview

**CRITICAL ARCHITECTURAL DECISION**: All stock value and sales calculations are performed in the backend Django views. The frontend should **ONLY** fetch and display the data—no calculations needed in JavaScript.

## API Endpoints

### 1. Stock Value Report

**Endpoint**: `GET /api/stock-tracker/{hotel_identifier}/reports/stock-value/`

**Query Parameters**:
- `period` (required): The StockPeriod ID (e.g., `7` for October 2024)

**Response Format**:
```json
{
  "period": {
    "id": 7,
    "period_name": "October 2024",
    "is_closed": true
  },
  "totals": {
    "cost_value": 27306.58,
    "sales_value": 88233.42,
    "potential_profit": 60926.84,
    "markup_percentage": 223.1
  },
  "categories": [
    {
      "category": "D",
      "name": "Draught Beers",
      "cost_value": 5311.62,
      "sales_value": 15126.41,
      "potential_profit": 9814.79,
      "markup_percentage": 184.8
    },
    // ... more categories
  ],
  "items": [
    {
      "sku": "S0610",
      "name": "Smirnoff 1Ltr",
      "category": "S",
      "cost_value": 1149.00,
      "sales_value": 7205.20,
      "potential_profit": 6056.20,
      "markup_percentage": 527.1,
      "has_price": true,
      "servings": 367.5,
      "menu_price": 19.60,
      "bottle_price": null
    },
    // ... more items
  ],
  "summary": {
    "total_items": 254,
    "items_with_price": 133,
    "items_without_price": 121
  }
}
```

**What This Tells You**:
- **Cost Value**: Total cost of current inventory (from closing stock snapshots)
- **Sales Value**: What you could sell current inventory for (servings × menu prices)
- **Potential Profit**: Sales Value - Cost Value
- **Markup %**: How much more you'd make vs what you paid

**Frontend Display Example**:
```javascript
async function displayStockValueReport(periodId) {
  const response = await fetch(
    `/api/stock-tracker/hotel-killarney/reports/stock-value/?period=${periodId}`
  );
  const data = await response.json();
  
  // Simply display the data - no calculations needed!
  document.getElementById('total-cost').textContent = 
    `€${data.totals.cost_value.toLocaleString()}`;
  document.getElementById('total-sales').textContent = 
    `€${data.totals.sales_value.toLocaleString()}`;
  document.getElementById('potential-profit').textContent = 
    `€${data.totals.potential_profit.toLocaleString()}`;
  document.getElementById('markup').textContent = 
    `${data.totals.markup_percentage.toFixed(1)}%`;
}
```

---

### 2. Sales Report

**Endpoint**: `GET /api/stock-tracker/{hotel_identifier}/reports/sales/`

**Query Parameters**:
- `period` (required): The StockPeriod ID (e.g., `7` for October 2024)

**Response Format**:
```json
{
  "period": {
    "id": 7,
    "period_name": "October 2024",
    "previous_period": "September 2024",
    "is_closed": true
  },
  "totals": {
    "revenue": 193653.60,
    "cost_of_sales": 92549.51,
    "gross_profit": 101104.09,
    "gross_profit_percentage": 52.2,
    "servings_sold": 98249
  },
  "stock_movement": {
    "sept_opening": 27438.94,
    "oct_purchases": 91882.19,
    "oct_closing": 27306.58,
    "consumed": 92549.51
  },
  "categories": [
    {
      "category": "D",
      "name": "Draught Beers",
      "consumption": 16026.25,
      "revenue": 86940.18,
      "cost_of_sales": 30836.82,
      "gross_profit": 56103.36,
      "gross_profit_percentage": 64.6,
      "servings_sold": 45234,
      "percent_of_total": 44.9
    },
    // ... more categories
  ],
  "items": [
    {
      "sku": "D0006",
      "name": "30 OT Wild Orchard",
      "category": "D",
      "consumption": 1426,
      "revenue": 9125.61,
      "cost_of_sales": 3251.73,
      "gross_profit": 5873.88,
      "gross_profit_percentage": 64.4,
      "has_price": true,
      "menu_price": 6.40
    },
    // ... more items
  ],
  "data_quality": {
    "has_mock_data": true,
    "warning": "Contains mock purchase data - Replace with actual POS figures",
    "mock_purchase_count": 317,
    "total_purchase_count": 317,
    "mock_purchase_value": 91882.19
  }
}
```

**What This Tells You**:
- **Revenue**: Total sales (consumed servings × menu prices)
- **Cost of Sales**: How much the consumed stock cost you
- **Gross Profit**: Revenue - Cost of Sales
- **GP%**: (Gross Profit ÷ Revenue) × 100
- **Servings Sold**: Total number of servings consumed

**Calculation Formula** (done in backend):
```
Sept Opening + Oct Purchases - Oct Closing = Consumption
Consumption × Menu Price = Revenue
```

**Frontend Display Example**:
```javascript
async function displaySalesReport(periodId) {
  const response = await fetch(
    `/api/stock-tracker/hotel-killarney/reports/sales/?period=${periodId}`
  );
  const data = await response.json();
  
  // Just display - no calculations!
  document.getElementById('revenue').textContent = 
    `€${data.totals.revenue.toLocaleString()}`;
  document.getElementById('cost-of-sales').textContent = 
    `€${data.totals.cost_of_sales.toLocaleString()}`;
  document.getElementById('gross-profit').textContent = 
    `€${data.totals.gross_profit.toLocaleString()}`;
  document.getElementById('gp-percentage').textContent = 
    `${data.totals.gross_profit_percentage.toFixed(1)}%`;
  
  // Show warning if mock data present
  if (data.data_quality.has_mock_data) {
    document.getElementById('warning').textContent = 
      `⚠️ ${data.data_quality.warning}`;
  }
}
```

---

## Mock Data Detection

The Sales Report includes a `data_quality` object that indicates whether the report contains mock purchase data:

- **`has_mock_data`**: `true` if any purchase movements have "Mock delivery" in their notes
- **`warning`**: Human-readable warning message
- **`mock_purchase_count`**: How many purchases are mock data
- **`total_purchase_count`**: Total purchases for the period
- **`mock_purchase_value`**: Total value of mock purchases

**When to show warnings**:
```javascript
if (data.data_quality.has_mock_data) {
  showWarningBanner(
    `This report contains ${data.data_quality.mock_purchase_count} ` +
    `mock purchases (€${data.data_quality.mock_purchase_value.toLocaleString()}). ` +
    `Replace with actual POS data for accurate results.`
  );
}
```

---

## Example: Full Report Page

```html
<!DOCTYPE html>
<html>
<head>
  <title>October 2024 Reports</title>
  <style>
    .report-section { margin: 20px; padding: 20px; border: 1px solid #ccc; }
    .warning { background: #fff3cd; padding: 10px; margin-bottom: 20px; }
    .metric { display: inline-block; margin: 10px 20px; }
    .metric label { display: block; font-size: 12px; color: #666; }
    .metric value { display: block; font-size: 24px; font-weight: bold; }
  </style>
</head>
<body>

<div class="report-section">
  <h2>Stock Value Report</h2>
  <div class="metric">
    <label>Cost Value</label>
    <value id="cost-value">Loading...</value>
  </div>
  <div class="metric">
    <label>Sales Value</label>
    <value id="sales-value">Loading...</value>
  </div>
  <div class="metric">
    <label>Potential Profit</label>
    <value id="potential-profit">Loading...</value>
  </div>
  <div class="metric">
    <label>Markup</label>
    <value id="markup">Loading...</value>
  </div>
</div>

<div class="report-section">
  <h2>Sales Report</h2>
  <div id="sales-warning" class="warning" style="display:none;"></div>
  <div class="metric">
    <label>Revenue</label>
    <value id="revenue">Loading...</value>
  </div>
  <div class="metric">
    <label>Cost of Sales</label>
    <value id="cost-of-sales">Loading...</value>
  </div>
  <div class="metric">
    <label>Gross Profit</label>
    <value id="gross-profit">Loading...</value>
  </div>
  <div class="metric">
    <label>GP%</label>
    <value id="gp-percentage">Loading...</value>
  </div>
  <div class="metric">
    <label>Servings Sold</label>
    <value id="servings-sold">Loading...</value>
  </div>
</div>

<script>
const PERIOD_ID = 7; // October 2024

async function loadReports() {
  try {
    // Load Stock Value Report
    const stockValueResp = await fetch(
      `/api/stock-tracker/hotel-killarney/reports/stock-value/?period=${PERIOD_ID}`
    );
    const stockValue = await stockValueResp.json();
    
    document.getElementById('cost-value').textContent = 
      `€${stockValue.totals.cost_value.toLocaleString('en-IE', {minimumFractionDigits: 2})}`;
    document.getElementById('sales-value').textContent = 
      `€${stockValue.totals.sales_value.toLocaleString('en-IE', {minimumFractionDigits: 2})}`;
    document.getElementById('potential-profit').textContent = 
      `€${stockValue.totals.potential_profit.toLocaleString('en-IE', {minimumFractionDigits: 2})}`;
    document.getElementById('markup').textContent = 
      `${stockValue.totals.markup_percentage.toFixed(1)}%`;
    
    // Load Sales Report
    const salesResp = await fetch(
      `/api/stock-tracker/hotel-killarney/reports/sales/?period=${PERIOD_ID}`
    );
    const sales = await salesResp.json();
    
    document.getElementById('revenue').textContent = 
      `€${sales.totals.revenue.toLocaleString('en-IE', {minimumFractionDigits: 2})}`;
    document.getElementById('cost-of-sales').textContent = 
      `€${sales.totals.cost_of_sales.toLocaleString('en-IE', {minimumFractionDigits: 2})}`;
    document.getElementById('gross-profit').textContent = 
      `€${sales.totals.gross_profit.toLocaleString('en-IE', {minimumFractionDigits: 2})}`;
    document.getElementById('gp-percentage').textContent = 
      `${sales.totals.gross_profit_percentage.toFixed(1)}%`;
    document.getElementById('servings-sold').textContent = 
      sales.totals.servings_sold.toLocaleString('en-IE');
    
    // Show warning if mock data
    if (sales.data_quality.has_mock_data) {
      const warning = document.getElementById('sales-warning');
      warning.textContent = `⚠️ ${sales.data_quality.warning}`;
      warning.style.display = 'block';
    }
    
  } catch (error) {
    console.error('Failed to load reports:', error);
    alert('Error loading reports. Please try again.');
  }
}

// Load reports when page loads
loadReports();
</script>

</body>
</html>
```

---

## Testing with curl

```bash
# Test Stock Value Report
curl "http://localhost:8000/api/stock-tracker/hotel-killarney/reports/stock-value/?period=7"

# Test Sales Report
curl "http://localhost:8000/api/stock-tracker/hotel-killarney/reports/sales/?period=7"
```

---

## Important Notes

1. **Period Must Be Closed**: Both reports require `is_closed=True` on the StockPeriod
2. **Previous Period Required**: Sales report needs a previous period for opening stock
3. **Menu Prices Required**: Items without `menu_price` won't contribute to revenue calculations
4. **Mock Data**: Check `data_quality.has_mock_data` to warn users about test data
5. **Decimal Precision**: All currency values use Python Decimal for accuracy
6. **No Frontend Calculations**: Everything is pre-calculated in Django views

---

## Summary

✓ **Stock Value Report**: Shows what your current inventory is worth  
✓ **Sales Report**: Shows what you sold and your profit margins  
✓ **Mock Data Detection**: Warns when test data is present  
✓ **Backend-Calculated**: Frontend just displays the numbers  
✓ **Production Ready**: Uses Decimal precision for financial accuracy
