# Understanding Period, Snapshot, and Stocktake Relationships

## Data Structure Overview

There are **three related but separate** models:

```
StockPeriod (ID: 9) ← defines time range
    ↓
StockSnapshot (many) ← actual stock counts at period end
    
Stocktake (ID: 4) ← optional workflow tracker
    ↓
StocktakeLine (many) ← tracks counting process
```

---

## Key Differences

### StockPeriod
- **Purpose**: Defines time ranges for stock tracking
- **ID**: Stable, never changes
- **Contains**: Time range (start_date, end_date)
- **Status**: `is_closed` (boolean)
- **One-to-Many**: Has many StockSnapshots

```json
{
  "id": 9,
  "period_name": "November 2025",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30",
  "is_closed": false
}
```

### StockSnapshot
- **Purpose**: Actual stock data (what you counted)
- **Links to**: Period via `period_id` (FK)
- **One per**: Item per period
- **Contains**: `closing_full_units`, `closing_partial_units`, values

```json
{
  "id": 3801,
  "period": 9,  // ← FK to Period
  "item": {
    "id": 250,
    "name": "Cronins 0.0%"
  },
  "closing_full_units": "0.00",
  "closing_partial_units": "69.0000",
  "closing_stock_value": "81.65"
}
```

### Stocktake (Legacy/Optional)
- **Purpose**: Workflow tracker for counting process
- **Links to**: Period via dates (NOT FK!)
- **ID**: Can change if deleted/recreated
- **Contains**: Opening balances, movements, variances

```json
{
  "id": 4,
  "period_start": "2025-11-01",  // ← Links via dates, not ID
  "period_end": "2025-11-30",
  "status": "DRAFT"
}
```

---

## ⚠️ Critical: IDs Can Mismatch!

### Scenario: Deleted and Recreated Stocktake

```
1. Create Period ID 9 (November 2025)
2. Create Stocktake ID 4 for November
3. Delete Stocktake ID 4
4. Create new Stocktake ID 7 for November
```

**Result:**
- Period ID: Still `9` ✓
- Stocktake ID: Now `7` (changed!)
- Snapshots: Still link to Period `9` via FK ✓

**DO NOT assume Period ID == Stocktake ID!**

---

## Frontend Guidance: Which Model to Use?

### ✅ Use StockPeriod + StockSnapshot (Recommended)

**Why:**
- Period ID is stable
- Snapshots directly link via FK
- No confusion with deleted stocktakes
- Simpler data flow

**API Endpoints:**
```
GET /api/stock_tracker/{hotel_id}/periods/
GET /api/stock_tracker/{hotel_id}/periods/{period_id}/
```

**Response includes snapshots:**
```json
{
  "id": 9,
  "period_name": "November 2025",
  "snapshots": [
    {
      "id": 3801,
      "item": { ... },
      "closing_full_units": "0.00",
      "closing_partial_units": "69.0000"
    }
  ]
}
```

---

### When to Use Stocktake Model?

**Only if you need:**
- Opening balances (from previous period)
- Period movements (purchases, sales, waste)
- Variance tracking (expected vs actual)
- Approval workflow

**But beware:**
- Stocktake links to Period via **dates**, not ID
- Stocktake ID can change if deleted/recreated
- More complex data structure

---

## Recommended Frontend Workflow

### Option 1: Period + Snapshots (Simple)

