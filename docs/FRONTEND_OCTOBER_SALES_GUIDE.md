# Frontend Guide: October 2024 Stock & Sales Display

## Overview
This guide explains how to display TWO different views for October 2024:

### 1. CURRENT STOCK VALUE (From Closed Period)
Shows the **October 2024 closing stock** in two ways:
- **Cost Value**: €27,306.58 - What you PAID for current inventory
- **Sales Value**: What you can SELL it for at menu prices
- **Potential Profit**: Markup between cost and selling price

### 2. OCTOBER SALES REPORT (With Mock Data)
Calculated from:
- **September 2024 Opening Stock** (created from targets)
- **October 2024 Purchases** (mock delivery data - €91,882)
- **October 2024 Closing Stock** (actual stocktake)
- **Result**: Sales = (Opening + Purchases) - Closing = **€193,653.60**

⚠️ **The sales data contains MOCK purchases - for display purposes only**

---

## SECTION A: CURRENT STOCK VALUE DISPLAY

### What to Show
Display the **October 2024 closing stock** (most recent closed period) with:
1. **Cost Value**: What you paid for inventory (€27,306.58)
2. **Sales Value**: What you can sell it for at menu prices
3. **Potential Profit**: Markup on current stock

### API Endpoints Required

#### 1. Get the Most Recent Closed Period
```http
GET /api/stock-tracker/periods/?is_closed=true&ordering=-end_date
```

**Response:**
```json
[
  {
    "id": 1,
    "period_name": "October 2024",
    "period_type": "MONTHLY",
    "start_date": "2024-10-01",
    "end_date": "2024-10-31",
    "is_closed": true,
    "year": 2024,
    "month": 10
  }
]
```

#### 2. Get Closing Stock Snapshots
```http
GET /api/stock-tracker/snapshots/?period=<period_id>
```

**Response:**
```json
[
  {
    "id": 1,
    "item": {
      "id": 1,
      "sku": "D0001",
      "name": "Guinness Keg 50L",
      "category": "D",
      "uom": 88.0,
      "menu_price": "6.30",
      "bottle_price": null
    },
    "closing_full_units": "2.00",
    "closing_partial_units": "15.5000",
    "closing_stock_value": "304.66"
  }
]
```

### Calculation Logic
```javascript
// Get October closing snapshots
const octoberSnapshots = await fetch(
  `/api/stock-tracker/snapshots/?period=${octoberPeriod.id}`
).then(r => r.json());

let totalCostValue = 0;
let totalSalesValue = 0;

octoberSnapshots.forEach(snapshot => {
  const item = snapshot.item;
  
  // 1. Cost Value (what we paid)
  totalCostValue += parseFloat(snapshot.closing_stock_value);
  
  // 2. Calculate servings in stock
  let servings;
  if (['D', 'B', 'M'].includes(item.category)) {
    servings = (parseFloat(snapshot.closing_full_units) * parseFloat(item.uom)) + 
               parseFloat(snapshot.closing_partial_units);
  } else {
    // S, W
    servings = (parseFloat(snapshot.closing_full_units) * parseFloat(item.uom)) + 
               (parseFloat(snapshot.closing_partial_units) * parseFloat(item.uom));
  }
  
  // 3. Sales Value (what we can sell it for)
  if (item.category === 'W' && item.bottle_price) {
    // Wine by bottle
    const bottles = parseFloat(snapshot.closing_full_units);
    totalSalesValue += bottles * parseFloat(item.bottle_price);
  } else if (item.menu_price) {
    // By serving
    totalSalesValue += servings * parseFloat(item.menu_price);
  }
});

const potentialProfit = totalSalesValue - totalCostValue;
const markupPercentage = (potentialProfit / totalCostValue) * 100;
```

### Display Component
```jsx
<div className="stock-value-dashboard">
  <h2>Current Stock Value (October 31, 2024)</h2>
  
  <div className="value-cards">
    <div className="card">
      <h3>📦 Cost Value</h3>
      <p className="subtitle">What You Paid</p>
      <p className="amount">€{totalCostValue.toLocaleString('en-IE', {minimumFractionDigits: 2})}</p>
      <small>Your investment in inventory</small>
    </div>
    
    <div className="card">
      <h3>💰 Sales Value</h3>
      <p className="subtitle">Potential Revenue</p>
      <p className="amount success">€{totalSalesValue.toLocaleString('en-IE', {minimumFractionDigits: 2})}</p>
      <small>If you sold all current stock</small>
    </div>
    
    <div className="card">
      <h3>📈 Potential Profit</h3>
      <p className="subtitle">Your Markup</p>
      <p className="amount success">€{potentialProfit.toLocaleString('en-IE', {minimumFractionDigits: 2})}</p>
      <p className="percentage">{markupPercentage.toFixed(1)}%</p>
    </div>
  </div>
</div>
```

