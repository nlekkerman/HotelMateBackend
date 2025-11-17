# ✓ SYRUPS FIX COMPLETE

## Problem Identified
Syrups and mixer juices (Monin, Teisseire, Grenadine, etc.) are **NOT sold individually** - they're used as ingredients in cocktails. They should be counted as **individual bottles** using a single decimal input (e.g., 10.5 bottles), not with separate "bottles + ml" fields.

## Changes Made

### 1. Model Storage (Already Correct)
- **Subcategory**: `SYRUPS`
- **UOM**: Bottle size in ml (700ml or 1000ml)
- **Stock Storage**:
  - `current_full_units`: Whole bottles (e.g., 10)
  - `current_partial_units`: Decimal fraction (e.g., 0.5 for half a bottle)
  - User enters: **10.5 bottles** → Stored as: full=10, partial=0.5

### 2. Serializer Input Validation ✓ FIXED
**Before:**
```python
'SYRUPS': {
    'full': {'name': 'counted_full_units', 'label': 'Bottles'},
    'partial': {'name': 'counted_partial_units', 'label': 'ml', 'max': 1000}
}
```

**After:**
```python
'SYRUPS': {
    'full': {'name': 'counted_full_units', 'label': None},
    'partial': {'name': 'counted_partial_units', 'label': 'Total Bottles', 'step': 0.01}
}
```

### 3. UOM Values Fixed ✓
All syrups now have correct UOM values:
- **700ml bottles**: Monin syrups, Mixer juices, Grenadine, Teisseire
- **1000ml bottles**: Monin purees, large format syrups

## Items Affected (17 SYRUPS)

| SKU | Name | UOM | Stock Type |
|-----|------|-----|------------|
| M0008 | Mixer Lemon Juice 700ML | 700ml | Individual bottle |
| M0009 | Mixer Lime Juice 700ML | 700ml | Individual bottle |
| M3 | Monin Agave Syrup 700ml | 700ml | Individual bottle |
| M0006 | Monin Chocolate Cookie LTR | 1000ml | Individual bottle |
| M13 | Monin Coconut Syrup 700ML | 700ml | Individual bottle |
| M04 | Monin Elderflower Syrup 700ML | 700ml | Individual bottle |
| M0014 | Monin Ginger Syrup | 700ml | Individual bottle |
| M2 | Monin Passionfruit Puree Ltr | 1000ml | Individual bottle |
| M03 | Monin Passionfruit Syrup 700ML | 700ml | Individual bottle |
| M05 | Monin Pink Grapefruit 700ML | 700ml | Individual bottle |
| M06 | Monin Puree Coconut LTR | 1000ml | Individual bottle |
| M1 | Monin Strawberry Puree Ltr | 1000ml | Individual bottle |
| M5 | Monin Strawberry Syrup 700ml | 700ml | Individual bottle |
| M9 | Monin Vanilla Syrup Ltr | 1000ml | Individual bottle |
| M02 | Monin Watermelon Syrup 700ML | 700ml | Individual bottle |
| M0320 | Grenadine Syrup | 700ml | Individual bottle |
| M0012 | Teisseire Bubble Gum | 700ml | Individual bottle |

## Items That REMAIN As Dozen (UOM = 12)

These ARE sold individually per bottle, so they stay as cases + bottles:
- All Splits (Sprite, Coke, 7UP, Fanta, etc.)
- Schweppes, Red Bull, Lucozade
- Appletiser, Fever-tree Tonics
- Any item with "Split" or "Doz" in size

## Frontend Behavior

### For SYRUPS (Monin, Mixer Juices, etc.)
**Input:** Single field - "Total Bottles"
- User enters: `10.5`
- Stored as: `counted_full_units=10, counted_partial_units=0.5`
- Display: "10.5 bottles"

### For SOFT_DRINKS (Splits, etc.)
**Input:** Two fields - "Cases" and "Bottles"
- User enters: Cases: `3`, Bottles: `7`
- Stored as: `counted_full_units=3, counted_partial_units=7`
- Display: "3 cases + 7 bottles"

## How Servings Are Calculated

**SYRUPS (35ml per serving):**
```
Total bottles: 10.5
Bottle size: 700ml
Total ml: 10.5 × 700ml = 7,350ml
Servings: 7,350ml ÷ 35ml = 210 servings
```

## Next Steps (If Needed)

1. **Frontend Update**: Ensure stocktake form shows single decimal input for SYRUPS
2. **Testing**: Verify stocktake entry works correctly with new validation
3. **Documentation**: Update user guide if needed
