# 🆕 NEW SUBCATEGORY: BULK_JUICES - Frontend Changes Required

## What Changed?

Added new subcategory **BULK_JUICES** for lemonade/juice items tracked as individual bottles (not on menu).

---

## Affected Items (3 total)

- **M0042**: Lemonade Red Nashs
- **M0210**: Lemonade WhiteNashes
- **M11**: Kulana Litre Juices

---

## Frontend Implementation

### 1. Input Fields - Show 2 fields:

```jsx
{item.subcategory === 'BULK_JUICES' && (
  <>
    <Input 
      label="Bottles" 
      name="counted_full_units"
      type="number"
      step={1}
    />
    <Input 
      label="Partial" 
      name="counted_partial_units"
      type="number"
      step={0.5}
      max={0.99}
      placeholder="0.5 for half bottle"
    />
  </>
)}
```

### 2. Display Format

**Change label from "Servings" to "Bottles":**

```jsx
// Opening/Counted/Variance display
{item.subcategory === 'BULK_JUICES' 
  ? `${full} bottles${partial > 0 ? `, ${partial} partial` : ''}`
  : `${servings} servings`
}
```

**Example displays:**
- Opening: `138 bottles`
- Counted: `117 bottles` 
- Variance: `-21 bottles`
- With partial: `43 bottles, 0.5 partial`

### 3. API Response Example

```json
{
  "item_sku": "M11",
  "subcategory": "BULK_JUICES",
  "opening_display_full_units": "138",
  "opening_display_partial_units": "0",
  "counted_full_units": 117.00,
  "counted_partial_units": 0.00,
  "variance_qty": "-21.0000",
  "input_fields": {
    "full": {"name": "counted_full_units", "label": "Bottles"},
    "partial": {"name": "counted_partial_units", "label": "Partial", "max": 0.99, "step": 0.5}
  }
}
```

---

## Key Differences from Other Subcategories

| Field | BULK_JUICES | Other Subcategories |
|-------|-------------|---------------------|
| **Full Unit** | Whole bottles | Cases/Kegs/Bottles |
| **Partial Unit** | Fractional bottle (0.5) | Bottles/Pints/ml |
| **Display Label** | "bottles" | "servings" |
| **Use Case** | Inventory only (NOT on menu) | Menu items |

---

## UI Changes Checklist

### ✅ Input Component
- [ ] Add BULK_JUICES condition to show bottle + partial fields
- [ ] Set step=0.5 for partial field (for half bottles)

### ✅ Display Component  
- [ ] Change "Servings" label to "Bottles" for BULK_JUICES
- [ ] Format: "X bottles" or "X bottles, 0.5 partial"
- [ ] Apply to: Opening, Counted, Expected, Variance

### ✅ Variance Display
- [ ] Show variance as bottles (e.g., "-21 bottles")
- [ ] NOT as servings

---

## Important Notes

⚠️ **"Servings" = "Bottles" for BULK_JUICES**  
The backend stores it as "servings" but it means bottles (1 bottle = 1 unit).

✅ **No serving size conversion**  
Unlike JUICES (200ml servings), BULK_JUICES just counts bottles as-is.

✅ **Partial = fractional bottles**  
0.5 = half bottle, 0.25 = quarter bottle, etc.

---

## Testing

Test with these items:
- M0042 (Lemonade Red Nashs)
- M0210 (Lemonade WhiteNashes)  
- M11 (Kulana Litre Juices)

Expected behavior:
1. Input shows "Bottles" + "Partial" fields
2. Display shows "X bottles" (not servings)
3. Can enter whole bottles (43) or with partial (43.5)
4. Variance displays as bottle difference

---

## Questions?

Contact backend team or check `BULK_JUICES_FRONTEND_GUIDE.md` for full details.
