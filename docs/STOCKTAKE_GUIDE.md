# Stocktake System Guide

## Overview

The Stocktake system provides an **editable view of a Period**, allowing staff to count physical stock and compare it against expected values. Each Stocktake is connected to a Period via dates (`period_start` and `period_end`), though Stocktake ID and Period ID are independent.

## Key Concepts

### Stocktake vs Period
- **Period**: Read-only snapshot of stock at period end
- **Stocktake**: Editable counting interface for the same period
- **Connection**: Via dates, not foreign key (IDs are independent)
- **Data**: Stocktake includes ALL Period data + editable counting lines

### Opening Stock vs Expected Stock

#### **Opening Stock** (START of Period)
What you **started with** at the beginning of the period:
- Comes from **previous period's closing stock** (what was last counted)
- Fixed - doesn't change during the period
- The baseline for all calculations

**Formula**: `Opening Stock = Previous Period Closing Stock`

#### **Expected Stock** (END of Period)
What you **should have now** based on all activity:
- **Starts with Opening Stock**
- **Adds all purchases** (stock coming in)
- **Subtracts all sales** (stock going out)
- **Subtracts waste, transfers out, etc.**

**Formula**: `Expected Stock = Opening Stock + Purchases - Sales - Waste ± Transfers ± Adjustments`

**In simple terms:**
- **Opening** = Previous closing (starting point)
- **Expected** = Opening adjusted for everything that happened during the period
- **Expected** is the "theoretical" closing stock before you physically count

**Example Flow**:
```
October 31 (Period 1 ends):
  Physical Count: 5 cases + 3 bottles
  ↓ This becomes...
  
November 1 (Period 2 starts):
  Opening Stock: 5 cases + 3 bottles ← Copied from Oct 31 closing
  
During November (Period 2):
  Starting with: 5 cases + 3 bottles (67 bottles)
  + Purchases:   2 cases (24 bottles)      ← New stock delivered
  - Sales:       45 bottles sold           ← Stock sold to customers
  - Waste:       1 bottle wasted           ← Broken/spillage
  ────────────────────────────────────────
  = Expected:    6 cases + 5 bottles (79 bottles)
  
November 30 (Period 2 ends):
  Expected Stock: 6 cases + 5 bottles ← What you SHOULD have
  Counted Stock:  6 cases + 3 bottles ← What you ACTUALLY counted
  ────────────────────────────────────
  Variance:       0 cases - 2 bottles ← 2 bottles missing!
```

**Key Relationships**:
```
Opening (Nov 1)    = Previous Closing (Oct 31)
Expected (Nov 30)  = Opening + All Movements During November
Variance           = Counted - Expected (shrinkage/theft/errors)
Next Opening (Dec 1) = Counted (Nov 30)  ← This becomes opening for next period!
```

**Why Expected Stock Matters**:
- Shows what you theoretically should have
- Helps identify shrinkage, theft, or errors
- If Counted < Expected = Missing stock (loss)
- If Counted > Expected = Extra stock (found/error in sales tracking)

## Category-Specific Display Formats

### Bottles (Category B) & Dozen Items (Category M with "Doz")

**UOM**: 12 servings = 1 case/dozen

**Display Format**:
- Full Units: **Cases** (whole numbers: 0, 1, 2, 3...)
- Partial Units: **Bottles** (whole numbers: 0, 1, 2...11)

**Example**:
```
Raw servings: 39.00
Calculation: 39 ÷ 12 = 3 cases, 3 bottles
Display: 3 cases + 3 bottles
```

**Opening Stock Flow**:
```
Previous Period Closing:
  - Counted: 5 cases + 7 bottles
  - Raw servings: (5 × 12) + 7 = 67 servings

Current Period Opening:
  - Display: 5 cases + 7 bottles
  - Raw servings: 67 servings
```

### Draught (Category D)

**UOM**: Variable (e.g., 88 pints = 1 keg for standard keg)

**Display Format**:
- Full Units: **Kegs** (whole numbers: 0, 1, 2...)
- Partial Units: **Pints** (2 decimal places: 0.00, 1.50, 45.75)

**Example**:
```
Raw servings: 133.50 pints
UOM: 88 pints per keg
Calculation: 133.50 ÷ 88 = 1 keg, 45.50 pints
Display: 1 keg + 45.50 pints
```

