# 🔍 STOCKTAKE CALCULATION ANALYSIS
**Date: November 10, 2025**  
**Analysis of Recent Migrations & Current Logic**

---

## 📅 RECENT MIGRATION TIMELINE (Nov 9-10, 2025)

### **November 9, 2025 - Sales Model Refactoring**
```
0005: Removed 'sales' field from StocktakeLine ❌
0006: Created NEW 'Sale' model ✅
0007: Added 'manual_sales_amount' to StockPeriod
0008: Added 'manual_sales_value' + 'manual_waste_value' to StocktakeLine
0009: Added 'manual_purchases_amount' to StockPeriod
```

### **November 10, 2025 - Cocktail Revenue Tracking**
```
0014: Added 'price' field to CocktailRecipe ✅
0015: ATTEMPTED to link CocktailConsumption → StockPeriod ⚠️
0016: REMOVED the link (kept cocktails separate) ✅
```

---

## 🏗️ CURRENT ARCHITECTURE

### **1. Stocktake Model**
Represents a stocktaking period for inventory verification.

```python
class Stocktake:
    hotel: ForeignKey
    period_start: DateField
    period_end: DateField
    status: CharField  # DRAFT or APPROVED
    
    # Related models:
    # - lines (StocktakeLine) - individual item counts
    # - sales (Sale) - sales records for stock items ONLY
```

### **2. Sale Model (NEW - Created Nov 9)**
**Purpose:** Track sales of STOCK ITEMS only.

```python
class Sale:
    stocktake: ForeignKey          # Links to Stocktake
    item: ForeignKey(StockItem)    # Stock item (NOT cocktails)
    quantity: Decimal              # Servings sold
    unit_cost: Decimal
    unit_price: Decimal
    total_cost: Decimal            # Auto-calculated
    total_revenue: Decimal         # Auto-calculated
    sale_date: DateField
```

**Key Points:**
- ✅ Links to `StockItem` (beer, spirits, wine, etc.)
- ❌ NO link to `CocktailRecipe`
- ✅ Links to `Stocktake` (belongs to a stocktake period)

### **3. CocktailConsumption Model**
**Purpose:** Track cocktail production independently.

```python
class CocktailConsumption:
    cocktail: ForeignKey(CocktailRecipe)
    quantity_made: PositiveIntegerField
    timestamp: DateTimeField
    hotel: ForeignKey
    
    # Revenue fields (added Nov 10):
    unit_price: Decimal
    total_revenue: Decimal
    total_cost: Decimal
    
    # NO stocktake field (removed in migration 0016)
```

**Key Points:**
- ❌ NO link to `Stocktake`
- ❌ NO link to `StockPeriod`
- ✅ Completely independent tracking
- ✅ Revenue calculated on save

---

## 💰 HOW STOCKTAKE REVENUE IS CALCULATED

### **Stocktake.total_revenue Property**

```python
@property
def total_revenue(self):
    """
    Calculate total sales revenue.
    Priority:
    1. Sum of manual_sales_value from lines
    2. StockPeriod.manual_sales_amount
    3. Sum of total_revenue from Sale records
    """
    
    # PRIORITY 1: Check StocktakeLine manual overrides
    manual_sales = self.lines.aggregate(
        total=Sum('manual_sales_value')
    )['total']
    
    if manual_sales and manual_sales > 0:
        return manual_sales  # ✅ Return manual entry
    
    # PRIORITY 2: Check StockPeriod manual override
    period = StockPeriod.objects.get(
        hotel=self.hotel,
        start_date=self.period_start,
        end_date=self.period_end
    )
    
    if period and period.manual_sales_amount is not None:
        return period.manual_sales_amount  # ✅ Return period override
    
    # PRIORITY 3: Calculate from Sale records
    total = self.sales.aggregate(total=Sum('total_revenue'))['total']
    return total or 0  # ✅ Return calculated sales
```

### **🔒 CRITICAL: COCKTAILS ARE NOT INCLUDED**

The `total_revenue` property:
- ❌ Does NOT query `CocktailConsumption`
- ❌ Does NOT include cocktail sales
- ✅ ONLY includes stock item sales from `Sale` model

---

## 💸 HOW STOCKTAKE COGS IS CALCULATED

### **Stocktake.total_cogs Property**

```python
@cached_property
def total_cogs(self):
    """
    Calculate total cost of goods sold.
    Priority:
    1. StockPeriod.manual_purchases_amount (single total)
    2. Sum of manual_purchases_value + manual_waste_value from lines
    3. Sum of total_cost from Sale records
    """
    
    # PRIORITY 1: Check StockPeriod manual purchases
    period = StockPeriod.objects.get(...)
    
    if period and period.manual_purchases_amount is not None:
        return period.manual_purchases_amount  # ✅ Manual override
    
    # PRIORITY 2: Check StocktakeLine manual values
    manual_totals = self.lines.aggregate(
        purchases=Sum('manual_purchases_value'),
        waste=Sum('manual_waste_value')
    )
    
    manual_total = manual_purchases + manual_waste
    if manual_total > 0:
        return manual_total  # ✅ Line-level manual values
    
    # PRIORITY 3: Calculate from Sale records
    total = self.sales.aggregate(total=Sum('total_cost'))['total']
    return total or 0  # ✅ Calculated COGS
```

### **🔒 CRITICAL: COCKTAILS ARE NOT INCLUDED**

