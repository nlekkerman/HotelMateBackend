# UOM Cheat Sheet - Quick Visual Reference

## Product Type Decision Tree

```
Is it liquid from a keg?
├─ YES → product_type: "Draught"
│         └─ Shows: pints_per_keg & half_pints_per_keg
│
└─ NO → Is it a spirit/liqueur bottle?
        ├─ YES → product_type: "Spirit" or "Liqueur"
        │         └─ Shows: shots_per_bottle
        │
        └─ NO → Is it bottled beer?
                ├─ YES → product_type: "Beer"
                │         └─ Shows: bottles per case
                │
                └─ NO → product_type: "Wine", "Soft Drink", etc.
                          └─ Shows: servings_per_unit
```

---

## Keg Size Reference (30L & 50L Focus)

### 30L Keg (Most Common) ⭐
```
┌────────────────────────────────┐
│   30 LITER KEG                 │
├────────────────────────────────┤
│   52.8 PINTS                   │
│   105.6 HALF-PINTS             │
├────────────────────────────────┤
│   Perfect for: Medium venues   │
│   Typical brands: Guinness,    │
│   Heineken, Coors, Murphy's    │
└────────────────────────────────┘
```

### 50L Keg (High Volume) ⭐
```
┌────────────────────────────────┐
│   50 LITER KEG                 │
├────────────────────────────────┤
│   88.0 PINTS                   │
│   176.0 HALF-PINTS             │
├────────────────────────────────┤
│   Perfect for: Busy bars,      │
│   events, high demand          │
│   Typical brands: Guinness,    │
│   Heineken, Coors              │
└────────────────────────────────┘
```

### 20L Keg (Small/Specialty) ⭐
```
┌────────────────────────────────┐
│   20 LITER KEG                 │
├────────────────────────────────┤
│   35.2 PINTS                   │
│   70.4 HALF-PINTS              │
├────────────────────────────────┤
│   Perfect for: Low volume,     │
│   specialty beers              │
│   Current: Heineken 00%        │
└────────────────────────────────┘
```

**Note:** Each keg size is a separate stock item with its own SKU!

---

## Spirit Bottle Reference

### 70cl Bottle (Standard) ⭐
```
┌────────────────────────────────┐
│   70cl (700ml) BOTTLE          │
├────────────────────────────────┤
│   25ml pour → 28 SHOTS         │
│   35ml pour → 20 SHOTS         │
├────────────────────────────────┤
│   Most common size for:        │
│   Vodka, Gin, Whiskey, Rum     │
└────────────────────────────────┘
```

### 1L Bottle (Large)
```
┌────────────────────────────────┐
│   1L (1000ml) BOTTLE           │
├────────────────────────────────┤
│   25ml pour → 40 SHOTS         │
│   35ml pour → 28 SHOTS         │
├────────────────────────────────┤
│   Common for: House spirits,   │
│   Baileys, high-volume items   │
└────────────────────────────────┘
```

---

## Bottled Beer Reference

### 330ml Bottle (Standard)
```
┌────────────────────────────────┐
│   330ml BOTTLE                 │
├────────────────────────────────┤
│   Case size: 12 or 24          │
│   Yield: 1 serving per bottle  │
├────────────────────────────────┤
│   Common brands: Heineken,     │
│   Corona, Budweiser            │
└────────────────────────────────┘
```

### 500ml Bottle (Large)
```
┌────────────────────────────────┐
│   500ml BOTTLE                 │
├────────────────────────────────┤
│   Case size: 12 or 24          │
│   Yield: 1 serving per bottle  │
├────────────────────────────────┤
│   Common brands: Craft beers,  │
│   Smithwicks, local brews      │
└────────────────────────────────┘
```

---

## UI Component Examples

### Draught Display
```tsx
// For 30L Keg
<div className="yield-badge">
  <span className="size">30L</span>
  <span className="yield">52.8 pints</span>
  <span className="alternative">(105.6 half-pints)</span>
</div>

// For 50L Keg
<div className="yield-badge">
  <span className="size">50L</span>
  <span className="yield">88.0 pints</span>
  <span className="alternative">(176.0 half-pints)</span>
</div>
```

