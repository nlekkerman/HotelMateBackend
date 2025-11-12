# 📐 STOCKTAKE FORMULAS - QUICK REFERENCE

**Purpose:** Quick lookup of all formulas used in stocktake calculations  
**Rule:** Backend calculates ALL formulas - Frontend only displays results

---

## 🔢 CORE FORMULAS

### 1. Expected Quantity
```
expected_qty = opening_qty + purchases - waste
```

**What it means:** This is what SHOULD be in stock before counting.

**Example:**
```
Opening:   0.00 servings
Purchases: 12.43 servings
Waste:     1.00 servings
Expected:  0.00 + 12.43 - 1.00 = 11.43 servings
```

**⚠️ IMPORTANT:** Sales are NOT in this formula!  
Sales are tracked separately for profit calculations.

---

### 2. Counted Quantity (Depends on Category)

#### For Draught Beer (D) + Dozen Items (Doz):
```
counted_qty = (counted_full_units × uom) + counted_partial_units
```

**Why:** Partial units are already in servings (pints/bottles).

**Example (Draught Beer):**
```
Counted: 2 kegs, 15.5 pints
UOM: 88 pints per keg
counted_qty = (2 × 88) + 15.5 = 191.5 servings
```

**Example (Bottled Beer Dozen):**
```
Counted: 1 case, 2 bottles
UOM: 12 bottles per case
counted_qty = (1 × 12) + 2 = 14 servings (bottles)
```

#### For Spirits (S) + Wine (W) + Other:
```
counted_qty = (counted_full_units × uom) + (counted_partial_units × uom)
```

**Why:** Partial units are fractional (0.5 = half a bottle).

**Example (Spirits):**
```
Counted: 1 bottle, 0.5 bottles
UOM: 20 shots per bottle
counted_qty = (1 × 20) + (0.5 × 20) = 30 servings (shots)
```

**Example (Wine):**
```
Counted: 2 bottles, 0.67 bottles
UOM: 1 glass per bottle
counted_qty = (2 × 1) + (0.67 × 1) = 2.67 servings (glasses)
```

---

### 3. Variance Quantity
```
variance_qty = counted_qty - expected_qty
```

**Results:**
- **Positive (+):** Surplus - Found more than expected
- **Negative (-):** Shortage - Missing stock
- **Zero (0):** Perfect match

**Example:**
```
Counted:  14.00 servings
Expected: 11.43 servings
Variance: 14.00 - 11.43 = +2.57 servings (Surplus!)
```

---

### 4. Expected Value
```
expected_value = expected_qty × valuation_cost
```

**Example:**
```
Expected: 11.43 servings
Cost:     €1.23 per serving
Value:    11.43 × 1.23 = €13.53
```

---

### 5. Counted Value
```
counted_value = counted_qty × valuation_cost
```

**Example:**
```
Counted: 14.00 servings
Cost:    €1.23 per serving
Value:   14.00 × 1.23 = €17.22
```

---

### 6. Variance Value
```
variance_value = counted_value - expected_value
```

**Example:**
```
Counted Value:  €17.22
Expected Value: €13.53
Variance:       €17.22 - €13.53 = +€3.69 (Surplus value!)
```

---

## 📊 DISPLAY UNIT CONVERSION

### Formula:
```
full_units = floor(servings / uom)
partial_units = servings % uom
```

### With Category-Specific Rounding:

#### Bottled Beer (B) + Dozen Minerals (M Doz):
```python
full = int(servings / uom)
partial = round(servings % uom)  # Whole numbers only
```

**Example:**
```
Servings: 11.43
UOM: 12
full = int(11.43 / 12) = 0 cases
partial = round(11.43 % 12) = round(11.43) = 11 bottles
Display: "0 cases, 11 bottles"
```

#### Draught Beer (D):
```python
full = int(servings / uom)
partial = round(servings % uom, 2)  # 2 decimal places
```

**Example:**
```
Servings: 191.567
UOM: 88
full = int(191.567 / 88) = 2 kegs
partial = round(191.567 % 88, 2) = round(15.567, 2) = 15.57 pints
Display: "2 kegs, 15.57 pints"
```

#### Spirits (S) + Wine (W) + Other:
```python
full = int(servings / uom)
partial = round(servings % uom, 2)  # 2 decimal places
```

**Example (Spirits):**
```
Servings: 30.678
UOM: 20
full = int(30.678 / 20) = 1 bottle
partial = round(30.678 % 20, 2) = round(10.678, 2) = 10.68 shots
Display: "1 bottle, 10.68 shots"
```

---

## 🎯 CATEGORY TOTALS

