# Minerals & Syrups Implementation Plan

## Executive Summary

Based on your new categorization document and current system analysis, here's what needs to change in the Django backend and serializers to properly handle all 5 sub-categories of Minerals & Syrups.

---

## 1. Current System Issues

### Problem 1: Inconsistent UOM Values
**Current Data:**
- Soft Drinks (Doz): UOM = 12 ✅ **CORRECT**
- BIB (18LT): UOM = 500 ❌ **WRONG** (should be 18 or serving-based)
- Syrups: UOM = 19.70 or 1.00 ❌ **INCONSISTENT**
- Juices: UOM = 1.00 ❌ **NO SERVING LOGIC**

### Problem 2: Mixed Serving Logic
Current code treats category 'M' with 3 different rules:
1. **Dozen items**: `partial = bottles` (0-11) ✅
2. **BIB (LT)**: `partial = liters` ⚠️ (but should be servings?)
3. **Everything else**: `partial = fractional bottle` ⚠️ (ignores ml-based servings)

### Problem 3: No Sub-Category Field
All items are just "M - Minerals & Syrups". No way to distinguish:
- Soft Drinks vs Syrups vs Juices vs Cordials vs BIB

---

## 2. Recommended Database Changes

### Option A: Add Sub-Category Field (RECOMMENDED)
```python
class StockItem(models.Model):
    # ... existing fields ...
    
    # NEW FIELD
    subcategory = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('SOFT_DRINKS', 'Soft Drinks (Bottled)'),
            ('SYRUPS', 'Syrups & Flavourings'),
            ('JUICES', 'Juices & Lemonades'),
            ('CORDIALS', 'Cordials'),
            ('BIB', 'Bag-in-Box (18L)'),
        ],
        help_text="Sub-category for Minerals (M) items only"
    )
```

**Pros:**
- Clean, explicit categorization
- Easy to filter and query
- Frontend can show different input fields per subcategory
- Can validate UOM based on subcategory

**Cons:**
- Requires data migration to populate existing items
- Need admin interface to set subcategory

### Option B: Auto-Detect from Size/Name (NOT RECOMMENDED)
Your document says: "Do **not** auto‑detect by volume"

**Why?** Because detection logic gets messy and fragile.

---

## 3. Required Model Changes

### 3.1 StockItem Model

```python
@property
def total_stock_in_servings(self):
    """
    Convert stock to servings based on category/subcategory
    """
    category = self.category_id
    
    # Handle Minerals subcategories
    if category == 'M' and self.subcategory:
        if self.subcategory == 'SOFT_DRINKS':
            # Cases + Bottles → bottles
            # Full = cases, Partial = bottles (0-11)
            # UOM = 12 bottles/case
            return (self.current_full_units * self.uom) + self.current_partial_units
        
        elif self.subcategory == 'SYRUPS':
            # Bottles + ml → servings (25ml per serving)
            # Full = bottles, Partial = ml
            # UOM = bottle size in ml (700, 1000)
            # Serving size = 25ml
            SYRUP_SERVING_SIZE = Decimal('25')  # ml per serving
            
            full_ml = self.current_full_units * self.uom  # bottles → ml
            total_ml = full_ml + self.current_partial_units  # add partial ml
            return total_ml / SYRUP_SERVING_SIZE  # ml → servings
        
        elif self.subcategory == 'JUICES':
            # Cases + Bottles + ml → servings (200ml per serving)
            # Full = bottles, Partial = ml
            # UOM = bottle size in ml (1000, 1500)
            # Serving size = 200ml
            JUICE_SERVING_SIZE = Decimal('200')  # ml per serving
            
            full_ml = self.current_full_units * self.uom  # bottles → ml
            total_ml = full_ml + self.current_partial_units  # add partial ml
            return total_ml / JUICE_SERVING_SIZE  # ml → servings
        
        elif self.subcategory == 'CORDIALS':
            # Cases + Bottles → bottles (no servings)
            # Full = cases, Partial = bottles
            # UOM = 12 bottles/case
            return (self.current_full_units * self.uom) + self.current_partial_units
        
        elif self.subcategory == 'BIB':
            # Boxes + Liters → servings (200ml per serving)
            # Full = boxes, Partial = liters
            # UOM = 18 liters/box
            # Serving size = 200ml = 0.2 liters
            BIB_SERVING_SIZE = Decimal('0.2')  # liters per serving
            
            full_liters = self.current_full_units * self.uom  # boxes → liters
            total_liters = full_liters + self.current_partial_units  # add partial liters
            return total_liters / BIB_SERVING_SIZE  # liters → servings
    
    # ... existing logic for D, B, S, W categories ...
```

