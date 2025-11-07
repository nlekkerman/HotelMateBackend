"""
Verify StockItems and StockSnapshots have correct data from Excel
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

from stock_tracker.models import StockItem, StockSnapshot, StockPeriod
from hotel.models import Hotel
from decimal import Decimal


hotel = Hotel.objects.first()
period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)

print("=" * 70)
print("VERIFICATION: Stock Items & Snapshots Data")
print("=" * 70)

print(f"\n🏨 Hotel: {hotel.name}")
print(f"📅 Period: {period.period_name}")
print(f"🔒 Status: {'CLOSED' if period.is_closed else 'OPEN'}")

# Get all snapshots
snapshots = StockSnapshot.objects.filter(hotel=hotel, period=period).select_related('item', 'item__category')

print(f"\n📊 Total Snapshots: {snapshots.count()}")

# Group by category
categories = {}
for snapshot in snapshots:
    cat = snapshot.item.category.code
    if cat not in categories:
        categories[cat] = {
            'count': 0,
            'value': Decimal('0.00'),
            'items': []
        }
    categories[cat]['count'] += 1
    categories[cat]['value'] += snapshot.closing_stock_value
    categories[cat]['items'].append({
        'sku': snapshot.item.sku,
        'name': snapshot.item.name,
        'full': snapshot.closing_full_units,
        'partial': snapshot.closing_partial_units,
        'value': snapshot.closing_stock_value
    })

# Display by category
print("\n" + "=" * 70)
print("BREAKDOWN BY CATEGORY")
print("=" * 70)

category_names = {
    'D': 'Draught Beers',
    'B': 'Bottled Beers',
    'S': 'Spirits',
    'W': 'Wines',
    'M': 'Minerals & Syrups'
}

for cat_code in ['D', 'B', 'S', 'W', 'M']:
    if cat_code in categories:
        cat = categories[cat_code]
        print(f"\n{cat_code} - {category_names[cat_code]}:")
        print(f"  Items: {cat['count']}")
        print(f"  Total Value: €{cat['value']:,.2f}")
        
        # Show first 5 items as sample
        print(f"  Sample items:")
        for item in cat['items'][:5]:
            print(f"    {item['sku']:<20} Full: {item['full']:>6.2f}  Partial: {item['partial']:>8.4f}  Value: €{item['value']:>10.2f}")
        
        if len(cat['items']) > 5:
            print(f"    ... and {len(cat['items']) - 5} more items")

# Grand total
grand_total = sum(cat['value'] for cat in categories.values())
excel_total = Decimal('27306.51')

print("\n" + "=" * 70)
print("FINAL VERIFICATION")
print("=" * 70)
print(f"\nDatabase Total: €{grand_total:,.2f}")
print(f"Excel Total:    €{excel_total:,.2f}")
print(f"Difference:     €{grand_total - excel_total:,.2f}")

if abs(grand_total - excel_total) < Decimal('0.10'):
    print("\n✅ PERFECT MATCH! All data is correct.")
elif abs(grand_total - excel_total) < Decimal('1.00'):
    print("\n✅ VERIFIED! Data matches Excel (within €1)")
else:
    print("\n⚠️  WARNING: Significant difference detected")

print(f"\n🔒 Period Status: {'CLOSED ✅' if period.is_closed else 'OPEN ⚠️'}")
print("=" * 70)