---

## SECTION B: OCTOBER SALES REPORT (WITH MOCK DATA)

### What to Show
Display **October 2024 sales** calculated from:
- September opening stock
- October purchases (MOCK DATA)
- October closing stock
- **Total Sales**: €193,653.60
- **Gross Profit**: €101,639.06 (52.5%)

⚠️ **Always show warning that purchases are MOCK DATA**

---

## HOW TO GET THE DATA: STEP-BY-STEP

### DISPLAY 1: Current Stock Value (What We Have Now)

**Goal**: Show current inventory value at COST vs potential SALES value

**Step 1**: Get the most recent closed period
```javascript
const response = await fetch('/api/stock-tracker/periods/?is_closed=true&ordering=-end_date');
const periods = await response.json();
const latestPeriod = periods[0]; // October 2024
```

**Step 2**: Get all closing stock snapshots for that period
```javascript
const snapshots = await fetch(`/api/stock-tracker/snapshots/?period=${latestPeriod.id}`);
const stockData = await snapshots.json();
```

**Step 3**: Calculate TWO values for each item
```javascript
let totalCostValue = 0;      // What we PAID for stock
let totalSalesValue = 0;     // What we can SELL it for

stockData.forEach(snapshot => {
  // 1. COST VALUE (what we paid)
  totalCostValue += parseFloat(snapshot.closing_stock_value);
  
  // 2. SALES VALUE (what we can sell it for)
  const item = snapshot.item;
  const servings = calculateServings(snapshot, item); // See calculation below
  
  if (item.menu_price) {
    totalSalesValue += servings * parseFloat(item.menu_price);
  }
});

const potentialProfit = totalSalesValue - totalCostValue;
```

**Result**:
- Cost Value: €27,306.58 (from `closing_stock_value`)
- Sales Value: Calculate from menu prices
- Potential Profit: Sales Value - Cost Value

---

### DISPLAY 2: October Sales Report (Mock Data)

**Goal**: Show October sales = (Sept Opening + Purchases) - Oct Closing

**Step 1**: Get BOTH September and October periods
```javascript
const allPeriods = await fetch('/api/stock-tracker/periods/').then(r => r.json());
const septemberPeriod = allPeriods.find(p => p.period_name === 'September 2024');
const octoberPeriod = allPeriods.find(p => p.period_name === 'October 2024');
```

**Step 2**: Get snapshots for BOTH periods
```javascript
const septSnapshots = await fetch(
  `/api/stock-tracker/snapshots/?period=${septemberPeriod.id}`
).then(r => r.json());

const octSnapshots = await fetch(
  `/api/stock-tracker/snapshots/?period=${octoberPeriod.id}`
).then(r => r.json());
```

**Step 3**: Get October purchases (MOCK DATA)
```javascript
const purchases = await fetch(
  `/api/stock-tracker/movements/?period=${octoberPeriod.id}&movement_type=PURCHASE`
).then(r => r.json());
```

**Step 4**: Calculate sales per item
```javascript
// For each item:
// Opening Servings (Sept) + Purchased Servings - Closing Servings (Oct) = Consumed
const consumed = septServings + purchasedServings - octServings;
const revenue = consumed * menuPrice;
```

**Result**:
- Total Sales: €193,653.60
- Gross Profit: €101,639.06 (52.5%)
- ⚠️ Contains €91,882 of MOCK purchases

---

## QUICK API REFERENCE

### For Display 1: Current Stock Value (Real Data)
**Purpose**: Show what we have in stock at COST vs potential SALES value

**Endpoints**:
```http
GET /api/stock-tracker/periods/?is_closed=true&ordering=-end_date
GET /api/stock-tracker/snapshots/?period={period_id}
```

**Returns**:
- Cost Value: €27,306.58 (what we paid)
- Sales Value: Calculate from menu_price × servings
- Potential Profit: markup on current stock

---

### For Display 2: October Sales Report (Mock Data)
**Purpose**: Show October sales using mock purchases

**Endpoints**:
```http
# 1. Get periods
GET /api/stock-tracker/periods/?period_name=September%202024
GET /api/stock-tracker/periods/?period_name=October%202024

# 2. Get opening stock (September closing)
GET /api/stock-tracker/snapshots/?period={september_id}

# 3. Get closing stock (October closing)
GET /api/stock-tracker/snapshots/?period={october_id}

# 4. Get purchases (MOCK DATA - €91,882)
GET /api/stock-tracker/movements/?period={october_id}&movement_type=PURCHASE
```

**Returns**:
- Total Sales: €193,653.60
- Gross Profit: €101,639.06 (52.5%)
- ⚠️ Warning: Contains mock purchase data

---

## COMPLETE WORKING EXAMPLE