### 3.2 StocktakeLine Model

Same logic needs to be applied to `counted_qty` property:

```python
@property
def counted_qty(self):
    """
    Convert counted units to servings
    """
    category = self.item.category_id
    
    # Handle Minerals subcategories
    if category == 'M' and self.item.subcategory:
        if self.item.subcategory == 'SOFT_DRINKS':
            # counted_full_units = cases
            # counted_partial_units = bottles
            return (self.counted_full_units * self.item.uom) + self.counted_partial_units
        
        elif self.item.subcategory == 'SYRUPS':
            # counted_full_units = bottles
            # counted_partial_units = ml
            SYRUP_SERVING_SIZE = Decimal('25')
            full_ml = self.counted_full_units * self.item.uom
            total_ml = full_ml + self.counted_partial_units
            return total_ml / SYRUP_SERVING_SIZE
        
        elif self.item.subcategory == 'JUICES':
            # counted_full_units = bottles
            # counted_partial_units = ml
            JUICE_SERVING_SIZE = Decimal('200')
            full_ml = self.counted_full_units * self.item.uom
            total_ml = full_ml + self.counted_partial_units
            return total_ml / JUICE_SERVING_SIZE
        
        elif self.item.subcategory == 'CORDIALS':
            # counted_full_units = cases
            # counted_partial_units = bottles
            return (self.counted_full_units * self.item.uom) + self.counted_partial_units
        
        elif self.item.subcategory == 'BIB':
            # counted_full_units = boxes
            # counted_partial_units = liters
            BIB_SERVING_SIZE = Decimal('0.2')
            full_liters = self.counted_full_units * self.item.uom
            total_liters = full_liters + self.counted_partial_units
            return total_liters / BIB_SERVING_SIZE
    
    # ... existing logic ...
```

---

## 4. Serializer Changes

### 4.1 StockItemSerializer

Add subcategory field:

```python
class StockItemSerializer(serializers.ModelSerializer):
    # ... existing fields ...
    
    subcategory = serializers.CharField(read_only=True)
    subcategory_display = serializers.SerializerMethodField()
    
    def get_subcategory_display(self, obj):
        if obj.subcategory:
            return obj.get_subcategory_display()
        return None
```

### 4.2 StocktakeLineSerializer

Add display helpers for UI input fields:

```python
class StocktakeLineSerializer(serializers.ModelSerializer):
    # ... existing fields ...
    
    # Add subcategory info
    subcategory = serializers.CharField(source='item.subcategory', read_only=True)
    
    # Add UI helper fields
    input_fields = serializers.SerializerMethodField()
    
    def get_input_fields(self, obj):
        """
        Return which fields the UI should show for counting
        """
        if obj.item.category_id == 'M' and obj.item.subcategory:
            if obj.item.subcategory == 'SOFT_DRINKS':
                return ['counted_cases', 'counted_bottles']
            elif obj.item.subcategory == 'SYRUPS':
                return ['counted_bottles', 'counted_ml']
            elif obj.item.subcategory == 'JUICES':
                return ['counted_cases', 'counted_bottles', 'counted_ml']
            elif obj.item.subcategory == 'CORDIALS':
                return ['counted_cases', 'counted_bottles']
            elif obj.item.subcategory == 'BIB':
                return ['counted_boxes', 'counted_liters']
        
        # Default fields for other categories
        return ['counted_full_units', 'counted_partial_units']
```

### 4.3 Display Unit Conversion