```javascript
// 1. Create period
const period = await fetch('/api/stock_tracker/1/periods/', {
  method: 'POST',
  body: JSON.stringify({
    period_type: 'MONTHLY',
    start_date: '2025-11-01',
    end_date: '2025-11-30'
  })
}).then(r => r.json());

// period.id = 9 (stable, won't change)

// 2. Populate opening stock
await fetch(`/api/stock_tracker/1/periods/${period.id}/populate-opening-stock/`, {
  method: 'POST'
});

// 3. Get snapshots
const periodData = await fetch(`/api/stock_tracker/1/periods/${period.id}/`)
  .then(r => r.json());

// 4. Display for counting
periodData.snapshots.forEach(snapshot => {
  displayItem({
    snapshotId: snapshot.id,
    itemName: snapshot.item.name,
    openingFull: snapshot.closing_full_units,
    openingPartial: snapshot.closing_partial_units
  });
});

// 5. Update counts
await fetch(`/api/stock_tracker/1/snapshots/${snapshotId}/`, {
  method: 'PATCH',
  body: JSON.stringify({
    closing_full_units: actualFull,
    closing_partial_units: actualPartial
  })
});

// 6. Close period
await fetch(`/api/stock_tracker/1/periods/${period.id}/`, {
  method: 'PATCH',
  body: JSON.stringify({ is_closed: true })
});
```

---

### Option 2: Stocktake Workflow (Complex)

Only use if you need variance tracking and approval flow:

```javascript
// 1. Create period first
const period = await createPeriod();

// 2. Create stocktake (links via dates)
const stocktake = await fetch('/api/stock_tracker/1/stocktakes/', {
  method: 'POST',
  body: JSON.stringify({
    period_start: period.start_date,
    period_end: period.end_date
  })
}).then(r => r.json());

// stocktake.id might be different from period.id!

// 3. Populate stocktake lines
await fetch(`/api/stock_tracker/1/stocktakes/${stocktake.id}/populate/`, {
  method: 'POST'
});

// 4. Get lines with opening/movements/expected
const lines = await fetch(`/api/stock_tracker/1/stocktakes/${stocktake.id}/lines/`)
  .then(r => r.json());

// 5. Update counted quantities
await fetch(`/api/stock_tracker/1/stocktake-lines/${lineId}/`, {
  method: 'PATCH',
  body: JSON.stringify({ counted_qty: actualCount })
});

// 6. Approve stocktake
await fetch(`/api/stock_tracker/1/stocktakes/${stocktake.id}/approve/`, {
  method: 'POST'
});
```

---

## Relationship Summary Table

| Model | ID Stability | Links To | Use For |
|-------|--------------|----------|---------|
| **StockPeriod** | ✅ Stable | - | Defining time ranges |
| **StockSnapshot** | ✅ Stable | Period (FK) | Actual stock counts |
| **Stocktake** | ⚠️ Can change | Period (dates) | Workflow tracking |
| **StocktakeLine** | ⚠️ Can change | Stocktake (FK) | Counting process |

---

## Best Practice Recommendations

### ✅ DO:
- Use Period ID as the primary identifier
- Store Period ID in your frontend state
- Link snapshots via Period ID
- Fetch snapshots from Period endpoint

### ❌ DON'T:
- Assume Stocktake ID == Period ID
- Use Stocktake ID as primary reference
- Rely on Stocktake if you only need counts
- Create unnecessary complexity

---

## Example: Real Data from Database

```
Period ID: 9
  Name: November 2025
  Dates: 2025-11-01 to 2025-11-30
  Snapshots: 254
  Status: OPEN

Stocktake ID: 4
  Dates: 2025-11-01 to 2025-11-30  ← Matches via dates
  Lines: 254
  Status: DRAFT

Snapshot ID: 3801
  Item: Cronins 0.0%
  Period FK: 9  ← Direct link to Period
  Full: 0.00
  Partial: 69.0000

StocktakeLine ID: 1709
  Item: Cronins 0.0%
  Stocktake FK: 4  ← Direct link to Stocktake
  Opening: 0.0000
  Counted: null
```

Notice:
- Period ID (9) ≠ Stocktake ID (4) ✓ This is normal!
- Snapshot links to Period via FK
- StocktakeLine links to Stocktake via FK
- Both track the same items, different purposes

---

## Conclusion

**For most frontend use cases:**

Use **StockPeriod + StockSnapshot**. They're simpler, more stable, and directly linked.

Only use **Stocktake** if you specifically need the workflow features (opening balances, movements, variances, approvals).

**Remember:** Period ID is your stable reference! 🎯
