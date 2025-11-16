# BULK_JUICES - New Subcategory for Individual Bottle Tracking

## What is BULK_JUICES?

**BULK_JUICES** is a new subcategory for juice/lemonade items that are:
- **NOT on the menu** (not sold individually)
- Only counted in **stocktakes** (bulk inventory tracking)
- Tracked as **individual bottles** (no cases, no ml fractions)

---

## Items in BULK_JUICES

Currently 3 items:
- **M0042**: Lemonade Red Nashs (1L bottles)
- **M0210**: Lemonade WhiteNashes (1L bottles)
- **M11**: Kulana Litre Juices (1L bottles)

---

## Backend Fields

### StockItem
```json
{
  "sku": "M0042",
  "name": "Lemonade Red Nashs",
  "category": "M",
  "subcategory": "BULK_JUICES",
  "size": "Ind",
  "uom": 1.00
}
```

### StocktakeLine
```json
{
  "item_sku": "M0042",
  "subcategory": "BULK_JUICES",
  "opening_display_full_units": "43",
  "opening_display_partial_units": "0",
  "counted_full_units": 40.00,
  "counted_partial_units": 0.00,
  "input_fields": {
    "full": {"name": "counted_full_units", "label": "Bottles"},
    "partial": null
  }
}
```

---

## Frontend Implementation

### 1. Input Fields

**Show TWO fields for bottles + partial:**
```tsx
{item.subcategory === 'BULK_JUICES' && (
  <>
    <Input
      label="Bottles"
      name="counted_full_units"
      type="number"
      min={0}
      step={1}
    />
    <Input
      label="Partial (e.g., 0.5)"
      name="counted_partial_units"
      type="number"
      min={0}
      max={0.99}
      step={0.5}
    />
  </>
)}
```

### 2. Display Values

**Opening/Counted/Expected:**
```tsx
// Display only full_units (bottles)
<div>
  {opening_display_full_units} bottles
  // Don't show partial_units (always 0)
</div>
```

**Example:**
- Opening: "43 bottles, 0.5 partial" or just "43.5 bottles"
- Counted: "40 bottles, 0 partial" or just "40 bottles"
- Variance: "-3.5 bottles"

### 3. Update Payload

**When user enters counted stock:**
```javascript
// User enters: 40 bottles + 0.5 partial
{
  "counted_full_units": 40,
  "counted_partial_units": 0.5
}
```

---

## Key Differences from Other Subcategories

| Subcategory | Full Unit | Partial Unit | Display |
|-------------|-----------|--------------|---------|
| SOFT_DRINKS | Cases | Bottles (0-11) | "5 cases, 3 bottles" |
| SYRUPS | Bottles | ml (0-999) | "10 bottles, 500ml" |
| JUICES | Cases | Bottles w/decimal | "9 cases, 7.2 bottles" |
| CORDIALS | Cases | Bottles | "12 cases, 5 bottles" |
| BIB | Boxes | Liters | "3 boxes, 4.5 liters" |
| **BULK_JUICES** | **Bottles** | **None** | **"43 bottles"** |

---

## No Serving Calculations

BULK_JUICES items are NOT on the menu, so:
- ❌ No serving size conversion
- ❌ No ml tracking
- ❌ No menu pricing
- ✅ Just track bottles: 40 bottles = 40 units

---

## Validation Rules

### Frontend
```javascript
if (item.subcategory === 'BULK_JUICES') {
  // Only validate full_units (bottles)
  if (counted_full_units < 0) {
    return "Bottles cannot be negative";
  }
  if (!Number.isInteger(counted_full_units)) {
    return "Bottles must be whole numbers";
  }
}
```

### Backend
- `counted_full_units`: Integer >= 0 (bottles)
- `counted_partial_units`: Ignored (always 0)
- `opening_qty`: Equals bottle count (no conversion)

---

## Example API Response

### GET /api/stocktake-lines/{id}/

```json
{
  "id": 1523,
  "item_sku": "M0042",
  "item_name": "Lemonade Red Nashs",
  "category_code": "M",
  "subcategory": "BULK_JUICES",
  "item_size": "Ind",
  "item_uom": "1.00",
  
  "opening_qty": "43.0000",
  "opening_display_full_units": "43",
  "opening_display_partial_units": "0",
  
  "counted_full_units": "40.00",
  "counted_partial_units": "0.00",
  "counted_display_full_units": "40",
  "counted_display_partial_units": "0",
  
  "expected_qty": "43.0000",
  "counted_qty": "40.0000",
  "variance_qty": "-3.0000",
  
  "expected_display_full_units": "43",
  "variance_display_full_units": "-3",
  
  "input_fields": {
    "full": {"name": "counted_full_units", "label": "Bottles"},
    "partial": null
  }
}
```

---

## UI Components Update Checklist

### ✅ StocktakeLine Input Component
- [ ] Check `subcategory === 'BULK_JUICES'`
- [ ] Show single input field: "Bottles"
- [ ] Hide partial units field
- [ ] Validate whole numbers only

### ✅ Display Components
- [ ] Opening Stock: Show bottles only
- [ ] Counted Stock: Show bottles only
- [ ] Expected Stock: Show bottles only
- [ ] Variance: Show bottle difference (e.g., "-3 bottles")

### ✅ Forms
- [ ] Update payload builder to handle BULK_JUICES
- [ ] Only send `counted_full_units` (no partial)

---

## Migration Impact

✅ **No database migration needed** - items already exist, just changed:
- `subcategory`: JUICES → BULK_JUICES
- `size`: Doz → Ind
- `uom`: 12 → 1

✅ **Stocktake re-population required** to recalculate opening values with new logic.

---

## Testing

Test cases for BULK_JUICES:

1. **Display opening stock**: Should show "43 bottles" (not "800 cases")
2. **Enter counted stock**: 40 → Should save as 40 bottles
3. **Calculate variance**: 43 - 40 = -3 bottles
4. **Closing stock**: Should save as 40 bottles for next period
5. **Next period opening**: Should automatically be 40 bottles

---

## Questions?

BULK_JUICES = Simple bottle counting for non-menu items. No cases, no ml, just bottles! 🍋
