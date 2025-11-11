"""
Compare September counted spirits values from Excel with database.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from hotel.models import Hotel

print("=" * 80)
print("COMPARE SEPTEMBER COUNTED SPIRITS - EXCEL vs DATABASE")
print("=" * 80)
print()

# September counted from import_september_counted.py
september_spirits = {
    'S0001': (2.00, 0.70, 91.34),
    'S0002': (8.00, 0.80, 116.69),
    'S0005': (2.00, 0.00, 26.80),
    'S0006': (2.00, 0.25, 51.16),
    'S0007': (6.00, 0.40, 212.29),
    'S0008': (2.00, 0.00, 25.00),
    'S0009': (2.00, 0.30, 69.15),
    'S0010': (2.00, 0.00, 106.06),
    'S0012': (1.00, 0.00, 18.17),
    'S0014': (2.00, 0.10, 65.29),
    'S0017': (1.00, 0.10, 15.28),
    'S0018': (2.00, 0.15, 35.43),
    'S002': (5.00, 0.90, 129.96),
    'S0021': (2.00, 0.30, 70.15),
    'S0022': (4.00, 0.90, 147.00),
    'S0023': (1.90, 0.00, 24.55),
    'S0026': (3.00, 0.65, 97.31),
    'S0027': (0.00, 0.85, 21.06),
    'S0028': (2.00, 0.00, 35.78),
    'S0029': (1.00, 0.90, 35.15),
    'S0041': (4.00, 0.00, 60.00),
    'S0045': (7.00, 0.05, 173.78),
    'S0064': (2.00, 0.20, 62.33),
    'S0065': (1.00, 0.90, 46.74),
    'S0071': (0.00, 0.80, 9.94),
    'S0074': (12.00, 0.90, 201.54),
    'S0080': (0.00, 0.90, 20.93),
    'S0100': (2.00, 0.00, 44.66),
    'S0105': (3.00, 0.55, 116.33),
    'S0120': (6.00, 0.85, 122.14),
    'S0130': (3.00, 0.70, 67.23),
    'S0135': (4.00, 0.05, 92.83),
    'S0140': (2.00, 0.60, 47.49),
    'S0147': (0.00, 0.90, 0.94),
    'S0150': (5.00, 0.70, 118.32),
    'S0162': (1.50, 0.00, 19.61),
    'S0170': (1.00, 0.70, 39.39),
    'S0180': (0.40, 0.00, 5.23),
    'S0190': (2.00, 0.10, 25.12),
    'S0195': (2.00, 0.00, 33.18),
    'S0205': (0.00, 0.60, 19.91),
    'S0215': (2.50, 0.00, 42.52),
    'S0220': (3.00, 0.90, 66.81),
    'S0230': (0.00, 0.10, 3.15),
    'S0245': (3.00, 0.30, 67.06),
    'S0255': (1.00, 0.95, 81.92),
    'S0265': (3.00, 0.30, 85.79),
    'S0271': (1.00, 0.85, 71.00),
    'S0306': (7.00, 0.15, 174.28),
    'S0310': (3.00, 0.95, 125.53),
    'S0325': (3.00, 0.20, 34.11),
    'S0327': (1.00, 0.20, 46.00),
    'S0335': (3.00, 0.50, 132.95),
    'S0365': (2.00, 0.40, 54.41),
    'S0370': (2.00, 0.75, 89.79),
    'S0380': (4.00, 0.40, 106.39),
    'S0385': (3.00, 0.50, 59.22),
    'S0405': (8.00, 0.15, 233.99),
    'S0420': (5.00, 0.95, 80.80),
    'S0455': (1.00, 0.90, 25.02),
    'S0485': (2.00, 0.70, 26.24),
    'S0530': (4.00, 0.70, 95.26),
    'S0543': (10.00, 0.55, 134.09),
    'S0545': (1.00, 0.00, 20.55),
    'S0550': (0.00, 0.05, 0.88),
    'S0555': (3.00, 0.25, 98.21),
    'S0575': (0.00, 0.60, 28.00),
    'S0585': (2.00, 0.20, 94.73),
    'S0605': (2.00, 0.20, 31.44),
    'S0610': (45.00, 0.80, 982.98),
    'S0625': (2.00, 0.80, 38.50),
    'S0630': (0.00, 0.05, 0.86),
    'S0635': (6.00, 0.95, 140.39),
    'S0638': (1.00, 0.40, 31.96),
    'S0640': (6.00, 0.50, 99.64),
    'S0647': (3.00, 0.00, 67.71),
    'S0653': (2.00, 0.95, 40.74),
    'S0699': (5.00, 0.60, 54.43),
    'S100': (5.00, 0.05, 131.30),
    'S1002': (3.00, 0.50, 73.68),
    'S1019': (2.00, 0.60, 45.06),
    'S1047': (1.00, 0.05, 27.09),
    'S1101': (2.00, 0.15, 103.20),
    'S1203': (2.00, 0.20, 36.85),
    'S1210': (3.00, 0.05, 269.19),
    'S1258': (0.00, 0.85, 30.74),
    'S1299': (1.00, 0.95, 42.90),
    'S1302': (2.00, 0.30, 75.14),
    'S1400': (0.00, 0.90, 17.50),
    'S1401': (3.00, 0.50, 44.94),
    'S1411': (1.80, 0.85, 161.76),
    'S1412': (10.00, 0.30, 460.31),
    'S2033': (2.00, 0.40, 42.79),
    'S2034': (9.00, 0.70, 198.85),
    'S2055': (2.00, 0.50, 95.80),
    'S2058': (0.00, 0.95, 28.25),
    'S2065': (0.00, 0.35, 10.62),
    'S2148': (2.00, 0.50, 77.08),
    'S2155': (2.00, 0.00, 63.38),
    'S2156': (2.00, 0.30, 49.10),
    'S2186': (2.00, 0.20, 69.04),
    'S2189': (1.00, 0.70, 53.35),
    'S2217': (0.00, 0.90, 30.01),
    'S2241': (1.00, 0.75, 100.33),
    'S2302': (1.00, 0.60, 50.67),
    'S2314': (2.00, 0.50, 46.68),
    'S2349': (0.00, 0.60, 19.75),
    'S2354': (1.00, 0.00, 31.99),
    'S2359': (2.00, 0.10, 83.41),
    'S2365': (1.00, 0.35, 35.78),
    'S2369': (4.00, 0.00, 150.00),
    'S2378': (1.00, 0.90, 46.70),
    'S24': (1.00, 0.50, 74.96),
    'S29': (0.00, 0.70, 17.81),
    'S3145': (26.00, 0.70, 652.01),
    'S3147': (7.00, 0.15, 160.88),
    'S3214': (6.00, 0.30, 115.48),
    'S5555': (2.00, 0.00, 28.50),
    'S9987': (7.00, 0.35, 167.80),
}

excel_total = sum(value for _, _, value in september_spirits.values())
print(f"September spirits from Excel: {len(september_spirits)} items")
print(f"Excel total value: €{excel_total:,.2f}")
print()

# Get September stocktake
hotel = Hotel.objects.first()
stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
)

spirit_lines = stocktake.lines.filter(
    item__category_id='S'
).order_by('item__sku')

print("Comparing September counted Excel vs Database:")
print("-" * 80)
print(f"{'SKU':<15} {'Excel Qty':<12} {'DB Qty':<12} {'Excel €':<12} {'DB €':<12} {'Match'}")
print("-" * 80)

db_total = Decimal('0.00')
mismatches = []

for line in spirit_lines:
    sku = line.item.sku
    db_qty = float(line.counted_full_units + line.counted_partial_units)
    db_value = line.counted_value
    db_total += db_value
    
    if sku in september_spirits:
        excel_full, excel_partial, excel_value = september_spirits[sku]
        excel_qty = excel_full + excel_partial
        
        qty_match = abs(excel_qty - db_qty) < 0.01
        value_match = abs(excel_value - float(db_value)) < 1.00
        
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
        
        if db_qty > 0:
            print(f"{sku:<15} {excel_qty:<12.2f} {db_qty:<12.2f} €{excel_value:<11.2f} €{db_value:<11.2f} {match}")
    else:
        if db_qty > 0:
            print(f"{sku:<15} {'N/A':<12} {db_qty:<12.2f} {'N/A':<12} €{db_value:<11.2f} ⚠️")

print("-" * 80)
print(f"Excel Total:  €{excel_total:,.2f}")
print(f"DB Total:     €{db_total:,.2f}")
print(f"Difference:   €{float(db_total) - excel_total:,.2f}")
print()

# Check for items in Excel not in database
print("Items in September Excel but not in database:")
print("-" * 80)
db_skus = set(line.item.sku for line in spirit_lines)
missing = []
for sku in september_spirits:
    if sku not in db_skus:
        excel_full, excel_partial, excel_value = september_spirits[sku]
        missing.append((sku, excel_full + excel_partial, excel_value))
        print(f"{sku:<15} {excel_full + excel_partial:<12.2f} bottles, €{excel_value:.2f}")

if not missing:
    print("✅ All Excel items exist in database")
print("-" * 80)
print()

if mismatches:
    print("MISMATCHES FOUND:")
    print("-" * 80)
    for item in mismatches:
        print(f"{item['sku']:<15} {item['name']}")
        print(f"           Qty:   Excel {item['excel_qty']:.2f}, DB {item['db_qty']:.2f}, Diff: {item['qty_diff']:+.2f}")
        print(f"           Value: Excel €{item['excel_value']:.2f}, DB €{item['db_value']:.2f}, Diff: €{item['value_diff']:+.2f}")
    print("-" * 80)
    print(f"Total mismatches: {len(mismatches)}")
else:
    print("✅ All values match!")

print()
print("=" * 80)