### Fetch Function for Display 1: Current Stock Value
```javascript
async function fetchCurrentStockValue() {
  try {
    // 1. Get latest closed period (October 2024)
    const periodsResponse = await fetch(
      '/api/stock-tracker/periods/?is_closed=true&ordering=-end_date&limit=1'
    );
    const periods = await periodsResponse.json();
    
    if (!periods.length) {
      throw new Error('No closed periods found');
    }
    
    const latestPeriod = periods[0];
    console.log(`Latest period: ${latestPeriod.period_name}`);
    
    // 2. Get all closing stock snapshots
    const snapshotsResponse = await fetch(
      `/api/stock-tracker/snapshots/?period=${latestPeriod.id}`
    );
    const snapshots = await snapshotsResponse.json();
    
    // 3. Calculate values
    let totalCostValue = 0;
    let totalSalesValue = 0;
    const categoryBreakdown = {};
    
    snapshots.forEach(snapshot => {
      const item = snapshot.item;
      const category = item.category;
      
      // Initialize category if needed
      if (!categoryBreakdown[category]) {
        categoryBreakdown[category] = {
          costValue: 0,
          salesValue: 0
        };
      }
      
      // Cost value (what we paid)
      const costValue = parseFloat(snapshot.closing_stock_value);
      totalCostValue += costValue;
      categoryBreakdown[category].costValue += costValue;
      
      // Calculate servings
      let servings;
      if (['D', 'B', 'M'].includes(category)) {
        servings = 
          (parseFloat(snapshot.closing_full_units) * parseFloat(item.uom)) + 
          parseFloat(snapshot.closing_partial_units);
      } else {
        // S, W
        servings = 
          (parseFloat(snapshot.closing_full_units) * parseFloat(item.uom)) + 
          (parseFloat(snapshot.closing_partial_units) * parseFloat(item.uom));
      }
      
      // Sales value (what we can sell it for)
      let salesValue = 0;
      if (category === 'W' && item.bottle_price) {
        const bottles = parseFloat(snapshot.closing_full_units);
        salesValue = bottles * parseFloat(item.bottle_price);
      } else if (item.menu_price) {
        salesValue = servings * parseFloat(item.menu_price);
      }
      
      totalSalesValue += salesValue;
      categoryBreakdown[category].salesValue += salesValue;
    });
    
    const potentialProfit = totalSalesValue - totalCostValue;
    const markupPercentage = (potentialProfit / totalCostValue) * 100;
    
    return {
      period: latestPeriod,
      costValue: totalCostValue,
      salesValue: totalSalesValue,
      potentialProfit: potentialProfit,
      markupPercentage: markupPercentage,
      categoryBreakdown: categoryBreakdown
    };
    
  } catch (error) {
    console.error('Error fetching stock value:', error);
    throw error;
  }
}

// Usage:
const stockValue = await fetchCurrentStockValue();
console.log(`Cost Value: €${stockValue.costValue.toFixed(2)}`);
console.log(`Sales Value: €${stockValue.salesValue.toFixed(2)}`);
console.log(`Potential Profit: €${stockValue.potentialProfit.toFixed(2)}`);
```

---

