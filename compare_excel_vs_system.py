"""
Compare Excel calculations vs System calculations item-by-item
to find the source of the €6.59 difference.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from decimal import Decimal

# Excel data from your spreadsheet
excel_data = {
    'D2133': {'cost_price': Decimal('59.72'), 'kegs': 2, 'pints': 0, 'excel_value': Decimal('68.25')},
    'D0007': {'cost_price': Decimal('92.08'), 'kegs': 1, 'pints': 26, 'excel_value': Decimal('137.25')},
    'D2354': {'cost_price': Decimal('133.6'), 'kegs': 2, 'pints': 35, 'excel_value': Decimal('763.73')},
    'D1003': {'cost_price': Decimal('112.72'), 'kegs': 1, 'pints': 45, 'excel_value': Decimal('419.69')},
    'D0008': {'cost_price': Decimal('115.08'), 'kegs': 0, 'pints': 26.5, 'excel_value': Decimal('57.53')},
    'D1258': {'cost_price': Decimal('196.08'), 'kegs': 6, 'pints': 39.93, 'excel_value': Decimal('1265.40')},
    'D0030': {'cost_price': Decimal('196.08'), 'kegs': 6, 'pints': 14, 'excel_value': Decimal('1207.63')},
    'D0006': {'cost_price': Decimal('117.12'), 'kegs': 1, 'pints': 40, 'excel_value': Decimal('205.56')},
    'D1022': {'cost_price': Decimal('117.12'), 'kegs': 5, 'pints': 31, 'excel_value': Decimal('654.25')},
    'D0005': {'cost_price': Decimal('186.48'), 'kegs': 2, 'pints': 70, 'excel_value': Decimal('521.20')},
    'D0011': {'cost_price': Decimal('144.64'), 'kegs': 0, 'pints': 5, 'excel_value': Decimal('13.64')},
}

# Fetch October 2025 stocktake
stocktake = Stocktake.objects.get(id=18)

print(f"\nITEM-BY-ITEM COMPARISON: Excel vs System")
print(f"=" * 120)
print(f"\n{'SKU':<10} {'Excel Calc':<50} {'System Calc':<50} {'Diff':<10}")
print(f"{'-'*10} {'-'*50} {'-'*50} {'-'*10}")

total_excel = Decimal('0.00')
total_system = Decimal('0.00')
total_diff = Decimal('0.00')

for line in stocktake.lines.filter(item__category__code='D').order_by('item__sku'):
    sku = line.item.sku
    
    if sku not in excel_data:
        continue
    
    excel_info = excel_data[sku]
    
    # Excel calculation
    excel_value = excel_info['excel_value']
    
    # System calculation
    system_counted_qty = line.counted_qty
    system_valuation_cost = line.valuation_cost
    system_value = line.counted_value
    
    # Calculate difference
    diff = system_value - excel_value
    
    total_excel += excel_value
    total_system += system_value
    total_diff += diff
    
    excel_desc = f"€{excel_value:.2f}"
    system_desc = f"{system_counted_qty:.4f} pints × €{system_valuation_cost:.4f} = €{system_value:.2f}"
    
    print(f"{sku:<10} {excel_desc:<50} {system_desc:<50} €{diff:>8.2f}")

print(f"\n{'='*120}")
print(f"{'TOTALS':<10} {'€' + str(total_excel):<50} {'€' + str(total_system):<50} {'€' + str(total_diff):>8}")
print(f"\n")

# Now let's calculate what Excel SHOULD have if using system's valuation_cost
print(f"\nRECALCULATING EXCEL WITH SYSTEM'S VALUATION_COST")
print(f"=" * 120)
print(f"\n{'SKU':<10} {'Excel Formula':<60} {'Recalc Value':<20} {'Original Excel':<15} {'Diff':<10}")
print(f"{'-'*10} {'-'*60} {'-'*20} {'-'*15} {'-'*10}")

total_recalc = Decimal('0.00')

for line in stocktake.lines.filter(item__category__code='D').order_by('item__sku'):
    sku = line.item.sku
    
    if sku not in excel_data:
        continue
    
    excel_info = excel_data[sku]
    
    # Use system's valuation cost with Excel's counted quantities
    kegs = excel_info['kegs']
    pints = Decimal(str(excel_info['pints']))
    uom = line.item.uom
    
    # Calculate total pints from Excel's kegs + pints
    excel_total_pints = (kegs * uom) + pints
    
    # Apply system's valuation cost
    system_valuation_cost = line.valuation_cost
    recalc_value = excel_total_pints * system_valuation_cost
    
    total_recalc += recalc_value
    
    excel_original = excel_info['excel_value']
    diff = recalc_value - excel_original
    
    formula = f"{kegs} kegs × {uom} + {pints} pints = {excel_total_pints:.4f} × €{system_valuation_cost:.4f}"
    
    print(f"{sku:<10} {formula:<60} €{recalc_value:<18.2f} €{excel_original:<14.2f} €{diff:>8.2f}")

print(f"\n{'='*120}")
print(f"Total Recalculated: €{total_recalc:.2f}")
print(f"Original Excel:     €{total_excel:.2f}")
print(f"Difference:         €{total_recalc - total_excel:.2f}")
print(f"\n")
print(f"CONCLUSION:")
print(f"If Excel used system's valuation_cost, total would be: €{total_recalc:.2f}")
print(f"System actual total: €{total_system:.2f}")
print(f"Match: {'YES ✓' if abs(total_recalc - total_system) < Decimal('0.01') else 'NO ✗'}")
