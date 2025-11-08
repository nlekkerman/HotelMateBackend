# FRONTEND NUMBERS - COPY & PASTE READY

## DISPLAY 1: CURRENT STOCK VALUE (October 2024 Closing Stock)

### Main Numbers
```json
{
  "period": "October 2024",
  "asOfDate": "2024-10-31",
  "costValue": 27306.58,
  "salesValue": 88233.42,
  "potentialProfit": 60926.84,
  "markupPercentage": 223.1
}
```

### Category Breakdown
```json
{
  "draughtBeers": {
    "name": "Draught Beers",
    "costValue": 5311.62,
    "salesValue": 15126.41,
    "potentialProfit": 9814.79,
    "markupPercentage": 184.8,
    "itemsWithPrice": 14,
    "itemsWithoutPrice": 0
  },
  "bottledBeers": {
    "name": "Bottled Beers",
    "costValue": 2288.47,
    "salesValue": 8554.80,
    "potentialProfit": 6266.33,
    "markupPercentage": 273.8,
    "itemsWithPrice": 16,
    "itemsWithoutPrice": 5
  },
  "spirits": {
    "name": "Spirits",
    "costValue": 11063.70,
    "salesValue": 47185.81,
    "potentialProfit": 36122.11,
    "markupPercentage": 326.5,
    "itemsWithPrice": 76,
    "itemsWithoutPrice": 52
  },
  "minerals": {
    "name": "Minerals/Syrups",
    "costValue": 3062.45,
    "salesValue": 313.60,
    "potentialProfit": -2748.85,
    "markupPercentage": -89.8,
    "itemsWithPrice": 2,
    "itemsWithoutPrice": 45,
    "warning": "Most items missing menu prices"
  },
  "wine": {
    "name": "Wine",
    "costValue": 5580.34,
    "salesValue": 17052.80,
    "potentialProfit": 11472.46,
    "markupPercentage": 205.6,
    "itemsWithPrice": 25,
    "itemsWithoutPrice": 19
  }
}
```

---

## DISPLAY 2: OCTOBER SALES REPORT (WITH MOCK PURCHASES)

### Main Numbers
```json
{
  "period": "October 2024",
  "totalRevenue": 193653.60,
  "totalCost": 92014.55,
  "grossProfit": 101639.06,
  "grossProfitPercentage": 52.48,
  "servingsSold": 98248.89,
  "mockPurchaseValue": 91882.19,
  "hasMockData": true,
  "warning": "Contains mock purchase data - Replace with actual POS figures"
}
```

### Category Performance
```json
{
  "draughtBeers": {
    "name": "Draught Beers",
    "revenue": 86940.18,
    "costOfSales": 30776.71,
    "grossProfit": 56163.47,
    "grossProfitPercentage": 64.6,
    "servingsSold": 13796.40,
    "percentOfTotal": 44.9
  },
  "bottledBeers": {
    "name": "Bottled Beers",
    "revenue": 25988.21,
    "costOfSales": 9323.77,
    "grossProfit": 16664.44,
    "grossProfitPercentage": 64.1,
    "servingsSold": 5760.20,
    "percentOfTotal": 13.4
  },
  "spirits": {
    "name": "Spirits",
    "revenue": 68008.11,
    "costOfSales": 17667.47,
    "grossProfit": 50340.64,
    "grossProfitPercentage": 74.0,
    "servingsSold": 15344.13,
    "percentOfTotal": 35.1
  },
  "minerals": {
    "name": "Minerals/Syrups",
    "revenue": 2131.01,
    "costOfSales": 29497.50,
    "grossProfit": -27366.49,
    "grossProfitPercentage": -1284.2,
    "servingsSold": 62785.97,
    "percentOfTotal": 1.1,
    "warning": "Most items missing menu prices - negative GP"
  },
  "wine": {
    "name": "Wine",
    "revenue": 10586.08,
    "costOfSales": 4749.09,
    "grossProfit": 5836.99,
    "grossProfitPercentage": 55.1,
    "servingsSold": 562.19,
    "percentOfTotal": 5.5
  }
}
```

### Stock Movement Summary
```json
{
  "septemberOpening": 27438.94,
  "octoberPurchases": 91882.19,
  "octoberClosing": 27306.58,
  "consumed": 92014.55,
  "formula": "(27438.94 + 91882.19) - 27306.58 = 92014.55"
}
```

---

## SAMPLE DISPLAY COMPONENTS

### Display 1: Stock Value Card
```jsx
<div className="stock-value-card">
  <h2>Current Stock Value</h2>
  <p className="date">As of October 31, 2024</p>
  
  <div className="metrics">
    <div className="metric">
      <span className="label">📦 Cost Value</span>
      <span className="value">€27,306.58</span>
      <span className="subtitle">What you paid</span>
    </div>
    
    <div className="metric">
      <span className="label">💰 Sales Value</span>
      <span className="value success">€88,233.42</span>
      <span className="subtitle">Potential revenue</span>
    </div>
    
    <div className="metric">
      <span className="label">📈 Potential Profit</span>
      <span className="value success">€60,926.84</span>
      <span className="subtitle">223.1% markup</span>
    </div>
  </div>
</div>
```

### Display 2: Sales Report Card (WITH WARNING)
```jsx
<div className="sales-report-card">
  <h2>October 2024 Sales Report</h2>
  
  <div className="warning-banner">
    ⚠️ This report contains €91,882 of MOCK purchase data
    <br />
    Replace with actual POS/till figures when available
  </div>
  
  <div className="metrics">
    <div className="metric">
      <span className="label">💵 Total Revenue</span>
      <span className="value">€193,653.60</span>
    </div>
    
    <div className="metric">
      <span className="label">💰 Gross Profit</span>
      <span className="value success">€101,639.06</span>
      <span className="subtitle">52.5% GP</span>
    </div>
    
    <div className="metric">
      <span className="label">🍺 Servings Sold</span>
      <span className="value">98,249</span>
    </div>
  </div>
  
  <h3>Top Categories</h3>
  <ul>
    <li>Draught Beers: €86,940 (44.9%)</li>
    <li>Spirits: €68,008 (35.1%)</li>
    <li>Bottled Beers: €25,988 (13.4%)</li>
    <li>Wine: €10,586 (5.5%)</li>
    <li>Minerals: €2,131 (1.1%)</li>
  </ul>
</div>
```

---

## IMPORTANT WARNINGS TO DISPLAY

### For Display 1 (Stock Value):
```
⚠️ Minerals category shows negative profit because 45 items are missing menu prices
```

### For Display 2 (Sales Report):
```
⚠️ WARNING: This report contains MOCK purchase data
   
   • Mock purchases: €91,882.19
   • These are randomly generated delivery records
   • Replace with actual POS/till data when available
   
   The sales calculation is:
   (Sept Opening + Mock Purchases) - Oct Closing = Sales
   (€27,439 + €91,882) - €27,307 = €92,015 cost of sales
```

---

## CSS FOR WARNING BANNER

```css
.warning-banner {
  background: #FFF3CD;
  border: 2px solid #FFC107;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
  color: #856404;
  font-weight: 500;
  text-align: center;
}

.warning-banner strong {
  color: #856404;
  font-weight: 700;
}
```

---

## QUICK REFERENCE

**Display 1 Numbers (Real):**
- Cost: €27,306.58
- Sales: €88,233.42
- Profit: €60,926.84

**Display 2 Numbers (Mock):**
- Revenue: €193,653.60
- GP: €101,639.06 (52.5%)
- Servings: 98,249
- ⚠️ Mock Purchases: €91,882

**Always show warnings for Display 2!**
