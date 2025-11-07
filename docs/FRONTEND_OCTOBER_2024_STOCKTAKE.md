# Frontend Guide: October 2024 Stocktake Display

## Overview
The October 2024 stocktake is now **CLOSED** and finalized in the backend. This document explains the data structure and how to fetch and display it.

---

## What We Created

### 1. Stock Period (CLOSED)
- **Period ID**: 7
- **Period Name**: "October 2024"
- **Date Range**: 2024-10-01 to 2024-10-31
- **Type**: MONTHLY
- **Status**: `is_closed = True` ✅ (LOCKED - cannot be modified)

### 2. Stock Snapshots (254 items)
All stock data is stored in `StockSnapshot` records linked to Period ID 7:
- **Total Items**: 254
- **Total Value**: €27,306.58
- **Breakdown**:
  - Draught Beers (D): 14 items = €5,311.62
  - Bottled Beers (B): 21 items = €2,288.47
  - Spirits (S): 128 items = €11,063.70
  - Wines (W): 44 items = €5,580.34
  - Minerals & Syrups (M): 47 items = €3,062.45

---

## API Endpoints to Use

### Get October 2024 Period
```http
GET /api/stock-tracker/periods/?year=2024&month=10
```

**Response:**
```json
{
  "id": 7,
  "period_name": "October 2024",
  "start_date": "2024-10-01",
  "end_date": "2024-10-31",
  "period_type": "MONTHLY",
  "is_closed": true,
  "created_at": "2025-11-07T...",
  "hotel": 2
}
```

### Get All Snapshots for October 2024
```http
GET /api/stock-tracker/snapshots/?period=7
```

**Response (example):**
```json
[
  {
    "id": 2695,
    "item": {
      "id": 250,
      "sku": "D2133",
      "name": "20 Heineken 00%",
      "category": {
        "code": "D",
        "name": "Draught Beer"
      },
      "size": "20Lt",
      "uom": 35.21
    },
    "closing_full_units": "0.00",
    "closing_partial_units": "40.0000",
    "closing_stock_value": "68.25",
    "unit_cost": "1.7063",
    "cost_per_serving": "0.0485",
    "total_servings": 40.0,
    "period": 7,
    "hotel": 2
  },
  // ... 253 more items
]
```

### Get Snapshots by Category
```http
GET /api/stock-tracker/snapshots/?period=7&category=D  # Draught
GET /api/stock-tracker/snapshots/?period=7&category=B  # Bottled
GET /api/stock-tracker/snapshots/?period=7&category=S  # Spirits
GET /api/stock-tracker/snapshots/?period=7&category=W  # Wines
GET /api/stock-tracker/snapshots/?period=7&category=M  # Minerals
```

---

## Data Structure Explained

### StockSnapshot Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | Integer | Snapshot ID | 2695 |
| `item.sku` | String | Product code | "D2133" |
| `item.name` | String | Product name | "20 Heineken 00%" |
| `item.category.code` | String | Category code (D/B/S/W/M) | "D" |
| `item.category.name` | String | Category full name | "Draught Beer" |
| `item.size` | String | Package size | "20Lt", "70cl", "75cl" |
| `item.uom` | Decimal | Units of measure (servings per unit) | 35.21 |
| `closing_full_units` | Decimal | **Full units at period end** | "0.00" |
| `closing_partial_units` | Decimal | **Partial units at period end** | "40.0000" |
| `closing_stock_value` | Decimal | **Total value (€) - FROM EXCEL** | "68.25" |
| `unit_cost` | Decimal | Cost per full unit | "1.7063" |
| `cost_per_serving` | Decimal | Cost per serving | "0.0485" |
| `total_servings` | Decimal | **CALCULATED**: (full × uom) + partial | 40.0 |
| `period` | Integer | Period ID | 7 |

### Important Notes

