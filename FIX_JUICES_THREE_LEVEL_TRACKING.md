# Fix: Juices Need 3-Level Tracking (Cases + Bottles + ml)

## Problem

**Current Implementation:**
```
JUICES: Bottles + ml → servings (200ml)
- counted_full_units = bottles
- counted_partial_units = ml
```

**Required Implementation:**
```
JUICES: Cases + Bottles + ml → servings (200ml)
- counted_cases = cases
- counted_bottles = bottles  
- counted_ml = ml
```

## Root Cause

The `StocktakeLine` model only has 2 fields for counting:
- `counted_full_units` (used for cases OR bottles)
- `counted_partial_units` (used for bottles OR ml)

**For JUICES to support Cases + Bottles + ml, we need 3 fields!**

## Solution Options

### Option 1: Add `counted_cases` field (RECOMMENDED)

Add a new field to `StocktakeLine`:

```python
class StocktakeLine(models.Model):
    # ... existing fields ...
    
    counted_cases = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        null=True,
        blank=True,
        help_text="Cases counted (for 3-level items like JUICES)"
    )
    
    # Then for JUICES:
    # counted_cases = cases
    # counted_full_units = bottles
    # counted_partial_units = ml
```

**Pros:**
- Clean, explicit field names
- Easy to understand
- Future-proof for other 3-level categories

**Cons:**
- Requires database migration
- Field is unused for most categories

### Option 2: Encode Cases into Bottles (CURRENT WORKAROUND)

Store total bottles in `counted_full_units`:

```python
# If user counts: 5 cases + 3 bottles + 250ml
# Store as: 63 bottles (5×12 + 3) + 250ml

counted_full_units = (cases × 12) + bottles  # = 63
counted_partial_units = ml  # = 250
```

**Pros:**
- No database migration needed
- Works with current 2-field structure

**Cons:**
- User can't see case count in UI
- Confusing display (shows 63 bottles instead of 5 cases + 3 bottles)
- Loss of information (can't reverse engineer exact case count)

## Recommended Implementation

### Step 1: Add Database Field

Create migration file: `stock_tracker/migrations/0022_add_counted_cases.py`

```python
from django.db import migrations, models
from decimal import Decimal

class Migration(migrations.Migration):
    dependencies = [
        ('stock_tracker', '0021_fix_minerals_uom'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocktakeline',
            name='counted_cases',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Cases counted (for 3-level items like JUICES)',
                max_digits=10,
                null=True
            ),
        ),
    ]
```

### Step 2: Update Model Logic

Update `StocktakeLine.counted_qty` property:

```python
elif self.item.subcategory == 'JUICES':
    # Cases + Bottles + ml → servings (200ml per serving)
    # counted_cases = cases (NEW!)
    # counted_full_units = bottles
    # counted_partial_units = ml
    
    # Calculate total bottles from cases
    bottles_from_cases = Decimal('0')
    if self.counted_cases:
        bottles_from_cases = self.counted_cases * Decimal('12')  # 12 bottles per case
    
    # Calculate total ml
    bottles_ml = (bottles_from_cases + self.counted_full_units) * self.item.uom
    total_ml = bottles_ml + self.counted_partial_units
    
    return total_ml / JUICE_SERVING_SIZE  # ml → servings
```

### Step 3: Update Serializer

Update `stock_serializers.py` to include `counted_cases`:

```python
class StocktakeLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StocktakeLine
        fields = [
            # ... existing fields ...
            'counted_cases',  # NEW
            'counted_full_units',
            'counted_partial_units',
            # ...
        ]
```

### Step 4: Update Display Logic

Update `_calculate_display_units()` in serializer:

```python
elif item.subcategory == 'JUICES':
    # servings → cases + bottles + ml
    total_ml = servings_decimal * JUICE_SERVING_SIZE
    uom = Decimal(str(item.uom))  # bottle size in ml
    
    # Calculate total bottles
    total_bottles = int(total_ml / uom)
    remaining_ml = int(total_ml % uom)
    
    # Split bottles into cases + loose bottles
    cases = int(total_bottles / 12)
    bottles = int(total_bottles % 12)
    
    # Return 3 values (need to extend return signature!)
    return {
        'cases': str(cases),
        'bottles': str(bottles),
        'ml': str(remaining_ml)
    }
```

### Step 5: Update Frontend

Frontend needs to show 3 input fields for JUICES:

```javascript
if (subcategory === 'JUICES') {
  return (
    <>
      <Input label="Cases" name="counted_cases" type="number" step="1" />
      <Input label="Bottles" name="counted_full_units" type="number" step="1" max="11" />
      <Input label="ml" name="counted_partial_units" type="number" step="1" />
    </>
  );
}
```

## Example Calculation

**Item:** Kulana 1L Juice (12 bottles per case)

**User Counts:**
- 5 cases
- 3 bottles
- 250ml (open bottle)

**Stored As:**
```python
counted_cases = 5
counted_full_units = 3  # loose bottles
counted_partial_units = 250  # ml
```

**Calculation:**
```python
# Total bottles = (5 cases × 12) + 3 bottles = 63 bottles
bottles_from_cases = 5 × 12 = 60
total_bottles = 60 + 3 = 63

# Total ml = 63 bottles × 1000ml + 250ml = 63,250ml
bottles_ml = 63 × 1000 = 63,000
total_ml = 63,000 + 250 = 63,250

# Servings = 63,250ml ÷ 200ml = 316.25 servings
servings = 63,250 ÷ 200 = 316.25
```

**Display:**
- Opening: 5 cases, 3 bottles, 250ml
- Expected: 5 cases, 3 bottles, 250ml  
- Counted: [user enters] 4 cases, 8 bottles, 100ml
- Variance: -1 case, +5 bottles, -150ml

## Alternative: Treat Juice Cases as SOFT_DRINKS

If all juices come in dozens (12-bottle cases), you could:

1. Change subcategory from `JUICES` to `SOFT_DRINKS` for dozen items
2. Keep `JUICES` only for individual bottles

This avoids the 3-field problem but may not match your business logic.

## Next Steps

1. **Decision:** Choose Option 1 (add field) or Option 2 (encode into bottles)
2. **If Option 1:** Create migration, update models, update serializers
3. **Update Frontend:** Add 3rd input field for JUICES
4. **Test:** Verify calculations with real data
5. **Update Documentation:** Reflect new 3-level structure

## Files to Update

If implementing Option 1:

1. `stock_tracker/models.py` - Add field, update `counted_qty` logic
2. `stock_tracker/migrations/0022_add_counted_cases.py` - New migration
3. `stock_tracker/stock_serializers.py` - Add field, update display logic
4. Frontend stocktake component - Add 3rd input field
5. `STOCKTAKE_LINES_FIELDS_EXPLAINED.md` - Update JUICES documentation

---

## Current vs Correct Behavior

**Current (WRONG):**
```
M0042 - Lemonade Red Nashs (Doz 12)
Opening: 716 bottles + 8ml  ← Should be cases!
Counted: 0 bottles + 16ml
```

**Correct (Option 1):**
```
M0042 - Lemonade Red Nashs (Doz 12)
Opening: 59 cases + 8 bottles + 8ml
Counted: 0 cases + 0 bottles + 16ml
```

**Correct (Option 2 - Workaround):**
```
M0042 - Lemonade Red Nashs (Doz 12)
Opening: 716 bottles + 8ml  ← Total bottles encoded
Counted: 0 bottles + 16ml
Note: 716 bottles = 59 cases + 8 bottles (calculated, not displayed)
```
