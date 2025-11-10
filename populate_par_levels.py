#!/usr/bin/env python
"""Populate par_level values for all stock items based on category."""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from hotel.models import Hotel
from decimal import Decimal

hotel = Hotel.objects.first()
if not hotel:
    print('No hotel found')
    exit(1)

# Define par levels by category (in servings)
PAR_LEVELS = {
    'D': 100,   # Draught Beer - 100 pints minimum
    'B': 60,    # Bottled Beer - 60 bottles minimum (5 cases)
    'S': 40,    # Spirits - 40 shots minimum (2 bottles)
    'W': 30,    # Wine - 30 glasses minimum (4-5 bottles)
    'M': 50,    # Minerals - 50 servings minimum
}

items = StockItem.objects.filter(hotel=hotel)
updated_count = 0

print("Setting par levels for all items...\n")

for item in items:
    category = item.category.code if item.category else None
    
    if category in PAR_LEVELS:
        par_level = Decimal(str(PAR_LEVELS[category]))
        item.par_level = par_level
        item.save(update_fields=['par_level'])
        updated_count += 1
        
        if updated_count <= 10:  # Show first 10
            print(f"  {item.sku:12} ({category}) -> par_level: {par_level}")

print(f"\n✓ Updated {updated_count} items with par levels")
print("\nPar level summary by category:")
for cat, level in PAR_LEVELS.items():
    count = items.filter(category__code=cat).count()
    print(f"  {cat}: {level} servings minimum ({count} items)")

# Now check low stock with par levels
print("\n" + "="*60)
print("Checking items below par level:")
print("="*60)

low_stock_items = []
for item in items:
    if item.par_level and item.total_stock_in_servings < item.par_level:
        low_stock_items.append(item)

print(f"\nItems below par level: {len(low_stock_items)}")

if low_stock_items:
    print("\nTop 15 items needing restock:")
    for item in low_stock_items[:15]:
        deficit = item.par_level - item.total_stock_in_servings
        print(f"  {item.sku:12} {item.name[:30]:32} | "
              f"Stock: {item.total_stock_in_servings:6.1f} | "
              f"Par: {item.par_level:6.1f} | "
              f"Need: {deficit:6.1f}")

print("\n✓ Par levels configured successfully!")
