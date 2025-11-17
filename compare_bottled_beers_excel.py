"""
Compare Excel bottled beers with database
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockItem, StockCategory, StockSnapshot, StockPeriod
)

# Excel data - SKU and Stock at Cost
excel_data = {
    'B0070': Decimal('21.54'),
    'B0075': Decimal('38.12'),
    'B0085': Decimal('50.60'),
    'B0095': Decimal('26.00'),
    'B0101': Decimal('25.21'),
    'B0012': Decimal('26.03'),
    'B1036': Decimal('55.88'),
    'B1022': Decimal('25.67'),
    'B2055': Decimal('18.33'),
    'B0140': Decimal('25.21'),
    'B11': Decimal('56.69'),
    'B14': Decimal('56.69'),
    'B1006': Decimal('48.40'),
    'B2308': Decimal('44.51'),
    'B0205': Decimal('27.50'),
    'B12': Decimal('47.85'),
    'B2588': Decimal('21.91'),
    'B2036': Decimal('37.58'),
    'B0235': Decimal('37.58'),
    'B10': Decimal('39.23'),
    'B0254': Decimal('23.83'),
}

excel_total = sum(excel_data.values())

print("=" * 80)
print("BOTTLED BEERS - EXCEL vs DATABASE COMPARISON")
print("=" * 80)
print(f"\nExcel items: {len(excel_data)}")
print(f"Excel total: €{excel_total:.2f}\n")

# Get database items
cat = StockCategory.objects.filter(code='B').first()
items = StockItem.objects.filter(
    hotel_id=2,
    category=cat,
    active=True
).order_by('sku')

jan = StockPeriod.objects.filter(
    start_date__year=2025,
    start_date__month=1
).first()

print(f"Database active items: {items.count()}\n")

print("=" * 80)
print("ITEM COMPARISON")
print("=" * 80)
print(f"{'SKU':<10} {'Name':<30} {'Excel €':<12} {'DB €':<12} {'Match':<8}")
print("-" * 80)

db_total = Decimal('0')
matched = 0
missing_in_db = []
extra_in_db = []

# Check Excel items against DB
for sku, excel_value in sorted(excel_data.items()):
    item = items.filter(sku=sku).first()
    if item:
        snap = StockSnapshot.objects.filter(
            item=item,
            period=jan
        ).first() if jan else None
        
        db_value = snap.closing_stock_value if snap else Decimal('0')
        db_total += db_value
        
        match = "✅" if abs(db_value - excel_value) < Decimal('0.01') else "❌"
        if match == "✅":
            matched += 1
        
        print(f"{sku:<10} {item.name[:28]:<30} {excel_value:>10.2f} {db_value:>10.2f}  {match}")
    else:
        missing_in_db.append(sku)
        print(f"{sku:<10} {'MISSING IN DB':<30} {excel_value:>10.2f} {'---':>10}  ❌")

# Check for extra items in DB
print("\n" + "=" * 80)
print("EXTRA ITEMS IN DATABASE (not in Excel)")
print("=" * 80)

for item in items:
    if item.sku not in excel_data:
        snap = StockSnapshot.objects.filter(
            item=item,
            period=jan
        ).first() if jan else None
        
        db_value = snap.closing_stock_value if snap else Decimal('0')
        db_total += db_value
        extra_in_db.append(item.sku)
        print(f"{item.sku:<10} {item.name[:28]:<30} {'---':>10} {db_value:>10.2f}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Excel total:     €{excel_total:>10.2f} ({len(excel_data)} items)")
print(f"Database total:  €{db_total:>10.2f} ({items.count()} items)")
print(f"Difference:      €{db_total - excel_total:>10.2f}")
print(f"\nMatched items:   {matched}/{len(excel_data)}")
print(f"Missing in DB:   {len(missing_in_db)}")
print(f"Extra in DB:     {len(extra_in_db)}")

if missing_in_db:
    print(f"\nMissing SKUs: {', '.join(missing_in_db)}")
if extra_in_db:
    print(f"\nExtra SKUs: {', '.join(extra_in_db)}")

print("\n" + "=" * 80)
