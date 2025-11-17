# 📊 INPUT COMPARISON: All Minerals Subcategories

## Quick Reference Table

| Subcategory | Full Field | Partial Field | Display | Logic Type |
|-------------|-----------|---------------|---------|------------|
| **SYRUPS** | Bottles (int) | Fraction (0-0.99) | "10.50 bottles" | Storage ✅ |
| **BIB** | Boxes (int) | Fraction (0-0.99) | "2.50 boxes" | Storage ✅ |
| **SOFT_DRINKS** | Cases (int) | Bottles (int) | "12 cases, 3 bottles" | Serving |
| **CORDIALS** | Cases (int) | Bottles (int) | "4 cases, 7 bottles" | Bottles only |
| **JUICES** | Cases (int) | Bottles.ml (decimal) | "59 cases, 8.50 bottles" | Serving |
| **BULK_JUICES** | Bottles (int) | Fraction (0-0.99) | "43.50 bottles" | Storage ✅ |

---

## Storage vs Serving Logic

### 🟢 STORAGE LOGIC (Simple)
**Used by:** SYRUPS, BIB, BULK_JUICES

```javascript
// Formula: (full + partial) × unit_cost
value = (full_units + partial_units) × unit_cost

// Examples:
SYRUPS:      10.5 bottles × €10.25 = €107.63
BIB:         2.5 boxes × €171.16 = €427.90
BULK_JUICES: 43.5 bottles × €3.60 = €156.60
```

### 🔵 SERVING LOGIC (Complex)
**Used by:** SOFT_DRINKS, JUICES

```javascript
// Convert to servings first, then value
servings = calculate_servings(full, partial, uom, serving_size)
value = servings × cost_per_serving
```

### 🟡 BOTTLES ONLY
**Used by:** CORDIALS

```javascript
// Just count total bottles (no servings)
total_bottles = (cases × 12) + bottles
```

---

## Detailed Comparison

### 1. SYRUPS (Storage)
```javascript
Input Fields:
  - Bottles: integer (0, 1, 2, ...)
  - Fraction: decimal (0.00 - 0.99)

Example Input:
  Bottles: 10
  Fraction: 0.50
  
Backend Storage:
  full_units: 10
  partial_units: 0.50
  
Display:
  "10.50 bottles"
  
Value Calculation:
  10.50 × €10.25 = €107.63
```

---

### 2. BIB (Storage) ⭐ SAME AS SYRUPS
```javascript
Input Fields:
  - Boxes: integer (0, 1, 2, ...)
  - Fraction: decimal (0.00 - 0.99)

Example Input:
  Boxes: 2
  Fraction: 0.50
  
Backend Storage:
  full_units: 2
  partial_units: 0.50
  
Display:
  "2.50 boxes"
  
Value Calculation:
  2.50 × €171.16 = €427.90
```

---

### 3. SOFT_DRINKS (Serving)
```javascript
Input Fields:
  - Cases: integer
  - Bottles: integer (whole bottles only)

Example Input:
  Cases: 12
  Bottles: 3
  
Backend Storage:
  full_units: 12
  partial_units: 3
  
Display:
  "12 cases, 3 bottles"
  = 147 bottles
  = 147 servings
  
Value Calculation:
  147 servings × cost_per_serving
```

---

### 4. CORDIALS (Bottles Only)
```javascript
Input Fields:
  - Cases: integer
  - Bottles: integer

Example Input:
  Cases: 4
  Bottles: 7
  
Backend Storage:
  full_units: 4
  partial_units: 7
  
Display:
  "4 cases, 7 bottles"
  = 55 total bottles
  
Value Calculation:
  Uses bottles, not servings
```

---

### 5. JUICES (Serving + 3-Level)
```javascript
Input Fields:
  - Cases: integer
  - Bottles: decimal (can include ml as .xx)

Example Input:
  Cases: 59
  Bottles: 8.50  (8 bottles + 500ml)
  
Backend Storage:
  full_units: 59
  partial_units: 8.50
  
Display:
  "59 cases, 8.50 bottles"
  
Value Calculation:
  Convert to servings → servings × cost_per_serving
```

