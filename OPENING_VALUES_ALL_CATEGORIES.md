# 📊 Opening Values: All Categories - Input & Calculation Guide

## Overview

**Opening values** come from `StockItem.current_full_units` and `current_partial_units`.  
These represent **what's in stock right now** before the stocktake begins.

---

## 1️⃣ MINERALS (M) - 5 Subcategories

### SOFT_DRINKS
**Storage:** Cases + Bottles  
**Serving:** 1 bottle = 1 serving

```python
# What gets sent:
current_full_units = 10      # cases
current_partial_units = 5    # bottles (0-11)
uom = 12                     # bottles per case

# Calculation:
servings = (10 × 12) + 5 = 125 bottles
```

**User enters:**
- Cases: `10`
- Bottles: `5`

**Display:** `"10 cases, 5 bottles" = 125 servings`

---

### SYRUPS
**Storage:** Bottles + ml  
**Serving:** 35ml per serving

```python
# What gets sent:
current_full_units = 3       # bottles
current_partial_units = 250  # ml
uom = 1000                   # ml per bottle

# Calculation:
total_ml = (3 × 1000) + 250 = 3,250ml
servings = 3,250 ÷ 35 = 92.86 servings
```

**User enters:**
- Bottles: `3`
- ml: `250`

**Display:** `"3 bottles, 250ml" = 92.86 servings`

---

### JUICES ✨ (3-Level Tracking)
**Storage:** Cases + Bottles (with decimal)  
**Serving:** 200ml per serving

```python
# What gets sent:
current_full_units = 59      # cases
current_partial_units = 8.008 # bottles (decimal = ml)
uom = 1000                    # ml per bottle

# Calculation:
cases = 59
bottles_decimal = 8.008
full_bottles = int(8.008) = 8
ml = (8.008 - 8) × 1000 = 8ml

total_ml = (59 × 12 × 1000) + (8 × 1000) + 8
         = 708,000 + 8,000 + 8
         = 716,008ml
servings = 716,008 ÷ 200 = 3,580.04 servings
```

**User enters (Option 1):**
- Cases: `59`
- Bottles: `8.008` (decimal allowed)

**User enters (Option 2):**
- Total Bottles: `716.008`
- Auto-converts to: `59 cases + 8.008 bottles`

**Display:** `"59 cases, 8.008 bottles" = 3,580.04 servings`

---

### CORDIALS
**Storage:** Cases + Bottles  
**Serving:** 1 bottle = 1 unit (no serving conversion)

```python
# What gets sent:
current_full_units = 4       # cases
current_partial_units = 7    # bottles
uom = 12                     # bottles per case

# Calculation:
bottles = (4 × 12) + 7 = 55 bottles
```

**User enters:**
- Cases: `4`
- Bottles: `7`

**Display:** `"4 cases, 7 bottles" = 55 bottles`

---

### BIB (Bag-in-Box)
**Storage:** Boxes + Liters  
**Serving:** 200ml (0.2L) per serving

```python
# What gets sent:
current_full_units = 2       # boxes
current_partial_units = 5.5  # liters
uom = 18                     # liters per box

# Calculation:
total_liters = (2 × 18) + 5.5 = 41.5 liters
servings = 41.5 ÷ 0.2 = 207.5 servings
```

**User enters:**
- Boxes: `2`
- Liters: `5.5`

**Display:** `"2 boxes, 5.5 liters" = 207.5 servings`

---

## 2️⃣ DRAUGHT (D)

**Storage:** Kegs + Pints  
**Serving:** 1 pint = 1 serving

```python
# What gets sent:
current_full_units = 3       # kegs
current_partial_units = 12   # pints
uom = 88                     # pints per keg

# Calculation:
servings = (3 × 88) + 12 = 276 pints
```

**User enters:**
- Kegs: `3`
- Pints: `12`

**Display:** `"3 kegs, 12 pints" = 276 pints`

---

## 3️⃣ BOTTLED BEER (B)

**Storage:** Cases + Bottles  
**Serving:** 1 bottle = 1 serving

```python
# What gets sent:
current_full_units = 8       # cases
current_partial_units = 10   # bottles
uom = 12                     # bottles per case

# Calculation:
servings = (8 × 12) + 10 = 106 bottles
```

**User enters:**
- Cases: `8`
- Bottles: `10`

**Display:** `"8 cases, 10 bottles" = 106 bottles`

---

## 4️⃣ SPIRITS (S)

