# Sales Data Architecture Decision

## Executive Summary

**Decision:** Keep sales data **separate** from variance calculations using the existing architecture.

**Status:** ✅ Approved - Ready for frontend implementation

---

## Architecture Overview

### Three-Tier Data Model

```
┌─────────────────────────────────────────────────────────────┐
│                     STOCKTAKE SYSTEM                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├──── Physical Stock Counting
                              │     (Variance Analysis)
                              │
                              └──── Sales Data Entry
                                    (Profitability Analysis)
```

### 1. Physical Stock (Stocktake & StocktakeLine)
**Purpose:** Track physical inventory movements

**Data Fields:**
- `opening_qty` - Opening stock in servings
- `purchases` - Purchases during period
- `waste` - Waste/breakage during period
- `counted_full_units` - Physical count (kegs, cases, bottles)
- `counted_partial_units` - Physical count (pints, loose bottles, fractional)

**Calculation:**
```python
expected_qty = opening_qty + purchases - waste
variance_qty = counted_qty - expected_qty
```

**Key Point:** ✅ **Sales NOT included** in variance calculation

---

### 2. Sales Data (Sale Model)
**Purpose:** Track sales revenue and cost of goods sold

**Data Fields:**
- `quantity` - Quantity sold (servings: pints, bottles, shots)
- `unit_cost` - Cost per serving
- `unit_price` - Selling price per serving
- `total_cost` - Auto-calculated (quantity × unit_cost)
- `total_revenue` - Auto-calculated (quantity × unit_price)
- `sale_date` - Date of sale

**Calculation:**
```python
gross_profit = total_revenue - total_cost
gp_percentage = (gross_profit / total_revenue) × 100
pour_cost_percentage = (total_cost / total_revenue) × 100
```

---

### 3. Manual Overrides (StocktakeLine & StockPeriod)
**Purpose:** Quick entry when itemized data is unavailable

**Line-Level Manual:**
- `manual_sales_value` - Total sales revenue (€)
- `manual_purchases_value` - Total purchase costs (€)
- `manual_waste_value` - Total waste value (€)

**Period-Level Manual:**
- `manual_sales_amount` - Total sales for entire period (€)
- `manual_purchases_amount` - Total COGS for entire period (€)

---

## Why Sales Are NOT in Variance Calculation

### Conceptual Separation

**Variance measures physical loss/gain:**
- ✅ Theft
- ✅ Spillage
- ✅ Measurement errors
- ✅ Breakage
- ✅ Over-pouring
- ✅ Unrecorded waste

**Sales measure business performance:**
- ✅ Revenue
- ✅ Cost of goods sold
- ✅ Gross profit %
- ✅ Pour cost %
- ✅ Best sellers
- ✅ Price optimization

### Mathematical Model

#### Traditional Approach (Including Sales)
```python
expected_closing = opening + purchases - sales - waste
variance = counted - expected_closing

# Problem: Variance now reflects BOTH:
# 1. Sales accuracy (POS vs actual)
# 2. Physical losses (theft, spillage)
# → Can't separate the two!
```

#### Our Approach (Excluding Sales)
```python
expected_closing = opening + purchases - waste
variance = counted - expected_closing

# Benefit: Variance shows ONLY physical losses
# Sales tracked separately for profitability

# Total Picture:
# Physical variance: -5 pints (€11.25 loss)  ← Theft/spillage
# Sales revenue: €2,450 (350 pints sold)     ← Business performance
```

### Real-World Example

**Guinness Draught - November 2024:**

```
Opening Stock:    2 kegs + 15 pints     (191 pints)
Purchases:        3 kegs                 (264 pints)
Waste:            0.5 kegs               (44 pints)
─────────────────────────────────────────────────────
Expected Stock:   4 kegs + 15 pints     (367 pints)
Counted Stock:    4 kegs + 10 pints     (362 pints)
─────────────────────────────────────────────────────
Physical Variance: -5 pints              (€11.25 loss)

Sales (Separate):  350 pints @ €7.00 = €2,450 revenue
                   Cost: €77.49
                   GP%: 96.8%
```

**Analysis:**
- ✅ Physical loss of 5 pints (theft/spillage)
- ✅ Good sales volume (350 pints)
- ✅ Excellent profitability (96.8% GP)

If we included sales in variance:
```
expected_closing = 191 + 264 - 350 - 44 = 61 pints
counted = 362 pints
variance = +301 pints (???)
```
❌ Meaningless number that combines everything!

---

## Data Entry Points

### Price Entry Locations

#### 1. StockItem.menu_price (Primary)
**Location:** Stock item master data
**Purpose:** Current selling price
**Updated:** When prices change
**Used for:**
- Pre-filling sale entry forms
- Profitability calculations
- Price comparison analysis

**Frontend:**
```jsx
<StockItemForm>
  <label>Menu Price (per serving)</label>
  <input type="number" name="menu_price" value="7.00" />
</StockItemForm>
```

---

#### 2. Sale.unit_price (Transaction)
**Location:** Individual sale records
**Purpose:** Price at time of sale
**Updated:** Per sale transaction
**Used for:**
- Exact revenue calculation
- Price history
- Promotional pricing tracking

**Frontend:**
```jsx
<SalesEntryModal>
  <label>Unit Price</label>
  <input 
    type="number" 
    name="unit_price" 
    defaultValue={item.menu_price}  // Pre-filled
  />
</SalesEntryModal>
```

---

#### 3. Manual Overrides (Alternative)
**Location:** StocktakeLine or StockPeriod
**Purpose:** Quick totals without itemization
**Updated:** Once per period
**Used for:**
- Historical data migration
- Simple stocktake workflows
- When POS data is unavailable

