"""
Find uncategorized minerals items
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

uncategorized = StockItem.objects.filter(
    category_id='M',
    subcategory__isnull=True
)

print(f'Uncategorized Minerals Items: {uncategorized.count()}\n')

for item in uncategorized:
    print(f'{item.sku}: {item.name}')
    print(f'  Size: {item.size}')
    print(f'  UOM: {item.uom}')
    print()
