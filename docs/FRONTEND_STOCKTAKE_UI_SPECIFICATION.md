# Frontend Stock Tracker - Complete UI/UX Specification

## 🚀 Quick Start: Getting October 2025 Closed Stocktake

**We just created October 2025 stocktake in the database:**
- Period ID: `2`
- Status: `Closed`
- Month: `10` (October)
- Year: `2025`
- Date Range: `2025-10-01` to `2025-10-31`
- Total Items: `244`
- Total Value: `€26,945.86`

### How to Fetch It:

```javascript
// Step 1: Get all periods to find October 2025
const response = await fetch('/api/stock/{hotel_id}/periods/');
const data = await response.json();

// Find October 2025 (closed)
const octoberPeriod = data.results.find(p => 
  p.year === 2025 && p.month === 10 && p.is_closed === true
);
// octoberPeriod.id = 2

// Step 2: Get full period with all 244 item snapshots
const periodResponse = await fetch(`/api/stock/{hotel_id}/periods/${octoberPeriod.id}/`);
const octoberData = await periodResponse.json();

// Now you have:
// - octoberData.snapshots = array of 244 items with closing stock
// - Each snapshot has: closing_full_units, closing_partial_units, closing_stock_value
// - Use this as "previous month" reference for November 2025 stocktake
```

---

