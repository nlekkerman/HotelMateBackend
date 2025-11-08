# Frontend Display Guide - October 2024 Stock & Sales

## What Frontend Needs to Do
**DON'T calculate anything - just fetch and display the data!**

---

## DISPLAY 1: Current Stock Value

### What to Show
Show the October 2024 closing stock in two values:
- **Cost Value**: €27,306.58 (what we paid)
- **Sales Value**: €88,233.42 (what we can sell it for)
- **Potential Profit**: €60,926.84 (markup)

### API Endpoints
```
GET /api/stock-tracker/periods/?is_closed=true&ordering=-end_date&limit=1
GET /api/stock-tracker/snapshots/?period={period_id}
```

### Simple Fetch Example
```javascript
// 1. Get latest closed period
const period = await fetch('/api/stock-tracker/periods/?is_closed=true&ordering=-end_date&limit=1')
  .then(r => r.json())
  .then(data => data[0]);

// 2. Get all snapshots
const snapshots = await fetch(`/api/stock-tracker/snapshots/?period=${period.id}`)
  .then(r => r.json());

// 3. Calculate totals
let costValue = 0;
let salesValue = 0;

snapshots.forEach(snap => {
  // Cost value (what we paid) - just add it up
  costValue += parseFloat(snap.closing_stock_value);
  
  // Sales value (what we can sell it for)
  const item = snap.item;
  
  // Calculate servings in stock
  let servings;
  if (['D', 'B', 'M'].includes(item.category)) {
    servings = (parseFloat(snap.closing_full_units) * parseFloat(item.uom)) + 
               parseFloat(snap.closing_partial_units);
  } else {
    servings = (parseFloat(snap.closing_full_units) * parseFloat(item.uom)) + 
               (parseFloat(snap.closing_partial_units) * parseFloat(item.uom));
  }
  
  // Sales value = servings × menu price
  if (item.menu_price) {
    salesValue += servings * parseFloat(item.menu_price);
  }
});

const profit = salesValue - costValue;
```

### Display Component
```jsx
<div className="stock-value">
  <h2>Current Stock Value - October 31, 2024</h2>
  
  <div className="cards">
    <div className="card">
      <h3>📦 Cost Value</h3>
      <p>€27,306.58</p>
      <small>What you paid</small>
    </div>
    
    <div className="card">
      <h3>💰 Sales Value</h3>
      <p>€88,233.42</p>
      <small>What you can sell it for</small>
    </div>
    
    <div className="card">
      <h3>📈 Profit</h3>
      <p>€60,926.84</p>
      <small>223% markup</small>
    </div>
  </div>
</div>
```

---

## DISPLAY 2: October Sales Report (Mock Data)

### What to Show
Show October sales calculated from mock purchases:
- **Total Revenue**: €193,653.60
- **Gross Profit**: €101,639.06 (52.5%)
- **Servings Sold**: 98,249
- ⚠️ **Warning**: Contains mock purchase data

### API Endpoints
```
GET /api/stock-tracker/periods/?period_name=September%202024
GET /api/stock-tracker/periods/?period_name=October%202024
GET /api/stock-tracker/snapshots/?period={september_id}
GET /api/stock-tracker/snapshots/?period={october_id}
GET /api/stock-tracker/movements/?period={october_id}&movement_type=PURCHASE
```

### Simple Fetch Example
```javascript
// 1. Get both periods
const periods = await fetch('/api/stock-tracker/periods/').then(r => r.json());
const sept = periods.find(p => p.period_name === 'September 2024');
const oct = periods.find(p => p.period_name === 'October 2024');

// 2. Get snapshots for both
const [septSnaps, octSnaps, purchases] = await Promise.all([
  fetch(`/api/stock-tracker/snapshots/?period=${sept.id}`).then(r => r.json()),
  fetch(`/api/stock-tracker/snapshots/?period=${oct.id}`).then(r => r.json()),
  fetch(`/api/stock-tracker/movements/?period=${oct.id}&movement_type=PURCHASE`).then(r => r.json())
]);

// 3. Calculate (or just display hardcoded numbers for now)
const totalRevenue = 193653.60;
const grossProfit = 101639.06;
const servingsSold = 98249;
const mockPurchases = 91882.19;
```

### Display Component
```jsx
<div className="sales-report">
  <h2>October 2024 Sales Report</h2>
  
  {/* IMPORTANT: Show warning banner */}
  <div className="warning">
    ⚠️ Contains €91,882 of MOCK purchase data
    <br />
    Replace with actual POS data when available
  </div>
  
  <div className="cards">
    <div className="card">
      <h3>💵 Total Revenue</h3>
      <p>€193,653.60</p>
    </div>
    
    <div className="card">
      <h3>💰 Gross Profit</h3>
      <p>€101,639.06</p>
      <small>52.5% GP</small>
    </div>
    
    <div className="card">
      <h3>🍺 Servings Sold</h3>
      <p>98,249</p>
    </div>
  </div>
  
  <h3>Sales by Category</h3>
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

## CSS Styling

```css
.stock-value, .sales-report {
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin: 20px 0;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
}

.card h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #666;
}

.card p {
  margin: 10px 0;
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.card small {
  color: #999;
  font-size: 14px;
}

.warning {
  background: #FFF3CD;
  border: 2px solid #FFC107;
  padding: 16px;
  border-radius: 8px;
  margin: 20px 0;
  color: #856404;
  font-weight: 500;
  text-align: center;
}
```

---

## Quick Numbers Reference

### Display 1: Current Stock Value
```
Cost Value:     €27,306.58
Sales Value:    €88,233.42
Profit:         €60,926.84
```

### Display 2: October Sales (Mock)
```
Revenue:        €193,653.60
Gross Profit:   €101,639.06
GP%:            52.5%
Servings:       98,249
Mock Purchases: €91,882.19
```

### By Category (Sales)
```
Draught:   €86,940 (44.9%)
Spirits:   €68,008 (35.1%)
Bottled:   €25,988 (13.4%)
Wine:      €10,586 (5.5%)
Minerals:  €2,131 (1.1%)
```

---

## IMPORTANT

1. **Always show warning** on Display 2 about mock data
2. **Don't do heavy calculations** in frontend - just sum up values
3. **Cost Value** comes directly from `closing_stock_value` field
4. **Sales Value** = calculate servings × menu_price
5. **Mock purchases** = €91,882 (hardcoded for now)

---

## Files to Use

- Read this file for API endpoints and display logic
- Copy numbers from `FRONTEND_NUMBERS_COPY_PASTE.md`
- Copy full calculation examples from `FRONTEND_OCTOBER_SALES_GUIDE.md` (if needed)