### Fetch Function for Display 2: October Sales Report
```javascript
async function fetchOctoberSalesReport() {
  try {
    // 1. Get periods
    const periodsResponse = await fetch('/api/stock-tracker/periods/');
    const periods = await periodsResponse.json();
    
    const septemberPeriod = periods.find(p => p.period_name === 'September 2024');
    const octoberPeriod = periods.find(p => p.period_name === 'October 2024');
    
    if (!septemberPeriod || !octoberPeriod) {
      throw new Error('Required periods not found');
    }
    
    // 2. Fetch all data in parallel
    const [septSnapshots, octSnapshots, purchases] = await Promise.all([
      fetch(`/api/stock-tracker/snapshots/?period=${septemberPeriod.id}`).then(r => r.json()),
      fetch(`/api/stock-tracker/snapshots/?period=${octoberPeriod.id}`).then(r => r.json()),
      fetch(`/api/stock-tracker/movements/?period=${octoberPeriod.id}&movement_type=PURCHASE`).then(r => r.json())
    ]);
    
    // 3. Create lookup for October snapshots
    const octLookup = {};
    octSnapshots.forEach(s => octLookup[s.item.id] = s);
    
    // 4. Create lookup for purchases by item
    const purchasesByItem = {};
    purchases.forEach(p => {
      if (!purchasesByItem[p.item.id]) {
        purchasesByItem[p.item.id] = 0;
      }
      purchasesByItem[p.item.id] += parseFloat(p.quantity);
    });
    
    // 5. Calculate sales
    let totalRevenue = 0;
    let totalCost = 0;
    let totalServingsSold = 0;
    const categoryResults = {};
    
    septSnapshots.forEach(septSnap => {
      const octSnap = octLookup[septSnap.item.id];
      if (!octSnap) return;
      
      const item = septSnap.item;
      const category = item.category;
      const purchasedServings = purchasesByItem[item.id] || 0;
      
      // Calculate servings
      let septServings, octServings;
      if (['D', 'B', 'M'].includes(category)) {
        septServings = 
          (parseFloat(septSnap.closing_full_units) * parseFloat(item.uom)) + 
          parseFloat(septSnap.closing_partial_units);
        octServings = 
          (parseFloat(octSnap.closing_full_units) * parseFloat(item.uom)) + 
          parseFloat(octSnap.closing_partial_units);
      } else {
        septServings = 
          (parseFloat(septSnap.closing_full_units) * parseFloat(item.uom)) + 
          (parseFloat(septSnap.closing_partial_units) * parseFloat(item.uom));
        octServings = 
          (parseFloat(octSnap.closing_full_units) * parseFloat(item.uom)) + 
          (parseFloat(octSnap.closing_partial_units) * parseFloat(item.uom));
      }
      
      // Consumption = Opening + Purchases - Closing
      const consumption = septServings + purchasedServings - octServings;
      
      if (consumption > 0) {
        // Calculate revenue
        let revenue = 0;
        if (category === 'W' && item.bottle_price) {
          const bottles = consumption / parseFloat(item.uom);
          revenue = bottles * parseFloat(item.bottle_price);
        } else if (item.menu_price) {
          revenue = consumption * parseFloat(item.menu_price);
        }
        
        totalRevenue += revenue;
        totalServingsSold += consumption;
        
        // Track by category
        if (!categoryResults[category]) {
          categoryResults[category] = {
            revenue: 0,
            servings: 0
          };
        }
        categoryResults[category].revenue += revenue;
        categoryResults[category].servings += consumption;
      }
    });
    
    // Calculate total cost
    septSnapshots.forEach(s => totalCost += parseFloat(s.closing_stock_value));
    purchases.forEach(p => totalCost += parseFloat(p.quantity) * parseFloat(p.unit_cost));
    octSnapshots.forEach(s => totalCost -= parseFloat(s.closing_stock_value));
    
    const grossProfit = totalRevenue - totalCost;
    const grossProfitPercentage = (grossProfit / totalRevenue) * 100;
    
    // Calculate purchase totals
    const totalPurchaseValue = purchases.reduce((sum, p) => 
      sum + (parseFloat(p.quantity) * parseFloat(p.unit_cost)), 0
    );
    
    return {
      totalRevenue: totalRevenue,
      totalCost: totalCost,
      grossProfit: grossProfit,
      grossProfitPercentage: grossProfitPercentage,
      servingsSold: totalServingsSold,
      categoryResults: categoryResults,
      hasMockData: true,
      mockPurchaseValue: totalPurchaseValue
    };
    
  } catch (error) {
    console.error('Error fetching sales report:', error);
    throw error;
  }
}

// Usage:
const salesReport = await fetchOctoberSalesReport();
console.log(`Total Revenue: €${salesReport.totalRevenue.toFixed(2)}`);
console.log(`Gross Profit: €${salesReport.grossProfit.toFixed(2)} (${salesReport.grossProfitPercentage.toFixed(1)}%)`);
console.log(`⚠️ Contains €${salesReport.mockPurchaseValue.toFixed(2)} of mock purchases`);
```

---

## API Endpoints Needed

### 1. Get Stock Periods
```http
GET /api/stock-tracker/periods/
```

**Response:**
```json
[
  {
    "id": 1,
    "period_name": "October 2024",
    "period_type": "MONTHLY",
    "start_date": "2024-10-01",
    "end_date": "2024-10-31",
    "is_closed": true,
    "year": 2024,
    "month": 10
  },
  {
    "id": 2,
    "period_name": "September 2024",
    "period_type": "MONTHLY",
    "start_date": "2024-09-01",
    "end_date": "2024-09-30",
    "is_closed": true,
    "year": 2024,
    "month": 9
  }
]
```

### 2. Get Period Snapshots
```http
GET /api/stock-tracker/snapshots/?period=<period_id>
```

**Response:**
```json
[
  {
    "id": 1,
    "item": {
      "id": 1,
      "sku": "D0001",
      "name": "Guinness Keg 50L",
      "category": "D",
      "uom": 88.0,
      "menu_price": "6.30",
      "unit_cost": "140.0000"
    },
    "period": 1,
    "closing_full_units": "2.00",
    "closing_partial_units": "15.5000",
    "unit_cost": "140.0000",
    "cost_per_serving": "1.5909",
    "closing_stock_value": "304.66",
    "menu_price": "6.30"
  }
]
```

### 3. Get Period Purchases
```http
GET /api/stock-tracker/movements/?period=<period_id>&movement_type=PURCHASE
```

