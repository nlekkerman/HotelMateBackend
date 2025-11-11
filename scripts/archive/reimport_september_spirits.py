"""
Re-import September counted with correct spirits data including Sea Dog & Dingle Whiskey.
Note: S_SEADOG and S_DINGLE_WHISKEY appear in September but NOT in August.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from hotel.models import Hotel

print("=" * 80)
print("RE-IMPORT SEPTEMBER SPIRITS COUNTED (WITH SEA DOG & DINGLE WHISKEY)")
print("=" * 80)
print()

# Get September stocktake
hotel = Hotel.objects.first()
stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
)

# September spirits counted from your Excel
# Note: Sea Dog Rum (17.13) and Dingle Whiskey (37.50) have NO August opening
september_spirits_counted = {
    'S0008': (2.00, 0.00),
    'S0006': (2.00, 0.25),
    'S3214': (6.00, 0.30),
    'S1019': (2.00, 0.60),
    'S0002': (8.00, 0.80),
    'S1401': (3.00, 0.50),
    'S0045': (7.00, 0.05),
    'S29': (0.00, 0.70),
    'S0074': (12.00, 0.90),
    'S2058': (0.00, 0.95),
    'S2033': (2.00, 0.40),
    'S2055': (2.00, 0.50),
    'S0065': (1.00, 0.90),
    'S2148': (2.00, 0.50),
    'S1400': (0.00, 0.90),
    'S0080': (0.00, 0.90),
    'S100': (5.00, 0.05),
    'S0215': (2.50, 0.00),
    'S0162': (1.50, 0.00),
    'S0180': (0.40, 0.00),
    'S0190': (2.00, 0.10),
    'S0195': (2.00, 0.00),
    'S5555': (2.00, 0.00),
    'S0147': (0.00, 0.90),
    'S0100': (2.00, 0.00),
    'S2314': (2.00, 0.50),
    'S2065': (0.00, 0.35),
    'S0105': (3.00, 0.55),
    'S0027': (0.00, 0.85),
    'S0120': (6.00, 0.85),
    'S0130': (3.00, 0.70),
    'S0135': (4.00, 0.05),
    'S0140': (2.00, 0.60),
    'S0150': (5.00, 0.70),
    'S1203': (2.00, 0.20),
    'S0170': (1.00, 0.70),
    'S0007': (6.00, 0.40),
    'S0205': (0.00, 0.60),
    'S0220': (3.00, 0.90),
    'S3145': (26.00, 0.70),
    'S2369': (4.00, 0.00),
    'S2034': (9.00, 0.70),
    'S0230': (0.00, 0.10),
    'S0026': (3.00, 0.65),
    'S0245': (3.00, 0.30),
    'S0014': (2.00, 0.10),
    'S0271': (1.00, 0.85),
    'S0327': (1.00, 0.20),
    'S002': (5.00, 0.90),
    'S0306': (7.00, 0.15),
    'S0310': (3.00, 0.95),
    'S1412': (10.00, 0.30),
    'S1258': (0.00, 0.85),
    'S0325': (3.00, 0.20),
    'S0029': (1.00, 0.90),
    'S2156': (2.00, 0.30),
    'S2354': (1.00, 0.00),
    'S1302': (2.00, 0.30),
    'S0335': (3.00, 0.50),
    'S0365': (2.00, 0.40),
    'S0380': (4.00, 0.40),
    'S0385': (3.00, 0.50),
    'S2186': (2.00, 0.20),
    'S0405': (8.00, 0.15),
    'S0255': (1.00, 0.95),
    'S2189': (1.00, 0.70),
    'S0370': (2.00, 0.75),
    'S1002': (3.00, 0.50),
    'S0420': (5.00, 0.95),
    'S1299': (1.00, 0.95),
    'S0021': (2.00, 0.30),
    'S9987': (7.00, 0.35),
    'S1101': (2.00, 0.15),
    'S0455': (1.00, 0.90),
    'S2155': (2.00, 0.00),
    'S0699': (5.00, 0.60),
    'S0485': (2.00, 0.70),
    'S2365': (1.00, 0.35),
    'S2349': (0.00, 0.60),
    'S1047': (1.00, 0.05),
    'S0064': (2.00, 0.20),
    'S0530': (4.00, 0.70),
    'S0041': (4.00, 0.00),
    'S24': (1.00, 0.50),
    'S0543': (10.00, 0.55),
    'S0545': (1.00, 0.00),
    'S0550': (0.00, 0.05),
    'S0555': (3.00, 0.25),
    'S2359': (2.00, 0.10),
    'S2241': (1.00, 0.75),
    'S0575': (0.00, 0.60),
    'S1210': (3.00, 0.05),
    'S0585': (2.00, 0.20),
    'S0022': (4.00, 0.90),
    'S2302': (1.00, 0.60),
    'S0605': (2.00, 0.20),
    'S0018': (2.00, 0.15),
    'S2217': (0.00, 0.90),
    'S0001': (2.00, 0.70),
    'S0610': (45.00, 0.80),
    'S0625': (2.00, 0.80),
    'S0010': (2.00, 0.00),
    'S0638': (1.00, 0.40),
    'S0638_00': (0.00, 0.00),  # Zero out - Tanquery 0.0% (not a real SKU)
    'S0630': (0.00, 0.05),
    'S0012': (1.00, 0.00),
    'S0635': (6.00, 0.95),
    'S0640': (6.00, 0.50),
    'S0653': (2.00, 0.95),
    'S3147': (7.00, 0.15),
    'S0647': (3.00, 0.00),
    'S0023': (1.90, 0.00),
    'S0028': (2.00, 0.00),
    'S0017': (1.00, 0.10),
    'S0005': (2.00, 0.00),
    'S2378': (1.00, 0.90),
    'S0071': (0.00, 0.80),
    'S1411': (1.80, 0.85),
    'S_SEADOG': (0.00, 0.80),  # Sea Dog Rum - 0.80 bottles (NOT in August)
    'S_DINGLE_WHISKEY': (2.00, 0.00),  # Dingle Whiskey - 2 bottles (NOT in August)
}

print(f"Updating {len(september_spirits_counted)} spirit items...")
print()

updated = 0
not_found = []

for sku, (full, partial) in september_spirits_counted.items():
    try:
        line = stocktake.lines.get(item__sku=sku, item__category_id='S')
        line.counted_full_units = Decimal(str(full))
        line.counted_partial_units = Decimal(str(partial))
        line.save()
        updated += 1
    except:
        not_found.append(sku)

print(f"✅ Updated {updated} spirit lines")
if not_found:
    print(f"⚠️  Not found: {', '.join(not_found)}")
print()

# Verify
spirit_lines = stocktake.lines.filter(item__category_id='S')
total = sum(line.counted_value for line in spirit_lines)

print("=" * 80)
print(f"Total spirits counted value: €{total:,.2f}")
print(f"Expected from Excel:         €10,406.35")
print(f"Difference:                  €{float(total) - 10406.35:,.2f}")
print("=" * 80)
