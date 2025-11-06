# Your Current Keg Inventory - Quick Reference

Based on `marko_stock_cleaned.csv` as of October 31, 2025

---

## 📊 Keg Size Breakdown

### 20L Kegs (1 brand)
| SKU | Brand | UOM | Pints | Half-Pints |
|-----|-------|-----|-------|------------|
| D2133 | Heineken 00% | 35 | 35.2 | 70.4 |

---

### 30L Kegs (11 brands) ⭐ MOST COMMON
| SKU | Brand | UOM | Pints | Half-Pints | Cost |
|-----|-------|-----|-------|------------|------|
| D0007 | Beamish | 53 | 52.8 | 105.6 | €92.08 |
| D1004 | Coors | 53 | 52.8 | 105.6 | €117.70 |
| D0004 | Heineken | 53 | 52.8 | 105.6 | €117.70 |
| D0012 | Killarney Blonde | 53 | 52.8 | 105.6 | €119.70 |
| D0011 | Lagunitas IPA | 53 | 52.8 | 105.6 | €144.14 |
| D2354 | Moretti | 53 | 52.8 | 105.6 | €133.15 |
| D1003 | Murphys | 53 | 52.8 | 105.6 | €112.34 |
| D0008 | Murphys Red | 53 | 52.8 | 105.6 | €114.68 |
| D1022 | Orchards | 53 | 52.8 | 105.6 | €116.75 |
| D0006 | OT Wild Orchard | 53 | 52.8 | 105.6 | €116.75 |

**Note:** UOM shows 53 because the CSV uses a different calculation method. Backend now correctly calculates 52.8 pints (30,000ml ÷ 568ml).

---

### 50L Kegs (3 brands) - High Volume
| SKU | Brand | UOM | Pints | Half-Pints | Cost |
|-----|-------|-----|-------|------------|------|
| D1258 | Coors | 88 | 88.0 | 176.0 | €196.14 |
| D0005 | Guinness | 88 | 88.0 | 176.0 | €186.51 |
| D0030 | Heineken | 88 | 88.0 | 176.0 | €196.14 |

---

## 🔑 Key Insights

### Size Distribution
- **20L:** 1 brand (6.7%)
- **30L:** 11 brands (73.3%) ⭐ **MAIN SIZE**
- **50L:** 3 brands (20%)

### Same Beer, Different Sizes
You stock some beers in **multiple keg sizes**:

| Brand | 20L SKU | 30L SKU | 50L SKU |
|-------|---------|---------|---------|
| **Heineken** | D2133 (00% only) | D0004 | D0030 |
| **Coors** | - | D1004 | D1258 |

### Why Separate SKUs?
Each size is a **different product** because:
1. **Different cost** (€117.70 for 30L vs €196.14 for 50L Heineken)
2. **Different yield** (52.8 vs 88.0 pints)
3. **Different ordering** (you may order 30L or 50L based on demand)
4. **Different storage** (50L kegs are heavier, need different handling)

---

## 💡 Recommended Approach

### ✅ Current System (Best Practice)
**Create separate stock items for each size**

**Example: Heineken**
```
Stock Item 1:
- SKU: D0004
- Name: "Heineken 30L"
- Size: 30L
- Pints: 52.8
- Cost: €117.70

Stock Item 2:
- SKU: D0030
- Name: "Heineken 50L"
- Size: 50L
- Pints: 88.0
- Cost: €196.14
```

**Benefits:**
- ✅ Accurate inventory tracking per size
- ✅ Different costs properly recorded
- ✅ Easy to see which size is in stock
- ✅ Separate par levels for each size
- ✅ Clear stocktake counting (2× 30L kegs vs 1× 50L keg)
- ✅ Better analytics (which size sells faster?)

---

## 🎯 Frontend Display Recommendations

### Product List View
```
┌─────────────────────────────────────┐
│ Heineken 30L Keg                    │
│ SKU: D0004                          │
│ Yield: 52.8 pints (105.6 half)     │
│ Cost: €117.70                       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Heineken 50L Keg                    │
│ SKU: D0030                          │
│ Yield: 88.0 pints (176.0 half)     │
│ Cost: €196.14                       │
└─────────────────────────────────────┘
```

### Filter/Group by Brand
Allow users to see all sizes of the same brand:
```
HEINEKEN
├─ Heineken 00% 20L (D2133) - €59.72
├─ Heineken 30L (D0004) - €117.70
└─ Heineken 50L (D0030) - €196.14
```

### Size Selector (Optional Feature)
If you want to add convenience, create a "variant" view:
```tsx
<ProductCard>
  <h3>Heineken</h3>
  <SizeSelector>
    <option value="D2133">20L - €59.72 (35.2 pints)</option>
    <option value="D0004">30L - €117.70 (52.8 pints)</option>
    <option value="D0030">50L - €196.14 (88.0 pints)</option>
  </SizeSelector>
</ProductCard>
```

But in the database, they remain **separate items**.

---

## 📦 Ordering Workflow

### When ordering kegs:
1. Select the **specific SKU** (not just "Heineken")
2. System knows the size automatically from SKU
3. Cost is already set per size
4. Par levels are per size (e.g., keep 2× 30L, 1× 50L)

### Example Order:
```
Order for Friday:
- 3× Guinness 50L (D0005) @ €186.51 = €559.53
- 2× Coors 30L (D1004) @ €117.70 = €235.40
- 1× Heineken 30L (D0004) @ €117.70 = €117.70
Total: €912.63
```

---

## 🔄 Migration Notes

If you currently have generic "Heineken" items without size distinction:

### Step 1: Create size-specific items
```sql
-- Instead of one "Heineken" item
-- Create:
INSERT INTO stock_item (sku, name, size, size_value, size_unit, ...)
VALUES 
  ('D0004', 'Heineken 30L', '30L', 30, 'L', ...),
  ('D0030', 'Heineken 50L', '50L', 50, 'L', ...);
```

### Step 2: Move inventory
- Split current stock quantity to appropriate sizes
- Set separate par levels

### Step 3: Update frontend
- Display size in item name
- Show pints per keg
- Filter/sort by brand and size

---

## Summary

✅ **Keep separate SKUs for each keg size** (current approach is correct)
✅ **20L, 30L, and 50L are all supported**
✅ **30L is your most common size** (11 out of 15 keg products)
✅ **Backend automatically calculates pints for each size**
✅ **Frontend just displays the calculated values**

**No changes needed to backend - it's already perfect for your needs!**