**Opening Stock Flow**:
```
Previous Period Closing:
  - Counted: 2 kegs + 23.75 pints
  - Raw servings: (2 × 88) + 23.75 = 199.75 pints

Current Period Opening:
  - Display: 2 kegs + 23.75 pints
  - Raw servings: 199.75 pints
```

### Spirits (Category S) & Wine (Category W)

**UOM**: Servings per bottle (e.g., 28 × 25ml shots = 1 × 700ml bottle)

**Display Format**:
- Full Units: **Bottles** (whole numbers: 0, 1, 2...)
- Partial Units: **Fractional** (2 decimal places: 0.00, 0.25, 0.75)

**Example**:
```
Raw servings: 45.50 shots
UOM: 28 shots per bottle
Calculation: 45.50 ÷ 28 = 1 bottle, 0.625 fractional
Display: 1 bottle + 0.63 (rounded to 2 decimals)
```

**Opening Stock Flow**:
```
Previous Period Closing:
  - Counted: 3 bottles + 0.50 partial
  - Raw servings: (3 × 28) + (0.50 × 28) = 98 servings

Current Period Opening:
  - Display: 3 bottles + 0.50 partial
  - Raw servings: 98 servings
```

## API Response Structure

### GET /api/stocktakes/{id}/

Returns complete Period data + editable stocktake lines:

```json
{
  "id": 4,
  "hotel": 1,
  "period_start": "2025-11-01",
  "period_end": "2025-11-30",
  "status": "pending",
  "is_locked": false,
  
  // Period Connection
  "period_id": 9,
  "period_name": "November 2025",
  "period_is_closed": false,
  
  // Snapshots (same as Period - all items with opening/closing)
  "snapshots": [
    {
      "id": 1234,
      "item": {
        "id": 1,
        "sku": "BUD-001",
        "name": "Budweiser",
        "category": "D",
        "size": "88 Pints Keg"
      },
      
      // Opening stock (from previous period closing)
      "opening_full_units": "2",           // 2 kegs
      "opening_partial_units": "23.75",    // 23.75 pints
      "opening_stock_value": "245.50",
      "opening_display_full_units": "2",
      "opening_display_partial_units": "23.75",
      
      // Closing stock (counted at period end)
      "closing_full_units": "1",
      "closing_partial_units": "45.50",
      "closing_stock_value": "178.25",
      "closing_display_full_units": "1",
      "closing_display_partial_units": "45.50",
      
      "unit_cost": "125.00",
      "cost_per_serving": "1.42"
    }
  ],
  
  // Stocktake Lines (editable counting data)
  "lines": [
    {
      "id": 5678,
      "item": 1,
      "item_sku": "BUD-001",
      "item_name": "Budweiser",
      "category_code": "D",
      
      // Opening quantities
      "opening_qty": "199.75",                    // Raw servings
      "opening_display_full_units": "2",          // 2 kegs
      "opening_display_partial_units": "23.75",   // 23.75 pints
      
      // Movements during period
      "purchases": "88.00",      // 1 keg purchased
      "sales": "152.25",         // Sold 152.25 pints
      "waste": "2.00",           // 2 pints wasted
      "transfers_in": "0.00",
      "transfers_out": "0.00",
      "adjustments": "0.00",
      
      // Expected closing
      "expected_qty": "133.50",                   // Raw servings
      "expected_display_full_units": "1",         // 1 keg
      "expected_display_partial_units": "45.50",  // 45.50 pints
      "expected_value": "189.57",
      
      // Counted closing (what staff counted)
      "counted_full_units": "1",                  // Staff counted 1 keg
      "counted_partial_units": "40.00",           // Staff counted 40 pints
      "counted_qty": "128.00",                    // Converted to servings
      "counted_display_full_units": "1",
      "counted_display_partial_units": "40.00",
      "counted_value": "181.76",
      
      // Variance (difference between expected and counted)
      "variance_qty": "-5.50",                    // 5.5 pints missing
      "variance_display_full_units": "0",
      "variance_display_partial_units": "-5.50",
      "variance_value": "-7.81"                   // £7.81 loss
    }
  ],
  
  // Summary
  "total_lines": 254,
  "total_items": 254,
  "total_value": "45678.90",
  "total_variance_value": "-234.56"
}
```

## Calculation Examples by Category

### Example 1: Bottles (Corona - 12 Doz)

