"""
Compare September counted wine values from Excel with database.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from hotel.models import Hotel

print("=" * 80)
print("COMPARE SEPTEMBER COUNTED WINE - EXCEL vs DATABASE")
print("=" * 80)
print()

# September counted from import_september_counted.py
september_counted = {
    'W0018': (3.00, 0.00, 30.75),
    'W0019': (3.00, 0.00, 56.01),
    'W0021': (18.00, 0.00, 177.84),
    'W0022': (49.70, 0.00, 340.44),
    'W0023': (2.00, 0.00, 16.28),
    'W0024': (5.00, 0.00, 77.50),
    'W0025': (1.00, 0.00, 16.33),
    'W0027': (23.00, 0.00, 172.50),
    'W0028': (7.00, 0.00, 108.50),
    'W0029': (12.00, 0.00, 117.96),
    'W0030': (6.00, 0.00, 87.00),
    'W0031': (11.00, 0.00, 93.50),
    'W0032': (3.00, 0.00, 32.49),
    'W0033': (15.00, 0.00, 127.50),
    'W0036': (6.00, 0.00, 94.98),
    'W0037': (8.00, 0.00, 140.00),
    'W0038': (4.00, 0.00, 39.32),
    'W0041': (10.20, 0.00, 106.39),
    'W0042': (21.50, 0.00, 139.32),
    'W0043': (4.10, 0.00, 21.28),
    'W1': (15.00, 0.00, 133.95),
    'W1004': (43.50, 0.00, 268.40),
    'W1013': (13.00, 0.00, 402.87),
    'W1020': (30.00, 0.00, 210.00),
    'W111': (18.00, 0.00, 75.06),
    'W2102': (6.00, 0.00, 45.84),
    'W2104': (48.70, 0.00, 337.00),
    'W2108': (50.80, 0.00, 346.96),
    'W2589': (26.40, 0.00, 162.89),
    'W45': (7.00, 0.00, 80.50),
}

excel_total = sum(value for _, _, value in september_counted.values())
print(f"September counted from Excel: {len(september_counted)} items")
print(f"Excel total value: €{excel_total:,.2f}")
print()

# Get September stocktake
hotel = Hotel.objects.first()
stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
)

wine_lines = stocktake.lines.filter(item__category_id='W').order_by('item__sku')

print("Comparing September counted Excel vs Database:")
print("-" * 80)
print(f"{'SKU':<10} {'Excel Qty':<12} {'DB Qty':<12} {'Excel €':<12} {'DB €':<12} {'Match'}")
print("-" * 80)

db_total = Decimal('0.00')
mismatches = []

for line in wine_lines:
    sku = line.item.sku
    db_qty = float(line.counted_full_units + line.counted_partial_units)
    db_value = line.counted_value
    db_total += db_value
    
    if sku in september_counted:
        excel_full, excel_partial, excel_value = september_counted[sku]
        excel_qty = excel_full + excel_partial
        
        qty_match = abs(excel_qty - db_qty) < 0.01
        value_match = abs(excel_value - float(db_value)) < 0.50
        
        match = "✅" if qty_match and value_match else "❌"
        
        if not (qty_match and value_match):
            mismatches.append({
                'sku': sku,
                'name': line.item.name,
                'excel_qty': excel_qty,
                'db_qty': db_qty,
                'excel_value': excel_value,
                'db_value': float(db_value),
                'qty_diff': db_qty - excel_qty,
                'value_diff': float(db_value) - excel_value
            })
        
        print(f"{sku:<10} {excel_qty:<12.2f} {db_qty:<12.2f} €{excel_value:<11.2f} €{db_value:<11.2f} {match}")
    else:
        if db_qty > 0:
            print(f"{sku:<10} {'N/A':<12} {db_qty:<12.2f} {'N/A':<12} €{db_value:<11.2f} ⚠️ (Not in Excel)")

print("-" * 80)
print(f"Excel Total:  €{excel_total:,.2f}")
print(f"DB Total:     €{db_total:,.2f}")
print(f"Difference:   €{float(db_total) - excel_total:,.2f}")
print()

# Check for items in Excel not in database
print("Items in September Excel but not in database:")
print("-" * 80)
db_skus = set(line.item.sku for line in wine_lines)
missing = []
for sku in september_counted:
    if sku not in db_skus:
        excel_full, excel_partial, excel_value = september_counted[sku]
        missing.append((sku, excel_full + excel_partial, excel_value))
        print(f"{sku:<10} {excel_full + excel_partial:<12.2f} bottles, €{excel_value:.2f}")

if not missing:
    print("✅ All Excel items exist in database")
print("-" * 80)
print()

if mismatches:
    print("MISMATCHES FOUND:")
    print("-" * 80)
    for item in mismatches:
        print(f"{item['sku']:<10} {item['name']}")
        print(f"           Qty:   Excel {item['excel_qty']:.2f}, DB {item['db_qty']:.2f}, Diff: {item['qty_diff']:+.2f}")
        print(f"           Value: Excel €{item['excel_value']:.2f}, DB €{item['db_value']:.2f}, Diff: €{item['value_diff']:+.2f}")
    print("-" * 80)
else:
    print("✅ All values match!")

print()
print("=" * 80)
