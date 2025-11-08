# Frontend: Complete Period Data in One Response

## Overview

The Period Detail endpoint now returns **ALL related data in ONE response**:
- Period information
- All snapshots (full data)
- All snapshot IDs (quick list)
- Related stocktake ID (if exists)
- Stocktake status
- Totals

**No need for multiple API calls!**

---

## API Endpoint

```
GET /api/stock_tracker/{hotel_id}/periods/{period_id}/
```

---

## Complete Response Structure

```json
{
  // ═══════════════════════════════════════════════════════
  // PERIOD DATA
  // ═══════════════════════════════════════════════════════
  "id": 9,
  "hotel": 2,
  "period_type": "MONTHLY",
  "period_name": "November 2025",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30",
  "year": 2024,
  "month": 11,
  "quarter": null,
  "week": null,
  "is_closed": false,
  
  // ═══════════════════════════════════════════════════════
  // SNAPSHOT DATA (Full objects - 254 items)
  // ═══════════════════════════════════════════════════════
  "snapshots": [
    {
      "id": 3801,
      "item": {
        "id": 250,
        "sku": "B0012",
        "name": "Cronins 0.0%",
        "category": {
          "code": "B",
          "name": "Bottled Beer"
        }
      },
      "closing_full_units": "0.00",
      "closing_partial_units": "69.0000",
      "display_full_units": "5",      // For UI (dozens)
      "display_partial_units": "9",    // For UI (bottles)
      "closing_stock_value": "81.65",
      "unit_cost": "14.2000",
      "cost_per_serving": "1.1833"
    },
    // ... 253 more items
  ],
  
  // ═══════════════════════════════════════════════════════
  // QUICK SNAPSHOT IDS LIST
  // ═══════════════════════════════════════════════════════
  "snapshot_ids": [3801, 3802, 3803, ..., 4054],
  
  // ═══════════════════════════════════════════════════════
  // RELATED STOCKTAKE (if exists)
  // ═══════════════════════════════════════════════════════
  "stocktake_id": 4,           // Can be different from period_id!
  "stocktake_status": "DRAFT", // or "APPROVED", or null if no stocktake
  
  // ═══════════════════════════════════════════════════════
  // TOTALS
  // ═══════════════════════════════════════════════════════
  "total_items": 254,
  "total_value": "26879.03"
}
```

---

## Frontend Usage

### Single API Call Gets Everything

```javascript
// One call, all data!
const periodData = await fetch(
  '/api/stock_tracker/1/periods/9/'
).then(r => r.json());

// Extract what you need
const {
  id: periodId,
  period_name,
  is_closed,
  snapshots,
  snapshot_ids,
  stocktake_id,
  stocktake_status,
  total_items,
  total_value
} = periodData;

console.log(`Period ${periodId}: ${period_name}`);
console.log(`Snapshots: ${total_items} items`);
console.log(`Total value: €${total_value}`);
console.log(`Stocktake: ${stocktake_id ? `ID ${stocktake_id} (${stocktake_status})` : 'None'}`);
```

---

## Understanding the Relationships

### Period ID vs Stocktake ID

```javascript
{
  "id": 9,              // ← Period ID (stable, never changes)
  "stocktake_id": 4,    // ← Stocktake ID (can be different!)
  "snapshot_ids": [3801, 3802, ...]  // ← Snapshot IDs (linked to period)
}
```

**Important:**
- `id` (9) = Period ID - use this as your primary reference
- `stocktake_id` (4) = Optional, can be null, can change if deleted/recreated
- `snapshot_ids` = Direct children of period, always present

---

## State Management Example (React)

```javascript
function StockDashboard() {
  const [periodData, setPeriodData] = useState(null);
  
  useEffect(() => {
    fetchPeriodData(9);
  }, []);
  
  const fetchPeriodData = async (periodId) => {
    const data = await fetch(`/api/stock_tracker/1/periods/${periodId}/`)
      .then(r => r.json());
    
    setPeriodData(data);
    
    // Store in state - everything you need!
    console.log('Period loaded:', {
      periodId: data.id,
      periodName: data.period_name,
      snapshotCount: data.total_items,
      hasStocktake: !!data.stocktake_id,
      stocktakeStatus: data.stocktake_status
    });
  };
  
  return (
    <div>
      <h2>{periodData?.period_name}</h2>
      <p>Status: {periodData?.is_closed ? 'Closed' : 'Open'}</p>
      <p>Items: {periodData?.total_items}</p>
      <p>Value: €{periodData?.total_value}</p>
      
      {periodData?.stocktake_id && (
        <p>
          Stocktake #{periodData.stocktake_id} - {periodData.stocktake_status}
        </p>
      )}
      
      <table>
        {periodData?.snapshots.map(snapshot => (
          <tr key={snapshot.id}>
            <td>{snapshot.item.name}</td>
            <td>{snapshot.display_full_units}</td>
            <td>{snapshot.display_partial_units}</td>
            <td>€{snapshot.closing_stock_value}</td>
          </tr>
        ))}
      </table>
    </div>
  );
}
```