Update `_calculate_display_units()` method:

```python
def _calculate_display_units(self, servings, item):
    """
    Calculate display units from servings
    """
    if servings is None or servings == 0:
        return "0", "0"
    
    category = item.category.code
    
    # Handle Minerals subcategories
    if category == 'M' and item.subcategory:
        if item.subcategory == 'SOFT_DRINKS':
            # servings = bottles → cases + bottles
            full = int(servings / item.uom)  # cases
            partial = int(servings % item.uom)  # bottles (0-11)
            return str(full), str(partial)
        
        elif item.subcategory == 'SYRUPS':
            # servings → bottles + ml
            SYRUP_SERVING_SIZE = Decimal('25')
            total_ml = servings * SYRUP_SERVING_SIZE
            full = int(total_ml / item.uom)  # bottles
            partial = int(total_ml % item.uom)  # ml
            return str(full), str(partial)
        
        elif item.subcategory == 'JUICES':
            # servings → bottles + ml
            JUICE_SERVING_SIZE = Decimal('200')
            total_ml = servings * JUICE_SERVING_SIZE
            full = int(total_ml / item.uom)  # bottles
            partial = int(total_ml % item.uom)  # ml
            return str(full), str(partial)
        
        elif item.subcategory == 'CORDIALS':
            # servings = bottles → cases + bottles
            full = int(servings / item.uom)  # cases
            partial = int(servings % item.uom)  # bottles
            return str(full), str(partial)
        
        elif item.subcategory == 'BIB':
            # servings → boxes + liters
            BIB_SERVING_SIZE = Decimal('0.2')
            total_liters = servings * BIB_SERVING_SIZE
            full = int(total_liters / item.uom)  # boxes
            partial_liters = total_liters % item.uom
            # Round to 2 decimals for liters
            partial_rounded = partial_liters.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            return str(full), str(partial_rounded)
    
    # ... existing logic for D, B, S, W ...
```

---

## 5. Data Migration Requirements

### 5.1 Add Subcategory Field
```python
# migration: add_minerals_subcategory.py
from django.db import migrations, models

class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='stockitem',
            name='subcategory',
            field=models.CharField(
                max_length=20,
                null=True,
                blank=True,
                choices=[
                    ('SOFT_DRINKS', 'Soft Drinks (Bottled)'),
                    ('SYRUPS', 'Syrups & Flavourings'),
                    ('JUICES', 'Juices & Lemonades'),
                    ('CORDIALS', 'Cordials'),
                    ('BIB', 'Bag-in-Box (18L)'),
                ],
            ),
        ),
    ]
```

### 5.2 Populate Subcategory Data
```python
# migration: populate_minerals_subcategory.py
from django.db import migrations

def populate_subcategories(apps, schema_editor):
    StockItem = apps.get_model('stock_tracker', 'StockItem')
    
    # Soft Drinks: Size = "Doz"
    StockItem.objects.filter(
        category_id='M',
        size__icontains='Doz'
    ).update(subcategory='SOFT_DRINKS')
    
    # BIB: Size contains "18LT"
    StockItem.objects.filter(
        category_id='M',
        size__icontains='18LT'
    ).update(subcategory='BIB')
    
    # Syrups: Name contains "Monin", "Grenadine", "Syrup"
    StockItem.objects.filter(
        category_id='M',
        name__icontains='syrup'
    ).update(subcategory='SYRUPS')
    
    StockItem.objects.filter(
        category_id='M',
        name__icontains='Monin'
    ).update(subcategory='SYRUPS')
    
    StockItem.objects.filter(
        category_id='M',
        name__icontains='Grenadine'
    ).update(subcategory='SYRUPS')
    
    # Cordials: Name contains "Miwadi", "Cordial"
    StockItem.objects.filter(
        category_id='M',
        name__icontains='Miwadi'
    ).update(subcategory='CORDIALS')
    
    StockItem.objects.filter(
        category_id='M',
        name__icontains='Cordial'
    ).update(subcategory='CORDIALS')
    
    # Juices: Name contains "Juice", "Kulana"
    StockItem.objects.filter(
        category_id='M',
        name__icontains='Juice'
    ).update(subcategory='JUICES')
    
    StockItem.objects.filter(
        category_id='M',
        name__icontains='Kulana'
    ).update(subcategory='JUICES')

class Migration(migrations.Migration):
    dependencies = [
        ('stock_tracker', 'add_minerals_subcategory'),
    ]
    
    operations = [
        migrations.RunPython(populate_subcategories),
    ]
```