**Previous Period (October)**:
- Closing Count: 8 cases + 5 bottles
- Raw Servings: (8 × 12) + 5 = 101 servings

**Current Period (November) - Opening**:
- Opening Display: 8 cases + 5 bottles
- Raw Servings: 101 servings

**Movements**:
- Purchases: +24 bottles (2 cases)
- Sales: -45 bottles
- Waste: -1 bottle

**Expected Closing**:
- Calculation: 101 + 24 - 45 - 1 = 79 servings
- Display: 79 ÷ 12 = 6 cases + 7 bottles

**Counted Closing**:
- Staff Count: 6 cases + 5 bottles
- Raw Servings: (6 × 12) + 5 = 77 servings

**Variance**:
- Difference: 77 - 79 = -2 bottles
- Display: 0 cases + (-2) bottles
- Missing 2 bottles!

### Example 2: Draught (Guinness - 88 Pint Keg)

**Previous Period (October)**:
- Closing Count: 3 kegs + 12.50 pints
- Raw Servings: (3 × 88) + 12.50 = 276.50 pints

**Current Period (November) - Opening**:
- Opening Display: 3 kegs + 12.50 pints
- Raw Servings: 276.50 pints

**Movements**:
- Purchases: +176 pints (2 kegs)
- Sales: -325.75 pints
- Waste: -3.25 pints

**Expected Closing**:
- Calculation: 276.50 + 176 - 325.75 - 3.25 = 123.50 pints
- Display: 123.50 ÷ 88 = 1 keg + 35.50 pints

**Counted Closing**:
- Staff Count: 1 keg + 33.00 pints
- Raw Servings: (1 × 88) + 33.00 = 121.00 pints

**Variance**:
- Difference: 121.00 - 123.50 = -2.50 pints
- Display: 0 kegs + (-2.50) pints
- Missing 2.5 pints

### Example 3: Spirits (Vodka - 28 Shots per 700ml)

**Previous Period (October)**:
- Closing Count: 5 bottles + 0.75 partial
- Raw Servings: (5 × 28) + (0.75 × 28) = 161 shots

**Current Period (November) - Opening**:
- Opening Display: 5 bottles + 0.75 partial
- Raw Servings: 161 shots

**Movements**:
- Purchases: +84 shots (3 bottles)
- Sales: -156 shots
- Waste: -2 shots

**Expected Closing**:
- Calculation: 161 + 84 - 156 - 2 = 87 shots
- Display: 87 ÷ 28 = 3 bottles + 0.11 partial

**Counted Closing**:
- Staff Count: 3 bottles + 0.25 partial
- Raw Servings: (3 × 28) + (0.25 × 28) = 91 shots

**Variance**:
- Difference: 91 - 87 = +4 shots
- Display: 0 bottles + 0.14 partial
- Extra 4 shots found!

## Understanding Snapshots vs Lines

### What are Snapshots?