### Spirit Display
```tsx
<div className="yield-badge">
  <span className="size">70cl</span>
  <span className="yield">28 shots</span>
  <span className="pour-size">(25ml pour)</span>
</div>
```

### Beer Display
```tsx
<div className="yield-badge">
  <span className="size">330ml</span>
  <span className="case-info">24/case</span>
</div>
```

---

## Color Coding Suggestion

```css
/* Product type colors */
.badge-draught {
  background: #FDB750; /* Amber/Beer color */
}

.badge-spirit {
  background: #8B4513; /* Brown/Whiskey color */
}

.badge-beer {
  background: #FFD700; /* Gold */
}

.badge-wine {
  background: #722F37; /* Wine red */
}
```

---

## Calculation Quick Reference

### Pints from Kegs
```
20L = 20,000ml ÷ 568ml = 35.2 pints
30L = 30,000ml ÷ 568ml = 52.8 pints ⭐
50L = 50,000ml ÷ 568ml = 88.0 pints ⭐
```

### Half-Pints from Kegs
```
Pints × 2 = Half-Pints
30L: 52.8 × 2 = 105.6 half-pints
50L: 88.0 × 2 = 176.0 half-pints
```

### Shots from Bottles
```
700ml ÷ 25ml = 28 shots (standard)
700ml ÷ 35ml = 20 shots (large pour)
1000ml ÷ 25ml = 40 shots
```

---

## Stocktake Display Examples

### Draught Count Display
```
╔════════════════════════════════╗
║ GUINNESS 30L                   ║
╠════════════════════════════════╣
║ Full Kegs:      [  2  ]        ║
║ Partial Pints:  [ 26.5 ]       ║
╠════════════════════════════════╣
║ Total: 132.1 pints             ║
╚════════════════════════════════╝
```

### Spirit Count Display
```
╔════════════════════════════════╗
║ SMIRNOFF VODKA 70cl            ║
╠════════════════════════════════╣
║ Full Bottles:   [  5  ]        ║
║ Partial Shots:  [ 15  ]        ║
╠════════════════════════════════╣
║ Total: 155 shots (3,875ml)     ║
╚════════════════════════════════╝
```

---

## Common Sizes in Your Excel Data

Based on `marko_stock_cleaned.csv`:

| Product | Size | Type | Yield |
|---------|------|------|-------|
| Heineken 00% | 20Lt | Draught | 35.2 pints |
| Beamish | 30Lt | Draught | 52.8 pints ⭐ |
| Coors | 30Lt | Draught | 52.8 pints ⭐ |
| Guinness | 50Lt | Draught | 88.0 pints ⭐ |
| Absolut Vodka | 70cl | Spirit | 28 shots |
| Bacardi | 1Lt | Spirit | 40 shots |
| Budweiser | 33cl | Beer | 12/case |
| Heineken | 330ml | Beer | 12/case |

---

## Error Handling

### Missing Data
```tsx
function displayYield(item: StockItem) {
  if (!item.pints_per_keg && !item.shots_per_bottle) {
    return <span className="text-muted">Yield not calculated</span>;
  }
  
  // Display logic...
}
```

### Zero Values
```tsx
if (item.pints_per_keg === 0) {
  return <Alert type="warning">Check keg size configuration</Alert>;
}
```

---

## Mobile Display (Compact)

```tsx
<div className="mobile-yield">
  {/* Draught */}
  <strong>30L</strong> → 52.8pt (105.6 ½pt)
  
  {/* Spirit */}
  <strong>70cl</strong> → 28 shots
  
  {/* Beer */}
  <strong>330ml</strong> → 24/case
</div>
```

---

## Summary

✅ **30L & 50L kegs are your main sizes**
✅ **Backend calculates everything - just display it**
✅ **Product type determines which yield to show**
✅ **Read-only fields - no manual entry needed**

**Print this page and keep it handy!** 📋
