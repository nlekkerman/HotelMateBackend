"""
Fetch October 2025 stocktake details
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine

print("=" * 100)
print("OCTOBER 2025 STOCKTAKE")
print("=" * 100)

# Get October 2025 stocktake
stocktake = Stocktake.objects.get(id=18)

print(f'\nStocktake ID: {stocktake.id}')
print(f'Period: {stocktake.period_start} to {stocktake.period_end}')
print(f'Status: {stocktake.status}')
print(f'Total Lines: {stocktake.lines.count()}')
print()

# Get draught beers (category D)
draught_lines = stocktake.lines.filter(
    item__category__code='D'
).select_related('item').order_by('item__name')

print(f'DRAUGHT BEERS ({draught_lines.count()} items):')
print('=' * 100)

for line in draught_lines:
    print(f'\n{line.item.sku} - {line.item.name}')
    print(f'  Size: {line.item.size} | UOM: {line.item.uom} pints/keg')
    print(f'  Opening: {line.opening_qty:.2f} pints')
    print(f'  Purchases: {line.purchases:.2f} pints')
    print(f'  Counted: {line.counted_full_units} kegs + {line.counted_partial_units} pints')
    print(f'  Counted Qty: {line.counted_qty:.2f} pints')
    print(f'  Valuation Cost: €{line.valuation_cost:.4f} per pint')
    print(f'  Counted Value: €{line.counted_value:.2f}')
    print(f'  Expected: {line.expected_qty:.2f} pints')
    print(f'  Variance: {line.variance_qty:.2f} pints (€{line.variance_value:.2f})')
    print('-' * 100)

print(f'\nTotal Draught Items: {draught_lines.count()}')

# Summary by category
print('\n' + '=' * 100)
print('SUMMARY BY CATEGORY')
print('=' * 100)

from stock_tracker.models import StockCategory
categories = StockCategory.objects.all()

for cat in categories:
    cat_lines = stocktake.lines.filter(item__category=cat)
    if cat_lines.exists():
        total_counted = sum(line.counted_value for line in cat_lines)
        total_variance = sum(line.variance_value for line in cat_lines)
        print(f'\n{cat.code} - {cat.name}:')
        print(f'  Items: {cat_lines.count()}')
        print(f'  Total Counted Value: €{total_counted:.2f}')
        print(f'  Total Variance: €{total_variance:.2f}')
