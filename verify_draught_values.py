"""
Verify draught beer closing values match Excel
Compare Excel data with current stocktake/snapshot values
"""
import os
import django
from decimal import Decimal, ROUND_HALF_UP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockPeriod, StockSnapshot
from hotel.models import Hotel

# Excel data (closing stock)
excel_data = {
    'D2133': {'name': '20 Heineken 00%', 'size': 35, 'unit_cost': Decimal('59.72'), 'kegs': 1, 'pints': 20, 'value': Decimal('93.85')},
    'D0007': {'name': '30 Beamish', 'size': 53, 'unit_cost': Decimal('92.08'), 'kegs': 1, 'pints': 20, 'value': Decimal('126.83')},
    'D1004': {'name': '30 Coors', 'size': 53, 'unit_cost': Decimal('117.70'), 'kegs': 1, 'pints': 20, 'value': Decimal('162.12')},
    'D0004': {'name': '30 Heineken', 'size': 53, 'unit_cost': Decimal('117.70'), 'kegs': 1, 'pints': 20, 'value': Decimal('162.12')},
    'D0012': {'name': '30 Killarney Blonde', 'size': 53, 'unit_cost': Decimal('119.70'), 'kegs': 1, 'pints': 20, 'value': Decimal('164.87')},
    'D0011': {'name': '30 Lagunitas IPA', 'size': 53, 'unit_cost': Decimal('144.14'), 'kegs': 1, 'pints': 20, 'value': Decimal('198.53')},
    'D2354': {'name': '30 Moretti', 'size': 53, 'unit_cost': Decimal('133.15'), 'kegs': 0, 'pints': 0, 'value': Decimal('0.00')},
    'D1003': {'name': '30 Murphys', 'size': 53, 'unit_cost': Decimal('112.34'), 'kegs': 1, 'pints': 20, 'value': Decimal('154.73')},
    'D0008': {'name': '30 Murphys Red', 'size': 53, 'unit_cost': Decimal('114.68'), 'kegs': 0, 'pints': 0, 'value': Decimal('0.00')},
    'D1022': {'name': '30 Orchards', 'size': 53, 'unit_cost': Decimal('116.75'), 'kegs': 1, 'pints': 20, 'value': Decimal('160.81')},
    'D0006': {'name': '30 OT Wild Orchard', 'size': 53, 'unit_cost': Decimal('116.75'), 'kegs': 1, 'pints': 20, 'value': Decimal('160.81')},
    'D1258': {'name': '50 Coors', 'size': 88, 'unit_cost': Decimal('196.14'), 'kegs': 1, 'pints': 20, 'value': Decimal('240.72')},
    'D0005': {'name': '50 Guinness', 'size': 88, 'unit_cost': Decimal('186.51'), 'kegs': 1, 'pints': 20, 'value': Decimal('228.90')},
    'D0030': {'name': '50 Heineken', 'size': 88, 'unit_cost': Decimal('196.14'), 'kegs': 1, 'pints': 20, 'value': Decimal('240.72')},
}

print("=" * 120)
print("DRAUGHT BEER VALUE VERIFICATION")
print("=" * 120)
print()

# Get most recent stocktake
hotel = Hotel.objects.first()
latest_stocktake = Stocktake.objects.filter(hotel=hotel).order_by('-period_start').first()

if latest_stocktake:
    print(f"Latest Stocktake: {latest_stocktake.id}")
    print(f"Period: {latest_stocktake.period_start} to {latest_stocktake.period_end}")
    print(f"Status: {latest_stocktake.status}")
    print()

# Check each item
excel_total = Decimal('0.00')
system_total = Decimal('0.00')
mismatches = []

print(f"{'SKU':<8} {'Name':<25} {'Excel Value':<15} {'System Value':<15} {'Diff':<10} {'Status'}")
print("-" * 120)

for sku, data in excel_data.items():
    # Calculate Excel expected value
    cost_per_pint = data['unit_cost'] / data['size']
    counted_pints = (data['kegs'] * data['size']) + data['pints']
    calculated_value = (Decimal(counted_pints) * cost_per_pint).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    excel_total += data['value']
    
    # Get system value (from stocktake line if exists)
    if latest_stocktake:
        line = StocktakeLine.objects.filter(
            stocktake=latest_stocktake,
            item__sku=sku
        ).first()
        
        if line:
            system_value = line.counted_value
            system_total += system_value
            diff = system_value - data['value']
            
            status = "✓" if abs(diff) < Decimal('0.50') else "✗"
            if abs(diff) >= Decimal('0.50'):
                mismatches.append({
                    'sku': sku,
                    'name': data['name'],
                    'excel': data['value'],
                    'system': system_value,
                    'diff': diff,
                    'counted_kegs': line.counted_full_units,
                    'counted_pints': line.counted_partial_units,
                    'valuation_cost': line.valuation_cost
                })
            
            print(f"{sku:<8} {data['name']:<25} €{data['value']:<14.2f} €{system_value:<14.2f} €{diff:<9.2f} {status}")
        else:
            print(f"{sku:<8} {data['name']:<25} €{data['value']:<14.2f} {'NOT FOUND':<15} {'N/A':<10} ✗")
    else:
        print(f"{sku:<8} {data['name']:<25} €{data['value']:<14.2f} {'NO STOCKTAKE':<15} {'N/A':<10} ✗")

print("-" * 120)
print(f"{'TOTALS:':<34} €{excel_total:<14.2f} €{system_total:<14.2f} €{system_total - excel_total:<9.2f}")
print()

# Show mismatches in detail
if mismatches:
    print("=" * 120)
    print("MISMATCHES FOUND:")
    print("=" * 120)
    for item in mismatches:
        print(f"\n{item['sku']} - {item['name']}")
        print(f"  Excel Expected: €{item['excel']:.2f}")
        print(f"  System Counted: €{item['system']:.2f}")
        print(f"  Difference: €{item['diff']:.2f}")
        print(f"  Counted: {item['counted_kegs']} kegs + {item['counted_pints']} pints")
        print(f"  Valuation Cost: €{item['valuation_cost']:.4f} per pint")
        
        # Calculate what it should be
        excel_item = excel_data[item['sku']]
        correct_cost = excel_item['unit_cost'] / excel_item['size']
        print(f"  Correct Cost: €{correct_cost:.4f} per pint")
else:
    print("✅ All values match!")

print()