**Response:**
```json
[
  {
    "id": 1,
    "item": {
      "id": 1,
      "sku": "D0001",
      "name": "Guinness Keg 50L"
    },
    "movement_type": "PURCHASE",
    "quantity": "176.00",
    "unit_cost": "1.5909",
    "reference": "INV-OCT-1-1234",
    "timestamp": "2024-10-03T10:30:00Z"
  }
]
```

---

## Data Calculation Logic

### Step 1: Fetch Data for Both Periods
```javascript
// Fetch September and October periods
const periods = await fetch('/api/stock-tracker/periods/').then(r => r.json());
const septemberPeriod = periods.find(p => p.period_name === 'September 2024');
const octoberPeriod = periods.find(p => p.period_name === 'October 2024');

// Fetch snapshots for both periods
const septemberSnapshots = await fetch(
  `/api/stock-tracker/snapshots/?period=${septemberPeriod.id}`
).then(r => r.json());

const octoberSnapshots = await fetch(
  `/api/stock-tracker/snapshots/?period=${octoberPeriod.id}`
).then(r => r.json());

// Fetch October purchases
const octoberPurchases = await fetch(
  `/api/stock-tracker/movements/?period=${octoberPeriod.id}&movement_type=PURCHASE`
).then(r => r.json());
```

### Step 2: Calculate Sales by Category
```javascript
const categories = {
  'D': { name: 'Draught Beers', code: 'D' },
  'B': { name: 'Bottled Beers', code: 'B' },
  'S': { name: 'Spirits', code: 'S' },
  'M': { name: 'Minerals/Syrups', code: 'M' },
  'W': { name: 'Wine', code: 'W' }
};

const salesByCategory = {};

// Initialize categories
Object.keys(categories).forEach(code => {
  salesByCategory[code] = {
    name: categories[code].name,
    septemberValue: 0,
    purchaseValue: 0,
    octoberValue: 0,
    consumptionCost: 0,
    servingsSold: 0,
    revenue: 0,
    items: []
  };
});

// Calculate September closing values
septemberSnapshots.forEach(snapshot => {
  const category = snapshot.item.category;
  salesByCategory[category].septemberValue += parseFloat(snapshot.closing_stock_value);
});

// Calculate October closing values
const octoberLookup = {};
octoberSnapshots.forEach(snapshot => {
  const category = snapshot.item.category;
  salesByCategory[category].octoberValue += parseFloat(snapshot.closing_stock_value);
  octoberLookup[snapshot.item.id] = snapshot;
});

// Calculate purchase values
octoberPurchases.forEach(purchase => {
  const category = purchase.item.sku[0]; // Category from SKU prefix
  const purchaseValue = parseFloat(purchase.quantity) * parseFloat(purchase.unit_cost);
  salesByCategory[category].purchaseValue += purchaseValue;
});
```

### Step 3: Calculate Item-Level Consumption
```javascript
// Group purchases by item
const purchasesByItem = {};
octoberPurchases.forEach(purchase => {
  if (!purchasesByItem[purchase.item.id]) {
    purchasesByItem[purchase.item.id] = 0;
  }
  purchasesByItem[purchase.item.id] += parseFloat(purchase.quantity);
});

// Calculate consumption per item
septemberSnapshots.forEach(septSnapshot => {
  const octSnapshot = octoberLookup[septSnapshot.item.id];
  if (!octSnapshot) return;

  const item = septSnapshot.item;
  const category = item.category;
  const uom = parseFloat(item.uom);
  const purchasedServings = purchasesByItem[item.id] || 0;

  // Calculate servings
  let septServings, octServings;
  
  if (['D', 'B', 'M'].includes(category)) {
    // Full units converted + partial units
    septServings = (parseFloat(septSnapshot.closing_full_units) * uom) + 
                   parseFloat(septSnapshot.closing_partial_units);
    octServings = (parseFloat(octSnapshot.closing_full_units) * uom) + 
                  parseFloat(octSnapshot.closing_partial_units);
  } else {
    // S, W: Bottles + percentage
    septServings = (parseFloat(septSnapshot.closing_full_units) * uom) + 
                   (parseFloat(septSnapshot.closing_partial_units) * uom);
    octServings = (parseFloat(octSnapshot.closing_full_units) * uom) + 
                  (parseFloat(octSnapshot.closing_partial_units) * uom);
  }

  // Consumption = Opening + Purchases - Closing
  const consumption = septServings + purchasedServings - octServings;

  if (consumption > 0) {
    salesByCategory[category].servingsSold += consumption;

    // Calculate revenue
    let itemRevenue = 0;
    if (category === 'W' && item.bottle_price) {
      // Wine sold by bottle
      const bottlesSold = consumption / uom;
      itemRevenue = bottlesSold * parseFloat(item.bottle_price);
    } else if (item.menu_price) {
      // Sold by serving
      itemRevenue = consumption * parseFloat(item.menu_price);
    }

    salesByCategory[category].revenue += itemRevenue;

    // Store item details
    salesByCategory[category].items.push({
      sku: item.sku,
      name: item.name,
      servingsSold: consumption,
      revenue: itemRevenue,
      menuPrice: item.menu_price
    });
  }
});

// Calculate consumption cost
Object.keys(salesByCategory).forEach(code => {
  const cat = salesByCategory[code];
  cat.consumptionCost = cat.septemberValue + cat.purchaseValue - cat.octoberValue;
});
```

