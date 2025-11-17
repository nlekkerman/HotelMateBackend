import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_mate.settings')
django.setup()

from stock_tracker.models import StocktakeLine

# Excel data with SKU, closing stock, and cost per unit
excel_data = {
    'M2236': {'closing': 12.95, 'cost': 3.50, 'expected_value': 62.09},
    'M0195': {'closing': 5.13, 'cost': 3.00, 'expected_value': 82.49},
    'M0140': {'closing': 17.00, 'cost': 0.00, 'expected_value': 0.00},
    'M2107': {'closing': 12.52, 'cost': 3.60, 'expected_value': 64.37},
    'M0320': {'closing': 6.16, 'cost': 0.00, 'expected_value': 0.00},
    'M11': {'closing': 1.00, 'cost': 0.00, 'expected_value': 0.00},
    'M0042': {'closing': 12.15, 'cost': 0.00, 'expected_value': 0.00},
    'M0210': {'closing': 13.05, 'cost': 0.00, 'expected_value': 0.00},
    'M0008': {'closing': 5.88, 'cost': 0.00, 'expected_value': 0.00},
    'M0009': {'closing': 5.88, 'cost': 0.00, 'expected_value': 0.00},
    'M3': {'closing': 9.98, 'cost': 0.00, 'expected_value': 0.00},
    'M0006': {'closing': 9.33, 'cost': 0.00, 'expected_value': 0.00},
    'M13': {'closing': 9.15, 'cost': 0.00, 'expected_value': 0.00},
    'M04': {'closing': 10.38, 'cost': 0.00, 'expected_value': 0.00},
    'M0014': {'closing': 10.25, 'cost': 0.00, 'expected_value': 0.00},
    'M2': {'closing': 15.37, 'cost': 0.00, 'expected_value': 0.00},
    'M03': {'closing': 9.15, 'cost': 0.00, 'expected_value': 0.00},
    'M05': {'closing': 10.25, 'cost': 0.00, 'expected_value': 0.00},
    'M06': {'closing': 14.64, 'cost': 0.00, 'expected_value': 0.00},
    'M1': {'closing': 12.13, 'cost': 0.00, 'expected_value': 0.00},
    'M01': {'closing': 10.31, 'cost': 0.00, 'expected_value': 0.00},
    'M5': {'closing': 10.31, 'cost': 0.00, 'expected_value': 0.00},
    'M9': {'closing': 8.83, 'cost': 0.00, 'expected_value': 0.00},
    'M02': {'closing': 8.95, 'cost': 0.00, 'expected_value': 0.00},
    'M0170': {'closing': 11.13, 'cost': 4.90, 'expected_value': 76.73},
    'M0123': {'closing': 19.35, 'cost': 5.00, 'expected_value': 60.33},
    'M0180': {'closing': 5.18, 'cost': 3.50, 'expected_value': 84.84},
    'M25': {'closing': 171.16, 'cost': 2.50, 'expected_value': 83.16},
    'M24': {'closing': 182.64, 'cost': 1.50, 'expected_value': 70.05},
    'M23': {'closing': 173.06, 'cost': 1.50, 'expected_value': 71.62},
    'M0050': {'closing': 6.35, 'cost': 3.50, 'expected_value': 81.40},
    'M0003': {'closing': 6.35, 'cost': 3.50, 'expected_value': 81.40},
    'M0040': {'closing': 7.00, 'cost': 3.50, 'expected_value': 79.50},
    'M0013': {'closing': 14.52, 'cost': 5.00, 'expected_value': 70.23},
    'M2105': {'closing': 6.60, 'cost': 3.50, 'expected_value': 80.67},
    'M0004': {'closing': 5.75, 'cost': 3.50, 'expected_value': 83.16},
    'M0034': {'closing': 5.75, 'cost': 3.50, 'expected_value': 83.16},
    'M0070': {'closing': 7.16, 'cost': 3.60, 'expected_value': 79.63},
    'M0135': {'closing': 8.80, 'cost': 3.70, 'expected_value': 75.62},
    'M0315': {'closing': 5.10, 'cost': 3.50, 'expected_value': 85.06},
    'M0016': {'closing': 10.24, 'cost': 3.60, 'expected_value': 70.84},
    'M0255': {'closing': 6.88, 'cost': 3.50, 'expected_value': 79.87},
    'M0122': {'closing': 6.50, 'cost': 3.60, 'expected_value': 81.49},
    'M0200': {'closing': 5.60, 'cost': 3.50, 'expected_value': 83.60},
    'M0312': {'closing': 8.40, 'cost': 3.60, 'expected_value': 76.08},
    'M0012': {'closing': 8.67, 'cost': 0.00, 'expected_value': 0.00},
    'M0011': {'closing': 0.00, 'cost': 3.60, 'expected_value': 100.00},
}

print(f"\n{'='*100}")
print(f"MINERALS & SYRUPS - Stock Value Verification")
print(f"{'='*100}\n")

# Get February stocktake lines
lines = StocktakeLine.objects.filter(
    stocktake__id=3,  # February stocktake
    stocktake__hotel__slug='bogans',
    item__category__code='M'
).select_related('item', 'stocktake').order_by('item__sku')

mismatches = []
correct = []

for line in lines:
    sku = line.item.sku
    
    if sku not in excel_data:
        continue
    
    excel = excel_data[sku]
    
    # Calculate expected stock value: closing × cost
    excel_value = excel['closing'] * excel['cost']
    system_value = float(line.counted_value or 0)
    
    # Get counted qty from system
    system_counted = float(line.counted_qty or 0)
    excel_counted = excel['closing']
    
    diff = abs(excel_value - system_value)
    
    if diff > 0.50:  # Allow 50 cent tolerance
        mismatches.append({
            'sku': sku,
            'name': line.item.name,
            'excel_counted': excel_counted,
            'system_counted': system_counted,
            'excel_cost': excel['cost'],
            'system_cost': float(line.valuation_cost or 0),
            'excel_value': excel_value,
            'system_value': system_value,
            'difference': diff
        })
    else:
        correct.append(sku)

print(f"✅ CORRECT: {len(correct)} items")
print(f"❌ MISMATCHES: {len(mismatches)} items\n")

if mismatches:
    print(f"{'SKU':<10} {'Name':<35} {'Excel Qty':<12} {'System Qty':<12} {'Excel Cost':<12} {'System Cost':<12} {'Excel Value':<12} {'System Value':<12} {'Diff':<10}")
    print(f"{'-'*140}")
    
    for item in mismatches:
        print(f"{item['sku']:<10} {item['name'][:34]:<35} {item['excel_counted']:<12.2f} {item['system_counted']:<12.2f} "
              f"€{item['excel_cost']:<11.2f} €{item['system_cost']:<11.2f} €{item['excel_value']:<11.2f} "
              f"€{item['system_value']:<11.2f} €{item['difference']:<9.2f}")

print(f"\n{'='*100}")
print("\n📊 ANALYSIS:")
print(f"  - Items where counted qty matches but value doesn't = COST ISSUE")
print(f"  - Items where counted qty doesn't match = DATA ENTRY ISSUE")
print(f"  - Excel formula: Stock Value = Closing Qty × Cost Per Unit")
print(f"  - System formula: counted_value = counted_qty × valuation_cost")
print(f"{'='*100}\n")