### 5.3 Fix UOM Values
```python
# migration: fix_minerals_uom.py
from django.db import migrations
from decimal import Decimal

def fix_uom_values(apps, schema_editor):
    StockItem = apps.get_model('stock_tracker', 'StockItem')
    
    # Soft Drinks: UOM = 12 (already correct)
    StockItem.objects.filter(
        category_id='M',
        subcategory='SOFT_DRINKS'
    ).update(uom=Decimal('12.00'))
    
    # BIB: UOM = 18 (liters per box)
    StockItem.objects.filter(
        category_id='M',
        subcategory='BIB'
    ).update(uom=Decimal('18.00'))
    
    # Syrups: UOM = bottle size in ml
    # 700ml bottles
    StockItem.objects.filter(
        category_id='M',
        subcategory='SYRUPS',
        size__icontains='70cl'
    ).update(uom=Decimal('700.00'))
    
    # 1L bottles
    StockItem.objects.filter(
        category_id='M',
        subcategory='SYRUPS',
        size__icontains='1L'
    ).update(uom=Decimal('1000.00'))
    
    # Juices: UOM = bottle size in ml
    # 1L bottles
    StockItem.objects.filter(
        category_id='M',
        subcategory='JUICES',
        size__icontains='1L'
    ).update(uom=Decimal('1000.00'))
    
    # 1.5L bottles
    StockItem.objects.filter(
        category_id='M',
        subcategory='JUICES',
        size__icontains='1.5L'
    ).update(uom=Decimal('1500.00'))
    
    # Cordials: UOM = 12 (bottles per case)
    StockItem.objects.filter(
        category_id='M',
        subcategory='CORDIALS'
    ).update(uom=Decimal('12.00'))

class Migration(migrations.Migration):
    dependencies = [
        ('stock_tracker', 'populate_minerals_subcategory'),
    ]
    
    operations = [
        migrations.RunPython(fix_uom_values),
    ]
```

---

## 6. Frontend Changes Required

### 6.1 Stocktake Input Form

The frontend needs to show different input fields based on subcategory:

```typescript
// Example React component logic
function MineralsInputFields({ line }) {
  const { subcategory } = line.item;
  
  if (subcategory === 'SOFT_DRINKS') {
    return (
      <>
        <Input label="Cases" name="counted_full_units" type="number" />
        <Input label="Bottles (0-11)" name="counted_partial_units" type="number" max="11" />
      </>
    );
  }
  
  if (subcategory === 'SYRUPS') {
    return (
      <>
        <Input label="Bottles" name="counted_full_units" type="number" />
        <Input label="ml" name="counted_partial_units" type="number" />
      </>
    );
  }
  
  if (subcategory === 'JUICES') {
    return (
      <>
        <Input label="Cases" name="counted_cases" type="number" />
        <Input label="Bottles" name="counted_bottles" type="number" />
        <Input label="ml (open bottle)" name="counted_ml" type="number" />
      </>
    );
  }
  
  if (subcategory === 'CORDIALS') {
    return (
      <>
        <Input label="Cases" name="counted_full_units" type="number" />
        <Input label="Bottles" name="counted_partial_units" type="number" />
      </>
    );
  }
  
  if (subcategory === 'BIB') {
    return (
      <>
        <Input label="Boxes" name="counted_full_units" type="number" />
        <Input label="Liters" name="counted_partial_units" type="number" step="0.1" />
      </>
    );
  }
  
  // Default fallback
  return (
    <>
      <Input label="Full Units" name="counted_full_units" type="number" />
      <Input label="Partial Units" name="counted_partial_units" type="number" />
    </>
  );
}
```