### Formula (for each category):
```
Sum all lines where category_code = 'B' (or 'D', 'S', 'W', 'M')

category_total_expected_qty = Σ expected_qty
category_total_counted_qty = Σ counted_qty
category_total_variance_qty = Σ variance_qty

category_total_expected_value = Σ expected_value
category_total_counted_value = Σ counted_value
category_total_variance_value = Σ variance_value
```

### Variance Percentage:
```
variance_percent = (|variance_value| / expected_value) × 100
```

**Example:**
```
Expected Value:  €244.03
Variance Value:  -€244.03
Percentage:      (244.03 / 244.03) × 100 = 100.0% variance
```

---

## 🧮 COMPLETE CALCULATION FLOW

### Step-by-Step Example (Bottled Beer):

**Given Data:**
- Item: B0012 - Cronins 0.0%
- Category: B (Bottled Beer)
- UOM: 12 bottles per case
- Valuation Cost: €1.23 per bottle
- Opening: 0.00 bottles
- Purchases: 12.43 bottles
- Waste: 1.00 bottle
- User Counted: 1 case, 2 bottles

**Calculations:**

1️⃣ **Expected Quantity**
```
expected_qty = 0.00 + 12.43 - 1.00 = 11.43 bottles
```

2️⃣ **Counted Quantity** (Category B uses special formula)
```
counted_qty = (1 × 12) + 2 = 14.00 bottles
```

3️⃣ **Variance Quantity**
```
variance_qty = 14.00 - 11.43 = +2.57 bottles (Surplus!)
```

4️⃣ **Expected Value**
```
expected_value = 11.43 × 1.23 = €13.53
```

5️⃣ **Counted Value**
```
counted_value = 14.00 × 1.23 = €17.22
```

6️⃣ **Variance Value**
```
variance_value = 17.22 - 13.53 = +€3.69 (Surplus!)
```

7️⃣ **Display Units - Expected**
```
full = int(11.43 / 12) = 0 cases
partial = round(11.43 % 12) = 11 bottles
Display: "0 cases, 11 bottles (€13.53)"
```

8️⃣ **Display Units - Counted**
```
full = int(14.00 / 12) = 1 case
partial = round(14.00 % 12) = 2 bottles
Display: "1 case, 2 bottles (€17.22)"
```

9️⃣ **Display Units - Variance**
```
full = int(2.57 / 12) = 0 cases
partial = round(2.57 % 12) = 3 bottles
Display: "+0 cases, +3 bottles (+€3.69)" with green background
```

---

## ⚠️ COMMON MISTAKES TO AVOID

### ❌ WRONG: Including sales in expected formula
```javascript
// DON'T DO THIS!
expected_qty = opening_qty + purchases - sales - waste
```
**Why wrong:** Sales are tracked separately. Expected formula only uses opening + purchases - waste.

### ❌ WRONG: Using wrong counted formula for category
```javascript
// DON'T DO THIS for Spirits!
counted_qty = (full_units × uom) + partial_units
```
**Why wrong:** Spirits use fractional partials, so you need `(partial_units × uom)`.

### ❌ WRONG: Calculating variance backwards
```javascript
// DON'T DO THIS!
variance = expected - counted
```
**Why wrong:** Variance is ALWAYS `counted - expected`. Positive = surplus, Negative = shortage.

### ❌ WRONG: Calculating on frontend
```javascript
// DON'T DO THIS!
const expected = opening + purchases - waste;
```
**Why wrong:** Backend calculates everything. Frontend only displays values from API.

---

## ✅ VALIDATION RULES

### Full Units (All Categories):
- Must be >= 0
- Whole numbers only
- No decimals

### Partial Units - Bottled Beer (B) + Dozen Minerals (M Doz):
- Must be >= 0
- Must be < UOM (e.g., 0-11 for UOM=12)
- Whole numbers only
- No decimals

### Partial Units - Draught (D), Spirits (S), Wine (W), Other:
- Must be >= 0.00
- Must be < UOM (e.g., 0.00-87.99 for UOM=88)
- Max 2 decimal places

---

## 📋 FORMULA SUMMARY TABLE

| Field | Formula | Who Calculates |
|-------|---------|----------------|
| `expected_qty` | `opening + purchases - waste` | ✅ Backend |
| `counted_qty` (D/Doz) | `(full × uom) + partial` | ✅ Backend |
| `counted_qty` (Other) | `(full × uom) + (partial × uom)` | ✅ Backend |
| `variance_qty` | `counted - expected` | ✅ Backend |
| `expected_value` | `expected_qty × cost` | ✅ Backend |
| `counted_value` | `counted_qty × cost` | ✅ Backend |
| `variance_value` | `counted_value - expected_value` | ✅ Backend |
| `display_full_units` | `floor(servings / uom)` | ✅ Backend |
| `display_partial_units` | `servings % uom` (with rounding) | ✅ Backend |

---

**END OF FORMULAS REFERENCE**
