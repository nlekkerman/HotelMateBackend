# October 2024 Stock Discrepancy Report

**Date:** November 7, 2025  
**Comparison:** Excel Data vs Database Calculations

---

## Executive Summary

### Overall Totals
| Category | Excel Value | Database Value | Difference | Status |
|----------|------------|----------------|------------|--------|
| **Draught Beers** | €5,311.62 | €5,258.36 | €53.26 | ❌ |
| **Bottled Beers** | €2,288.46 | €3,079.04 | -€790.58 | ❌ |
| **Spirits** | €11,063.66 | €10,398.24 | €665.42 | ❌ |
| **Minerals/Syrups** | €3,062.43 | €4,185.64 | -€1,123.21 | ❌ |
| **Wine** | €5,580.35 | €3,978.87 | €1,601.48 | ❌ |
| **GRAND TOTAL** | **€27,306.52** | **€26,900.15** | **€406.37** | ❌ |

**Key Finding:** The database shows **€406.37 LESS** than the Excel spreadsheet.

---

## Category Analysis

### 1. Draught Beers (€53.26 Difference)

**Issues Identified:**

#### Major Discrepancies:
1. **30 Heineken (D0030)**
   - Excel: 0 kegs, 0 pints = €0.00
   - Database: 5 kegs, 0 pints = €980.70
   - **Difference: -€980.70** ❌
   - *Issue: Database has 5 full kegs that Excel shows as zero*

2. **50 Heineken (D1004)**
   - Excel: 0 kegs, 542 pints = €1,208.04
   - Database: 3 kegs, 26.5 pints = €411.95
   - **Difference: €796.09** ❌
   - *Issue: Excel shows 542 partial pints, DB shows 3 full kegs + 26.5 pints*

3. **30 Moretti (D2354)**
   - Excel: 0 kegs, 304 pints = €763.73
   - Database: 2 kegs, 13.25 pints = €299.59
   - **Difference: €464.14** ❌
   - *Issue: Excel shows 304 partial pints, DB shows 2 kegs + 13.25 pints*

4. **30 Coors (D0004)**
   - Excel: 0 kegs, 0 pints = €0.00
   - Database: 2 kegs, 26.5 pints = €294.25
   - **Difference: -€294.25** ❌

5. **30 Lagunitas IPA (D0011)**
   - Excel: 0 kegs, 5 pints = €13.60
   - Database: 1 keg, 26.5 pints = €216.21
   - **Difference: -€202.61** ❌

**Root Cause:** The Excel spreadsheet appears to have **full kegs converted to partial pints incorrectly**. The database properly separates full kegs from partial pints.

---

### 2. Bottled Beers (-€790.58 Difference)

**Database shows MORE value than Excel**

The database has €3,079.04 while Excel shows only €2,288.46. This suggests:
- Items may have been added to the database after Excel was created
- Quantities in database are higher than Excel records
- Need item-by-item comparison to identify specific differences

**Action Required:** Review all bottled beer items individually to find which items have higher quantities in the database.

---

### 3. Spirits (€665.42 Difference)

**Excel shows MORE value than Database**

Top differences likely include:
- Some spirits may be recorded in Excel but not imported to database
- Quantities in Excel may be higher
- Cost prices may differ between Excel and database

**Top Items by Value (Database):**
- Smirnoff 1Ltr: €999.81
- Dingle Gin 70cl: €652.01
- Green Spot: €460.31
- Redbreast 15 Years Old: €269.19

**Action Required:** Compare each spirit item's quantities and costs between Excel and database.

---

### 4. Minerals/Syrups (-€1,123.21 Difference)

**Database shows MORE value than Excel**

This is a significant discrepancy (€4,185.64 vs €3,062.43).

**Possible Causes:**
- Database may have more items recorded
- Quantities in database higher than Excel
- Items may have been added after Excel creation

**Action Required:** Full item-by-item comparison needed.

---

### 5. Wine (€1,601.48 Difference)

**Excel shows MORE value than Database**

This is the **largest category discrepancy** (€5,580.35 vs €3,978.87).

**Top Items by Value (Database):**
- Pannier: €402.87
- Cheval Chardonny: €346.96
- Sonnetti Pinot Grigo: €340.45
- Santa Ana Malbec: €337.00

**Possible Causes:**
- Some wines in Excel may not be in database
- Bottle counts in Excel may be higher
- Fractional bottles handled differently

**Action Required:** Full wine inventory comparison needed.

---

## Detailed Draught Beer Item Comparison

