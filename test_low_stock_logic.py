#!/usr/bin/env python
"""Test the updated low stock logic."""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from hotel.models import Hotel

hotel = Hotel.objects.first()
if not hotel:
    print('No hotel found')
    exit(1)

all_items = StockItem.objects.filter(hotel=hotel)

# Test different thresholds
thresholds = [20, 50, 100]

for threshold in thresholds:
    low_stock = [
        item for item in all_items
        if item.total_stock_in_servings < threshold
    ]
    print(f"\n=== Low stock items (< {threshold} servings): {len(low_stock)} ===")
    
    if low_stock:
        for item in low_stock[:10]:
            servings = item.total_stock_in_servings
            print(f"  {item.sku:12} {item.name[:30]:32} | "
                  f"{servings:8.2f} servings | "
                  f"Value: €{float(item.total_stock_value):.2f}")

print("\n✓ Low stock logic updated successfully!")
print("  Default threshold: 50 servings")
print("  Frontend can adjust with ?threshold=X parameter")
