# Frontend Guide: Creating Periods & Stocktakes from Scratch

## Overview
This guide explains the complete workflow for creating stock periods and stocktakes in the correct order.

---

## 📋 **Step-by-Step Process**

### **What Frontend Creates:**
1. ✅ **Period** (manual API call)
2. ✅ **Stocktake** (manual API call)

### **What Backend Creates Automatically:**
3. ✅ **Stocktake Lines** (via populate endpoint - creates ALL lines)
4. ✅ **Snapshots** (when period is closed - stores closing stock)

---

### **1️⃣ Create a Stock Period**

A **Period** represents a time frame (week, month, quarter, year) for tracking stock.

#### **Endpoint:**
```http
POST /api/stock-tracker/{hotel_identifier}/periods/
```

#### **Request Body:**
```json
{
  "period_type": "MONTHLY",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30"
}
```

#### **Period Types:**
- `WEEKLY` - 7 days
- `MONTHLY` - 1 month (most common)
- `QUARTERLY` - 3 months
- `YEARLY` - 1 year

#### **Response:**
```json
{
  "id": 123,
  "hotel": 1,
  "period_type": "MONTHLY",
  "period_name": "November 2025",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30",
  "year": 2025,
  "month": 11,
  "is_closed": false,
  "stocktake_id": null
}
```

---

### **2️⃣ Create a Stocktake**

A **Stocktake** is the actual inventory count for a period.

#### **Endpoint:**
```http
POST /api/stock-tracker/{hotel_identifier}/stocktakes/
```

#### **Request Body:**
```json
{
  "period_start": "2025-11-01",
  "period_end": "2025-11-30",
  "notes": "November monthly stocktake"
}
```

#### **Response:**
```json
{
  "id": 456,
  "hotel": 1,
  "period_start": "2025-11-01",
  "period_end": "2025-11-30",
  "status": "DRAFT",
  "is_locked": false,
  "lines": [],
  "total_lines": 0,
  "notes": "November monthly stocktake"
}
```

**Note:** The stocktake is created **empty** (no lines yet).

---

### **3️⃣ Populate the Stocktake**

This creates all the stocktake lines with opening balances.

#### **Endpoint:**
```http
POST /api/stock-tracker/{hotel_identifier}/stocktakes/{stocktake_id}/populate/
```

#### **Request Body:**
```json
{}
```
*(No body needed)*

#### **What Happens:**
1. Backend fetches all `StockItem` records
2. For each item, calculates **opening balance**:
   - **If first stocktake:** Uses current inventory (`StockItem.total_stock_in_servings`)
   - **If NOT first:** Uses previous period's closing stock
3. Calculates **purchases, waste, transfers** from period movements
4. Creates a `StocktakeLine` for each item

#### **Opening Balance Logic:**
```
Priority Order:
1. Previous Period's Closing Stock (from StockSnapshot)
   → Example: October closing = 69.00, November opening = 69.00

2. Current Stock Inventory (for first stocktake)
   → Example: Item has 292 servings in stock, opening = 292.00

3. Historical Movements (legacy fallback)
   → Calculates from StockMovement records
```

#### **Response:**
```json
{
  "message": "Created 254 stocktake lines",
  "lines_created": 254
}
```

---

### **4️⃣ The Stocktake is Ready for Counting**

After population, GET the stocktake to see all lines:

#### **Endpoint:**
```http
GET /api/stock-tracker/{hotel_identifier}/stocktakes/{stocktake_id}/
```

#### **Response:**
```json
{
  "id": 456,
  "status": "DRAFT",
  "period_start": "2025-11-01",
  "period_end": "2025-11-30",
  "lines": [
    {
      "id": 1001,
      "item_sku": "B0012",
      "item_name": "Cronins 0.0%",
      "category_code": "B",
      "item_size": "Doz",
      "item_uom": 12,
      
      // Opening stock (from October closing)
      "opening_qty": "69.0000",
      "opening_display_full_units": "5",
      "opening_display_partial_units": "9",
      
      // Period movements
      "purchases": "10.8400",
      "waste": "1.0000",
      "transfers_in": "0.0000",
      "transfers_out": "0.0000",
      
      // Calculated expected
      "expected_qty": "79.8400",
      "expected_display_full_units": "6",
      "expected_display_partial_units": "8",
      
      // Counting fields (user fills these)
      "counted_full_units": 0,
      "counted_partial_units": 0,
      "counted_qty": "0.0000",
      
      // Variance (calculated)
      "variance_qty": "-79.8400",
      "variance_value": "-80.23",
      
      // Values
      "expected_value": "80.23",
      "counted_value": "0.00"
    }
    // ... 253 more items
  ],
  "total_lines": 254
}
```