#### For Draught Beers (Category D):
- `closing_full_units` = Number of **kegs**
- `closing_partial_units` = Number of **pints** (loose pints, not kegs)
- Example: `full=6.00, partial=39.75` means "6 kegs + 39.75 pints"

#### For Spirits (Category S):
- `closing_full_units` = Number of **bottles**
- `closing_partial_units` = **Fraction** of a bottle (0.70 = 70% of a bottle)
- Example: `full=2.00, partial=0.30` means "2 bottles + 30% of a bottle"

#### For Wines (Category W):
- `closing_full_units` = Number of **bottles**
- `closing_partial_units` = **Fraction** of a bottle
- Example: `full=10.00, partial=0.00` means "10 full bottles"

#### For Bottled Beers (Category B):
- `closing_full_units` = Number of **cases/dozens** (always 0 in this stocktake)
- `closing_partial_units` = Number of **individual bottles**
- Example: `full=0.00, partial=113.00` means "113 bottles"

#### For Minerals & Syrups (Category M):
- Mixed format depending on item
- Some use full units (BIB bags), others use partial units (bottles)

---

## UI Display Requirements

### 1. Period Header
```
📅 October 2024 Stocktake
Status: 🔒 CLOSED
Date Range: 01 Oct 2024 - 31 Oct 2024
Total Value: €27,306.58
Total Items: 254
```

### 2. Category Tabs/Sections
Display 5 categories with counts and totals:

```
┌─────────────────────────────────────────┐
│ [Draught (14)] [Bottled (21)] ...       │
└─────────────────────────────────────────┘
```

**Category Breakdown:**
- 🍺 Draught Beers: 14 items = €5,311.62
- 🍾 Bottled Beers: 21 items = €2,288.47
- 🥃 Spirits: 128 items = €11,063.70
- 🍷 Wines: 44 items = €5,580.34
- 🥤 Minerals & Syrups: 47 items = €3,062.45

### 3. Item List Table (per category)

**Columns to Display:**

| SKU | Name | Full Units | Partial Units | Total Servings | Stock Value |
|-----|------|-----------|---------------|----------------|-------------|
| D2133 | 20 Heineken 00% | 0 kegs | 40.00 pints | 40.0 | €68.25 |
| D1258 | 50 Coors | 6 kegs | 39.75 pints | 567.75 | €1,265.44 |
| S0610 | Jameson | 41 btls | 0.30 btl | 829.0 shots | €901.58 |
| W0040 | House Wine Red | 36 btls | 0.00 btl | 36.0 | €124.92 |
| B0070 | Budweiser 33cl | 0 doz | 113 btls | 113 | €110.65 |

**Unit Labels by Category:**
- Draught (D): "kegs" / "pints"
- Spirits (S): "bottles" / "% bottle"
- Wines (W): "bottles" / "% bottle"
- Bottled (B): "dozen" / "bottles"
- Minerals (M): depends on item (show as is)

### 4. Category Totals (footer)
```
─────────────────────────────────────────
Total Items: 14
Total Value: €5,311.62
─────────────────────────────────────────
```

### 5. Grand Total (page footer)
```
═════════════════════════════════════════
GRAND TOTAL
Items: 254 | Value: €27,306.58
═════════════════════════════════════════
```

---

## Important Frontend Rules

### ✅ DO:
1. **Display `closing_stock_value` directly** - This is the EXACT value from Excel
2. **Show category totals** - Sum up `closing_stock_value` for each category
3. **Display "CLOSED" badge** - Period cannot be edited when `is_closed = true`
4. **Format currency** - Always show 2 decimal places: €1,234.56
5. **Show `total_servings`** - This is calculated correctly by backend
6. **Use proper unit labels** - "kegs/pints" for draught, "bottles/% bottle" for spirits/wines

