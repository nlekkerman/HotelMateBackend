import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("=" * 80)
print("JUICES ITEMS - CATEGORY CHECK")
print("=" * 80)

items = StockItem.objects.filter(subcategory='JUICES').order_by('sku')

print(f"\n{'SKU':<8} {'Name':<40} {'Size':<8} {'UOM':<8} {'Correct Category'}")
print("-" * 80)

for item in items:
    # Split bottles (small bottles in dozens) should be SOFT_DRINKS
    # 1L bottles should stay as JUICES
    if 'Split' in item.name or (item.size == 'Doz' and 'Litre' not in item.name):
        correct_category = 'SOFT_DRINKS'
    else:
        correct_category = 'JUICES (OK)'
    
    print(f"{item.sku:<8} {item.name[:40]:<40} {item.size:<8} {item.uom:<8} {correct_category}")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)
print("Split bottles should be SOFT_DRINKS (cases + bottles tracking)")
print("1L bottles should stay JUICES (cases + bottles + ml tracking)")
