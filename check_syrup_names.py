"""
Check current syrup names to see which need "Monin" prefix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

skus = ['M3', 'M04', 'M03', 'M05', 'M06', 'M1', 'M01', 'M5', 'M9', 'M02', 
        'M2', 'M13', 'M0006', 'M0014', 'M0008', 'M0009']

print("Current names in database:")
print("=" * 70)

for sku in skus:
    try:
        item = StockItem.objects.get(sku=sku, category_id='M')
        has_monin = 'Monin' in item.name
        marker = '✓' if has_monin else '❌'
        print(f"{marker} {item.sku}\t{item.name}")
    except StockItem.DoesNotExist:
        print(f"❌ {sku}\tNOT FOUND")
