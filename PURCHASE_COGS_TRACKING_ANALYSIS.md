# 📊 Purchase & COGS Tracking Analysis

## Current System Investigation

### **What We Have:**

## 1. **Sale Model** (Primary COGS Tracking) ✅

**Location:** `stock_tracker/models.py` - `Sale` model

**Purpose:** Track individual sales transactions with both cost and revenue

**Fields:**
```python
Sale:
  - stocktake (FK) → Links to period
  - item (FK) → The item sold
  - quantity → Servings sold
  - unit_cost → Cost per serving (COGS)
  - unit_price → Selling price per serving
  - total_cost → Auto-calculated (quantity × unit_cost)
  - total_revenue → Auto-calculated (quantity × unit_price)
  - sale_date → When sold
```

**How It Works:**
- Create one `Sale` record for each item sold in a period
- `total_cost` is **automatically calculated** on save
- All Sale records are summed to get `Stocktake.total_cogs`

**Current Status:** ✅ **ALREADY IN USE**
- October 2025 has 19 Sale records
- Total COGS: €18,999.99 (~€19,000)

---

## 2. **StockPeriod.manual_sales_amount** (Revenue Total) ✅

**Location:** `stock_tracker/models.py` - `StockPeriod` model

**Purpose:** Store total sales revenue when you don't have itemized data

**Field:**
```python
StockPeriod:
  - manual_sales_amount → Total revenue for period (€)
```

**How It Works:**
- Set once per period
- Used by `Stocktake.total_revenue` if available
- Falls back to sum of `Sale.total_revenue` if not set

**Current Status:** ✅ **ALREADY SET**
- October 2025: €62,000

---

## 3. **StocktakeLine.manual_purchases_value** (Line-Level Override) ⚠️

**Location:** `stock_tracker/models.py` - `StocktakeLine` model

**Purpose:** Manual override for purchase value **per item**

**Field:**
```python
StocktakeLine:
  - manual_purchases_value → Manual purchase cost for this item (€)
```

**Current Status:** ⚠️ **EXISTS BUT NOT USED**
- Field is available but not connected to GP% calculations
- Not displayed in serializers
- Not used in any calculations

---

## 4. **StocktakeLine.purchases** (Quantity Tracking) ✅

**Location:** `stock_tracker/models.py` - `StocktakeLine` model

**Purpose:** Track purchase **quantities** (servings)

**Field:**
```python
StocktakeLine:
  - purchases → Quantity purchased in servings
```

**How It Works:**
- Auto-calculated from `StockMovement` records (type='PURCHASE')
- Used in variance calculation: `expected = opening + purchases - waste`
- Tracks **quantity**, not cost

**Current Status:** ✅ **WORKING**
- Automatically updates when movements are added

---

## 5. **Stocktake Properties** (Auto-Calculated) ✅

**Location:** `stock_tracker/models.py` - `Stocktake` model

**Properties:**
```python
@property
def total_cogs(self):
    # Sum of Sale.total_cost
    return sum(sale.total_cost for sale in self.sales.all())

@property
def total_revenue(self):
    # From StockPeriod.manual_sales_amount OR sum of Sale.total_revenue
    if period.manual_sales_amount:
        return period.manual_sales_amount
    return sum(sale.total_revenue for sale in self.sales.all())

@property
def gross_profit_percentage(self):
    return ((revenue - cogs) / revenue) * 100

@property
def pour_cost_percentage(self):
    return (cogs / revenue) * 100
```

**Current Status:** ✅ **WORKING PERFECTLY**
- October 2025: GP% = 69.35%, Pour Cost% = 30.65%

---

## 📋 CURRENT WORKFLOW (What's Working)

### **For October 2025:**

1. ✅ **COGS Tracking:** 19 `Sale` records created → Total: €19,000
2. ✅ **Revenue Tracking:** `StockPeriod.manual_sales_amount` = €62,000
3. ✅ **GP% Calculation:** Auto-calculated = 69.35%
4. ✅ **API Access:** `GET /stocktakes/5/` returns all metrics

---

## 🔍 RECOMMENDATIONS

### **Option A: Keep Current System** ⭐ **RECOMMENDED**

**Reason:** It's already working perfectly!

**Use Case:** When you have:
- Total purchase costs (€19,000)
- Total sales revenue (€62,000)
- Don't need item-level detail