### Step 4: Calculate Totals
```javascript
const totals = {
  septemberValue: 0,
  purchaseValue: 0,
  octoberValue: 0,
  consumptionCost: 0,
  servingsSold: 0,
  revenue: 0
};

Object.values(salesByCategory).forEach(category => {
  totals.septemberValue += category.septemberValue;
  totals.purchaseValue += category.purchaseValue;
  totals.octoberValue += category.octoberValue;
  totals.consumptionCost += category.consumptionCost;
  totals.servingsSold += category.servingsSold;
  totals.revenue += category.revenue;
});

const grossProfit = totals.revenue - totals.consumptionCost;
const grossProfitPercentage = (grossProfit / totals.revenue) * 100;
```

---

## Display Components

### 1. Summary Dashboard
```jsx
<div className="sales-summary">
  <h2>October 2024 Sales Report</h2>
  
  <div className="summary-cards">
    <div className="card">
      <h3>Total Revenue</h3>
      <p className="amount">€{totals.revenue.toLocaleString('en-IE', {minimumFractionDigits: 2})}</p>
    </div>
    
    <div className="card">
      <h3>Cost of Sales</h3>
      <p className="amount">€{totals.consumptionCost.toLocaleString('en-IE', {minimumFractionDigits: 2})}</p>
    </div>
    
    <div className="card">
      <h3>Gross Profit</h3>
      <p className="amount success">€{grossProfit.toLocaleString('en-IE', {minimumFractionDigits: 2})}</p>
      <p className="percentage">{grossProfitPercentage.toFixed(1)}%</p>
    </div>
    
    <div className="card">
      <h3>Servings Sold</h3>
      <p className="amount">{totals.servingsSold.toLocaleString('en-IE', {maximumFractionDigits: 0})}</p>
    </div>
  </div>

  <p className="warning">⚠️ This contains MOCK purchase data - Replace with actual POS figures</p>
</div>
```

### 2. Category Breakdown Table
```jsx
<table className="category-breakdown">
  <thead>
    <tr>
      <th>Category</th>
      <th>Sept Opening</th>
      <th>Purchases</th>
      <th>Oct Closing</th>
      <th>Consumed</th>
      <th>Revenue</th>
      <th>GP%</th>
    </tr>
  </thead>
  <tbody>
    {Object.values(salesByCategory).map(category => {
      const categoryGP = category.revenue > 0 
        ? ((category.revenue - category.consumptionCost) / category.revenue) * 100 
        : 0;
      
      return (
        <tr key={category.name}>
          <td><strong>{category.name}</strong></td>
          <td>€{category.septemberValue.toFixed(2)}</td>
          <td>€{category.purchaseValue.toFixed(2)}</td>
          <td>€{category.octoberValue.toFixed(2)}</td>
          <td>€{category.consumptionCost.toFixed(2)}</td>
          <td>€{category.revenue.toFixed(2)}</td>
          <td className={categoryGP > 60 ? 'success' : 'warning'}>
            {categoryGP.toFixed(1)}%
          </td>
        </tr>
      );
    })}
  </tbody>
  <tfoot>
    <tr>
      <th>TOTAL</th>
      <th>€{totals.septemberValue.toFixed(2)}</th>
      <th>€{totals.purchaseValue.toFixed(2)}</th>
      <th>€{totals.octoberValue.toFixed(2)}</th>
      <th>€{totals.consumptionCost.toFixed(2)}</th>
      <th>€{totals.revenue.toFixed(2)}</th>
      <th>{grossProfitPercentage.toFixed(1)}%</th>
    </tr>
  </tfoot>
</table>
```

### 3. Category Chart (Chart.js / Recharts)
```jsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const chartData = Object.values(salesByCategory).map(cat => ({
  category: cat.name,
  revenue: cat.revenue,
  cost: cat.consumptionCost
}));

<BarChart width={800} height={400} data={chartData}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="category" />
  <YAxis />
  <Tooltip formatter={(value) => `€${value.toFixed(2)}`} />
  <Legend />
  <Bar dataKey="revenue" fill="#4CAF50" name="Revenue" />
  <Bar dataKey="cost" fill="#FF9800" name="Cost" />
</BarChart>
```