| SKU | Name | Excel Full | DB Full | Excel Partial | DB Partial | Excel Value | DB Value | Difference |
|-----|------|-----------|---------|--------------|-----------|------------|----------|-----------|
| D2133 | 20 Heineken 00% | 0.00 | 0.00 | 40.00 | 26.25 | €68.25 | €0.00 | €68.25 ❌ |
| D0007 | 30 Beamish | 0.00 | 0.00 | 79.00 | 17.67 | €137.25 | €30.69 | €106.56 ❌ |
| D0004 | 30 Coors | 0.00 | 2.00 | 0.00 | 26.50 | €0.00 | €294.25 | -€294.25 ❌ |
| D0030 | 30 Heineken | 0.00 | 5.00 | 0.00 | 0.00 | €0.00 | €980.70 | -€980.70 ❌ |
| D0012 | 30 Killarney Blonde | 0.00 | 0.00 | 0.00 | 0.00 | €0.00 | €0.00 | €0.00 ✅ |
| D0011 | 30 Lagunitas IPA | 0.00 | 1.00 | 5.00 | 26.50 | €13.60 | €216.21 | -€202.61 ❌ |
| D2354 | 30 Moretti | 0.00 | 2.00 | 304.00 | 13.25 | €763.73 | €299.59 | €464.14 ❌ |
| D1003 | 30 Murphys | 0.00 | 2.00 | 198.00 | 26.50 | €419.69 | €280.85 | €138.84 ❌ |
| D0008 | 30 Murphys Red | 0.00 | 1.00 | 26.50 | 26.50 | €57.34 | €172.02 | -€114.68 ❌ |
| D1022 | 30 Orchards | 0.00 | 4.00 | 296.00 | 0.00 | €652.04 | €467.00 | €185.04 ❌ |
| D0006 | 30 OT Wild Orchard | 0.00 | 2.00 | 93.00 | 0.00 | €204.86 | €233.50 | -€28.64 ❌ |
| D1258 | 50 Coors | 6.00 | 6.00 | 39.75 | 39.75 | €1,265.44 | €1,265.44 | €0.00 ✅ |
| D0005 | 50 Guinness | 0.00 | 3.00 | 246.00 | 22.00 | €521.38 | €606.16 | -€84.78 ❌ |
| D1004 | 50 Heineken | 0.00 | 3.00 | 542.00 | 26.50 | €1,208.04 | €411.95 | €796.09 ❌ |

---

## Recommendations

### Immediate Actions:

1. **Draught Beers:**
   - Review the conversion logic between full kegs and partial pints
   - Verify if the Excel data incorrectly converted full kegs to partial pints
   - Check the actual physical stock for items with large discrepancies:
     - D0030 (30 Heineken): 5 kegs difference
     - D1004 (50 Heineken): major partial pints difference
     - D2354 (30 Moretti): 304 pints vs 2 kegs + 13 pints

2. **Bottled Beers:**
   - Generate item-by-item comparison report
   - Identify which items have higher quantities in database
   - Verify if new stock was added after Excel was created

3. **Spirits:**
   - Compare each spirit SKU between Excel and database
   - Check for missing items in database
   - Verify quantity counts match

4. **Minerals/Syrups:**
   - Full item-by-item audit needed
   - Check if database has items not in Excel
   - Verify all quantities

5. **Wine:**
   - Complete wine inventory comparison required
   - Check fractional bottle handling
   - Verify all wine SKUs present in both systems

### System Issues to Address:

1. **Data Entry Consistency:**
   - Ensure clear rules for entering full vs partial units
   - For draught: full kegs vs partial pints
   - For bottled: cases vs individual bottles

2. **Import Process:**
   - Review the `upload_october_stock.py` script
   - Verify it correctly interprets Excel data
   - Check UOM calculations for each category

3. **Calculation Verification:**
   - The database calculations appear more accurate
   - Excel may have manual calculation errors
   - Consider using database as source of truth

---

## Next Steps

1. ✅ **Completed:** Overall comparison and major discrepancy identification
2. ⏳ **In Progress:** Detailed draught beer analysis
3. 🔜 **Required:** Item-by-item comparison for all categories
4. 🔜 **Required:** Physical stock verification for high-value discrepancies
5. 🔜 **Required:** Decision on which system to use as source of truth

---

## Technical Notes

### Database Information:
- **Period:** October 2024 (ID: 5)
- **Date Range:** 2024-10-01 to 2024-10-31
- **Status:** Open
- **Total Snapshots:** 244 items

### Calculation Methods:
- **Draught Beers (D):** Full kegs + partial pints
  - UOM = pints per keg (e.g., 50L keg = 88.03 pints)
  - Value = (full × unit_cost) + (partial × cost_per_pint)

- **Bottled Beers (B):** Cases + individual bottles
  - UOM = 12 (bottles per case)
  - Value calculated using cost per serving

- **Spirits (S):** Bottles + fractional bottles
  - UOM = shots per bottle
  - Value = total shots × cost per shot

- **Wine (W):** Bottles + fractional bottles
  - UOM = 1 (sold by bottle)
  - Value = total bottles × cost per bottle

- **Minerals (M):** Varies by item type
  - Some use individual units
  - Some use cases/dozens
  - Some use liters

---

**Report Generated:** November 7, 2025  
**Generated By:** Stock Comparison Analysis Script  
**Contact:** Review with stock management team