### ❌ DON'T:
1. **Don't recalculate `closing_stock_value`** - Use the value from API directly
2. **Don't allow edits** - Period is CLOSED (read-only)
3. **Don't calculate totals yourself** - Sum the `closing_stock_value` from snapshots
4. **Don't mix unit types** - Follow the unit conventions per category

---

## Example Frontend Code (React)

### Fetch October 2024 Data
```javascript
const fetchOctoberStocktake = async () => {
  try {
    // Get period
    const periodResponse = await fetch('/api/stock-tracker/periods/?year=2024&month=10');
    const periods = await periodResponse.json();
    const period = periods[0];
    
    if (!period) {
      console.error('October 2024 period not found');
      return;
    }
    
    // Get all snapshots
    const snapshotsResponse = await fetch(`/api/stock-tracker/snapshots/?period=${period.id}`);
    const snapshots = await snapshotsResponse.json();
    
    // Group by category
    const grouped = snapshots.reduce((acc, snapshot) => {
      const category = snapshot.item.category.code;
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(snapshot);
      return acc;
    }, {});
    
    // Calculate totals
    const totals = {};
    for (const [cat, items] of Object.entries(grouped)) {
      totals[cat] = items.reduce((sum, item) => 
        sum + parseFloat(item.closing_stock_value), 0
      );
    }
    
    const grandTotal = Object.values(totals).reduce((sum, val) => sum + val, 0);
    
    return {
      period,
      snapshots: grouped,
      totals,
      grandTotal,
      itemCount: snapshots.length
    };
    
  } catch (error) {
    console.error('Error fetching stocktake:', error);
  }
};
```

### Display Category
```jsx
const StocktakeCategory = ({ category, snapshots }) => {
  const categoryTotal = snapshots.reduce(
    (sum, s) => sum + parseFloat(s.closing_stock_value), 0
  );
  
  const getUnitLabel = (category, isPartial) => {
    if (category === 'D') return isPartial ? 'pints' : 'kegs';
    if (category === 'B') return isPartial ? 'bottles' : 'dozen';
    if (category === 'S' || category === 'W') return isPartial ? '% bottle' : 'bottles';
    return 'units';
  };
  
  return (
    <div>
      <h3>{category} - {snapshots.length} items - €{categoryTotal.toFixed(2)}</h3>
      <table>
        <thead>
          <tr>
            <th>SKU</th>
            <th>Name</th>
            <th>Full Units</th>
            <th>Partial Units</th>
            <th>Total Servings</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {snapshots.map(snapshot => (
            <tr key={snapshot.id}>
              <td>{snapshot.item.sku}</td>
              <td>{snapshot.item.name}</td>
              <td>{snapshot.closing_full_units} {getUnitLabel(category, false)}</td>
              <td>{snapshot.closing_partial_units} {getUnitLabel(category, true)}</td>
              <td>{snapshot.total_servings}</td>
              <td>€{parseFloat(snapshot.closing_stock_value).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## Verification Checklist

Before deploying frontend, verify:

- [ ] Period shows as "CLOSED" with 🔒 icon
- [ ] All 254 items are displayed
- [ ] Grand total shows €27,306.58
- [ ] Category totals match:
  - [ ] Draught: €5,311.62 (14 items)
  - [ ] Bottled: €2,288.47 (21 items)
  - [ ] Spirits: €11,063.70 (128 items)
  - [ ] Wines: €5,580.34 (44 items)
  - [ ] Minerals: €3,062.45 (47 items)
- [ ] Unit labels are correct per category
- [ ] Currency formatting is consistent (2 decimals)
- [ ] No edit buttons shown (period is closed)

---

## Questions?

If you encounter issues:
1. Check period `is_closed` status - should be `true`
2. Verify period ID is 7
3. Ensure all 254 snapshots are fetched
4. Sum `closing_stock_value` directly - don't recalculate
5. Check category codes: D, B, S, W, M

**Backend Contact**: The October 2024 stocktake is finalized and locked. All data matches Excel values within €0.07 (essentially perfect).