### 4. Top Selling Items
```jsx
// Get all items from all categories and sort by revenue
const allItems = [];
Object.values(salesByCategory).forEach(category => {
  category.items.forEach(item => {
    allItems.push({
      ...item,
      category: category.name
    });
  });
});

const topItems = allItems
  .sort((a, b) => b.revenue - a.revenue)
  .slice(0, 10);

<div className="top-sellers">
  <h3>Top 10 Selling Items</h3>
  <table>
    <thead>
      <tr>
        <th>Rank</th>
        <th>SKU</th>
        <th>Name</th>
        <th>Category</th>
        <th>Servings Sold</th>
        <th>Revenue</th>
      </tr>
    </thead>
    <tbody>
      {topItems.map((item, index) => (
        <tr key={item.sku}>
          <td>{index + 1}</td>
          <td>{item.sku}</td>
          <td>{item.name}</td>
          <td>{item.category}</td>
          <td>{item.servingsSold.toFixed(0)}</td>
          <td>€{item.revenue.toFixed(2)}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

### 5. Performance Indicators
```jsx
<div className="performance-indicators">
  <h3>Performance Metrics</h3>
  
  <div className="metric">
    <label>Overall Gross Profit %:</label>
    <div className={`value ${grossProfitPercentage > 50 ? 'success' : 'warning'}`}>
      {grossProfitPercentage.toFixed(1)}%
    </div>
    <small>Target: 50-60%</small>
  </div>

  {Object.values(salesByCategory).map(category => {
    const categoryGP = category.revenue > 0 
      ? ((category.revenue - category.consumptionCost) / category.revenue) * 100 
      : 0;
    const percentOfTotal = (category.revenue / totals.revenue) * 100;
    
    return (
      <div key={category.name} className="metric">
        <label>{category.name}:</label>
        <div className="metric-details">
          <span>Revenue: €{category.revenue.toFixed(2)}</span>
          <span>GP: {categoryGP.toFixed(1)}%</span>
          <span>{percentOfTotal.toFixed(1)}% of total</span>
        </div>
      </div>
    );
  })}