---

## 🎯 **User Workflow (Frontend UI)**

### **Step 1: List Periods**
```
GET /api/stock-tracker/{hotel}/periods/
```
Show table of existing periods with status.

### **Step 2: Create New Period Button**
- Show modal with date pickers
- User selects start/end dates
- POST to create period

### **Step 2b: Delete Period Button (Superuser Only)**
- Show **red "Delete" button** next to each period
- Only visible if `user.is_superuser === true`
- On click: Show confirmation modal:
  ```
  ⚠️ DELETE PERIOD AND ALL DATA?
  
  This will permanently delete:
  - Period: November 2025
  - 1 Stocktake
  - 254 Stocktake Lines
  - 254 Stock Snapshots
  
  This action CANNOT be undone!
  
  [Cancel] [⚠️ DELETE PERMANENTLY]
  ```
- On confirm: `DELETE /api/stock-tracker/{hotel}/periods/{id}/`
- Show success message with deleted counts
- Refresh period list

**JavaScript Example:**
```javascript
const deletePeriod = async (periodId) => {
  // Show confirmation dialog
  const confirmed = confirm(
    'Are you sure? This will delete the period and ALL related data (stocktake, lines, snapshots). This cannot be undone!'
  );
  
  if (!confirmed) return;
  
  try {
    const response = await fetch(`/api/stock-tracker/hotel1/periods/${periodId}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.status === 403) {
      alert('Only superusers can delete periods');
      return;
    }
    
    const data = await response.json();
    console.log('✅ Period deleted:', data);
    
    alert(`Deleted: ${data.message}\n` +
          `- Stocktakes: ${data.deleted.stocktakes}\n` +
          `- Lines: ${data.deleted.stocktake_lines}\n` +
          `- Snapshots: ${data.deleted.snapshots}`);
    
    // Refresh list
    fetchPeriods();
  } catch (error) {
    console.error('❌ Delete failed:', error);
    alert('Failed to delete period');
  }
};
```

### **Step 3: Create Stocktake Button**
- Appears when period has no stocktake
- POST to create stocktake (auto-links to period by dates)

### **Step 4: Populate Button**
- Appears when stocktake has 0 lines
- POST to populate
- Show loading spinner (can take 2-3 seconds for 250+ items)

### **Step 5: Counting Interface**
- Show table of all lines
- Group by category (D, B, S, W, M)
- Allow input for counted_full_units and counted_partial_units
- PATCH each line as user counts:
  ```http
  PATCH /api/stock-tracker/{hotel}/stocktake-lines/{line_id}/
  {
    "counted_full_units": 5,
    "counted_partial_units": 9
  }
  ```

### **Step 6: Approve Stocktake**
- Button appears when counting is complete
- POST to approve:
  ```http
  POST /api/stock-tracker/{hotel}/stocktakes/{id}/approve/
  ```
- Creates adjustment movements for variances
- Locks the stocktake (can't edit anymore)

### **Step 7: Close Period**
- Button appears when stocktake is approved
- POST to close period (or combined approve+close):
  ```http
  POST /api/stock-tracker/{hotel}/periods/{id}/approve-and-close/
  ```
- **Backend automatically creates StockSnapshot records**
  - One snapshot per item with closing stock
  - These snapshots become the opening stock for the next period!

---

## 📊 **Display Data for Frontend**

### **Opening Stock Display:**
Show user-friendly units instead of raw servings:

```javascript
// Draught Beer
Opening: "5 kegs + 12.5 pints"  // Not "172.5 servings"

// Bottled Beer  
Opening: "5 cases + 9 bottles"  // Not "69 bottles"