**Snapshots** are read-only records showing the **opening and closing stock** for all items in the period. They come from the Period model and show:
- Opening stock (from previous period's closing)
- Closing stock (what was counted at period end)
- Stock values at both points

**Use snapshots when you need:**
- Display opening stock values
- Show historical closing stock
- Read-only reference data
- Stock values for reporting

### What are Lines?

**Lines** are editable stocktake records showing:
- Opening quantities (same as snapshot opening)
- All movements during period (purchases, sales, waste, etc.)
- Expected closing (calculated from movements)
- **Counted closing (what staff physically counted)**
- Variance (difference between expected and counted)

**Use lines when you need:**
- Editable counting interface
- Movement tracking (purchases, sales, waste)
- Expected vs counted comparison
- Variance calculations

### When to Use Each

```javascript
// SCENARIO 1: Display opening stock with values
// Use SNAPSHOTS - they have opening_stock_value
stocktakeData.snapshots.forEach(snapshot => {
  console.log(`${snapshot.item.name}:`);
  console.log(`  Opening: ${snapshot.opening_display_full_units} + ${snapshot.opening_display_partial_units}`);
  console.log(`  Opening Value: £${snapshot.opening_stock_value}`);
  console.log(`  Closing: ${snapshot.closing_display_full_units} + ${snapshot.closing_display_partial_units}`);
  console.log(`  Closing Value: £${snapshot.closing_stock_value}`);
});

// SCENARIO 2: Count stock and record variances
// Use LINES - they have counted fields and variance
stocktakeData.lines.forEach(line => {
  console.log(`${line.item_name}:`);
  console.log(`  Expected: ${line.expected_display_full_units} + ${line.expected_display_partial_units}`);
  console.log(`  Counted: ${line.counted_display_full_units} + ${line.counted_display_partial_units}`);
  console.log(`  Variance: ${line.variance_display_full_units} + ${line.variance_display_partial_units}`);
  console.log(`  Variance Value: £${line.variance_value}`);
});

// SCENARIO 3: Opening stock table with values
// Use SNAPSHOTS - they have the values
const OpeningStockTable = ({ snapshots }) => {
  return (
    <table>
      <thead>
        <tr>
          <th>Item</th>
          <th>Opening Stock</th>
          <th>Opening Value</th>
          <th>Closing Stock</th>
          <th>Closing Value</th>
        </tr>
      </thead>
      <tbody>
        {snapshots.map(snapshot => (
          <tr key={snapshot.id}>
            <td>{snapshot.item.name}</td>
            <td>
              {snapshot.opening_display_full_units} + {snapshot.opening_display_partial_units}
            </td>
            <td>£{snapshot.opening_stock_value}</td>
            <td>
              {snapshot.closing_display_full_units} + {snapshot.closing_display_partial_units}
            </td>
            <td>£{snapshot.closing_stock_value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

// SCENARIO 4: Stocktake counting interface
// Use LINES - they have editable counted fields
const StocktakeCountingTable = ({ lines, onUpdate }) => {
  return (
    <table>
      <thead>
        <tr>
          <th>Item</th>
          <th>Expected</th>
          <th>Counted (Input)</th>
          <th>Variance</th>
        </tr>
      </thead>
      <tbody>
        {lines.map(line => (
          <tr key={line.id}>
            <td>{line.item_name}</td>
            <td>
              {line.expected_display_full_units} + {line.expected_display_partial_units}
            </td>
            <td>
              <input 
                type="number" 
                value={line.counted_full_units}
                onChange={(e) => onUpdate(line.id, 'full', e.target.value)}
              />
              <input 
                type="number" 
                value={line.counted_partial_units}
                onChange={(e) => onUpdate(line.id, 'partial', e.target.value)}
              />
            </td>
            <td className={parseFloat(line.variance_value) < 0 ? 'negative' : 'positive'}>
              {line.variance_display_full_units} + {line.variance_display_partial_units}
              <br/>
              £{line.variance_value}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

### Key Differences

| Feature | Snapshots | Lines |
|---------|-----------|-------|
| **Opening Stock** | ✅ Yes (with value) | ✅ Yes (no separate value field) |
| **Opening Value** | ✅ `opening_stock_value` | ❌ Use snapshot for this |
| **Closing Stock** | ✅ Yes (with value) | ❌ Not in lines |
| **Closing Value** | ✅ `closing_stock_value` | ❌ Use snapshot for this |
| **Expected Stock** | ❌ No | ✅ Yes (calculated) |
| **Expected Value** | ❌ No | ✅ `expected_value` |
| **Counted Stock** | ❌ No | ✅ Yes (editable) |
| **Counted Value** | ❌ No | ✅ `counted_value` |
| **Variance** | ❌ No | ✅ Yes (calculated) |
| **Movements** | ❌ No | ✅ purchases, sales, waste, etc. |
| **Editable** | ❌ Read-only | ✅ Can update counted fields |

### Complete Example: Opening Stock Report

```javascript
// Get stocktake data
const response = await fetch('/api/stocktakes/4/');
const stocktakeData = await response.json();

// Generate opening stock report with values
const generateOpeningStockReport = (data) => {
  console.log(`Opening Stock Report - ${data.period_name}`);
  console.log('=' .repeat(80));
  
  // Use SNAPSHOTS for opening stock with values
  let totalOpeningValue = 0;
  
  data.snapshots.forEach(snapshot => {
    const openingStock = `${snapshot.opening_display_full_units} + ${snapshot.opening_display_partial_units}`;
    const openingValue = parseFloat(snapshot.opening_stock_value);
    totalOpeningValue += openingValue;
    
    console.log(`${snapshot.item.name.padEnd(30)} | ${openingStock.padEnd(15)} | £${snapshot.opening_stock_value}`);
  });
  
  console.log('=' .repeat(80));
  console.log(`Total Opening Stock Value: £${totalOpeningValue.toFixed(2)}`);
};

// Generate variance report
const generateVarianceReport = (data) => {
  console.log(`Variance Report - ${data.period_name}`);
  console.log('=' .repeat(80));
  
  // Use LINES for variance analysis
  let totalVarianceValue = 0;
  const significantVariances = [];
  
  data.lines.forEach(line => {
    const varianceValue = parseFloat(line.variance_value);
    totalVarianceValue += varianceValue;
    
    if (Math.abs(varianceValue) > 10.00) {
      significantVariances.push({
        name: line.item_name,
        variance: `${line.variance_display_full_units} + ${line.variance_display_partial_units}`,
        value: varianceValue
      });
    }
  });
  
  console.log('Significant Variances (>£10):');
  significantVariances.forEach(item => {
    console.log(`${item.name.padEnd(30)} | ${item.variance.padEnd(15)} | £${item.value.toFixed(2)}`);
  });
  
  console.log('=' .repeat(80));
  console.log(`Total Variance Value: £${totalVarianceValue.toFixed(2)}`);
};

generateOpeningStockReport(stocktakeData);
generateVarianceReport(stocktakeData);
```

### Quick Reference

**Need opening/closing stock values?** → Use `snapshots`
```javascript
snapshot.opening_stock_value
snapshot.closing_stock_value
```

**Need to count stock?** → Use `lines`
```javascript
line.counted_full_units = "5"
line.counted_partial_units = "7"
```

**Need variance?** → Use `lines`
```javascript
line.variance_value
line.variance_display_full_units
line.variance_display_partial_units
```

**Need movements?** → Use `lines`
```javascript
line.purchases
line.sales
line.waste
```

## Frontend Display Logic

### IMPORTANT: Opening vs Expected Display

**The API provides TWO different values - use the RIGHT one:**

```javascript
// From API line data:
{
  // OPENING STOCK (what you started with from previous period)
  opening_qty: "0.0000",                    // No previous stock
  opening_display_full_units: "0",
  opening_display_partial_units: "0",
  
  // EXPECTED STOCK (opening + movements = what you should have now)
  expected_qty: "348.0000",                 // 29 cases purchased
  expected_display_full_units: "29",
  expected_display_partial_units: "0"
}
```

**Frontend Display Rules:**

| Column | Display | Field to Use | Explanation |
|--------|---------|--------------|-------------|
| **Opening Stock** | Start of period | `opening_display_full_units` + `opening_display_partial_units` | What you had at beginning (from previous closing) |
| **Expected Stock** | End of period | `expected_display_full_units` + `expected_display_partial_units` | What you should have now (opening + purchases - sales) |
| **Counted Stock** | Physical count | `counted_display_full_units` + `counted_display_partial_units` | What you actually counted |

**Your Current Display is CORRECT:**

```
Opening Stock: 0 cases + 0 bottles    ← Correct! No previous period
Expected Stock: 29 cases + 0 bottles  ← Correct! 0 opening + 29 purchased = 29 expected
```

**What's happening in your data:**
- **November is the FIRST period** (no October closing stock)
- Opening Stock = 0 (no previous period)
- Purchases = 29 cases
- Expected Stock = 0 + 29 = 29 cases ✅

**Example with Previous Period:**

```javascript
// Item that HAD stock in October
{
  // October 31 closing: 5 cases + 3 bottles
  opening_display_full_units: "5",      // Started November with 5 cases
  opening_display_partial_units: "3",   // + 3 bottles
  
  // During November: +24 bottles, -45 bottles sold, -1 waste
  purchases: "24.0000",
  sales: "45.0000",
  waste: "1.0000",
  
  // Expected at end of November
  expected_display_full_units: "6",     // Should have 6 cases
  expected_display_partial_units: "5"   // + 5 bottles
}

// Display:
// Opening:  5 cases + 3 bottles (67 total) ← From Oct 31
// Expected: 6 cases + 5 bottles (79 total) ← After movements
```

### Frontend Table Display Example

```jsx
const StocktakeTable = ({ lines }) => {
  return (
    <table>
      <thead>
        <tr>
          <th>Item</th>
          <th>Opening Stock<br/>(Previous Period)</th>
          <th>Expected Stock<br/>(After Movements)</th>
          <th>Counted Stock</th>
          <th>Variance</th>
        </tr>
      </thead>
      <tbody>
        {lines.map(line => {
          const labels = getUnitLabels(line.category_code, line.item_size);
          
          return (
            <tr key={line.id}>
              <td>{line.item_name}</td>
              
              {/* OPENING - what you started with */}
              <td>
                {line.opening_display_full_units} {labels.full} + 
                {line.opening_display_partial_units} {labels.partial}
                <br/>
                <small>{line.opening_qty} servings</small>
              </td>
              
              {/* EXPECTED - what you should have now */}
              <td>
                {line.expected_display_full_units} {labels.full} + 
                {line.expected_display_partial_units} {labels.partial}
                <br/>
                <small>€{line.expected_value}</small>
              </td>
              
              {/* COUNTED - what you physically counted */}
              <td>
                <input 
                  type="number" 
                  value={line.counted_full_units}
                  placeholder={labels.full}
                />
                <input 
                  type="number" 
                  value={line.counted_partial_units}
                  placeholder={labels.partial}
                />
              </td>
              
              {/* VARIANCE - difference */}
              <td className={parseFloat(line.variance_value) < 0 ? 'loss' : 'gain'}>
                {line.variance_display_full_units} {labels.full} + 
                {line.variance_display_partial_units} {labels.partial}
                <br/>
                <small>€{line.variance_value}</small>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};
```

### Why Opening is 0 for November

Your November stocktake shows **Opening = 0** because:

1. **October period doesn't exist** (or wasn't closed with counted stock)
2. **November is the first period** in the system
3. This is **normal and correct** for the first period

**What happens next:**
```
November (First Period):
  Opening: 0 cases + 0 bottles (no previous period)
  Purchases: 29 cases
  Expected: 29 cases
  Counted: 29 cases (you count this)
  ↓
December (Second Period):
  Opening: 29 cases (from November counted stock)
  Purchases: +X
  Sales: -Y
  Expected: 29 + X - Y
```

### Bottles Display
```javascript
// API returns:
{
  opening_display_full_units: "8",    // cases
  opening_display_partial_units: "5"   // bottles
}

// Display as:
"8 cases + 5 bottles"
"Total: 101 bottles" // Optional: (8 × 12) + 5
```

### Draught Display
```javascript
// API returns:
{
  opening_display_full_units: "3",      // kegs
  opening_display_partial_units: "12.50" // pints
}

// Display as:
"3 kegs + 12.50 pints"
```

### Spirits Display
```javascript
// API returns:
{
  opening_display_full_units: "5",    // bottles
  opening_display_partial_units: "0.75" // fractional
}

// Display as:
"5 bottles + 0.75"
"5¾ bottles" // Optional: fraction display
```

## Database Structure

### How Opening Stock is Determined

```python
# StockSnapshotNestedSerializer - get_opening_full_units()
def get_opening_full_units(self, obj):
    """
    Get opening stock from previous period's closing stock.
    This is what was counted at END of previous period.
    """
    prev_snapshot = StockSnapshot.objects.filter(
        hotel=obj.hotel,
        item=obj.item,
        period__end_date__lt=obj.period.start_date
    ).order_by('-period__end_date').first()
    
    if prev_snapshot:
        return str(prev_snapshot.closing_full_units)
    return "0.00"
```

### Display Calculation Logic

```python
# StocktakeLineSerializer - _calculate_display_units()
def _calculate_display_units(self, servings, item):
    """
    Calculate display full and partial units from servings.
    Returns (full_units, partial_units) as strings.
    """
    from decimal import Decimal, ROUND_HALF_UP
    
    if servings is None or servings == 0:
        return "0", "0"
    
    servings_decimal = Decimal(str(servings))
    uom = Decimal(str(item.uom))
    
    # Full units (kegs/cases/bottles)
    full = int(servings_decimal / uom)
    
    # Partial units (pints/bottles/fractional)
    partial = servings_decimal % uom
    
    # Category-specific rounding
    category = item.category.code
    
    if category == 'B' or (category == 'M' and 'Doz' in item.size):
        # Bottles - whole numbers only
        partial_display = str(int(round(float(partial))))
    elif category == 'D':
        # Draught - pints with 2 decimals
        partial_rounded = partial.quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        partial_display = str(partial_rounded)
    else:
        # Spirits/Wine/Others - 2 decimals
        partial_rounded = partial.quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        partial_display = str(partial_rounded)
    
    return str(full), partial_display
```

## Common Use Cases

### 1. Starting a New Stocktake

When a new stocktake is created, opening quantities are automatically populated from the previous period's closing stock.

**API Call**: `POST /api/stocktakes/`
```json
{
  "period_start": "2025-11-01",
  "period_end": "2025-11-30"
}
```

**System Action**:
1. Find previous period (ending before 2025-11-01)
2. Copy closing stock as opening stock
3. Create stocktake lines with opening quantities populated

### 2. Counting Stock

Staff physically count stock and enter full + partial units.

**API Call**: `PATCH /api/stocktake-lines/{id}/`
```json
{
  "counted_full_units": "6",
  "counted_partial_units": "5"
}
```

**System Action**:
1. Convert to servings: (6 × 12) + 5 = 77
2. Calculate variance: 77 - 79 = -2
3. Update variance displays automatically

### 3. Reviewing Variances

Frontend displays items with significant variances:

```javascript
// Filter high-value variances
const significantVariances = stocktakeLine.lines.filter(line => {
  return Math.abs(parseFloat(line.variance_value)) > 10.00;
});

// Display by category
significantVariances.forEach(line => {
  if (line.category_code === 'B') {
    console.log(`${line.item_name}: ${line.variance_display_partial_units} bottles missing`);
  } else if (line.category_code === 'D') {
    console.log(`${line.item_name}: ${line.variance_display_partial_units} pints missing`);
  } else {
    console.log(`${line.item_name}: ${line.variance_display_partial_units} servings variance`);
  }
});
```

### 4. Closing a Stocktake

When stocktake is approved, it updates the Period's closing stock.

**API Call**: `POST /api/stocktakes/{id}/approve/`

**System Action**:
1. Lock stocktake (status = 'approved')
2. Update Period snapshots with counted values
3. Mark Period as closed
4. Counted stock becomes opening stock for next period

## Validation Rules

### Display Range Validation

**Bottles (Doz)**:
- Full units: 0 to ∞
- Partial units: 0 to 11 (whole numbers)
- ❌ Invalid: 12 bottles (should be 1 case + 0 bottles)

**Draught**:
- Full units: 0 to ∞
- Partial units: 0.00 to (UOM - 0.01)
- ❌ Invalid: 88 pints for 88-pint keg (should be 1 keg + 0.00 pints)

**Spirits/Wine**:
- Full units: 0 to ∞
- Partial units: 0.00 to 0.99
- ❌ Invalid: 1.00 partial (should be 1 bottle + 0.00 partial)

## Troubleshooting

### Issue: Opening stock shows 0.00

**Cause**: No previous period exists or previous period has no closing stock.

**Solution**: 
1. Check if previous period exists
2. Verify previous period was closed with counted stock
3. For first-ever stocktake, manually enter opening stock

### Issue: Display numbers don't match raw servings

**Cause**: Frontend trying to calculate display values instead of using API values.

**Solution**: Always use `*_display_full_units` and `*_display_partial_units` fields directly from API.

### Issue: Variance seems incorrect

**Cause**: Movements (purchases, sales, waste) not recorded correctly.

**Solution**:
1. Verify all purchases were entered
2. Check sales match POS records
3. Ensure waste is recorded
4. Review transfers in/out

## Best Practices

1. **Always use display fields**: Don't recalculate - use API's `*_display_*` fields
2. **Validate partial units**: Ensure they're within valid range for category
3. **Show variance prominently**: Highlight items with significant variances
4. **Category-specific UI**: Show "cases + bottles" for B, "kegs + pints" for D, etc.
5. **Summary totals**: Display total variance value to show overall stock accuracy
6. **Previous vs Current**: Show side-by-side comparison of opening and closing stock

## Summary

- **Opening Stock** = Previous period's closing stock (what was counted last time)
- **Display Fields** = Pre-calculated by API, category-specific formatting
- **Bottles**: Cases + Bottles (whole numbers)
- **Draught**: Kegs + Pints (2 decimals)
- **Spirits/Wine**: Bottles + Fractional (2 decimals)
- **Frontend**: Use `*_display_*` fields directly - no calculations needed
- **Stocktake** = Editable Period with complete snapshot data + counting interface

