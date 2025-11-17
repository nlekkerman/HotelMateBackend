import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine

# Get BIB items
bib_lines = StocktakeLine.objects.filter(
    stocktake__id=3,
    stocktake__hotel__slug='bogans',
    item__subcategory='BIB'
).select_related('item')

print(f"\n{'='*100}")
print(f"BIB ITEMS - Cost Analysis")
print(f"{'='*100}\n")

for line in bib_lines:
    print(f"SKU: {line.item.sku} - {line.item.name}")
    print(f"  Counted Full: {line.counted_full_units} containers")
    print(f"  Counted Partial: {line.counted_partial_units} liters")
    print(f"  Counted Qty: {line.counted_qty:.2f} servings")
    print(f"  Valuation Cost: €{line.valuation_cost:.4f} per ??? (serving? liter?)")
    print(f"  Counted Value: €{line.counted_value:.2f}")
    print()
    print(f"  📊 If cost is per SERVING:")
    print(f"     {line.counted_qty:.2f} servings × €{line.valuation_cost:.4f} = €{line.counted_qty * line.valuation_cost:.2f}")
    print()
    print(f"  📊 If cost is per LITER:")
    total_liters = (float(line.counted_full_units or 0) * 18) + float(line.counted_partial_units or 0)
    print(f"     {total_liters:.2f} liters × €{line.valuation_cost:.4f} = €{total_liters * float(line.valuation_cost):.2f}")
    print()
    print(f"  ❓ Which matches counted_value €{line.counted_value:.2f}?")
    print(f"{'-'*100}\n")
