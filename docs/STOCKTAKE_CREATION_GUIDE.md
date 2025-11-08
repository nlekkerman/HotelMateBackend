# Stocktake Creation and Population Guide

## Overview

When creating a stocktake for a period, the backend provides all the data needed from the **Period Snapshots**. Frontend just needs to understand the relationships and how to send the data back.

---

## Data Relationships

```
Period (e.g., November 2025)
  ├── Snapshots (254 items)
  │   ├── Snapshot #3801 (Budweiser)
  │   │   ├── opening_stock (from October's closing)
  │   │   └── closing_stock (to be counted)
  │   └── Snapshot #3802 (Heineken)
  │       ├── opening_stock (from October's closing)
  │       └── closing_stock (to be counted)
  └── Stocktake (created by frontend)
      ├── period_start = Period.start_date
      ├── period_end = Period.end_date
      └── Lines (created from Snapshots)
          ├── Line #1 (for Budweiser)
          │   ├── item = Snapshot.item
          │   ├── opening_qty = Snapshot.opening_partial_units
          │   └── counted = (user enters)
          └── Line #2 (for Heineken)
              ├── item = Snapshot.item
              ├── opening_qty = Snapshot.opening_partial_units
              └── counted = (user enters)
```

---

## Step 1: Get Period Data

```javascript
// GET /api/stock_tracker/{hotel_id}/periods/{period_id}/
const periodData = await fetch('/api/stock_tracker/1/periods/9/')
  .then(r => r.json());

console.log({
  period_id: periodData.id,                    // 9
  period_name: periodData.period_name,         // "November 2025"
  start_date: periodData.start_date,           // "2025-11-01"
  end_date: periodData.end_date,               // "2025-11-30"
  snapshots: periodData.snapshots.length,      // 254 items
  stocktake_id: periodData.stocktake_id,       // 4 (if already exists)
  stocktake_status: periodData.stocktake_status // "DRAFT" or "APPROVED"
});
```

---

## Step 2: Check if Stocktake Already Exists

```javascript
if (periodData.stocktake_id) {
  // Stocktake already exists - fetch it
  const stocktake = await fetch(
    `/api/stock_tracker/1/stocktakes/${periodData.stocktake_id}/`
  ).then(r => r.json());
  
  console.log('Existing stocktake:', stocktake.id);
  console.log('Status:', stocktake.status);
  console.log('Lines:', stocktake.lines.length);
  
  // Use existing stocktake
} else {
  // Need to create new stocktake
  console.log('No stocktake exists - need to create one');
}
```

---

## Step 3: Create New Stocktake

