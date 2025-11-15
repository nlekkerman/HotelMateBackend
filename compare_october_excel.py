"""
Compare October 2025 Stocktake with Excel
Find the €7 difference between Excel (€5311.62) and Database (€5318.21)
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake

# Excel data for Draught Beers
excel_data = {
    'D2133': {'closing_full': 0, 'closing_partial': 40.00, 'valuation': Decimal('59.72'), 'excel_value': Decimal('68.25')},
    'D0007': {'closing_full': 0, 'closing_partial': 79.00, 'valuation': Decimal('92.08'), 'excel_value': Decimal('137.25')},
    'D1004': {'closing_full': 0, 'closing_partial': 0.00, 'valuation': Decimal('117.70'), 'excel_value': Decimal('0.00')},
    'D0004': {'closing_full': 0, 'closing_partial': 0.00, 'valuation': Decimal('117.70'), 'excel_value': Decimal('0.00')},
    'D0012': {'closing_full': 0, 'closing_partial': 0.00, 'valuation': Decimal('119.70'), 'excel_value': Decimal('0.00')},
    'D0011': {'closing_full': 0, 'closing_partial': 5.00, 'valuation': Decimal('144.14'), 'excel_value': Decimal('13.60')},
    'D2354': {'closing_full': 0, 'closing_partial': 304.00, 'valuation': Decimal('133.15'), 'excel_value': Decimal('763.73')},
    'D1003': {'closing_full': 0, 'closing_partial': 198.00, 'valuation': Decimal('112.34'), 'excel_value': Decimal('419.69')},
    'D0008': {'closing_full': 0, 'closing_partial': 26.50, 'valuation': Decimal('114.68'), 'excel_value': Decimal('57.34')},
    'D1022': {'closing_full': 0, 'closing_partial': 296.00, 'valuation': Decimal('116.75'), 'excel_value': Decimal('652.04')},
    'D0006': {'closing_full': 0, 'closing_partial': 93.00, 'valuation': Decimal('116.75'), 'excel_value': Decimal('204.86')},
    'D1258': {'closing_full': 6, 'closing_partial': 39.75, 'valuation': Decimal('196.14'), 'excel_value': Decimal('1265.44')},
    'D0005': {'closing_full': 0, 'closing_partial': 246.00, 'valuation': Decimal('186.51'), 'excel_value': Decimal('521.38')},
    'D0030': {'closing_full': 0, 'closing_partial': 542.00, 'valuation': Decimal('196.14'), 'excel_value': Decimal('1208.04')},
}

# Get October 2025 stocktake
stocktake = Stocktake.objects.get(id=18)

print("=" * 120)
print("DRAUGHT BEER COMPARISON - October 2025")
print("=" * 120)
print()

draught_lines = stocktake.lines.filter(item__category__code='D').select_related('item').order_by('item__sku')

total_excel = Decimal('0')
total_db = Decimal('0')
discrepancies = []

for line in draught_lines:
    sku = line.item.sku
    
    if sku in excel_data:
        excel_info = excel_data[sku]
        
        # Database values
        db_full = line.counted_full_units
        db_partial = line.counted_partial_units
        db_valuation = line.valuation_cost
        db_value = line.counted_value
        
        # Excel values
        excel_full = excel_info['closing_full']
        excel_partial = excel_info['closing_partial']
        excel_valuation = excel_info['valuation']
        excel_value = excel_info['excel_value']
        
        # Calculate what Excel should be based on DB valuation
        # Excel uses: Cost Price / UOM = cost per serving
        # Then: (full * UOM + partial) * cost_per_serving = value
        
        uom = line.item.uom
        
        # Excel's cost per serving
        excel_cost_per_serving = excel_valuation / uom
        
        # Our cost per serving
        db_cost_per_serving = db_valuation
        
        # Calculate total servings
        total_servings = (Decimal(str(db_full)) * uom) + Decimal(str(db_partial))
        
        # Calculate expected value using Excel's cost per serving
        expected_from_excel_cost = total_servings * excel_cost_per_serving
        
        difference = db_value - excel_value
        
        if abs(difference) > Decimal('0.01'):
            discrepancies.append({
                'sku': sku,
                'name': line.item.name,
                'difference': difference
            })
            
            print(f"{sku} - {line.item.name}")
            print(f"  UOM: {uom}")
            print(f"  Counted: {db_full} kegs + {db_partial} pints = {total_servings} total servings")
            print(f"  Excel Cost/Serving: €{excel_cost_per_serving:.4f} (from €{excel_valuation}/{uom})")
            print(f"  DB Cost/Serving:    €{db_cost_per_serving:.4f}")
            print(f"  Excel Value:  €{excel_value:.2f}")
            print(f"  DB Value:     €{db_value:.2f}")
            print(f"  Difference:   €{difference:.2f}")
            print(f"  Expected from Excel cost: €{expected_from_excel_cost:.2f}")
            print("-" * 120)
        
        total_excel += excel_value
        total_db += db_value

print()
print("=" * 120)
print("SUMMARY")
print("=" * 120)
print(f"Total Excel Value:    €{total_excel:.2f}")
print(f"Total Database Value: €{total_db:.2f}")
print(f"Total Difference:     €{total_db - total_excel:.2f}")
print()

if discrepancies:
    print(f"Found {len(discrepancies)} items with discrepancies:")
    for disc in discrepancies:
        print(f"  {disc['sku']} - {disc['name']}: €{disc['difference']:.2f}")
