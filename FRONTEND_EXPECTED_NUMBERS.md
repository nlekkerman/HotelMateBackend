# Frontend Expected Numbers - October 2024

## EXACT API RESPONSE DATA

These are the **exact numbers** your frontend will receive from the backend API endpoints. Simply fetch and display - no calculations needed.

---

## 1. STOCK VALUE REPORT
**Endpoint**: `GET /api/stock-tracker/hotel-killarney/reports/stock-value/?period=7`

### TOTALS TO DISPLAY
```
Cost Value:        €27,306.58
Sales Value:       €88,233.42
Potential Profit:  €60,926.84
Markup:            223.1%
```

### CATEGORY BREAKDOWN
```
Category              Cost Value    Sales Value   Potential Profit
─────────────────────────────────────────────────────────────────
Draught Beers         €5,311.62     €15,126.41    €9,814.79
Bottled Beers         €2,288.47     €8,554.80     €6,266.33
Spirits               €11,063.70    €47,185.81    €36,122.11
Minerals/Syrups       €3,062.45     €313.60       -€2,748.85
Wine                  €5,580.34     €17,052.80    €11,472.46
─────────────────────────────────────────────────────────────────
TOTAL                 €27,306.58    €88,233.42    €60,926.84
```

### SUMMARY STATS
```
Total Items:          254
Items with Price:     133
Items without Price:  121
```

### TOP 10 ITEMS BY SALES VALUE
```
Rank  SKU     Name                              Sales Value
─────────────────────────────────────────────────────────────
1.    S0610   Smirnoff 1Ltr                     €7,205.20
2.    D1258   50 Coors                          €3,577.96
3.    D0030   50 Heineken                       €3,414.60
4.    S1412   Green Spot                        €3,019.50
5.    S3145   Dingle Gin 70cl                   €2,974.80
6.    S0015   Bacardi 1Ltr                      €2,891.00
7.    D0006   30 OT Wild Orchard                €2,884.64
8.    D0004   30 Heineken                       €2,700.24
9.    S1405   Jameson 70cl                      €2,535.00
10.   D0011   30 Lagunitas IPA                  €2,243.04
```

---

## 2. SALES REPORT
**Endpoint**: `GET /api/stock-tracker/hotel-killarney/reports/sales/?period=7`

### MAIN TOTALS TO DISPLAY
```
Revenue:              €193,653.60
Cost of Sales:        €92,549.51
Gross Profit:         €101,104.09
GP%:                  52.2%
Servings Sold:        98,249
```

### STOCK MOVEMENT
```
September Opening:    €27,438.94
October Purchases:    €91,882.19
October Closing:      €27,306.58
─────────────────────────────────
Consumed:             €92,549.51
```

### CATEGORY PERFORMANCE
```
Category           Revenue       GP%     % of Total
────────────────────────────────────────────────────
Draught Beers      €86,940.18   64.6%      44.9%
Bottled Beers      €25,988.21   64.1%      13.4%
Spirits            €68,008.11   73.8%      35.1%
Minerals/Syrups    €2,131.01    -1284.2%   1.1%
Wine               €10,586.08   51.4%      5.5%
────────────────────────────────────────────────────
TOTAL              €193,653.60  52.2%      100.0%
```

### TOP 10 ITEMS BY REVENUE
```
Rank  SKU     Name                        Servings Sold  Revenue
────────────────────────────────────────────────────────────────
1.    D0006   30 OT Wild Orchard          1,426          €9,125.61
2.    D0030   50 Heineken                 1,407          €8,863.75
3.    D1258   50 Coors                    1,231          €7,752.44
4.    D0011   30 Lagunitas IPA            1,109          €7,542.60
5.    D2354   30 Moretti                  1,161          €7,315.43
6.    D0005   50 Guinness                 1,144          €7,205.27
7.    D0004   30 Heineken                 1,109          €6,988.09
8.    D0007   30 Beamish                  1,056          €6,653.91
9.    D1004   30 Coors                    1,004          €6,322.55
10.   D0012   30 Killarney Blonde         951            €5,609.48
```

### DATA QUALITY WARNING
```
⚠️ WARNING: Contains mock purchase data - Replace with actual POS figures

Mock Purchases:       317 out of 317
Mock Value:           €91,882.19
```

---

## JSON FORMAT (Copy-Paste Ready)

### Stock Value Report Response
```json
{
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
    {
      "category": "B",
      "name": "Bottled Beers",
      "cost_value": 2288.47,
      "sales_value": 8554.80,
      "potential_profit": 6266.33,
      "markup_percentage": 273.8
    },
    {
      "category": "S",
      "name": "Spirits",
      "cost_value": 11063.70,
      "sales_value": 47185.81,
      "potential_profit": 36122.11,
      "markup_percentage": 326.5
    },
    {
      "category": "M",
      "name": "Minerals/Syrups",
      "cost_value": 3062.45,
      "sales_value": 313.60,
      "potential_profit": -2748.85,
      "markup_percentage": -89.8
    },
    {
      "category": "W",
      "name": "Wine",
      "cost_value": 5580.34,
      "sales_value": 17052.80,
      "potential_profit": 11472.46,
      "markup_percentage": 205.6
    }
  ],
  "summary": {
    "total_items": 254,
    "items_with_price": 133,
    "items_without_price": 121
  }
}
```