The `total_cogs` property:
- ❌ Does NOT query `CocktailConsumption`
- ❌ Does NOT include cocktail costs
- ✅ ONLY includes stock item costs from `Sale` model

---

## 📊 WHERE COCKTAILS APPEAR

### **StockPeriod Properties (Analysis Only)**

```python
class StockPeriod:
    
    @property
    def cocktail_revenue(self):
        """READS cocktail data for date range"""
        return CocktailConsumption.objects.filter(
            hotel=self.hotel,
            timestamp__gte=self.start_date,
            timestamp__lte=self.end_date
        ).aggregate(total=Sum('total_revenue'))['total'] or 0
    
    @property
    def total_sales_with_cocktails(self):
        """⚠️ ANALYSIS ONLY - combines for display"""
        stock_sales = sum(
            stocktake.total_revenue 
            for stocktake in self.stocktakes.all()
        )
        return stock_sales + self.cocktail_revenue
```

**Key Points:**
- ✅ These are READ-ONLY properties
- ✅ They DO NOT modify stocktake calculations
- ✅ Used for reporting/analytics only
- ⚠️ Names are misleading (should be prefixed with `analysis_`)

---

## 📈 DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│                    STOCK ITEM SALES                         │
│                                                             │
│  StockItem → Sale → Stocktake.sales                        │
│                          ↓                                  │
│                   Stocktake.total_revenue ✅               │
│                   Stocktake.total_cogs ✅                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   COCKTAIL SALES                            │
│                    (SEPARATE)                               │
│  CocktailRecipe → CocktailConsumption                       │
│                          ↓                                  │
│                   (No link to Stocktake)                    │
│                          ↓                                  │
│         StockPeriod.cocktail_revenue ✅ (read-only)        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 COMBINED REPORTING                          │
│                (Analysis Layer Only)                        │
│                                                             │
│  StockPeriod.total_sales_with_cocktails                    │
│      = Stocktake sales + Cocktail revenue                  │
│                                                             │
│  ⚠️ This is DISPLAY ONLY - does not affect stocktakes     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 ISOLATION VERIFICATION

### ✅ **What's Isolated:**
1. `Stocktake.total_revenue` - Only `Sale` records (stock items)
2. `Stocktake.total_cogs` - Only `Sale` records (stock items)
3. `StocktakeLine` calculations - Never touch cocktails
4. `Sale` model - Only links to `StockItem`, not `CocktailRecipe`

### ⚠️ **What Could Be Confusing:**
1. `StockPeriod.total_sales_with_cocktails` - Misleading name
2. `StockPeriod.total_cost_with_cocktails` - Misleading name
3. `StockPeriod.profit_with_cocktails` - Misleading name

**These properties combine data for reporting but DO NOT affect stocktake logic.**

---

## 🎯 CALCULATION PRIORITIES

### **Revenue Calculation Priority:**
1. **Manual Entry (Line Level)** - `StocktakeLine.manual_sales_value`
2. **Manual Entry (Period Level)** - `StockPeriod.manual_sales_amount`
3. **Calculated from Sales** - `Sum(Sale.total_revenue)`

### **COGS Calculation Priority:**
1. **Manual Entry (Period Level)** - `StockPeriod.manual_purchases_amount`
2. **Manual Entry (Line Level)** - `StocktakeLine.manual_purchases_value + manual_waste_value`
3. **Calculated from Sales** - `Sum(Sale.total_cost)`

**🔒 Cocktails are NEVER part of any priority level.**

---

## ✅ CONCLUSION

### **Current System is SAFE:**
- ✅ Stocktakes calculate revenue from `Sale` model only
- ✅ Stocktakes calculate COGS from `Sale` model only
- ✅ `Sale` model only links to `StockItem` (not cocktails)
- ✅ `CocktailConsumption` has NO link to `Stocktake`
- ✅ Cocktails are tracked independently

### **Areas for Improvement:**
- ⚠️ Rename `StockPeriod.total_sales_with_cocktails` → `analysis_total_sales_combined`
- ⚠️ Add clear docstrings marking analysis-only properties
- ⚠️ Create separate API layer for combining sales data

### **What We're Building:**
- 🆕 Sales Analysis API (separate endpoint)
- 🆕 Ability to view combined sales (display only)
- 🆕 Category breakdown with cocktails as separate category
- 🔒 All analysis happens at API layer, NOT model layer

---

## 📝 MIGRATION HISTORY SUMMARY

| Date | Migration | Action | Purpose |
|------|-----------|--------|---------|
| Nov 9 | 0005 | Removed `sales` field from `StocktakeLine` | Clean up old structure |
| Nov 9 | 0006 | Created `Sale` model | Track stock item sales separately |
| Nov 9 | 0007 | Added `manual_sales_amount` to `StockPeriod` | Allow manual total entry |
| Nov 9 | 0008 | Added manual fields to `StocktakeLine` | Allow line-level manual entry |
| Nov 9 | 0009 | Added `manual_purchases_amount` to `StockPeriod` | Manual COGS entry |
| Nov 10 | 0014 | Added `price` to `CocktailRecipe` | Enable cocktail pricing |
| Nov 10 | 0015 | Added `stocktake` link to `CocktailConsumption` | ❌ Attempted integration |
| Nov 10 | 0016 | **REMOVED** `stocktake` link | ✅ Kept cocktails separate |

**Final State:** Cocktails and stocktakes are completely decoupled. ✅