**Implementation:**
```python
# 1. Create Sale records with COGS
for item in consumed_items:
    Sale.objects.create(
        stocktake=stocktake,
        item=item,
        quantity=consumed_qty,
        unit_cost=cost_per_serving,  # This is COGS
        unit_price=menu_price,
        sale_date=period_start
    )

# 2. Set manual sales total
period.manual_sales_amount = Decimal('62000.00')
period.save()

# 3. GP% auto-calculated!
print(stocktake.gross_profit_percentage)  # 69.35%
```

**Pros:**
- ✅ Already implemented and tested
- ✅ Flexible (itemized or total)
- ✅ Auto-calculates GP% and Pour Cost%
- ✅ Works with your €19K / €62K numbers

**Cons:**
- None - it's working!

---

### **Option B: Use manual_purchases_value** (NOT Recommended)

**Reason:** Field exists but is disconnected from calculations

**What Would Be Needed:**
1. Connect `manual_purchases_value` to `Stocktake.total_cogs`
2. Update serializers to expose it
3. Add API endpoints to set it
4. Document new workflow

**Implementation Effort:** Medium (2-3 hours)

**Pros:**
- Per-item purchase cost tracking

**Cons:**
- ❌ Requires code changes
- ❌ Duplicates functionality of Sale model
- ❌ Less flexible than Sale model
- ❌ Not currently used anywhere

---

### **Option C: Hybrid Approach** (Advanced)

**Use Case:** When you need both:
- Itemized sales tracking (Sale model)
- Quick period totals (manual fields)

**Implementation:**
```python
# For itemized tracking
Sale.objects.create(...)  # Track each sale

# For quick override
period.manual_sales_amount = Decimal('62000.00')

# Stocktake uses whichever is available
# Priority: manual_sales_amount > sum(Sale.total_revenue)
```

**Current Status:** ✅ **ALREADY AVAILABLE**
- This is how it currently works!

---

## 🎯 FINAL RECOMMENDATION

### **ACTION: Continue Using Current System**

**Rationale:**
1. ✅ **It's working** - October 2025 shows correct GP% (69.35%)
2. ✅ **Meets requirements** - Tracks €19K COGS and €62K revenue
3. ✅ **Flexible** - Can do itemized OR totals
4. ✅ **No changes needed** - Everything is already in place

### **Workflow to Follow:**

**For Each Period:**

1. **Track COGS** (Choose one):
   - **Method A:** Create `Sale` records (itemized)
   - **Method B:** Just use total (set manual_sales_amount)

2. **Track Revenue:**
   - Set `StockPeriod.manual_sales_amount` = total sales

3. **View Results:**
   - `GET /stocktakes/{id}/` returns GP% and Pour Cost%

### **API Endpoints to Use:**

```bash
# Create Sale records (COGS tracking)
POST /api/stock_tracker/hotel-killarney/sales/
{
  "stocktake": 5,
  "item": 45,
  "quantity": "100.00",
  "unit_cost": "2.50",      # COGS per serving
  "unit_price": "5.00",     # Revenue per serving
  "sale_date": "2025-10-15"
}

# Set manual sales total (Revenue tracking)
PATCH /api/stock_tracker/hotel-killarney/periods/7/
{
  "manual_sales_amount": "62000.00"
}

# View calculated GP%
GET /api/stock_tracker/hotel-killarney/stocktakes/5/
# Returns: total_cogs, total_revenue, gross_profit_percentage, pour_cost_percentage
```

---

## 📊 SUMMARY

| Feature | Current Status | Recommendation |
|---------|---------------|----------------|
| **COGS Tracking** | ✅ Sale model working | Keep using Sale model |
| **Revenue Tracking** | ✅ manual_sales_amount working | Keep current approach |
| **GP% Calculation** | ✅ Auto-calculated | No changes needed |
| **API Endpoints** | ✅ All available | Use existing endpoints |
| **manual_purchases_value** | ⚠️ Exists but unused | No need to implement |

---

## ✅ CONCLUSION

**Your system is already optimal!** The combination of:
- `Sale` model for COGS
- `StockPeriod.manual_sales_amount` for revenue
- Auto-calculated GP% properties

...provides exactly what you need with no additional work required.

**October 2025 proves it works:**
- COGS: €19,000 ✅
- Revenue: €62,000 ✅
- GP%: 69.35% ✅
- Pour Cost%: 30.65% ✅

**No further action needed!** 🎉