---

## 7. Testing Checklist

### 7.1 Unit Tests
- [ ] Test `total_stock_in_servings` for each subcategory
- [ ] Test `counted_qty` conversion for each subcategory
- [ ] Test display unit conversion for each subcategory
- [ ] Test cost calculations with new serving logic
- [ ] Test variance calculations

### 7.2 Integration Tests
- [ ] Create stocktake with all 5 subcategories
- [ ] Count stock using UI input fields
- [ ] Verify expected vs counted calculations
- [ ] Verify stock value calculations
- [ ] Test period closing with minerals items

### 7.3 Data Migration Tests
- [ ] Test subcategory population on existing data
- [ ] Test UOM fixes don't break existing stocktakes
- [ ] Verify October stocktake still calculates correctly
- [ ] Test rollback migration

---

## 8. Implementation Steps

### Phase 1: Database Changes (Backend Only)
1. Create migration to add `subcategory` field
2. Create migration to populate subcategory values
3. Create migration to fix UOM values
4. Run migrations on test database
5. Verify existing data still works

### Phase 2: Model Logic Updates
1. Update `StockItem.total_stock_in_servings`
2. Update `StocktakeLine.counted_qty`
3. Add constants for serving sizes (25ml, 200ml, 0.2L)
4. Add validation to ensure UOM matches subcategory

### Phase 3: Serializer Updates
1. Add subcategory fields to serializers
2. Update display unit conversion logic
3. Add `input_fields` helper for frontend
4. Test API responses

### Phase 4: Frontend Updates
1. Update stocktake form to show correct input fields
2. Add subcategory-specific validation
3. Update display formatting
4. Test all 5 subcategories

### Phase 5: Testing & Documentation
1. Write unit tests
2. Write integration tests
3. Update API documentation
4. Create user guide for counting minerals

---

## 9. Constants Definition

Add to `models.py`:

```python
# Serving size constants for Minerals subcategories
MINERALS_SERVING_SIZES = {
    'SOFT_DRINKS': None,  # Tracked by bottle, no serving conversion
    'SYRUPS': Decimal('25'),  # 25ml per serving
    'JUICES': Decimal('200'),  # 200ml per serving
    'CORDIALS': None,  # No serving size, tracked by bottle
    'BIB': Decimal('0.2'),  # 200ml = 0.2 liters per serving
}
```

---

## 10. Questions to Resolve

1. **Juices with Cases**: Your document says "Cases + Bottles + ml" for juices
   - Should we track cases separately from bottles?
   - Or just bottles + ml?
   - If cases: need to add `counted_cases` field to StocktakeLine

2. **Syrups**: Are all syrups 25ml per serving?
   - Or does it vary by cocktail recipe?
   - Should we link to cocktail ingredient definitions?

3. **BIB Current Stock**: The output shows crazy values like "18490.1499 liters"
   - This is clearly wrong (should be ~18 liters per box)
   - Need to fix existing data during migration?

4. **Cordials**: You say "no serving unit"
   - So we just track bottle count for inventory?
   - How do you calculate sales/consumption?

---

## 11. Recommended Approach

### My Recommendation: **OPTION A - Add Subcategory Field**

**Why?**
1. ✅ Explicit, clear categorization
2. ✅ Easy to maintain and understand
3. ✅ Frontend can show correct input fields
4. ✅ Can add validation rules per subcategory
5. ✅ Future-proof for adding new subcategories

**Implementation Timeline:**
- Database changes: 1-2 hours
- Model logic: 2-3 hours
- Serializers: 1-2 hours
- Testing: 2-3 hours
- **Total Backend: 6-10 hours**

Frontend changes are separate (not in this scope).

---

## 12. Next Steps

**What do you want to do?**

1. **Proceed with subcategory field?** 
   - I'll create the migrations and update the models

2. **Different approach?**
   - Tell me what you prefer

3. **Questions first?**
   - Let's discuss the unclear points above

**Let me know and I'll start implementing!** 🚀
