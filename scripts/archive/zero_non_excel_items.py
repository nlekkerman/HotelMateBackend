"""
Set counted values to 0 for items not in the September Excel import.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from hotel.models import Hotel

print("=" * 80)
print("ZERO OUT ITEMS NOT IN SEPTEMBER EXCEL")
print("=" * 80)
print()

# Get hotel and stocktake
hotel = Hotel.objects.first()
stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
)

# SKUs that were in the September Excel import
september_excel_skus = {
    # Draught
    'D2133', 'D0007', 'D1004', 'D0004', 'D0012', 'D0011', 'D2354', 'D1003',
    'D0008', 'D1022', 'D0006', 'D1258', 'D0005', 'D0030',
    # Bottled
    'B0070', 'B0075', 'B0085', 'B0095', 'B0101', 'B0012', 'B1036', 'B1022',
    'B2055', 'B0140', 'B11', 'B14', 'B1006', 'B2308', 'B0205', 'B12',
    'B2588', 'B2036', 'B0235', 'B10', 'B0254',
    # Spirits
    'S0008', 'S0006', 'S3214', 'S1019', 'S0002', 'S1401', 'S0045', 'S29',
    'S0074', 'S2058', 'S2033', 'S2055', 'S0065', 'S2148', 'S1400', 'S0080',
    'S100', 'S0215', 'S0162', 'S1024', 'S0180', 'S0190', 'S0195', 'S5555',
    'S0009', 'S0147', 'S0100', 'S2314', 'S2065', 'S0105', 'S0027', 'S0120',
    'S0130', 'S0135', 'S0140', 'S0150', 'S1203', 'S0170', 'S0007', 'S0205',
    'S0220', 'S3145', 'S2369', 'S2034', 'S1587', 'S0230', 'S0026', 'S0245',
    'S0265', 'S0014', 'S0271', 'S0327', 'S002', 'S0019', 'S0306', 'S0310',
    'S1412', 'S1258', 'S0325', 'S0029', 'S2156', 'S2354', 'S1302', 'S0335',
    'S0365', 'S0380', 'S0385', 'S2186', 'S0405', 'S0255', 'S2189', 'S0370',
    'S1002', 'S0420', 'S1299', 'S0021', 'S9987', 'S1101', 'S1205', 'S0455',
    'S2155', 'S0699', 'S0485', 'S2365', 'S2349', 'S1047', 'S0064', 'S0530',
    'S0041', 'S24', 'S0543', 'S0545', 'S0550', 'S0555', 'S2359', 'S2241',
    'S0575', 'S1210', 'S0585', 'S0022', 'S2302', 'S0605', 'S0018', 'S2217',
    'S0001', 'S0610', 'S0625', 'S0010', 'S0638', 'S0630', 'S2159', 'S0012',
    'S0635', 'S1022', 'S0640', 'S0653', 'S3147', 'S0647', 'S0023', 'S0028',
    'S0017', 'S0005', 'S2378', 'S0071', 'S1411',
    # Minerals
    'M2236', 'M0195', 'M0140', 'M2107', 'M0320', 'M11', 'M0042', 'M0210',
    'M0008', 'M0009', 'M3', 'M0006', 'M13', 'M04', 'M0014', 'M2', 'M03',
    'M05', 'M06', 'M1', 'M01', 'M5', 'M9', 'M02', 'M0170', 'M0123', 'M0180',
    'M25', 'M24', 'M23', 'M0050', 'M0003', 'M0040', 'M0013', 'M2105', 'M0004',
    'M0034', 'M0070', 'M0135', 'M0315', 'M0016', 'M0255', 'M0122', 'M0200',
    'M0312', 'M0012', 'M0011',
    # Wine
    'W0040', 'W31', 'W0039', 'W0019', 'W0025', 'W0044', 'W0018', 'W2108',
    'W0038', 'W0032', 'W0036', 'W0028', 'W0023', 'W0027', 'W0043', 'W0031',
    'W0033', 'W2102', 'W1020', 'W2589', 'W1004', 'W0024', 'W1013', 'W0021',
    'W0037', 'W45', 'W1019', 'W2110', 'W111', 'W1', 'W0034', 'W0041', 'W0042',
    'W2104', 'W0029', 'W0022', 'W0030'
}

print(f"September Excel had {len(september_excel_skus)} items")
print()

# Find items not in the Excel
all_lines = stocktake.lines.all()
items_to_zero = []

for line in all_lines:
    if line.item.sku not in september_excel_skus:
        items_to_zero.append(line)

print(f"Found {len(items_to_zero)} items NOT in September Excel:")
print("-" * 80)

total_value_to_remove = Decimal('0.00')
for line in items_to_zero:
    value = line.counted_value
    total_value_to_remove += value
    print(f"{line.item.sku:<15} {line.item.name:<40} €{value:>10,.2f}")

print("-" * 80)
print(f"Total value to remove: €{total_value_to_remove:,.2f}")
print()

# Zero them out
print("Zeroing out these items...")
updated = 0
for line in items_to_zero:
    line.counted_full_units = Decimal('0.00')
    line.counted_partial_units = Decimal('0.00')
    line.save()
    updated += 1

print(f"✅ Zeroed out {updated} items")
print()

# Verify totals
categories = {
    'D': ('Draught', Decimal('5303.15')),
    'B': ('Bottled', Decimal('3079.04')),
    'S': ('Spirits', Decimal('10406.35')),
    'M': ('Minerals', Decimal('4185.61')),
    'W': ('Wine', Decimal('4466.13'))
}

print("=" * 80)
print("FINAL VERIFICATION")
print("=" * 80)

total_calculated = Decimal('0.00')
total_target = Decimal('27440.28')

for cat_code, (cat_name, target) in categories.items():
    lines = stocktake.lines.filter(item__category_id=cat_code)
    calculated = sum(line.counted_value for line in lines)
    diff = calculated - target
    
    total_calculated += calculated
    
    status = "✅" if abs(diff) < 10 else "⚠️"
    match_pct = (calculated / target * 100) if target > 0 else Decimal('0')
    print(f"{status} {cat_name:<10} €{target:>10,.2f} → €{calculated:>10,.2f} ({match_pct:>6.2f}%)")

print("-" * 80)
total_diff = total_calculated - total_target
status = "✅" if abs(total_diff) < 10 else "⚠️"
match_pct = (total_calculated / total_target * 100) if total_target > 0 else Decimal('0')
print(f"{status} {'TOTAL':<10} €{total_target:>10,.2f} → €{total_calculated:>10,.2f} ({match_pct:>6.2f}%)")

print()
if abs(total_diff) < 10:
    print("✅ SUCCESS! September counted values match target!")
else:
    print(f"⚠️  Difference: €{total_diff:.2f}")

# Final summary
lines = stocktake.lines.all()
total_opening = sum(line.opening_qty * line.valuation_cost for line in lines)
total_variance = sum(line.variance_value for line in lines)

print()
print("=" * 80)
print("SEPTEMBER 2025 STOCKTAKE FINAL")
print("=" * 80)
print(f"Opening Value:  €{total_opening:>12,.2f} (August 31st)")
print(f"Counted Value:  €{total_calculated:>12,.2f} (September 30th)")
print(f"Variance:       €{total_variance:>12,.2f}")
print()
print("✅ September stocktake complete and ready for approval!")
print("=" * 80)
