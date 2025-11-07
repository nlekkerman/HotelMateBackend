# 🔄 Frontend Migration: Old Stocktakes → New Periods

## ⚠️ BREAKING CHANGE

The stock tracker has been completely refactored. **All old `stocktakes` endpoints are now `periods` endpoints.**

---

## 🚨 The Error You're Seeing

```
❌ GET /api/stock_tracker/hotel-killarney/stocktakes/2/
404 Not Found - "No Stocktake matches the given query."
```

**Why:** The `stocktakes` endpoint no longer exists. We refactored to use `periods`.

---

## ✅ Quick Fix

### Change This:
```javascript
// ❌ OLD - Will fail with 404
const response = await fetch(
  'https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/stocktakes/2/'
);
```

### To This:
```javascript
// ✅ NEW - Correct endpoint
const response = await fetch(
  'https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/periods/2/'
);
```

---

## 📋 Complete URL Mapping

### Local Development
```
OLD: http://127.0.0.1:8000/api/stock_tracker/1/stocktakes/
NEW: http://127.0.0.1:8000/api/stock_tracker/1/periods/

OLD: http://127.0.0.1:8000/api/stock_tracker/hotel-killarney/stocktakes/
NEW: http://127.0.0.1:8000/api/stock_tracker/hotel-killarney/periods/
```

### Production (Heroku)
```
OLD: https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/stocktakes/2/
NEW: https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/periods/2/
```

---

## 🔍 All Endpoint Changes

### List Endpoints
```javascript
// OLD
GET /api/stock_tracker/{hotel}/stocktakes/

// NEW
GET /api/stock_tracker/{hotel}/periods/
```

### Detail Endpoints
```javascript
// OLD
GET /api/stock_tracker/{hotel}/stocktakes/{id}/

// NEW
GET /api/stock_tracker/{hotel}/periods/{id}/
```

### Lines/Snapshots
```javascript
// OLD
GET /api/stock_tracker/{hotel}/stocktakes/{id}/lines/

// NEW
GET /api/stock_tracker/{hotel}/periods/{id}/snapshots/
// OR the detail endpoint includes snapshots automatically:
GET /api/stock_tracker/{hotel}/periods/{id}/
```

---

## 📊 Response Structure Changes

### OLD Stocktake Response:
```javascript
{
  "id": 2,
  "name": "October 2024 Stocktake",
  "date": "2024-10-31",
  "status": "completed",
  "lines": [
    {
      "id": 1,
      "item": {...},
      "quantity": 12.45,
      "value": 186.75
    }
  ]
}
```

### NEW Period Response:
```javascript
{
  "id": 2,
  "period_type": "MONTHLY",
  "period_name": "October 2025",
  "year": 2025,
  "month": 10,
  "is_closed": true,
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  "snapshots": [  // ← "lines" renamed to "snapshots"
    {
      "id": 1,
      "item": {
        "id": 1,
        "sku": "B0012",
        "name": "Cronins 0.0%",
        "category": "B",
        "category_display": "Bottled Beer",
        "size": "330ml",
        "unit_cost": 1.18,
        "menu_price": 4.50
      },
      "closing_full_units": 0.00,      // ← Split into full/partial
      "closing_partial_units": 16.00,
      "total_quantity": 16.00,
      "closing_stock_value": 18.93,
      "gp_percentage": 73.78,          // ← NEW: Profitability
      "markup_percentage": 281.36,
      "pour_cost_percentage": 26.22
    }
  ]
}
```

---

## 🔧 Field Name Changes

| OLD Field | NEW Field | Notes |
|-----------|-----------|-------|
| `name` | `period_name` | e.g., "October 2025" |
| `status` | `is_closed` | Boolean: true/false |
| `date` | `start_date`, `end_date` | Date range instead of single date |
| `lines` | `snapshots` | Array of item counts |
| `quantity` | `closing_full_units` + `closing_partial_units` | Split into whole + partial |
| `value` | `closing_stock_value` | Same concept, renamed |
| N/A | `period_type` | NEW: "MONTHLY", "WEEKLY", etc. |
| N/A | `year`, `month` | NEW: Numeric identifiers |
| N/A | `gp_percentage` | NEW: Gross profit % |
| N/A | `markup_percentage` | NEW: Markup % |

---

## 🛠️ Frontend Code Updates

### 1. Fetching All Periods (was: all stocktakes)

**Before:**
```javascript
const response = await fetch('/api/stock_tracker/hotel-killarney/stocktakes/');
const stocktakes = await response.json();
```

**After:**
```javascript
const response = await fetch('/api/stock_tracker/hotel-killarney/periods/');
const data = await response.json();
const periods = data.results;  // ← Now paginated
```

---

### 2. Fetching Single Period (was: single stocktake)

**Before:**
```javascript
const response = await fetch('/api/stock_tracker/hotel-killarney/stocktakes/2/');
const stocktake = await response.json();
const items = stocktake.lines;  // ← OLD
```

**After:**
```javascript
const response = await fetch('/api/stock_tracker/hotel-killarney/periods/2/');
const period = await response.json();
const items = period.snapshots;  // ← NEW
```

---

### 3. Accessing Item Data

**Before:**
```javascript
stocktake.lines.forEach(line => {
  console.log(line.item.name);
  console.log(line.quantity);
  console.log(line.value);
});
```

**After:**
```javascript
period.snapshots.forEach(snapshot => {
  console.log(snapshot.item.name);
  
  // Quantity now split:
  const fullUnits = snapshot.closing_full_units;
  const partialUnits = snapshot.closing_partial_units;
  const totalQty = snapshot.total_quantity;  // Or: full + partial
  
  console.log(snapshot.closing_stock_value);
  
  // NEW: Profitability metrics
  console.log(`GP: ${snapshot.gp_percentage}%`);
});
```