---

## When to Use Each Field

### `id` (Period ID)
✅ **Always use as primary reference**
- Store in URL params
- Use for API calls
- Link snapshots to periods

### `snapshots` (Full array)
✅ **Display in UI**
- Show in table
- Edit counts
- Calculate totals

### `snapshot_ids` (Quick list)
✅ **Check completeness**
- Verify all items loaded
- Batch operations
- Quick lookups

### `stocktake_id` + `stocktake_status`
✅ **Optional workflow tracking**
- Show if stocktake exists
- Display approval status
- Link to stocktake details (if needed)

---

## Complete Workflow Example

```javascript
// 1. Load period with everything
const loadPeriod = async (periodId) => {
  const data = await fetch(`/api/stock_tracker/1/periods/${periodId}/`)
    .then(r => r.json());
  
  return {
    // Period info
    periodId: data.id,
    periodName: data.period_name,
    isOpen: !data.is_closed,
    
    // Snapshots
    items: data.snapshots.map(s => ({
      snapshotId: s.id,
      itemName: s.item.name,
      sku: s.item.sku,
      category: s.item.category.code,
      fullUnits: s.display_full_units,
      partialUnits: s.display_partial_units,
      value: s.closing_stock_value
    })),
    
    // Metadata
    totalItems: data.total_items,
    totalValue: data.total_value,
    
    // Stocktake (optional)
    stocktakeId: data.stocktake_id,
    stocktakeStatus: data.stocktake_status
  };
};

// 2. Use in component
const periodInfo = await loadPeriod(9);

console.log('Period:', periodInfo.periodName);
console.log('Items:', periodInfo.items.length);
console.log('Has stocktake:', periodInfo.stocktakeId ? 'Yes' : 'No');

// 3. Display items
periodInfo.items.forEach(item => {
  displayStockItem(item);
});

// 4. Update a count
await updateSnapshot(
  periodInfo.items[0].snapshotId,
  { closing_full_units: 10, closing_partial_units: 5 }
);

// 5. Close period when done
await closePeriod(periodInfo.periodId);
```

---

## Handling Null Stocktake

If no stocktake exists:

```javascript
{
  "id": 9,
  "period_name": "November 2025",
  "snapshots": [...],
  "snapshot_ids": [...],
  "stocktake_id": null,        // ← No stocktake
  "stocktake_status": null,    // ← No status
  "total_items": 254,
  "total_value": "26879.03"
}
```

**Frontend handling:**

```javascript
if (periodData.stocktake_id) {
  // Show stocktake workflow UI
  showStocktakeSection(periodData.stocktake_id, periodData.stocktake_status);
} else {
  // Just show simple stock counting
  showSimpleStockCount(periodData.snapshots);
}
```

---

## Key Benefits

✅ **One API call** - All data in single response  
✅ **Clear relationships** - Period ↔ Snapshots ↔ Stocktake  
✅ **No ID confusion** - Everything clearly linked  
✅ **Optional stocktake** - Works with or without  
✅ **Display-ready data** - Includes display_full_units, display_partial_units  

---

## Response Fields Reference

| Field | Type | Always Present | Description |
|-------|------|----------------|-------------|
| `id` | int | ✅ Yes | Period ID (stable reference) |
| `period_name` | string | ✅ Yes | "November 2025" |
| `is_closed` | boolean | ✅ Yes | Period status |
| `snapshots` | array | ✅ Yes | Full snapshot objects |
| `snapshot_ids` | array | ✅ Yes | Quick ID list |
| `stocktake_id` | int/null | ⚠️ Maybe | Stocktake ID (if exists) |
| `stocktake_status` | string/null | ⚠️ Maybe | "DRAFT" or "APPROVED" |
| `total_items` | int | ✅ Yes | Count of items |
| `total_value` | string | ✅ Yes | Total stock value |

---

## Summary

**Everything in one place!** 🎯

The frontend gets:
- Period data
- All 254 snapshots with display values
- Snapshot IDs for quick access
- Related stocktake (if exists)
- Totals

**No more multiple API calls or confusion about relationships!**