// Spirits
Opening: "5 bottles + 0.75 shots"  // Not "105.75 servings"
```

Use these fields from the API:
- `opening_display_full_units` (kegs/cases/bottles)
- `opening_display_partial_units` (pints/bottles/shots)

### **Variance Indicators:**
```javascript
if (variance_qty < -10) {
  // Show ⚠️ warning icon (significant shortage)
} else if (variance_qty > 10) {
  // Show ⚠️ warning icon (significant surplus)
}
```

---

## 🔄 **Creating Future Periods**

### **December Stocktake (after November is closed):**

1. **Create December Period:**
   ```json
   POST /periods/
   {
     "period_type": "MONTHLY",
     "start_date": "2025-12-01",
     "end_date": "2025-12-31"
   }
   ```

2. **Create December Stocktake:**
   ```json
   POST /stocktakes/
   {
     "period_start": "2025-12-01",
     "period_end": "2025-12-31"
   }
   ```

3. **Populate:**
   ```
   POST /stocktakes/{id}/populate/
   ```
   - **Opening balance automatically comes from November's closing stock!**
   - Example: November closing = 85 bottles → December opening = 85 bottles

---

## ⚠️ **Important Notes**

### **1. Period & Stocktake Relationship:**
- Periods and Stocktakes are linked by **dates** (not FK)
- One Period = One Stocktake
- Match by `period.start_date == stocktake.period_start`

### **2. Opening Balance Source:**
```
First Stocktake (September):
  Opening = Current inventory in system

Second Stocktake (October):
  Opening = September closing stock

Third Stocktake (November):
  Opening = October closing stock
```

### **3. Zero Opening Issue (FIXED):**
The backend now correctly:
- ✅ Uses previous period's closing as opening
- ✅ Falls back to current inventory for first stocktake
- ✅ No more zero opening balances!

### **4. Repopulating:**
If opening balances are wrong:
```
1. Delete the stocktake
2. Create new stocktake
3. Populate again
```

---

## 🔧 **Common API Endpoints**

### **Get All Periods:**
```
GET /api/stock-tracker/{hotel}/periods/
```

### **Get Period with Snapshots:**
```
GET /api/stock-tracker/{hotel}/periods/{id}/
```

### **Delete Period (Superuser Only):**
```
DELETE /api/stock-tracker/{hotel}/periods/{id}/
```
**⚠️ WARNING: This deletes:**
- The Period
- All Stocktakes for this period
- All StocktakeLine records
- All StockSnapshot records

**Response:**
```json
{
  "message": "Period 'November 2025' and all related data deleted successfully",
  "deleted": {
    "period": 1,
    "stocktakes": 1,
    "stocktake_lines": 254,
    "snapshots": 254
  }
}
```

**Permission:**
- Only **superusers** can delete periods
- Returns 403 Forbidden for non-superusers

### **Get All Stocktakes:**
```
GET /api/stock-tracker/{hotel}/stocktakes/
```

### **Get Stocktake with Lines:**
```
GET /api/stock-tracker/{hotel}/stocktakes/{id}/
```

### **Update Counted Values:**
```
PATCH /api/stock-tracker/{hotel}/stocktake-lines/{line_id}/
{
  "counted_full_units": 5,
  "counted_partial_units": 9
}
```

### **Category Totals:**
```
GET /api/stock-tracker/{hotel}/stocktakes/{id}/category_totals/
```

---

## 📝 **Example Complete Flow**

```javascript
// 1. Create Period
const period = await fetch('/api/stock-tracker/hotel1/periods/', {
  method: 'POST',
  body: JSON.stringify({
    period_type: 'MONTHLY',
    start_date: '2025-11-01',
    end_date: '2025-11-30'
  })
});

// 2. Create Stocktake
const stocktake = await fetch('/api/stock-tracker/hotel1/stocktakes/', {
  method: 'POST',
  body: JSON.stringify({
    period_start: '2025-11-01',
    period_end: '2025-11-30'
  })
});

// 3. Populate
await fetch(`/api/stock-tracker/hotel1/stocktakes/${stocktake.id}/populate/`, {
  method: 'POST'
});

// 4. Get populated stocktake
const populated = await fetch(`/api/stock-tracker/hotel1/stocktakes/${stocktake.id}/`);

// 5. User counts inventory...
// 6. Update each line with counted values...

// 7. Approve
await fetch(`/api/stock-tracker/hotel1/stocktakes/${stocktake.id}/approve/`, {
  method: 'POST'
});