---

### 4. Creating New Period (was: creating stocktake)

**Before:**
```javascript
await fetch('/api/stock_tracker/hotel-killarney/stocktakes/', {
  method: 'POST',
  body: JSON.stringify({
    name: "November 2025 Stocktake",
    date: "2025-11-30",
    status: "open"
  })
});
```

**After:**
```javascript
await fetch('/api/stock_tracker/hotel-killarney/periods/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    period_type: "MONTHLY",
    period_name: "November 2025",
    year: 2025,
    month: 11,
    start_date: "2025-11-01",
    end_date: "2025-11-30",
    is_closed: false  // ← Boolean, not string
  })
});
```

---

### 5. Updating Stock Count (was: updating line)

**Before:**
```javascript
await fetch('/api/stock_tracker/hotel-killarney/stocktake-lines/123/', {
  method: 'PATCH',
  body: JSON.stringify({
    quantity: 12.45
  })
});
```

**After:**
```javascript
await fetch('/api/stock_tracker/hotel-killarney/snapshots/123/', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    closing_full_units: 12,      // ← Split quantity
    closing_partial_units: 0.45
  })
});
```

---

### 6. Closing/Finalizing Period

**Before:**
```javascript
await fetch('/api/stock_tracker/hotel-killarney/stocktakes/2/', {
  method: 'PATCH',
  body: JSON.stringify({
    status: "completed"
  })
});
```

**After:**
```javascript
await fetch('/api/stock_tracker/hotel-killarney/periods/2/', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    is_closed: true  // ← Boolean
  })
});
```

---

## 🚀 Production Deployment Checklist

### ⚠️ Before Deploying to Heroku:

1. **Run Migrations**
   ```bash
   git push heroku main
   heroku run python manage.py migrate --app hotel-porter-d25ad83b12cf
   ```

2. **Create October 2025 Period (if needed)**
   ```bash
   heroku run python manage.py create_october_2025 --app hotel-porter-d25ad83b12cf
   ```

3. **Verify Periods Exist**
   ```bash
   # Check in browser:
   https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/periods/
   ```

4. **Update Frontend Code**
   - Replace all `stocktakes` → `periods`
   - Replace all `lines` → `snapshots`
   - Update field names (see table above)
   - Update quantity handling (full + partial)

5. **Test on Production**
   ```javascript
   // Should work:
   fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/periods/')
   fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/periods/2/')
   ```

---

## 🔍 How to Check What Exists on Heroku

### Option 1: Browser
```
https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/periods/
```

### Option 2: cURL
```bash
curl https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/periods/
```

### Option 3: JavaScript Console
```javascript
fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/periods/')
  .then(r => r.json())
  .then(data => console.log('Available periods:', data.results));
```

---

## 💾 Example: Complete Fetch Pattern

```javascript
// Step 1: Get all periods
const periodsResponse = await fetch(
  'https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/periods/'
);
const periodsData = await periodsResponse.json();

console.log('Available periods:', periodsData.results);

// Step 2: Find October 2025
const octoberPeriod = periodsData.results.find(p => 
  p.year === 2025 && p.month === 10
);

if (!octoberPeriod) {
  console.error('October 2025 period not found! Need to create it on Heroku.');
  return;
}

// Step 3: Get period with all items
const periodResponse = await fetch(
  `https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/periods/${octoberPeriod.id}/`
);
const periodData = await periodResponse.json();

console.log('Period:', periodData.period_name);
console.log('Items:', periodData.snapshots.length);
console.log('Total Value:', periodData.snapshots.reduce((sum, s) => sum + parseFloat(s.closing_stock_value), 0));

// Step 4: Display items
periodData.snapshots.forEach(snapshot => {
  console.log({
    name: snapshot.item.name,
    sku: snapshot.item.sku,
    fullUnits: snapshot.closing_full_units,
    partialUnits: snapshot.closing_partial_units,
    totalQty: snapshot.total_quantity,
    value: snapshot.closing_stock_value,
    gp: snapshot.gp_percentage
  });
});
```

---

## 📝 Summary of Changes

| Aspect | Old | New |
|--------|-----|-----|
| **Endpoint** | `/stocktakes/` | `/periods/` |
| **Model Name** | Stocktake | StockPeriod |
| **Items Array** | `lines` | `snapshots` |
| **Status** | `"open"` / `"completed"` | `is_closed: true/false` |
| **Quantity** | Single `quantity` field | `closing_full_units` + `closing_partial_units` |
| **Profitability** | Not available | `gp_percentage`, `markup_percentage` |
| **Time Range** | Single `date` | `start_date` + `end_date` |

---

## ✅ Action Items

1. **Search your frontend codebase** for:
   - `stocktakes` → replace with `periods`
   - `.lines` → replace with `.snapshots`
   - `status` → replace with `is_closed`
   - `.quantity` → replace with `.closing_full_units` + `.closing_partial_units`

2. **Update API base URL constants**
   ```javascript
   // OLD
   const STOCKTAKE_API = '/api/stock_tracker/hotel-killarney/stocktakes/';
   
   // NEW
   const PERIOD_API = '/api/stock_tracker/hotel-killarney/periods/';
   ```

3. **Test locally first** with `http://127.0.0.1:8000`

4. **Deploy and test on Heroku** with `https://hotel-porter-d25ad83b12cf.herokuapp.com`

---

**🎯 Once you update all `stocktakes` → `periods`, everything will work!**
