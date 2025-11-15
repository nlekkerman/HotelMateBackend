"""
Display ALL Draught Beers, Spirits, and Minerals from October 2025
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake

# Get October 2025 stocktake (ID 18)
stocktake = Stocktake.objects.get(id=18)

print("=" * 120)
print(f"OCTOBER 2025 STOCKTAKE - ID: {stocktake.id}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print(f"Status: {stocktake.status}")
print(f"Total Lines: {stocktake.lines.count()}")
print("=" * 120)

# DRAUGHT BEERS (D)
draught = stocktake.lines.filter(item__category__code='D').select_related('item')
print(f"\n\nDRAUGHT BEERS - {draught.count()} items")
print("=" * 120)

for line in draught:
    print(f"\n{line.item.sku} - {line.item.name}")
    print(f"  Size: {line.item.size} | UOM: {line.item.uom}")
    print(f"  Opening: {line.opening_qty} | Purchases: {line.purchases}")
    print(f"  Expected: {line.expected_qty} | Counted: {line.counted_qty} ({line.counted_full_units} + {line.counted_partial_units})")
    print(f"  Variance: {line.variance_qty}")
    print(f"  Valuation: €{line.valuation_cost} | Counted Value: €{line.counted_value} | Variance Value: €{line.variance_value}")

# SPIRITS (S)
spirits = stocktake.lines.filter(item__category__code='S').select_related('item')
print(f"\n\nSPIRITS - {spirits.count()} items")
print("=" * 120)

for line in spirits:
    print(f"\n{line.item.sku} - {line.item.name}")
    print(f"  Size: {line.item.size} | UOM: {line.item.uom}")
    print(f"  Opening: {line.opening_qty} | Purchases: {line.purchases}")
    print(f"  Expected: {line.expected_qty} | Counted: {line.counted_qty} ({line.counted_full_units} + {line.counted_partial_units})")
    print(f"  Variance: {line.variance_qty}")
    print(f"  Valuation: €{line.valuation_cost} | Counted Value: €{line.counted_value} | Variance Value: €{line.variance_value}")

# MINERALS (M)
minerals = stocktake.lines.filter(item__category__code='M').select_related('item')
print(f"\n\nMINERALS - {minerals.count()} items")
print("=" * 120)

for line in minerals:
    print(f"\n{line.item.sku} - {line.item.name}")
    print(f"  Size: {line.item.size} | UOM: {line.item.uom}")
    print(f"  Opening: {line.opening_qty} | Purchases: {line.purchases}")
    print(f"  Expected: {line.expected_qty} | Counted: {line.counted_qty} ({line.counted_full_units} + {line.counted_partial_units})")
    print(f"  Variance: {line.variance_qty}")
    print(f"  Valuation: €{line.valuation_cost} | Counted Value: €{line.counted_value} | Variance Value: €{line.variance_value}")

# SUMMARY
print("\n" + "=" * 120)
print("SUMMARY")
print("=" * 120)

total_draught_value = sum(line.counted_value for line in draught)
total_spirits_value = sum(line.counted_value for line in spirits)
total_minerals_value = sum(line.counted_value for line in minerals)

print(f"\nDraught Beers: {draught.count()} items | Total Value: €{total_draught_value:.2f}")
print(f"Spirits:       {spirits.count()} items | Total Value: €{total_spirits_value:.2f}")
print(f"Minerals:      {minerals.count()} items | Total Value: €{total_minerals_value:.2f}")
print(f"\nGrand Total:   {draught.count() + spirits.count() + minerals.count()} items | Total Value: €{(total_draught_value + total_spirits_value + total_minerals_value):.2f}")