// 8. Close period
await fetch(`/api/stock-tracker/hotel1/periods/${period.id}/approve-and-close/`, {
  method: 'POST'
});
```

---

## ✅ **Summary**

1. **Create Period** → Set date range
2. **Create Stocktake** → Links to period by dates
3. **Populate** → Auto-fills opening balances + movements
4. **Count** → User enters actual inventory
5. **Approve** → Locks stocktake, creates adjustments
6. **Close Period** → Finalizes the period

**Opening balance will automatically come from previous period's closing stock!**

---

## 🔍 **Debugging & Monitoring (Console Logs)**

Add these console logs to help track the process and catch issues:

### **1. Period Creation:**
```javascript
console.log('📅 Creating period:', {
  start_date: startDate,
  end_date: endDate,
  period_type: periodType
});

const periodResponse = await createPeriod();
console.log('✅ Period created:', {
  id: periodResponse.id,
  period_name: periodResponse.period_name,
  is_closed: periodResponse.is_closed
});
```

### **2. Stocktake Creation:**
```javascript
console.log('📦 Creating stocktake for period:', {
  period_start: periodStart,
  period_end: periodEnd,
  period_id: periodId
});

const stocktakeResponse = await createStocktake();
console.log('✅ Stocktake created:', {
  id: stocktakeResponse.id,
  status: stocktakeResponse.status,
  total_lines: stocktakeResponse.total_lines
});
```

### **3. Populate:**
```javascript
console.log('🔄 Populating stocktake #' + stocktakeId);
console.time('populate-duration');

const populateResponse = await populateStocktake();
console.timeEnd('populate-duration');

console.log('✅ Population complete:', {
  lines_created: populateResponse.lines_created,
  message: populateResponse.message
});
```

### **4. Verify Opening Balances:**
```javascript
const stocktake = await fetchStocktake(stocktakeId);

// Check first few lines for opening stock
console.log('🔍 Checking opening balances:');
stocktake.lines.slice(0, 5).forEach(line => {
  console.log(`  ${line.item_sku} - ${line.item_name}:`, {
    opening_qty: line.opening_qty,
    opening_display: `${line.opening_display_full_units} + ${line.opening_display_partial_units}`,
    purchases: line.purchases,
    expected_qty: line.expected_qty,
    source: line.opening_qty === '0.0000' ? '❌ ZERO (ERROR!)' : '✅ Has opening'
  });
});

// Alert if all opening balances are zero
const allZero = stocktake.lines.every(line => 
  parseFloat(line.opening_qty) === 0
);

if (allZero) {
  console.error('❌ WARNING: All opening balances are ZERO!');
  console.error('This indicates a backend issue. Contact support.');
} else {
  console.log('✅ Opening balances look good!');
}
```

### **5. Counting Progress:**
```javascript
// Track counting progress
const totalLines = stocktake.lines.length;
const countedLines = stocktake.lines.filter(line => 
  parseFloat(line.counted_qty) > 0
).length;

console.log('📊 Counting progress:', {
  counted: countedLines,
  total: totalLines,
  percentage: Math.round((countedLines / totalLines) * 100) + '%',
  remaining: totalLines - countedLines
});
```

### **6. Line Update:**
```javascript
console.log('✏️ Updating line:', {
  line_id: lineId,
  item: itemSku,
  counted_full: countedFull,
  counted_partial: countedPartial
});

const updateResponse = await updateLine(lineId, data);
console.log('✅ Line updated:', {
  counted_qty: updateResponse.counted_qty,
  variance_qty: updateResponse.variance_qty,
  variance_value: updateResponse.variance_value
});
```

### **7. Variance Check:**
```javascript
// Before approving, check for large variances
const largeVariances = stocktake.lines.filter(line => 
  Math.abs(parseFloat(line.variance_qty)) > 10
);

if (largeVariances.length > 0) {
  console.warn('⚠️ Large variances detected:', {
    count: largeVariances.length,
    items: largeVariances.map(line => ({
      sku: line.item_sku,
      name: line.item_name,
      variance: line.variance_qty,
      variance_value: line.variance_value
    }))
  });
}
```

### **8. Approve:**
```javascript
console.log('🔒 Approving stocktake #' + stocktakeId);