---

### 6. BULK_JUICES (Storage)
```javascript
Input Fields:
  - Bottles: integer
  - Partial: decimal (0.00 - 0.99)

Example Input:
  Bottles: 43
  Partial: 0.50
  
Backend Storage:
  full_units: 43
  partial_units: 0.50
  
Display:
  "43.50 bottles"
  
Value Calculation:
  43.50 × unit_cost
```

---

## Frontend Decision Tree

```
Is it SYRUPS, BIB, or BULK_JUICES?
  ├─ YES → Use STORAGE logic
  │         - Two fields: Full + Fraction (0-0.99)
  │         - Display as single decimal
  │         - Value = (full + partial) × unit_cost
  │
  └─ NO → Is it SOFT_DRINKS, JUICES, or CORDIALS?
            └─ YES → Use SERVING logic
                      - Two fields: Cases + Bottles
                      - Display separately
                      - Value uses servings
```

---

## Key Differences Summary

### Partial Field Type

| Subcategory | Partial Type | Max Value | Step | Purpose |
|-------------|-------------|-----------|------|---------|
| SYRUPS | Decimal | 0.99 | 0.01 | Bottle fraction |
| BIB | Decimal | 0.99 | 0.01 | Box fraction |
| BULK_JUICES | Decimal | 0.99 | 0.5 | Bottle fraction |
| SOFT_DRINKS | Integer | ~23 | 1 | Whole bottles |
| CORDIALS | Integer | ~11 | 1 | Whole bottles |
| JUICES | Decimal | No max | 0.01 | Bottles + ml |

---

## Value Calculation Methods

### Method 1: Storage (Unit Cost)
**Used by:** SYRUPS, BIB, BULK_JUICES

```javascript
value = (full + partial) × unit_cost
```

**Why:** These items are valued at wholesale/storage cost, not by serving

---

### Method 2: Serving (Cost Per Serving)
**Used by:** SOFT_DRINKS, JUICES

```javascript
servings = convert_to_servings(full, partial)
value = servings × cost_per_serving
```

**Why:** These items are sold by the glass/serving

---

### Method 3: Bottles Only
**Used by:** CORDIALS

```javascript
total_bottles = (full × 12) + partial
value = total_bottles × cost_per_bottle
```

**Why:** Cordials are sold by bottle, not serving

---

## Frontend Implementation Priority

### ✅ Already Implemented
- SOFT_DRINKS (cases + bottles)
- CORDIALS (cases + bottles)
- JUICES (cases + bottles with decimals)

### 🔄 Need Updates
- **SYRUPS**: Change to decimal input (currently may be wrong)
- **BIB**: Change from "Liters" to "Fraction"
- **BULK_JUICES**: Already correct (bottles + fraction)

---

## Testing Matrix

| Subcategory | Test Input | Expected Display | Expected Value |
|-------------|-----------|------------------|----------------|
| SYRUPS | 10.5 | "10.50 bottles" | 10.5 × unit_cost |
| BIB | 2.5 | "2.50 boxes" | 2.5 × unit_cost |
| SOFT_DRINKS | 12 + 3 | "12 cases, 3 bottles" | servings × cps |
| CORDIALS | 4 + 7 | "4 cases, 7 bottles" | 55 bottles |
| JUICES | 59 + 8.5 | "59 cases, 8.50 bottles" | servings × cps |
| BULK_JUICES | 43.5 | "43.50 bottles" | 43.5 × unit_cost |

*(cps = cost_per_serving)*

---

## 🎯 Bottom Line

**BIB = Same logic as SYRUPS**
- Two fields: Full + Fraction
- Fraction is 0-0.99 (decimal)
- Display as single number
- Value = (full + partial) × unit_cost
- NO liters, NO servings, NO conversions