**Storage:** Bottles + Fractional  
**Serving:** Shots (calculated from bottle ml ÷ 25ml)

```python
# What gets sent:
current_full_units = 5       # bottles
current_partial_units = 0.75 # fractional (75% of bottle)
uom = 28                     # shots per bottle (700ml ÷ 25ml)

# Calculation:
full_shots = 5 × 28 = 140
partial_shots = 0.75 × 28 = 21
servings = 140 + 21 = 161 shots
```

**User enters:**
- Bottles: `5`
- Fractional: `0.75` (or 75%)

**Display:** `"5.75 bottles" = 161 shots`

---

## 5️⃣ WINE (W)

**Storage:** Bottles + Fractional  
**Serving:** Glasses (calculated from bottle ml ÷ 175ml)

```python
# What gets sent:
current_full_units = 12      # bottles
current_partial_units = 0.5  # fractional (50% of bottle)
uom = 4                      # glasses per bottle (750ml ÷ 175ml)

# Calculation:
full_glasses = 12 × 4 = 48
partial_glasses = 0.5 × 4 = 2
servings = 48 + 2 = 50 glasses
```

**User enters:**
- Bottles: `12`
- Fractional: `0.5` (or 50%)

**Display:** `"12.5 bottles" = 50 glasses`

---

## Summary Table

| Category | Full Unit | Partial Unit | Serving Size | Display Format |
|----------|-----------|--------------|--------------|----------------|
| **Soft Drinks** | Cases | Bottles (0-11) | 1 bottle | "X cases, Y bottles" |
| **Syrups** | Bottles | ml | 35ml | "X bottles, Yml" |
| **Juices** | Cases | Bottles (decimal) | 200ml | "X cases, Y.ZZ bottles" |
| **Cordials** | Cases | Bottles | 1 bottle | "X cases, Y bottles" |
| **BIB** | Boxes | Liters | 0.2L (200ml) | "X boxes, Y liters" |
| **Draught** | Kegs | Pints | 1 pint | "X kegs, Y pints" |
| **Bottled** | Cases | Bottles | 1 bottle | "X cases, Y bottles" |
| **Spirits** | Bottles | Fractional | 25ml shot | "X.YZ bottles" |
| **Wine** | Bottles | Fractional | 175ml glass | "X.YZ bottles" |

---

## Frontend Implementation

### Input Fields by Category

```javascript
// SOFT_DRINKS, CORDIALS, BOTTLED, DRAUGHT
<Input label="Cases/Kegs" name="current_full_units" type="number" step="1" />
<Input label="Bottles/Pints" name="current_partial_units" type="number" step="1" />

// SYRUPS
<Input label="Bottles" name="current_full_units" type="number" step="1" />
<Input label="ml" name="current_partial_units" type="number" step="1" />

// JUICES (special!)
<Input label="Cases" name="current_full_units" type="number" step="1" />
<Input label="Bottles" name="current_partial_units" type="number" step="0.001" />
// Allow decimals like 8.008

// BIB
<Input label="Boxes" name="current_full_units" type="number" step="1" />
<Input label="Liters" name="current_partial_units" type="number" step="0.1" />

// SPIRITS, WINE
<Input label="Bottles" name="current_full_units" type="number" step="1" />
<Input label="Fractional" name="current_partial_units" type="number" step="0.01" min="0" max="0.99" />
```

---

## API Response Example

```json
{
  "item_code": "M0042",
  "name": "Lemonade Red Nashs",
  "category": "M",
  "subcategory": "JUICES",
  "current_full_units": 59,        // cases
  "current_partial_units": 8.008,  // bottles (decimal)
  "uom": 1000,                      // ml per bottle
  "total_stock_in_servings": 3580.04,
  "display": "59 cases, 8.008 bottles"
}
```

---

## Key Points

✅ **Opening values** = `current_full_units` + `current_partial_units`  
✅ **Each category** has specific units and serving calculations  
✅ **JUICES special:** Uses decimal bottles to represent 3 levels (cases + bottles + ml)  
✅ **Backend handles all conversions** - frontend just sends the numbers  
✅ **Display format** matches user input format for clarity  

---

## Testing Opening Values

```python
# Test script to verify opening calculations
from stock_tracker.models import StockItem

# Test JUICES opening
item = StockItem.objects.get(item_code='M0042')
print(f"Opening: {item.current_full_units} cases, {item.current_partial_units} bottles")
print(f"Servings: {item.total_stock_in_servings}")

# Expected: 59 cases, 8.008 bottles = 3,580.04 servings
```