const approveResponse = await approveStocktake();
console.log('✅ Stocktake approved:', {
  adjustments_created: approveResponse.adjustments_created,
  status: approveResponse.stocktake?.status,
  approved_at: approveResponse.stocktake?.approved_at
});
```

### **9. Close Period:**
```javascript
console.log('🔐 Closing period #' + periodId);

const closeResponse = await closePeriod();
console.log('✅ Period closed:', {
  period_name: closeResponse.period.period_name,
  closed_at: closeResponse.period.closed_at,
  stocktake_approved: closeResponse.stocktake_updated
});
```

### **10. Delete Period (Superuser):**
```javascript
console.log('🗑️ Deleting period #' + periodId, {
  period_name: period.period_name,
  user_is_superuser: user.is_superuser
});

try {
  const deleteResponse = await deletePeriod(periodId);
  console.log('✅ Period deleted:', {
    message: deleteResponse.message,
    deleted: deleteResponse.deleted
  });
} catch (error) {
  if (error.response?.status === 403) {
    console.error('❌ Permission denied: Only superusers can delete periods');
  } else {
    console.error('❌ Delete failed:', error);
  }
}
```

### **11. Error Handling:**
```javascript
try {
  await populateStocktake(stocktakeId);
} catch (error) {
  console.error('❌ Populate failed:', {
    status: error.response?.status,
    message: error.response?.data?.error || error.message,
    stocktake_id: stocktakeId
  });
  
  // Common errors:
  if (error.response?.status === 400) {
    if (error.response.data.error?.includes('approved')) {
      console.error('Cannot populate: Stocktake is already approved/locked');
    }
  }
}
```

### **12. Network Request Logging:**
```javascript
// Axios interceptor example
axios.interceptors.request.use(request => {
  console.log('🌐 API Request:', {
    method: request.method.toUpperCase(),
    url: request.url,
    data: request.data
  });
  return request;
});

axios.interceptors.response.use(
  response => {
    console.log('✅ API Response:', {
      status: response.status,
      url: response.config.url,
      data: response.data
    });
    return response;
  },
  error => {
    console.error('❌ API Error:', {
      status: error.response?.status,
      url: error.config?.url,
      error: error.response?.data
    });
    return Promise.reject(error);
  }
);
```

### **13. Performance Monitoring:**
```javascript
// Track time for each operation
const performance = {
  period_creation: 0,
  stocktake_creation: 0,
  populate: 0,
  counting: 0,
  approve: 0
};

console.time('period_creation');
await createPeriod();
performance.period_creation = console.timeEnd('period_creation');

// At the end:
console.log('📈 Performance Summary:', performance);
```

### **Expected Console Output (Successful Flow):**
```
📅 Creating period: { start_date: "2025-11-01", end_date: "2025-11-30", period_type: "MONTHLY" }
✅ Period created: { id: 123, period_name: "November 2025", is_closed: false }

📦 Creating stocktake for period: { period_start: "2025-11-01", period_end: "2025-11-30", period_id: 123 }
✅ Stocktake created: { id: 456, status: "DRAFT", total_lines: 0 }

🔄 Populating stocktake #456
populate-duration: 2.341s
✅ Population complete: { lines_created: 254, message: "Created 254 stocktake lines" }

🔍 Checking opening balances:
  B0012 - Cronins 0.0%: { opening_qty: "69.0000", opening_display: "5 + 9", purchases: "10.84", expected_qty: "79.84", source: "✅ Has opening" }
  B0070 - Budweiser 33cl: { opening_qty: "113.0000", opening_display: "9 + 5", purchases: "14.01", expected_qty: "127.01", source: "✅ Has opening" }
  ...
✅ Opening balances look good!

📊 Counting progress: { counted: 125, total: 254, percentage: "49%", remaining: 129 }
```

### **Red Flags to Watch For:**
```javascript
// ❌ BAD: All zeros
opening_qty: "0.0000" for all items

// ❌ BAD: No previous period found when it should exist
"No valid periods found" error on populate

// ❌ BAD: Negative expected quantities
expected_qty: "-50.0000"

// ✅ GOOD: Opening matches previous closing
October closing: 69.00 → November opening: 69.00
```

---

*For questions, contact backend team or check the full API documentation.*
