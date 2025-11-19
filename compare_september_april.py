import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 100)
print("SEPTEMBER 2025 vs APRIL 2025 STOCKTAKE COMPARISON")
print("=" * 100)

hotel = Hotel.objects.first()

# Get September 2025 stocktake
sept_stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
).first()

# Get April 2025 stocktake
april_stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).first()

if not sept_stocktake:
    print("\n⚠️  September 2025 stocktake NOT FOUND in system!")
else:
    print(f"\n✓ September 2025 stocktake found: ID {sept_stocktake.id}")

if not april_stocktake:
    print("⚠️  April 2025 stocktake NOT FOUND in system!")
else:
    print(f"✓ April 2025 stocktake found: ID {april_stocktake.id}")

# September Excel data
sept_excel = {
    'D': {'name': 'Draught Beer', 'total': Decimal('2436.33')},
    'B': {'name': 'Bottled Beer', 'total': Decimal('1097.25')},
    'S': {'name': 'Spirits', 'total': Decimal('11282.39')},
    'M': {'name': 'Minerals/Syrups', 'total': Decimal('2950.86')},
    'W': {'name': 'Wine', 'total': Decimal('1355.87')}
}

# April Excel/Frontend data
april_excel = {
    'D': {'name': 'Draught Beer', 'total': Decimal('2437.59')},
    'B': {'name': 'Bottled Beer', 'total': Decimal('1097.25')},
    'S': {'name': 'Spirits', 'total': Decimal('11282.39')},
    'M': {'name': 'Minerals/Syrups', 'total': Decimal('2950.87')},
    'W': {'name': 'Wine', 'total': Decimal('1349.74')}
}

print("\n" + "=" * 100)
print("EXCEL DATA COMPARISON")
print("=" * 100)

print(f"\n{'Category':<25} {'Sept Excel':>15} {'April Excel':>15} {'Difference':>15}")
print("-" * 75)

sept_grand_total = Decimal('0.00')
april_grand_total = Decimal('0.00')

for cat_code in ['D', 'B', 'S', 'M', 'W']:
    sept_val = sept_excel[cat_code]['total']
    april_val = april_excel[cat_code]['total']
    
    sept_grand_total += sept_val
    april_grand_total += april_val
    
    diff = sept_val - april_val
    
    print(f"{sept_excel[cat_code]['name']:<25} €{sept_val:>13.2f} €{april_val:>13.2f} €{diff:>13.2f}")

print("-" * 75)
print(f"{'GRAND TOTAL':<25} €{sept_grand_total:>13.2f} €{april_grand_total:>13.2f} €{sept_grand_total - april_grand_total:>13.2f}")

print("\n" + "=" * 100)
print("KEY FINDINGS:")
print("=" * 100)

print(f"\n1. September Excel Grand Total: €{sept_grand_total:,.2f}")
print(f"   (Note: Your sheet shows €19,122.70 but adding up gives €{sept_grand_total:,.2f})")

print(f"\n2. April System/Excel Total: €{april_grand_total:,.2f}")

print(f"\n3. Differences by Category:")
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    diff = sept_excel[cat_code]['total'] - april_excel[cat_code]['total']
    if abs(diff) > Decimal('0.10'):
        print(f"   - {sept_excel[cat_code]['name']}: €{diff:+.2f}")

# Check if September stocktake exists in system
if sept_stocktake:
    print("\n" + "=" * 100)
    print("SYSTEM DATA FOR SEPTEMBER 2025")
    print("=" * 100)
    
    sept_lines = StocktakeLine.objects.filter(
        stocktake=sept_stocktake
    ).select_related('item', 'item__category')
    
    sept_category_totals = {}
    
    for line in sept_lines:
        cat_code = line.item.category.code
        if cat_code not in sept_category_totals:
            sept_category_totals[cat_code] = Decimal('0.00')
        sept_category_totals[cat_code] += line.counted_value
    
    print(f"\n{'Category':<25} {'System Total':>15} {'Excel Total':>15} {'Difference':>15}")
    print("-" * 75)
    
    for cat_code in ['D', 'B', 'S', 'M', 'W']:
        sys_val = sept_category_totals.get(cat_code, Decimal('0.00'))
        excel_val = sept_excel[cat_code]['total']
        diff = sys_val - excel_val
        
        match = "✓" if abs(diff) < Decimal('0.10') else "✗"
        
        print(f"{sept_excel[cat_code]['name']:<25} €{sys_val:>13.2f} €{excel_val:>13.2f} €{diff:>13.2f} {match}")

print("\n" + "=" * 100)
