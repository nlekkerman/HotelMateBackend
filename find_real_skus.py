"""
Find actual SKUs in database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n=== BOTTLED BEER (first 10) ===")
for item in StockItem.objects.filter(sku__startswith='BB').order_by('sku')[:10]:
    print(f"{item.sku}: {item.name}")

print("\n=== DRAUGHT BEER (all) ===")
for item in StockItem.objects.filter(sku__startswith='DB').order_by('sku'):
    print(f"{item.sku}: {item.name}")

print("\n=== MINERALS (first 20) ===")
for item in StockItem.objects.filter(sku__startswith='M').order_by('sku')[:20]:
    print(f"{item.sku}: {item.name}")

print("\n=== Search for specific items ===")
searches = ['Killarney', 'Guinness', 'Heineken', 'Split 7up', 'Splash Cola']
for search in searches:
    items = StockItem.objects.filter(name__icontains=search)
    print(f"\n'{search}':")
    for item in items:
        print(f"  {item.sku}: {item.name}")
