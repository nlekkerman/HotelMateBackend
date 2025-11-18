# 🧪 SYRUPS - Frontend Display Guide

## Overview
Syrups are **STORAGE ONLY** items - we track **BOTTLES**, not servings.

---

## ✅ What to Display

### Input Fields
```
Bottles: [____]  (whole number)
Partial: [____]  (0.00 - 0.99 decimal)
```

**Example user input:**
- Bottles: `4`
- Partial: `0.50`
- Result: `4.5 bottles`

---

### Display Format

**Opening Stock:**
```
4.5 bottles
Value: €41.98
```

**Counted:**
```
4.5 bottles  
Value: €41.98
```

**Variance:**
```
+2.5 bottles
+€23.33
```

---

## ❌ What NOT to Display

**DON'T show:**
- ❌ Servings
- ❌ Shots
- ❌ "128.57 servings"
- ❌ ml conversions

**Why?**
Servings (35ml shots) are used internally for **consumption tracking**, but syrups are **valued and displayed as BOTTLES**.

---

## 📊 Complete Example

```jsx
// Syrup stocktake line display
{
  sku: "M0006",
  name: "Monin Chocolate Cookie LTR",
  subcategory: "SYRUPS",
  
  // Opening
  opening_display_full_units: "4",      // bottles
  opening_display_partial_units: "0.50", // partial bottle
  opening_value: "41.98",               // €
  
  // Display as:
  "Opening: 4.5 bottles (€41.98)"
  
  // Counted
  counted_full_units: 4,
  counted_partial_units: 0.5,
  counted_value: "41.98",
  
  // Display as:
  "Counted: 4.5 bottles (€41.98)"
  
  // Variance
  variance_display_full_units: "0",
  variance_display_partial_units: "0.00",
  variance_value: "0.00",
  
  // Display as:
  "Variance: 0 bottles (€0.00)"
}
```

---

## 🎨 UI Component Logic

```jsx
if (item.subcategory === 'SYRUPS') {
  // Input: Bottles + Partial (decimal)
  return (
    <>
      <label>Bottles</label>
      <input type="number" step="1" min="0" />
      
      <label>Partial</label>
      <input type="number" step="0.01" min="0" max="0.99" />
    </>
  );
}

// Display
if (item.subcategory === 'SYRUPS') {
  const total = full + partial;
  return (
    <div>
      <span>{total.toFixed(2)} bottles</span>
      <span>€{value}</span>
    </div>
  );
}

// Variance display
if (item.subcategory === 'SYRUPS') {
  const variance = variance_full + variance_partial;
  const sign = variance >= 0 ? '+' : '';
  
  return (
    <div>
      <span>{sign}{variance.toFixed(2)} bottles</span>
      <span>{sign}€{variance_value}</span>
    </div>
  );
}
```

---

## 📋 Summary Table

| Field | Unit | Display |
|-------|------|---------|
| Opening | Bottles | "4.5 bottles" |
| Counted | Bottles | "4.5 bottles" |
| Expected | Bottles | "4.5 bottles" |
| Variance | Bottles | "+2.5 bottles" |
| Value | EUR | "€41.98" |

---

## 🔑 Key Points

1. **Input**: Bottles (integer) + Partial (0-0.99 decimal)
2. **Display**: `X.XX bottles` (NOT servings)
3. **Value**: Bottles × Cost per bottle
4. **Variance**: Show as bottle difference
5. **Same logic as**: Spirits, Wine (bottles + fractional)

---

## ⚠️ Important

**Backend sends:**
- `counted_qty` = servings (internal calculation)
- `counted_value` = bottles × unit_cost ✓

**Frontend should:**
- **Ignore** `counted_qty` for display
- **Use** `counted_full_units` + `counted_partial_units`
- **Display** as bottles
- **Show** `counted_value` as value

---

## 🧪 Example API Response

```json
{
  "item_sku": "M0006",
  "item_name": "Monin Chocolate Cookie LTR",
  "subcategory": "SYRUPS",
  "item_size": "Ind",
  "item_uom": "1000.00",
  
  "counted_full_units": "4.00",
  "counted_partial_units": "0.50",
  "counted_qty": "128.5714",        // ← IGNORE (internal)
  "counted_value": "41.98",         // ← USE THIS
  
  "counted_display_full_units": "4",
  "counted_display_partial_units": "0.50",
  
  "variance_display_full_units": "0",
  "variance_display_partial_units": "0.00",
  "variance_value": "0.00"
}
```

**Display:**
```
Opening: 4.5 bottles (€41.98)
Counted: 4.5 bottles (€41.98)
Variance: 0 bottles (€0.00)
```

---

## ✅ Checklist

- [ ] Input shows: Bottles + Partial fields
- [ ] Display shows: "X.XX bottles" (not servings)
- [ ] Value shows: €XX.XX (bottle value)
- [ ] Variance shows: "+X.XX bottles" 
- [ ] NO mention of servings/shots/ml in UI
