# 🔄 Restore Zeroed Stock Items

You have **two JSON backup files** available for restoration:
1. `september_closing_stock.json` - September closing stock values
2. `october_closing_stock.json` - October closing stock values (if available)

---

## Quick Restore Method (Recommended)

### Step 1: Check which items are zeroed
```bash
python manage.py shell
```

Then in the shell:
```python
from stock_tracker.models import StockItem
from decimal import Decimal

zeroed = StockItem.objects.filter(
    current_full_units=Decimal('0'),
    current_partial_units=Decimal('0'),
    active=True
)
print(f"Zeroed items: {zeroed.count()}")
```

### Step 2: Restore from September backup
```python
exec(open('quick_restore_from_september.py').read())
```

This will:
- ✓ Load data from `september_closing_stock.json`
- ✓ Only restore items that are currently zeroed
- ✓ Skip items that already have data
- ✓ Show progress as it restores

---

## Alternative: Manual Restoration via Menu

If you prefer an interactive menu, use:

```bash
python restore_zeroed_stock_items.py
```

**Note:** This requires the virtual environment to be activated first.

---

## What Gets Restored

From the JSON backup, the script restores:
- `current_full_units` - Full cases/kegs/bottles
- `current_partial_units` - Partial units

**Example from backup:**
```json
"B0012": {
  "sku": "B0012",
  "name": "Cronins 0.0%",
  "counted_full_units": "0.00",
  "counted_partial_units": "16.00"
}
```

This would restore B0012 to have 16 bottles in stock.

---

## Verification After Restore

Check the restoration was successful:

```python
from stock_tracker.models import StockItem

# Check a specific item
item = StockItem.objects.get(sku='B0012')
print(f"{item.sku}: {item.current_full_units} full, {item.current_partial_units} partial")

# Count non-zero items
non_zero = StockItem.objects.exclude(
    current_full_units=0,
    current_partial_units=0
).filter(active=True).count()
print(f"Items with stock: {non_zero}")
```

---

## If You Need to Restore from a Stocktake Instead

If the JSON files don't have the data you need, you can restore from any previous stocktake:

```python
from stock_tracker.models import Stocktake, StockItem

# List available stocktakes
for st in Stocktake.objects.all().order_by('-period_start')[:5]:
    print(f"ID: {st.id} | {st.period_start} to {st.period_end}")

# Restore from a specific stocktake (e.g., ID 18)
stocktake = Stocktake.objects.get(id=18)

for line in stocktake.lines.all():
    item = line.item
    if item.current_full_units == 0 and item.current_partial_units == 0:
        item.current_full_units = line.counted_full_units
        item.current_partial_units = line.counted_partial_units
        item.save()
        print(f"Restored {item.sku}")
```

---

## Safety Notes

✓ **Safe to run** - Only affects items with BOTH full and partial units at zero
✓ **Non-destructive** - Skips items that already have data
✓ **Reversible** - You can re-zero items if needed

---

## Questions?

- **Q: Will this overwrite existing stock data?**
  - A: No, only restores items where both full and partial units are zero

- **Q: Can I restore specific categories only?**
  - A: Yes, modify the script to filter by category

- **Q: What if the JSON backup is missing items?**
  - A: Those items will be skipped and reported as "not found"