**Frontend:**
```jsx
<ManualEntryForm>
  <label>Total Sales Revenue</label>
  <input type="number" name="manual_sales_amount" />
  
  <label>Total Purchase Costs (COGS)</label>
  <input type="number" name="manual_purchases_amount" />
</ManualEntryForm>
```

---

## Data Priority System

When calculating stocktake profitability, the backend uses a **3-tier fallback**:

### Revenue Calculation Priority:
```python
# 1. Line-level manual (highest priority)
if stocktake_line.manual_sales_value:
    revenue = sum(line.manual_sales_value for line in lines)

# 2. Period-level manual
elif stock_period.manual_sales_amount:
    revenue = stock_period.manual_sales_amount

# 3. Itemized sales (default)
else:
    revenue = sum(sale.total_revenue for sale in sales)
```

### COGS Calculation Priority:
```python
# 1. Period-level manual (highest priority)
if stock_period.manual_purchases_amount:
    cogs = stock_period.manual_purchases_amount

# 2. Line-level manual
elif any(line.manual_purchases_value or line.manual_waste_value):
    cogs = sum(line.manual_purchases_value + line.manual_waste_value)

# 3. Itemized sales (default)
else:
    cogs = sum(sale.total_cost for sale in sales)
```

**Benefits:**
- ✅ Flexibility for different workflows
- ✅ Historical data support
- ✅ Gradual migration path
- ✅ No data loss

---

## Frontend Implementation Plan

### Phase 1: Sales Entry (Recommended)
Add "Enter Sales" button to each stocktake line:
1. ✅ Button opens modal
2. ✅ Form pre-fills from `item.menu_price` and `item.cost_per_serving`
3. ✅ Staff enters quantity sold
4. ✅ System calculates totals (revenue, cost, GP%)
5. ✅ Save creates `Sale` record
6. ✅ Display shows current sales total

**User Experience:**
```
┌─────────────────────────────────────────────┐
│ Guinness Draught (50L Keg)                  │
│                                             │
│ Opening:  2 kegs + 15 pints                 │
│ Purchases: 3 kegs                           │
│ Waste:    0.5 kegs                          │
│ Expected:  4 kegs + 15 pints               │
│ Counted:   4 kegs + 10 pints [Edit]        │
│ Variance: -5 pints (€11.25 loss) ← THEFT   │
│                                             │
│ [📊 Enter Sales] ← NEW BUTTON              │
│ Sales: 350 pints (€2,450) ← REVENUE        │
└─────────────────────────────────────────────┘
```

### Phase 2: Manual Entry (Optional)
For simpler workflows, add period-level manual entry:
1. ✅ Form accepts total sales amount
2. ✅ Form accepts total COGS amount
3. ✅ System calculates GP%
4. ✅ Skips itemized sales tracking

---

## Benefits Summary

### ✅ Separation of Concerns
- Physical counting separate from sales tracking
- Clear variance analysis (physical loss only)
- Independent profitability metrics

### ✅ Flexibility
- Supports itemized sales OR manual totals
- Gradual adoption (can mix both)
- Historical data migration friendly

### ✅ Better Analytics
- Track sales patterns by item
- Identify best sellers
- Analyze price sensitivity
- Monitor pour cost by product

### ✅ Operational Clarity
- Staff understand what variance means
- Theft/waste clearly visible
- Sales performance clearly visible
- No confusion between the two

### ✅ Industry Standard
- Matches hospitality best practices
- Compatible with POS systems
- Follows FIFO/LIFO accounting
- Audit-friendly

---

## Migration Path

### For Existing Data
1. ✅ Keep all existing variance calculations unchanged
2. ✅ Add sales data entry to new stocktakes
3. ✅ Use manual overrides for historical periods
4. ✅ Gradually adopt itemized sales tracking

### For New Deployments
1. ✅ Start with itemized sales entry
2. ✅ Train staff on sales vs variance concept
3. ✅ Use manual overrides as fallback
4. ✅ Monitor data quality

---

## Technical Implementation Status

### ✅ Backend (Complete)
- [x] Sale model with all fields
- [x] SaleViewSet with CRUD operations
- [x] Sales summary endpoint
- [x] Bulk create endpoint
- [x] Line-item sales endpoint
- [x] Manual override fields
- [x] Priority calculation system
- [x] Serializers with profitability metrics

### 🔲 Frontend (Ready to Build)
- [ ] Sales entry button on stocktake lines
- [ ] Sales entry modal component
- [ ] Sales list display
- [ ] Sales summary dashboard
- [ ] Manual entry form (optional)
- [ ] Real-time updates
- [ ] Data validation

---

## Documentation

### Available Guides
1. ✅ **SALES_API_QUICK_REFERENCE.md** - API endpoints reference
2. ✅ **FRONTEND_SALES_ENTRY_GUIDE.md** - Frontend integration guide
3. ✅ **SALES_ARCHITECTURE_DECISION.md** - This document

### Code Examples
- [x] React components (modal, form, summary)
- [x] API fetch examples
- [x] Data validation patterns
- [x] Error handling

---

## Conclusion

**The current architecture is optimal:**
- ✅ Sales data is separated from variance calculations
- ✅ Backend is fully prepared and tested
- ✅ Multiple entry methods supported (itemized + manual)
- ✅ Priority system handles all scenarios
- ✅ Ready for frontend implementation

**Next Step:** Build frontend UI components using the provided guides and examples.

**No backend changes needed** - everything is ready! 🎉