## Table of Contents
1. [Screen Overview](#screen-overview)
2. [Screen 1: Stocktake Entry (Simple)](#screen-1-stocktake-entry-simple)
3. [Screen 2: Item Detail Modal (Extended Analysis)](#screen-2-item-detail-modal-extended-analysis)
4. [Screen 3: Stocktake Summary Report](#screen-3-stocktake-summary-report)
5. [Screen 4: Period Comparison Dashboard](#screen-4-period-comparison-dashboard)
6. [Data Structure Guide](#data-structure-guide)
7. [API Endpoints Reference](#api-endpoints-reference)

---

## Screen Overview

```
User Flow:
┌─────────────────────┐
│ 1. STOCKTAKE ENTRY  │  ← Staff counts bottles (SIMPLE)
└──────────┬──────────┘
           │ Click item
           ↓
┌─────────────────────┐
│ 2. ITEM DETAIL      │  ← Shows expected vs actual (EXTENDED)
└──────────┬──────────┘
           │ Save all
           ↓
┌─────────────────────┐
│ 3. SUMMARY REPORT   │  ← Totals, comparisons, financials
└──────────┬──────────┘
           │ View history
           ↓
┌─────────────────────┐
│ 4. PERIOD COMPARE   │  ← Month-over-month trends
└─────────────────────┘
```

---

## Screen 1: Stocktake Entry (Simple)

### Purpose
Staff quickly enter bottle counts during physical stocktaking. **No calculations or analysis shown here** - just pure data entry.

### What to Display

```
╔════════════════════════════════════════════════════════════╗
║ NOVEMBER 2024 STOCKTAKE                    Status: Open    ║
╠════════════════════════════════════════════════════════════╣
║ Filter: [All Categories ▼] [Search: ______]               ║
╠════════════════════════════════════════════════════════════╣
║ ITEM INFO (Static - Never Changes)    | STAFF COUNT       ║
╠════════════════════════════════════════════════════════════╣
║ 📦 SPIRITS                                                 ║
╟────────────────────────────────────────────────────────────╢
║ Jameson Irish Whiskey                                      ║
║ Size: 700ml | Unit: bottle                                ║
║ Cost: €15.00 | Price: €4.50/shot                          ║
║                                        Full: [17] Partial: [0.3] ║
║                                        [👁️ View Details]    ║
╟────────────────────────────────────────────────────────────╢
║ Smirnoff Vodka                                             ║
║ Size: 700ml | Unit: bottle                                ║
║ Cost: €12.50 | Price: €4.00/shot                          ║
║                                        Full: [8] Partial: [0.75] ║
║                                        [👁️ View Details]    ║
╟────────────────────────────────────────────────────────────╢
║ 🍺 BEERS                                                   ║
╟────────────────────────────────────────────────────────────╢
║ Guinness Draught                                           ║
║ Size: 50L | Unit: keg                                     ║
║ Cost: €185.00 | Price: €5.50/pint                         ║
║                                        Full: [2] Partial: [0.6] ║
║                                        [👁️ View Details]    ║
╟────────────────────────────────────────────────────────────╢
║                            [Save Progress] [Finalize ✓]    ║
╚════════════════════════════════════════════════════════════╝
```

### Data Sources

**API Endpoint to get closed October 2025 period:**
```
GET /api/stock/{hotel}/periods/
```

**Response:**
```javascript
{
  "count": 1,
  "results": [
    {
      "id": 2,
      "period_type": "MONTHLY",
      "period_name": "October 2025",
      "year": 2025,
      "month": 10,
      "is_closed": true,
      "start_date": "2025-10-01",
      "end_date": "2025-10-31"
    }
  ]
}
```

**Then fetch period details with all items:**
```
GET /api/stock/{hotel}/periods/{period_id}/
```

**Response Structure:**
```javascript
{
  "id": 2,
  "period_type": "MONTHLY",
  "period_name": "October 2025",
  "year": 2025,
  "month": 10,
  "is_closed": true,
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  "snapshots": [
    {
      "id": 501,
      "item": {
        // ── ITEM INFO (Display in left column) ──
        "id": 25,
        "sku": "JAME001",
        "name": "Jameson Irish Whiskey",
        "category": "S",
        "category_display": "Spirits",
        "size": 700,
        "uom": "ml",
        "unit_cost": 15.00,
        "menu_price": 4.50,
        "bottle_price": null
      },
      
      // ── STAFF COUNT (Input fields) ──
      "full_units": 17,      // ← Staff enters
      "partial_units": 0.3,  // ← Staff enters
      "total_quantity": 17.3 // Auto-calculated
    }
  ]
}
```

### What NOT to Show
- ❌ Expected stock calculations
- ❌ Variance warnings
- ❌ Previous period data
- ❌ GP% or profitability metrics
- ❌ Stock movements/deliveries

**Keep it simple for counting!**

---

## Screen 2: Item Detail Modal (Extended Analysis)

### Purpose
When staff clicks "👁️ View Details", show comprehensive analysis including expected stock, variance, and profitability.

### What to Display

```
╔════════════════════════════════════════════════════════════╗
║ 🥃 JAMESON IRISH WHISKEY                          [✕ Close]║
╠════════════════════════════════════════════════════════════╣
║ ITEM INFORMATION                                           ║
╟────────────────────────────────────────────────────────────╢
║ SKU: JAME001                    Category: Spirits          ║
║ Size: 700ml                     UOM: bottle                ║
║ Unit Cost: €15.00               Menu Price: €4.50/shot     ║
║ Bottle Price: -                                            ║
╠════════════════════════════════════════════════════════════╣
║ PREVIOUS STOCKTAKE (October 31, 2024)                      ║
╟────────────────────────────────────────────────────────────╢
║ Closing Balance: 12 full + 0.45 partial = 12.45 bottles   ║
║ Stock Value: €186.75                                       ║
║ GP%: 70.0% | Markup: 200%                                  ║
╠════════════════════════════════════════════════════════════╣
║ STOCK MOVEMENTS (Nov 1 - Nov 30)                           ║
╟────────────────────────────────────────────────────────────╢
║ + Deliveries:        24.0 bottles  (Nov 5, 2024)          ║
║ - Sales/Usage:      -18.0 bottles                          ║
║ - Adjustments:        0.0 bottles                          ║
║ ─────────────────────────────────────────────────────────  ║
║ Net Change:         +6.0 bottles                           ║
╠════════════════════════════════════════════════════════════╣
║ EXPECTED vs ACTUAL                                         ║
╟────────────────────────────────────────────────────────────╢
║ Expected Stock:     18.45 bottles                          ║
║                     (12.45 + 6.0 movement)                 ║
║                                                            ║
║ Actual Count:       17.3 bottles                           ║
║                     (17 full + 0.3 partial)                ║
║                                                            ║
║ ⚠️ VARIANCE:        -1.15 bottles (-6.2%)                  ║
║ ⚠️ Value Loss:      €17.25                                 ║
║ Status:             WARNING                                ║
╠════════════════════════════════════════════════════════════╣
║ CURRENT STOCK VALUE (as counted)                           ║
╟────────────────────────────────────────────────────────────╢
║ Cost Value:         €259.50  (17.3 × €15.00)              ║
║ Potential Sales:    €1,038.00 (if sold at menu price)     ║
║ Potential Profit:   €778.50                                ║
║ GP%:                75.0%                                  ║
╠════════════════════════════════════════════════════════════╣
║                                        [OK] [Re-count?]    ║
╚════════════════════════════════════════════════════════════╝
```

### Data Sources

**API Endpoint:**
```
GET /api/stock/{hotel}/items/{item_id}/stocktake-guidance/?current_period={period_id}
```

**Response Structure:**
```javascript
{
  "item": {
    "sku": "JAME001",
    "name": "Jameson Irish Whiskey",
    "category": "S",
    "category_display": "Spirits",
    "size": 700,
    "uom": "ml",
    "unit_cost": 15.00,
    "menu_price": 4.50,
    "bottle_price": null
  },
  
  "previous_stocktake": {
    "period": "October 2024",
    "date": "2024-10-31",
    "full_units": 12,
    "partial_units": 0.45,
    "total_quantity": 12.45,
    "stock_value": 186.75,
    "gp_percentage": 70.0,
    "markup_percentage": 200.0
  },
  
  "movements": {
    "deliveries": 24.0,
    "sales": -18.0,
    "adjustments": 0.0,
    "total_change": 6.0,
    "details": [
      {
        "date": "2024-11-05",
        "type": "IN",
        "quantity": 24.0,
        "reference": "Delivery #1234"
      }
    ]
  },
  
  "expected_stock": {
    "calculated_quantity": 18.45,
    "message": "Based on previous stock and movements"
  },
  
  "actual_count": {
    "full_units": 17,
    "partial_units": 0.3,
    "total_quantity": 17.3
  },
  
  "variance": {
    "difference": -1.15,
    "percentage": -6.2,
    "value_impact": -17.25,
    "status": "WARNING"  // "OK", "WARNING", "CRITICAL"
  },
  
  "current_value": {
    "cost_value": 259.50,
    "potential_sales": 1038.00,
    "potential_profit": 778.50,
    "gp_percentage": 75.0
  }
}
```

### Variance Status Rules
- ✅ **OK**: Difference ≤ 5%
- ⚠️ **WARNING**: Difference 5-15%
- 🚨 **CRITICAL**: Difference > 15%

---

## Screen 3: Stocktake Summary Report

### Purpose
After stocktake is finalized, show comprehensive financial summary with period comparison.

### What to Display

```
╔════════════════════════════════════════════════════════════╗
║ 📊 STOCKTAKE SUMMARY - NOVEMBER 2024                       ║
║                                        Status: Closed ✓    ║
╠════════════════════════════════════════════════════════════╣
║ CURRENT PERIOD (November 2024)                             ║
╟────────────────────────────────────────────────────────────╢
║ Total Items Counted:           244                         ║
║ Total Stock Value (Cost):      €12,450.00                 ║
║ Potential Sales Value:         €41,280.00                 ║
║ Potential Gross Profit:        €28,830.00                 ║
║ Overall GP%:                   69.8%                       ║
╠════════════════════════════════════════════════════════════╣
║ PREVIOUS PERIOD (October 2024)                             ║
╟────────────────────────────────────────────────────────────╢
║ Total Items Counted:           244                         ║
║ Total Stock Value (Cost):      €11,200.00                 ║
║ Potential Sales Value:         €38,500.00                 ║
║ Potential Gross Profit:        €27,300.00                 ║
║ Overall GP%:                   70.9%                       ║
╠════════════════════════════════════════════════════════════╣
║ COMPARISON (November vs October)                           ║
╟────────────────────────────────────────────────────────────╢
║ Stock Value Change:            +€1,250.00  (+11.2%) ↑     ║
║ Sales Value Change:            +€2,780.00  (+7.2%) ↑      ║
║ Gross Profit Change:           +€1,530.00  (+5.6%) ↑      ║
║ GP% Change:                    -1.1% ↓                     ║
║ Trend:                         Stock Increased             ║
╠════════════════════════════════════════════════════════════╣
║ BREAKDOWN BY CATEGORY                                      ║
╟────┬─────────┬────────────┬─────────────┬────────┬────────╢
║ Cat│ Name    │Stock Value │Sales Value  │  GP%   │vs Prev ║
╟────┼─────────┼────────────┼─────────────┼────────┼────────╢
║ 🥃 │ Spirits │ €5,200.00  │ €18,500.00  │ 71.9%  │ +2.3%↑ ║
║ 🍺 │ Beers   │ €3,100.00  │  €8,200.00  │ 62.2%  │ -1.5%↓ ║
║ 🍷 │ Wines   │ €2,800.00  │ €10,100.00  │ 72.3%  │ +0.8%↑ ║
║ 🍻 │ Draught │ €1,150.00  │  €3,800.00  │ 69.7%  │ -0.5%↓ ║
║ 🥤 │ Mixers  │   €200.00  │    €680.00  │ 70.6%  │ +1.2%↑ ║
╟────┴─────────┴────────────┴─────────────┴────────┴────────╢
║ TOTAL          €12,450.00   €41,280.00   69.8%   -1.1%    ║
╠════════════════════════════════════════════════════════════╣
║ VARIANCE ALERTS                                            ║
╟────────────────────────────────────────────────────────────╢
║ 🚨 3 Critical Variances (>15% difference)                  ║
║ ⚠️  8 Warnings (5-15% difference)                          ║
║ ✅ 233 Items OK (<5% difference)                           ║
║                                        [View Details →]    ║
╠════════════════════════════════════════════════════════════╣
║              [📄 Export PDF] [📊 View Charts]              ║
╚════════════════════════════════════════════════════════════╝
```

### Data Sources

**API Endpoint:**
```
GET /api/stock/{hotel}/periods/{period_id}/summary/
```

**Response Structure:**
```javascript
{
  "current_period": {
    "id": 2,
    "month": "November",
    "year": 2024,
    "status": "closed",
    "item_count": 244,
    "total_stock_value_cost": 12450.00,
    "total_potential_sales": 41280.00,
    "total_gross_profit": 28830.00,
    "overall_gp_percentage": 69.8
  },
  
  "previous_period": {
    "id": 1,
    "month": "October",
    "year": 2024,
    "status": "closed",
    "item_count": 244,
    "total_stock_value_cost": 11200.00,
    "total_potential_sales": 38500.00,
    "total_gross_profit": 27300.00,
    "overall_gp_percentage": 70.9
  },
  
  "comparison": {
    "stock_value_change": 1250.00,
    "stock_value_change_percent": 11.2,
    "sales_value_change": 2780.00,
    "sales_value_change_percent": 7.2,
    "profit_change": 1530.00,
    "profit_change_percent": 5.6,
    "gp_change": -1.1,
    "trend": "stock_increased"
  },
  
  "by_category": [
    {
      "category": "S",
      "category_name": "Spirits",
      "emoji": "🥃",
      "current": {
        "stock_value": 5200.00,
        "sales_value": 18500.00,
        "gp_percentage": 71.9
      },
      "previous": {
        "stock_value": 4800.00,
        "sales_value": 17100.00,
        "gp_percentage": 69.6
      },
      "change": {
        "gp_percentage_diff": 2.3
      }
    }
    // ... other categories
  ],
  
  "variance_summary": {
    "critical_count": 3,
    "warning_count": 8,
    "ok_count": 233
  }
}
```

---

## Screen 4: Period Comparison Dashboard

### Purpose
Compare any two periods side-by-side to analyze trends.

### What to Display

```
╔════════════════════════════════════════════════════════════╗
║ 📈 PERIOD COMPARISON                                       ║
╠════════════════════════════════════════════════════════════╣
║ Compare: [October 2024 ▼]  vs  [November 2024 ▼]         ║
╠════════════════════════════════════════════════════════════╣
║                    October 2024  │  November 2024  │ Δ     ║
╟────────────────────────────────────────────────────────────╢
║ Stock Value (Cost) €11,200.00    │ €12,450.00      │+11.2%↑║
║ Sales Value        €38,500.00    │ €41,280.00      │ +7.2%↑║
║ Gross Profit       €27,300.00    │ €28,830.00      │ +5.6%↑║
║ GP%                70.9%          │ 69.8%           │ -1.1%↓║
║ Items              244            │ 244             │ -     ║
╠════════════════════════════════════════════════════════════╣
║ TOP IMPROVERS (GP% increase)                               ║
╟────────────────────────────────────────────────────────────╢
║ 1. Jameson Irish Whiskey          70.0% → 75.0%  (+5.0%)  ║
║ 2. Smirnoff Vodka                 68.0% → 72.5%  (+4.5%)  ║
║ 3. Grey Goose Vodka               71.0% → 74.0%  (+3.0%)  ║
╠════════════════════════════════════════════════════════════╣
║ CONCERNS (GP% decrease)                                    ║
╟────────────────────────────────────────────────────────────╢
║ 1. Heineken Beer                  45.0% → 38.0%  (-7.0%)🚨║
║ 2. Corona Beer                    42.0% → 37.0%  (-5.0%)⚠️ ║
╠════════════════════════════════════════════════════════════╣
║                            [📊 View Chart] [📄 Export]     ║
╚════════════════════════════════════════════════════════════╝
```

### Data Sources

**API Endpoint:**
```
GET /api/stock/{hotel}/periods/compare/?period1={id1}&period2={id2}
```

**Response Structure:**
```javascript
{
  "period1": {
    "id": 1,
    "month": "October",
    "year": 2024,
    "totals": {
      "stock_value": 11200.00,
      "sales_value": 38500.00,
      "gross_profit": 27300.00,
      "gp_percentage": 70.9,
      "item_count": 244
    }
  },
  
  "period2": {
    "id": 2,
    "month": "November",
    "year": 2024,
    "totals": {
      "stock_value": 12450.00,
      "sales_value": 41280.00,
      "gross_profit": 28830.00,
      "gp_percentage": 69.8,
      "item_count": 244
    }
  },
  
  "changes": {
    "stock_value_percent": 11.2,
    "sales_value_percent": 7.2,
    "profit_percent": 5.6,
    "gp_percent": -1.1
  },
  
  "top_improvers": [
    {
      "item": "Jameson Irish Whiskey",
      "period1_gp": 70.0,
      "period2_gp": 75.0,
      "improvement": 5.0
    }
  ],
  
  "concerns": [
    {
      "item": "Heineken Beer",
      "period1_gp": 45.0,
      "period2_gp": 38.0,
      "decline": -7.0,
      "severity": "CRITICAL"
    }
  ]
}
```

---

## Data Structure Guide

### Understanding the Two Types of Data

#### 1. ITEM INFO (Static Master Data)
**Source:** `StockItem` model  
**Changes:** Rarely (only when you update product info)  
**What it includes:**
- `sku` - Product code
- `name` - Product name
- `category` - Category code (S/B/W/D/M)
- `size` - Package size (700, 330, etc.)
- `uom` - Unit of measure (ml, L, bottle)
- `unit_cost` - What you pay supplier
- `menu_price` - What customer pays (per serving)
- `bottle_price` - Bottle price (if applicable)

#### 2. STOCKTAKE DATA (Period-Specific)
**Source:** `StockSnapshot` model  
**Changes:** Every stocktake  
**What it includes:**
- `full_units` - Whole bottles/kegs counted
- `partial_units` - Partial bottles (0.45 = 45% full)
- `total_quantity` - Auto-calculated (full + partial)
- `total_value` - Quantity × unit_cost
- `gp_percentage` - Gross profit %
- `markup_percentage` - Markup %

---

## API Endpoints Reference

### Core Endpoints

```
GET    /api/stock/{hotel}/periods/                    # List all periods
GET    /api/stock/{hotel}/periods/{id}/               # Period detail + all snapshots
POST   /api/stock/{hotel}/periods/                    # Create new period
PATCH  /api/stock/{hotel}/periods/{id}/               # Update period (e.g., finalize)

GET    /api/stock/{hotel}/items/                      # List all items
GET    /api/stock/{hotel}/items/{id}/                 # Item detail

POST   /api/stock/{hotel}/snapshots/                  # Create/update snapshot (staff count)
```

### New Endpoints (To Be Created)

```
GET    /api/stock/{hotel}/items/{id}/stocktake-guidance/
       ?current_period={period_id}
       → Returns expected vs actual with variance

GET    /api/stock/{hotel}/periods/{id}/summary/
       → Returns financial summary with category breakdown

GET    /api/stock/{hotel}/periods/compare/
       ?period1={id1}&period2={id2}
       → Side-by-side period comparison
```

---

## Summary: What Goes Where

| Data Type | Screen 1 (Entry) | Screen 2 (Detail) | Screen 3 (Summary) | Screen 4 (Compare) |
|-----------|------------------|-------------------|--------------------|--------------------|
| Item Info | ✅ Name, Size, Cost | ✅ Full details | ❌ | ❌ |
| Staff Count | ✅ Input fields | ✅ Read-only | ❌ | ❌ |
| Previous Period | ❌ Hidden | ✅ Closing balance | ✅ Totals | ✅ Full comparison |
| Movements | ❌ Hidden | ✅ Deliveries/Sales | ❌ | ❌ |
| Expected Stock | ❌ Hidden | ✅ Calculated | ❌ | ❌ |
| Variance | ❌ Hidden | ✅ Highlighted | ✅ Alert count | ❌ |
| GP% | ❌ Hidden | ✅ Current + Previous | ✅ Overall + Category | ✅ Trend analysis |
| Financials | ❌ Hidden | ✅ Item-level | ✅ Period totals | ✅ Change % |

---

## Key Principles

1. **Screen 1 = Simple** → Staff focuses on counting, no distractions
2. **Screen 2 = Analysis** → Deep dive per item, show everything
3. **Screen 3 = Overview** → Big picture, management decisions
4. **Screen 4 = Trends** → Historical comparison, strategic insights

**Any questions before I implement the backend endpoints?** 🎯
