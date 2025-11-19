import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 100)
print("COMPLETE STOCKTAKE COMPARISON - SYSTEM vs YOUR FRONTEND DATA")
print("=" * 100)

hotel = Hotel.objects.first()

stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).first()

# Get all lines by category
all_lines = StocktakeLine.objects.filter(
    stocktake=stocktake
).select_related('item', 'item__category')

# Calculate totals by category
category_totals = {}

for line in all_lines:
    cat_code = line.item.category.code
    cat_name = line.item.category.name
    
    if cat_code not in category_totals:
        category_totals[cat_code] = {
            'name': cat_name,
            'count': 0,
            'total': Decimal('0.00')
        }
    
    category_totals[cat_code]['count'] += 1
    category_totals[cat_code]['total'] += line.counted_value

# Frontend data from the user
frontend_data = {
    'B': {'name': 'Bottled Beer', 'items': 21, 'total': Decimal('1097.25')},
    'D': {'name': 'Draught Beer', 'items': 14, 'total': Decimal('2437.59')},
    'M': {'name': 'Minerals & Syrups', 'items': 46, 'total': Decimal('2950.87')},
    'S': {'name': 'Spirits', 'items': 128, 'total': Decimal('11282.39')},
    'W': {'name': 'Wine', 'items': 44, 'total': Decimal('1349.74')}
}

print(f"\n{'Category':<25} {'Items':>8} {'System Total':>15} {'Frontend Total':>15} {'Difference':>15}")
print("-" * 90)

system_grand_total = Decimal('0.00')
frontend_grand_total = Decimal('0.00')

for cat_code in sorted(frontend_data.keys()):
    sys_data = category_totals.get(cat_code, {'name': '???', 'count': 0, 'total': Decimal('0.00')})
    fe_data = frontend_data[cat_code]
    
    system_grand_total += sys_data['total']
    frontend_grand_total += fe_data['total']
    
    diff = sys_data['total'] - fe_data['total']
    
    match_symbol = "✓" if abs(diff) < Decimal('0.10') else "✗"
    
    print(f"{fe_data['name']:<25} {sys_data['count']:>8} €{sys_data['total']:>13.2f} €{fe_data['total']:>13.2f} €{diff:>13.2f} {match_symbol}")

print("-" * 90)
print(f"{'GRAND TOTAL':<25} {'253':>8} €{system_grand_total:>13.2f} €{frontend_grand_total:>13.2f} €{system_grand_total - frontend_grand_total:>13.2f}")

print("\n" + "=" * 100)
print("DETAILED BREAKDOWN OF DIFFERENCES:")
print("=" * 100)

for cat_code in sorted(frontend_data.keys()):
    sys_data = category_totals.get(cat_code, {'total': Decimal('0.00')})
    fe_data = frontend_data[cat_code]
    diff = sys_data['total'] - fe_data['total']
    
    if abs(diff) >= Decimal('0.10'):
        print(f"\n{fe_data['name']}:")
        print(f"  System:   €{sys_data['total']:,.2f}")
        print(f"  Frontend: €{fe_data['total']:,.2f}")
        print(f"  Diff:     €{diff:+,.2f}")

print("\n" + "=" * 100)
print("TOTAL STOCK VALUE SHOWN AT TOP OF FRONTEND:")
print(f"Frontend shows: €19,117.84")
print(f"System total:   €{system_grand_total:,.2f}")
print(f"Difference:     €{system_grand_total - Decimal('19117.84'):+,.2f}")
print("=" * 100)
