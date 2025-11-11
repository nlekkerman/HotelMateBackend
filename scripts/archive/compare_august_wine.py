"""
Compare August closing wine data with September opening stock.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from hotel.models import Hotel

print("=" * 80)
print("COMPARE AUGUST CLOSING WITH SEPTEMBER OPENING (WINE)")
print("=" * 80)
print()

# August closing from Excel
august_wine = {
    'W0040': (36.00, 0.00, 124.92),
    'W31': (57.00, 0.00, 184.11),
    'W0039': (0.00, 0.00, 0.00),
    'W0019': (10.00, 0.00, 186.70),
    'W0025': (6.00, 0.00, 97.98),
    'W0044': (3.00, 0.00, 36.18),
    'W0018': (12.00, 0.00, 123.00),
    'W2108': (62.20, 0.00, 424.83),
    'W0038': (11.00, 0.00, 108.13),
    'W0032': (6.00, 0.00, 64.98),
    'W0036': (6.00, 0.00, 94.98),
    'W0028': (11.00, 0.00, 170.50),
    'W0023': (6.00, 0.00, 48.84),
    'W0027': (28.10, 0.00, 210.75),
    'W0043': (4.20, 0.00, 21.80),
    'W0031': (13.10, 0.00, 111.35),
    'W0033': (12.00, 0.00, 102.00),
    'W2102': (28.05, 0.00, 214.30),
    'W1020': (24.90, 0.00, 174.30),
    'W2589': (43.50, 0.00, 268.40),
    'W1004': (50.40, 0.00, 310.97),
    'W0024': (8.00, 0.00, 124.00),
    'W1013': (13.00, 0.00, 402.87),
    'W0021': (27.00, 0.00, 266.76),
    'W0037': (8.00, 0.00, 140.00),
    'W45': (8.00, 0.00, 92.00),
    'W1019': (4.00, 0.00, 37.32),
    'W2110': (1.00, 0.00, 7.96),
    'W111': (8.70, 0.00, 36.28),
    'W1': (10.00, 0.00, 89.30),
    'W0034': (15.20, 0.00, 114.00),
    'W0041': (18.00, 0.00, 187.74),
    'W0042': (6.00, 0.00, 38.88),
    'W2104': (86.20, 0.00, 596.50),
    'W0029': (13.00, 0.00, 127.79),
    'W0022': (44.50, 0.00, 304.83),
    'W0030': (6.00, 0.00, 87.00),
}

print(f"August wine closing: {len(august_wine)} items, Total: €5,732.24")
print()

# Get September stocktake
hotel = Hotel.objects.first()
stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
)

wine_lines = stocktake.lines.filter(item__category_id='W').order_by('item__sku')

print("Comparing August closing with September opening:")
print("-" * 80)
print(f"{'SKU':<10} {'Aug Qty':<10} {'Sep Open':<10} {'Match':<8} {'Name'}")
print("-" * 80)

mismatches = []
for line in wine_lines:
    sku = line.item.sku
    sept_opening = float(line.opening_qty)
    
    if sku in august_wine:
        aug_full, aug_partial, aug_value = august_wine[sku]
        aug_qty = aug_full + aug_partial
        
        match = "✅" if abs(aug_qty - sept_opening) < 0.01 else "❌"
        if match == "❌":
            mismatches.append({
                'sku': sku,
                'name': line.item.name,
                'august': aug_qty,
                'september': sept_opening,
                'diff': sept_opening - aug_qty
            })
        
        print(f"{sku:<10} {aug_qty:<10.2f} {sept_opening:<10.2f} {match:<8} {line.item.name}")
    else:
        print(f"{sku:<10} {'N/A':<10} {sept_opening:<10.2f} {'⚠️':<8} {line.item.name} (Not in August)")

print("-" * 80)
print()

# Check for items in August not in September
print("Items in August Excel but not found in September stocktake:")
print("-" * 80)
sept_skus = set(line.item.sku for line in wine_lines)
missing = []
for sku in august_wine:
    if sku not in sept_skus:
        aug_full, aug_partial, aug_value = august_wine[sku]
        missing.append((sku, aug_full + aug_partial, aug_value))
        print(f"{sku:<10} {aug_full + aug_partial:<10.2f} bottles, €{aug_value:.2f}")

if not missing:
    print("✅ All August items exist in September stocktake")
print("-" * 80)
print()

if mismatches:
    print("MISMATCHES FOUND:")
    print("-" * 80)
    for item in mismatches:
        print(f"{item['sku']:<10} August: {item['august']:.2f}, "
              f"September: {item['september']:.2f}, Diff: {item['diff']:+.2f}")
        print(f"           {item['name']}")
    print("-" * 80)
else:
    print("✅ All quantities match between August closing and September opening!")

print()
print("=" * 80)
