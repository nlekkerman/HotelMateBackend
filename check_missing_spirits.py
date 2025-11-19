import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from hotel.models import Hotel

hotel = Hotel.objects.first()

# Search for the items that have blank codes in Excel
search_terms = [
    'Tanquery 70cl 0.0',
    'Tanquery 0.0',
    'Sea Dog',
    'Dingle Whiskey'
]

print("Searching for potentially missing items in system:")
print("=" * 80)

for term in search_terms:
    items = StockItem.objects.filter(
        hotel=hotel,
        category__code='S',
        name__icontains=term
    )
    
    if items.exists():
        print(f"\n✓ Found items matching '{term}':")
        for item in items:
            print(f"  SKU: {item.sku:<20} Name: {item.name}")
            print(f"  Unit Cost: €{item.unit_cost}")
    else:
        print(f"\n✗ No items found matching '{term}'")

print("\n" + "=" * 80)
print("\nAll Spirits items in system:")
print("=" * 80)

all_spirits = StockItem.objects.filter(
    hotel=hotel,
    category__code='S'
).order_by('sku')

print(f"Total: {all_spirits.count()} items\n")

for item in all_spirits:
    print(f"{item.sku:<20} {item.name[:50]:<50} €{item.unit_cost:>8.2f}")