```javascript
async function createStocktake(hotelId, periodData) {
  // Create stocktake linked to period via dates
  const stocktakeData = {
    period_start: periodData.start_date,  // "2025-11-01"
    period_end: periodData.end_date,      // "2025-11-30"
    notes: `Stocktake for ${periodData.period_name}`
  };
  
  const stocktake = await fetch(
    `/api/stock_tracker/${hotelId}/stocktakes/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(stocktakeData)
    }
  ).then(r => r.json());
  
  console.log('Created stocktake:', stocktake.id);
  return stocktake;
}
```

---

## Step 4: Populate Stocktake Lines from Snapshots

```javascript
async function populateStocktakeLines(hotelId, stocktakeId, periodData) {
  // Create a line for each snapshot
  const lines = periodData.snapshots.map(snapshot => {
    return {
      stocktake: stocktakeId,
      item: snapshot.item.id,
      
      // Opening stock from snapshot (previous period's closing)
      opening_qty: snapshot.opening_partial_units,
      
      // Counts - user will enter these
      counted_full_units: 0,
      counted_partial_units: 0,
      
      // Movements - backend will calculate these
      purchases: 0,
      sales: 0,
      waste: 0,
      transfers_in: 0,
      transfers_out: 0,
      adjustments: 0
    };
  });
  
  // Create all lines in batch
  const createdLines = await Promise.all(
    lines.map(line => 
      fetch(`/api/stock_tracker/${hotelId}/stocktake-lines/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(line)
      }).then(r => r.json())
    )
  );
  
  console.log(`Created ${createdLines.length} stocktake lines`);
  return createdLines;
}
```

---

## Step 5: Display Stocktake for Counting

```javascript
function displayStocktake(periodData, stocktakeLines) {
  return periodData.snapshots.map((snapshot, index) => {
    const line = stocktakeLines.find(l => l.item === snapshot.item.id);
    
    return {
      // Item info
      item_id: snapshot.item.id,
      sku: snapshot.item.sku,
      name: snapshot.item.name,
      category: snapshot.item.category_display,
      size: snapshot.item.size,
      
      // Opening stock (from snapshot)
      opening_display: {
        full: snapshot.opening_display_full_units,
        partial: snapshot.opening_display_partial_units
      },
      opening_value: snapshot.opening_stock_value,
      
      // User enters counts here
      counted: {
        full: line.counted_full_units,
        partial: line.counted_partial_units
      },
      
      // Costs (for value calculation)
      unit_cost: snapshot.unit_cost,
      cost_per_serving: snapshot.cost_per_serving,
      
      // Line ID (for updating)
      line_id: line.id
    };
  });
}
```

---

## Step 6: User Enters Counts

```javascript
async function updateCount(hotelId, lineId, fullUnits, partialUnits) {
  const updated = await fetch(
    `/api/stock_tracker/${hotelId}/stocktake-lines/${lineId}/`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        counted_full_units: fullUnits,
        counted_partial_units: partialUnits
      })
    }
  ).then(r => r.json());
  
  // Backend automatically calculates:
  // - counted_qty (total servings)
  // - expected_qty (opening + purchases - sales)
  // - variance_qty (counted - expected)
  // - counted_value
  // - variance_value
  
  return updated;
}
```

---

## Complete Workflow Example

```javascript
class StocktakeManager {
  constructor(hotelId, periodId) {
    this.hotelId = hotelId;
    this.periodId = periodId;
    this.periodData = null;
    this.stocktake = null;
    this.lines = null;
  }
  
  async initialize() {
    // 1. Get period data with snapshots
    this.periodData = await fetch(
      `/api/stock_tracker/${this.hotelId}/periods/${this.periodId}/`
    ).then(r => r.json());
    
    console.log(`Period: ${this.periodData.period_name}`);
    console.log(`Snapshots: ${this.periodData.snapshots.length}`);
    
    // 2. Check if stocktake exists
    if (this.periodData.stocktake_id) {
      // Fetch existing stocktake
      this.stocktake = await fetch(
        `/api/stock_tracker/${this.hotelId}/stocktakes/${this.periodData.stocktake_id}/`
      ).then(r => r.json());
      
      this.lines = this.stocktake.lines;
      console.log(`Using existing stocktake #${this.stocktake.id}`);
    } else {
      // Create new stocktake
      await this.createNewStocktake();
    }
    
    return this.getDisplayData();
  }
  
  async createNewStocktake() {
    // 3. Create stocktake
    this.stocktake = await fetch(
      `/api/stock_tracker/${this.hotelId}/stocktakes/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          period_start: this.periodData.start_date,
          period_end: this.periodData.end_date,
          notes: `Stocktake for ${this.periodData.period_name}`
        })
      }
    ).then(r => r.json());
    
    console.log(`Created stocktake #${this.stocktake.id}`);
    
    // 4. Create lines from snapshots
    this.lines = [];
    for (const snapshot of this.periodData.snapshots) {
      const line = await fetch(
        `/api/stock_tracker/${this.hotelId}/stocktake-lines/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stocktake: this.stocktake.id,
            item: snapshot.item.id,
            opening_qty: snapshot.opening_partial_units,
            counted_full_units: 0,
            counted_partial_units: 0
          })
        }
      ).then(r => r.json());
      
      this.lines.push(line);
    }
    
    console.log(`Created ${this.lines.length} lines`);
  }
  
  getDisplayData() {
    return this.periodData.snapshots.map(snapshot => {
      const line = this.lines.find(l => l.item === snapshot.item.id);
      
      return {
        line_id: line.id,
        item_id: snapshot.item.id,
        sku: snapshot.item.sku,
        name: snapshot.item.name,
        category: snapshot.item.category_display,
        size: snapshot.item.size,
        
        // Opening (from snapshot)
        opening: {
          full: snapshot.opening_display_full_units,
          partial: snapshot.opening_display_partial_units,
          value: snapshot.opening_stock_value
        },
        
        // Counted (from line)
        counted: {
          full: line.counted_full_units,
          partial: line.counted_partial_units,
          qty: line.counted_qty,
          value: line.counted_value
        },
        
        // Expected (from line - backend calculated)
        expected: {
          qty: line.expected_qty,
          value: line.expected_value
        },
        
        // Variance (from line - backend calculated)
        variance: {
          qty: line.variance_qty,
          value: line.variance_value
        },
        
        // Costs
        cost_per_serving: snapshot.cost_per_serving
      };
    });
  }
  
  async updateCount(lineId, fullUnits, partialUnits) {
    const updated = await fetch(
      `/api/stock_tracker/${this.hotelId}/stocktake-lines/${lineId}/`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          counted_full_units: fullUnits,
          counted_partial_units: partialUnits
        })
      }
    ).then(r => r.json());
    
    // Update local line
    const index = this.lines.findIndex(l => l.id === lineId);
    if (index !== -1) {
      this.lines[index] = updated;
    }
    
    return updated;
  }
  
  async approveStocktake() {
    // Submit for approval
    const approved = await fetch(
      `/api/stock_tracker/${this.hotelId}/stocktakes/${this.stocktake.id}/approve/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }
    ).then(r => r.json());
    
    this.stocktake = approved;
    console.log('Stocktake approved!');
    return approved;
  }
}

// Usage
const manager = new StocktakeManager(1, 9);
await manager.initialize();

// Display data
const displayData = manager.getDisplayData();
console.log('Items to count:', displayData.length);

// User enters count for first item
await manager.updateCount(displayData[0].line_id, 10, 5);

// When done
await manager.approveStocktake();
```

---

## React Component Example

```jsx
import React, { useEffect, useState } from 'react';

function StocktakeCounting({ hotelId, periodId }) {
  const [loading, setLoading] = useState(true);
  const [periodData, setPeriodData] = useState(null);
  const [stocktake, setStocktake] = useState(null);
  const [items, setItems] = useState([]);
  
  useEffect(() => {
    initializeStocktake();
  }, [periodId]);
  
  const initializeStocktake = async () => {
    // 1. Get period data
    const period = await fetch(
      `/api/stock_tracker/${hotelId}/periods/${periodId}/`
    ).then(r => r.json());
    
    setPeriodData(period);
    
    // 2. Get or create stocktake
    let st;
    if (period.stocktake_id) {
      st = await fetch(
        `/api/stock_tracker/${hotelId}/stocktakes/${period.stocktake_id}/`
      ).then(r => r.json());
    } else {
      st = await createStocktake(period);
    }
    
    setStocktake(st);
    
    // 3. Map snapshots to display items
    const displayItems = period.snapshots.map(snap => {
      const line = st.lines.find(l => l.item === snap.item.id);
      return {
        snapshot: snap,
        line: line
      };
    });
    
    setItems(displayItems);
    setLoading(false);
  };
  
  const createStocktake = async (period) => {
    // Create stocktake
    const st = await fetch(
      `/api/stock_tracker/${hotelId}/stocktakes/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          period_start: period.start_date,
          period_end: period.end_date
        })
      }
    ).then(r => r.json());
    
    // Create lines from snapshots
    const lines = await Promise.all(
      period.snapshots.map(snap =>
        fetch(`/api/stock_tracker/${hotelId}/stocktake-lines/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stocktake: st.id,
            item: snap.item.id,
            opening_qty: snap.opening_partial_units,
            counted_full_units: 0,
            counted_partial_units: 0
          })
        }).then(r => r.json())
      )
    );
    
    st.lines = lines;
    return st;
  };
  
  const handleCountChange = async (lineId, full, partial) => {
    const updated = await fetch(
      `/api/stock_tracker/${hotelId}/stocktake-lines/${lineId}/`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          counted_full_units: full,
          counted_partial_units: partial
        })
      }
    ).then(r => r.json());
    
    // Update local state
    setItems(items.map(item => 
      item.line.id === lineId 
        ? { ...item, line: updated }
        : item
    ));
  };
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      <h1>Stocktake: {periodData.period_name}</h1>
      <p>Status: {stocktake.status}</p>
      
      <table>
        <thead>
          <tr>
            <th>Item</th>
            <th>Opening Stock</th>
            <th>Count (Full)</th>
            <th>Count (Partial)</th>
            <th>Expected</th>
            <th>Variance</th>
          </tr>
        </thead>
        <tbody>
          {items.map(({ snapshot, line }) => (
            <tr key={line.id}>
              <td>
                {snapshot.item.name}
                <br />
                <small>{snapshot.item.sku}</small>
              </td>
              <td>
                {snapshot.opening_display_full_units} + 
                {snapshot.opening_display_partial_units}
              </td>
              <td>
                <input
                  type="number"
                  value={line.counted_full_units}
                  onChange={(e) => handleCountChange(
                    line.id,
                    e.target.value,
                    line.counted_partial_units
                  )}
                />
              </td>
              <td>
                <input
                  type="number"
                  value={line.counted_partial_units}
                  onChange={(e) => handleCountChange(
                    line.id,
                    line.counted_full_units,
                    e.target.value
                  )}
                />
              </td>
              <td>{line.expected_qty}</td>
              <td style={{ color: line.variance_qty < 0 ? 'red' : 'green' }}>
                {line.variance_qty}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default StocktakeCounting;
```

---

## Key Relationships

### Period ↔ Stocktake
- Linked via **dates** (not FK)
- `Stocktake.period_start` = `Period.start_date`
- `Stocktake.period_end` = `Period.end_date`
- Period can have 0 or 1 stocktake

### Period → Snapshots
- Direct FK: `Snapshot.period` → `Period.id`
- One-to-many: One period has many snapshots

### Snapshot ↔ Stocktake Line
- Linked via **item** (not FK)
- `StocktakeLine.item` = `Snapshot.item`
- Opening qty comes from snapshot

### Data Flow
```
Period.snapshots[i].opening_partial_units 
  → StocktakeLine.opening_qty
  
User enters counts
  → StocktakeLine.counted_full_units
  → StocktakeLine.counted_partial_units
  
Backend calculates
  → StocktakeLine.expected_qty
  → StocktakeLine.variance_qty
  → StocktakeLine.counted_value
```

---

## Summary

✅ **To create stocktake:**
1. Get period data (includes all snapshots)
2. Create stocktake with period dates
3. Create lines from snapshots (use opening_partial_units)
4. User enters counts
5. Backend calculates variance

✅ **Frontend gets from Period Snapshots:**
- Opening stock (opening_display_full_units, opening_display_partial_units)
- Item info (id, sku, name, category, size)
- Costs (cost_per_serving)
- Display values (already formatted)

✅ **Frontend sends to Stocktake Lines:**
- item (from snapshot.item.id)
- opening_qty (from snapshot.opening_partial_units)
- counted_full_units (user input)
- counted_partial_units (user input)

✅ **Backend calculates automatically:**
- expected_qty
- counted_qty
- variance_qty
- counted_value
- variance_value

**All the data is in the Period response - just map it to Stocktake Lines!** 🎉