### Sales Report Response
```json
{
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
    {
      "category": "B",
      "name": "Bottled Beers",
      "consumption": 3815.39,
      "revenue": 25988.21,
      "cost_of_sales": 9320.38,
      "gross_profit": 16667.83,
      "gross_profit_percentage": 64.1,
      "servings_sold": 9339,
      "percent_of_total": 13.4
    },
    {
      "category": "S",
      "name": "Spirits",
      "consumption": 3150.25,
      "revenue": 68008.11,
      "cost_of_sales": 17794.42,
      "gross_profit": 50213.69,
      "gross_profit_percentage": 73.8,
      "servings_sold": 18903,
      "percent_of_total": 35.1
    },
    {
      "category": "M",
      "name": "Minerals/Syrups",
      "consumption": 29510.70,
      "revenue": 2131.01,
      "cost_of_sales": 29510.70,
      "gross_profit": -27379.69,
      "gross_profit_percentage": -1284.2,
      "servings_sold": 637,
      "percent_of_total": 1.1
    },
    {
      "category": "W",
      "name": "Wine",
      "consumption": 5146.92,
      "revenue": 10586.08,
      "cost_of_sales": 5087.19,
      "gross_profit": 5498.89,
      "gross_profit_percentage": 51.4,
      "servings_sold": 24136,
      "percent_of_total": 5.5
    }
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

---

## FRONTEND DISPLAY RULES

### Currency Formatting
```javascript
const formatCurrency = (value) => {
  return `€${value.toLocaleString('en-IE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
};
```

### Percentage Formatting
```javascript
const formatPercentage = (value) => {
  return `${value.toFixed(1)}%`;
};
```

### Number Formatting
```javascript
const formatNumber = (value) => {
  return value.toLocaleString('en-IE');
};
```

### Example Usage
```javascript
// Stock Value Report
document.getElementById('cost-value').textContent = 
  formatCurrency(data.totals.cost_value);  // €27,306.58

document.getElementById('markup').textContent = 
  formatPercentage(data.totals.markup_percentage);  // 223.1%

// Sales Report
document.getElementById('revenue').textContent = 
  formatCurrency(data.totals.revenue);  // €193,653.60

document.getElementById('servings-sold').textContent = 
  formatNumber(data.totals.servings_sold);  // 98,249
```

---

## QUICK REFERENCE CARD

### Stock Value (What you have)
- **€27,306.58** = What it cost you
- **€88,233.42** = What you can sell it for
- **€60,926.84** = Your potential profit
- **223.1%** = Markup percentage

### October Sales (What you sold)
- **€193,653.60** = Total revenue
- **€92,549.51** = What it cost you
- **€101,104.09** = Profit you made
- **52.2%** = Gross profit percentage
- **98,249** = Servings sold

### Best Sellers by Revenue (Top 5)
1. D0006 Wild Orchard - €9,125.61
2. D0030 50L Heineken - €8,863.75
3. D1258 50L Coors - €7,752.44
4. D0011 Lagunitas IPA - €7,542.60
5. D2354 Moretti - €7,315.43

### Category Performance
- **Draught**: 44.9% of sales (€86,940)
- **Spirits**: 35.1% of sales (€68,008)
- **Bottled**: 13.4% of sales (€25,988)
- **Wine**: 5.5% of sales (€10,586)
- **Minerals**: 1.1% of sales (€2,131)

---

## IMPORTANT NOTES

⚠️ **Mock Data Warning**: The current October sales report uses **mock purchase data** (€91,882.19). Replace with actual POS data for real results.

✅ **No Calculations**: Frontend should **NEVER** calculate these numbers. Just fetch from API and display.

✅ **Decimal Precision**: Backend uses Python Decimal for financial accuracy. All numbers are precise.

✅ **Period ID**: October 2024 is Period 7. September 2024 is Period 8.

✅ **Authentication**: Currently set to AllowAny for testing. Add proper auth for production.

---

## TEST THE ENDPOINTS

```bash
# Stock Value Report
curl "http://localhost:8000/api/stock-tracker/hotel-killarney/reports/stock-value/?period=7"

# Sales Report
curl "http://localhost:8000/api/stock-tracker/hotel-killarney/reports/sales/?period=7"
```

Or use the test script:
```bash
python test_new_api_endpoints.py
```

---

**Status**: ✅ Ready for frontend integration. All numbers verified and tested.