</div>
```

---

## CSS Styling Example

```css
.sales-summary {
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card h3 {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 14px;
  font-weight: normal;
}

.card .amount {
  font-size: 32px;
  font-weight: bold;
  margin: 10px 0;
  color: #333;
}

.card .amount.success {
  color: #4CAF50;
}

.card .percentage {
  font-size: 18px;
  color: #4CAF50;
}

.warning {
  background: #FFF3CD;
  border: 1px solid #FFC107;
  padding: 10px;
  border-radius: 4px;
  margin: 20px 0;
  color: #856404;
}

.category-breakdown {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

.category-breakdown th,
.category-breakdown td {
  padding: 12px;
  text-align: right;
  border-bottom: 1px solid #ddd;
}

.category-breakdown th:first-child,
.category-breakdown td:first-child {
  text-align: left;
}

.category-breakdown thead th {
  background: #f8f9fa;
  font-weight: 600;
}

.category-breakdown tfoot {
  background: #f8f9fa;
  font-weight: bold;
}

.category-breakdown .success {
  color: #4CAF50;
}

.category-breakdown .warning {
  color: #FF9800;
}
```

---

## Complete React Component Example

```jsx
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

function OctoberSalesReport() {
  const [loading, setLoading] = useState(true);
  const [salesData, setSalesData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSalesData();
  }, []);

  const fetchSalesData = async () => {
    try {
      // Fetch periods
      const periods = await fetch('/api/stock-tracker/periods/').then(r => r.json());
      const septemberPeriod = periods.find(p => p.period_name === 'September 2024');
      const octoberPeriod = periods.find(p => p.period_name === 'October 2024');

      if (!septemberPeriod || !octoberPeriod) {
        throw new Error('Required periods not found');
      }

      // Fetch snapshots and purchases
      const [septSnapshots, octSnapshots, purchases] = await Promise.all([
        fetch(`/api/stock-tracker/snapshots/?period=${septemberPeriod.id}`).then(r => r.json()),
        fetch(`/api/stock-tracker/snapshots/?period=${octoberPeriod.id}`).then(r => r.json()),
        fetch(`/api/stock-tracker/movements/?period=${octoberPeriod.id}&movement_type=PURCHASE`).then(r => r.json())
      ]);

      // Calculate sales data (use logic from Step 2-4 above)
      const calculated = calculateSalesData(septSnapshots, octSnapshots, purchases);
      setSalesData(calculated);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  if (loading) return <div>Loading sales data...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!salesData) return <div>No data available</div>;

  return (
    <div className="sales-report">
      <h1>October 2024 Sales Report</h1>
      
      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="card">
          <h3>Total Revenue</h3>
          <p className="amount">€{salesData.totals.revenue.toLocaleString('en-IE', {minimumFractionDigits: 2})}</p>
        </div>
        <div className="card">
          <h3>Gross Profit</h3>
          <p className="amount success">€{salesData.grossProfit.toLocaleString('en-IE', {minimumFractionDigits: 2})}</p>
          <p className="percentage">{salesData.grossProfitPercentage.toFixed(1)}%</p>
        </div>
      </div>

      <p className="warning">⚠️ Contains mock purchase data - Replace with actual POS figures</p>

      {/* Category Chart */}
      <div className="chart-container">
        <h3>Revenue by Category</h3>
        <BarChart width={800} height={400} data={salesData.chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="category" />
          <YAxis />
          <Tooltip formatter={(value) => `€${value.toFixed(2)}`} />
          <Legend />
          <Bar dataKey="revenue" fill="#4CAF50" name="Revenue" />
          <Bar dataKey="cost" fill="#FF9800" name="Cost" />
        </BarChart>
      </div>

      {/* Category Table */}
      <table className="category-breakdown">
        {/* Use table structure from Section 2 above */}
      </table>

      {/* Top Sellers */}
      <div className="top-sellers">
        {/* Use top sellers structure from Section 4 above */}
      </div>
    </div>
  );
}

export default OctoberSalesReport;
```

---

## Important Notes

1. **Mock Data Warning**: Always display a prominent warning that purchase data is mocked until real POS data is available

2. **Negative GP% for Minerals**: The Minerals category shows negative GP because most items are missing `menu_price` - fix by adding prices

3. **Category Codes**: Categories are identified by SKU prefix:
   - D = Draught Beers
   - B = Bottled Beers  
   - S = Spirits
   - M = Minerals/Syrups
   - W = Wine

4. **Serving Calculations**:
   - Draught/Bottled/Minerals: `(full_units × uom) + partial_units`
   - Spirits/Wine: `(full_units × uom) + (partial_units × uom)`

5. **Revenue Calculation**:
   - Most items: `servings_sold × menu_price`
   - Wine: `bottles_sold × bottle_price`

6. **Expected GP%**:
   - Draught: 60-70%
   - Spirits: 70-80%
   - Bottled: 60-70%
   - Wine: 50-60%
   - Minerals: 50-60%

---

## Summary: What Numbers to Display

### Display 1: CURRENT STOCK VALUE (Real Data)
From **October 2024 Closing Stock** (actual stocktake):

```
📦 COST VALUE:        €27,306.58  (What you paid)
💰 SALES VALUE:       €88,233.42  (What you can sell it for)
📈 POTENTIAL PROFIT:  €60,926.84  (Your markup - 223.1%)
```

**By Category (Cost → Sales → Profit):**
- Draught Beers:     €5,311.62 → €15,126.41 → €9,814.79 (184.8% markup)
- Bottled Beers:     €2,288.47 → €8,554.80 → €6,266.33 (273.8% markup)
- Spirits:          €11,063.70 → €47,185.81 → €36,122.11 (326.5% markup)
- Minerals/Syrups:   €3,062.45 → €313.60 → -€2,748.85 (-89.8% - MISSING PRICES!)
- Wine:              €5,580.34 → €17,052.80 → €11,472.46 (205.6% markup)

**This shows**: 
- How much money is locked in inventory (€27,306.58)
- Potential revenue when it sells (€88,233.42)
- Your markup/profit margin (€60,926.84)

**⚠️ Note**: Minerals shows negative because 45 items are missing menu prices!

---

### Display 2: OCTOBER SALES REPORT (Mock Data - For Display Only)
From **September Opening + Mock Purchases - October Closing**:

```
💵 TOTAL SALES:       €193,653.60
💰 COST OF SALES:      €92,014.55
📈 GROSS PROFIT:      €101,639.06 (52.5%)
🍺 SERVINGS SOLD:      98,249
```

**By Category:**
- Draught Beers:     €86,940 revenue (44.9% of total)
- Spirits:           €68,008 revenue (35.1% of total)
- Bottled Beers:     €25,988 revenue (13.4% of total)
- Wine:              €10,586 revenue (5.5% of total)
- Minerals:           €2,131 revenue (1.1% of total)

⚠️ **IMPORTANT**: This uses €91,882 of MOCK purchase data
⚠️ **ALWAYS SHOW**: Yellow warning banner that purchases are mock data
⚠️ **REPLACE WITH**: Actual POS/till data when available

---

## Next Steps

1. Create the API endpoints if they don't exist
2. Implement **BOTH displays** using this guide:
   - Display 1: Current Stock Value (Real data)
   - Display 2: October Sales Report (Mock data with warning)
3. Replace mock purchase data with actual POS totals when available
4. Add menu prices for all Minerals/Syrups items to fix GP%
5. Consider adding date range filters for different periods
