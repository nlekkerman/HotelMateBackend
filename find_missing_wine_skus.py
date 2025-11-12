"""
Find all Wine items in database and identify missing SKUs
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockPeriod, StockSnapshot
from hotel.models import Hotel

hotel = Hotel.objects.first()

# Get September period
sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)

print("=" * 100)
print("ALL WINE ITEMS IN DATABASE")
print("=" * 100)
print()

# Get all Wine items
wine_items = StockItem.objects.filter(
    hotel=hotel,
    category__name='Wine'
).order_by('sku')

print(f"Total Wine items in database: {wine_items.count()}")
print()

# SKUs from Excel data
excel_skus = {
    'W0040', 'W31', 'W0039', 'W0019', 'W0025', 'W0044', 'W0018', 'W2108',
    'W0038', 'W0032', 'W0036', 'W0028', 'W0023', 'W0027', 'W0043', 'W0031',
    'W0033', 'W2102', 'W1020', 'W2589', 'W1004', 'W0024', 'W1013', 'W0021',
    'W0037', 'W45', 'W1019', 'W2110', 'W111', 'W1', 'W0034', 'W0041',
    'W0042', 'W2104', 'W0029', 'W0022', 'W0030',
    # Items without SKU codes in Excel
    'W_PACSAUD', 'W_PINOT_SNIPES', 'W_PROSECCO_NA',
    'W_MDC_PROSECCO', 'W_OG_SHIRAZ_75', 'W_OG_SHIRAZ_187', 'W_OG_SAUV_187'
}

print(f"SKUs from Excel: {len(excel_skus)}")
print()

# Check which database items are NOT in Excel
db_skus = set(wine_items.values_list('sku', flat=True))
missing_in_excel = db_skus - excel_skus
in_excel_but_not_db = excel_skus - db_skus

print("=" * 100)
print("DATABASE SKUs NOT IN EXCEL (these need values assigned):")
print("=" * 100)
for sku in sorted(missing_in_excel):
    item = wine_items.get(sku=sku)
    snapshot = StockSnapshot.objects.filter(
        period=sept_period,
        item=item
    ).first()
    current_value = snapshot.closing_stock_value if snapshot else Decimal('0.00')
    print(f"{sku:20s} - {item.name:50s} Current: €{current_value:>8.2f}")

print()
print("=" * 100)
print("EXCEL SKUs NOT IN DATABASE (these might be typos):")
print("=" * 100)
for sku in sorted(in_excel_but_not_db):
    print(f"  {sku}")

print()
print("=" * 100)
print("CURRENT SEPTEMBER WINE TOTAL BY SKU:")
print("=" * 100)
total = Decimal('0.00')
for item in wine_items:
    snapshot = StockSnapshot.objects.filter(
        period=sept_period,
        item=item
    ).first()
    if snapshot and snapshot.closing_stock_value > 0:
        print(f"{item.sku:20s}: €{snapshot.closing_stock_value:>8.2f}")
        total += snapshot.closing_stock_value

print("-" * 100)
print(f"{'TOTAL':20s}: €{total:>8.2f}")
print(f"Expected: €4,466.13")
print(f"Difference: €{total - Decimal('4466.13'):.2f}")
print()
print("=" * 100)
