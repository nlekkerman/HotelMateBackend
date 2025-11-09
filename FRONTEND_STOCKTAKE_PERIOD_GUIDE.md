# FRONTEND GUIDE: Getting Stocktake from Period

## ✅ IMPLEMENTED SOLUTION (November 2025)

**The Period API now includes complete stocktake information!**

Period and Stocktake are separate models with different IDs, but the backend now handles this for you.

Example:
- November 2025: Period ID = **9**, Stocktake ID = **4**
- October 2025: Period ID = **7**, Stocktake ID = **5**
- September 2025: Period ID = **8**, Stocktake ID = **8**

**IDs don't match**, but you don't need to worry about it anymore!

## ⭐ RECOMMENDED: Use Enhanced Period Response

### Current Implementation (EASIEST)

The Period API now returns a complete `stocktake` object with all basic information:

```javascript
// Get period - stocktake info is automatically included!
const response = await fetch('/api/stock_tracker/hotel-killarney/periods/8/');
const period = await response.json();

console.log(period);
// {
//   "id": 8,
//   "period_name": "September 2025",
//   "start_date": "2025-09-01",
//   "end_date": "2025-09-30",
//   "is_closed": false,
//   "stocktake_id": 8,          // Quick reference
//   "stocktake": {              // Full basic info
//     "id": 8,
//     "status": "APPROVED",
//     "total_lines": 254,
//     "lines_counted": 220,
//     "lines_at_zero": 34,
//     "total_cogs": 18265.03,
//     "total_revenue": 51207.00,
//     "gross_profit_percentage": 64.33,
//     "pour_cost_percentage": 35.67,
//     "approved_at": "2025-11-09T19:55:18",
//     "notes": "September 2025 stocktake"
//   }
// }

// Check if stocktake exists
if (period.stocktake) {
  console.log(`Stocktake ID: ${period.stocktake.id}`);
  console.log(`Status: ${period.stocktake.status}`);
  console.log(`Items: ${period.stocktake.lines_counted}/${period.stocktake.total_lines}`);
  console.log(`GP%: ${period.stocktake.gross_profit_percentage}%`);
  
  // Only fetch full stocktake if you need line details
  if (needLineDetails) {
    const fullStocktake = await fetch(
      `/api/stock_tracker/hotel-killarney/stocktakes/${period.stocktake.id}/`
    ).then(r => r.json());
    // fullStocktake.lines contains all stocktake line items
  }
} else {
  console.log('No stocktake exists for this period yet');
}
```

### Benefits:
✅ **No extra API calls** - All info in one request  
✅ **Item counts included** - total_lines, lines_counted, lines_at_zero  
✅ **Financial summary** - COGS, Revenue, GP%, Pour Cost%  
✅ **Status check** - DRAFT or APPROVED  
✅ **Null-safe** - Returns `null` if no stocktake exists  

---

---

## 📝 When You Need Full Stocktake Line Details

The `stocktake` object in the Period response includes **summary metrics only**. 

**If you need individual stocktake lines** (items counted, SKU details, quantities), make a separate call:

```javascript
const period = await fetch('/api/periods/8/').then(r => r.json());

if (period.stocktake_id) {
  // Fetch complete stocktake with all lines
  const fullStocktake = await fetch(
    `/api/stocktakes/${period.stocktake_id}/`
  ).then(r => r.json());
  
  // Now you have all stocktake lines
  console.log(fullStocktake.lines);  // Array of StocktakeLine objects
  console.log(fullStocktake.lines[0].item.name);  // Item details
  console.log(fullStocktake.lines[0].counted_full_units);  // Quantity
}
```

---

## 🔧 Legacy Methods (For Reference Only)

<details>
<summary>Click to expand old implementation methods</summary>

These methods are **no longer needed** but documented for legacy code reference.

### OLD Method 1: Search by Dates

```javascript
// Step 1: Get the Period
const period = await fetch(`/api/periods/${periodId}/`).then(r => r.json());

// Step 2: Get ALL Stocktakes and filter by dates
const stocktakes = await fetch('/api/stocktakes/').then(r => r.json());

// Step 3: Find matching stocktake by date range
const matchingStocktake = stocktakes.find(
  st => st.period_start === period.start_date && 
        st.period_end === period.end_date
);
```

**Problem:** Requires fetching all stocktakes and client-side filtering.

### OLD Method 2: Query by Date Parameters

```javascript
const period = await fetch(`/api/periods/${periodId}/`).then(r => r.json());

// Query stocktake by date range
const stocktakes = await fetch(
  `/api/stocktakes/?start_date=${period.start_date}&end_date=${period.end_date}`
).then(r => r.json());

const stocktake = stocktakes[0];
```

**Problem:** Extra API call with query parameters.

</details>

---

## 📊 Real Data Examples

### September 2025
```javascript
const period = await fetch('/api/periods/8/').then(r => r.json());

console.log(period);
// {
//   id: 8,
//   period_name: "September 2025",
//   start_date: "2025-09-01",
//   end_date: "2025-09-30",
//   stocktake_id: 8,
//   stocktake: {
//     id: 8,
//     status: "APPROVED",
//     total_lines: 254,
//     lines_counted: 220,
//     lines_at_zero: 34,
//     total_cogs: 18265.03,
//     total_revenue: 51207.00,
//     gross_profit_percentage: 64.33,
//     pour_cost_percentage: 35.67
//   }
// }
```

### October 2025
```javascript
const period = await fetch('/api/periods/7/').then(r => r.json());
// stocktake_id: 5
// stocktake.status: "APPROVED"
// stocktake.total_lines: 254
```

### November 2025
```javascript
const period = await fetch('/api/periods/9/').then(r => r.json());
// stocktake_id: 4
// stocktake.status: "DRAFT" or "APPROVED"
```

---

## ⚠️ Important Notes

### Period and Stocktake are Separate Models
- A Period can exist **WITHOUT** a Stocktake
- A Stocktake is only created when a stock count is performed
- **Always check** if `period.stocktake` is `null` before accessing properties

```javascript
// SAFE: Check before accessing
if (period.stocktake) {
  const status = period.stocktake.status;
  const total = period.stocktake.total_lines;
} else {
  console.log('No stocktake exists for this period yet');
}
```

### ID Mismatch is Normal
- Period ID ≠ Stocktake ID (they're different tables)
- November: Period **9** → Stocktake **4**
- October: Period **7** → Stocktake **5**
- September: Period **8** → Stocktake **8**

The backend matches them by **date range**, not by ID.

### What's Included vs Not Included

✅ **Included in `period.stocktake`:**
- ID, status, approval timestamp
- Item counts (total, counted, at zero)
- Financial summary (COGS, revenue, GP%, pour cost%)
- Notes field

❌ **NOT included (requires separate API call):**
- Individual stocktake lines
- Item-level details (SKU, name, category)
- Unit quantities per item

---

## 🎯 Quick Reference

| Need | Use | API Calls |
|------|-----|-----------|
| Check if stocktake exists | `period.stocktake !== null` | 1 |
| Get stocktake ID | `period.stocktake_id` | 1 |
| Get stocktake status | `period.stocktake.status` | 1 |
| Get item counts | `period.stocktake.lines_counted` | 1 |
| Get financials summary | `period.stocktake.total_cogs` | 1 |
| Get stocktake lines | `fetch('/api/stocktakes/{id}/')` | 2 |
| Get item details | `fetch('/api/stocktakes/{id}/')` | 2 |

---

## 📅 Last Updated
**November 2025** - Enhanced Period API implementation
