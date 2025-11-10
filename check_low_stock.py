#!/usr/bin/env python
"""Check low stock items and their details."""
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

# Get all items
all_items = StockItem.objects.filter(hotel=hotel)
print(f"Total items: {all_items.count()}")

# Get low stock items (current_full_units <= 2)
low_stock = all_items.filter(current_full_units__lte=2)
print(f"Low stock items (full_units <= 2): {low_stock.count()}")

# Check items with zero stock (both full and partial)
zero_stock = all_items.filter(
    current_full_units=0,
    current_partial_units=0
)
print(f"Zero stock items: {zero_stock.count()}")

# Check items with some partial stock but no full units
partial_only = all_items.filter(
    current_full_units=0,
    current_partial_units__gt=0
)
print(f"Partial stock only: {partial_only.count()}")

# Show distribution
print("\n=== Stock Distribution ===")
print(f"Full units = 0: {all_items.filter(current_full_units=0).count()}")
print(f"Full units = 1: {all_items.filter(current_full_units=1).count()}")
print(f"Full units = 2: {all_items.filter(current_full_units=2).count()}")
print(f"Full units > 2: {all_items.filter(current_full_units__gt=2).count()}")

print("\n=== Sample Low Stock Items ===")
for item in low_stock[:15]:
    total_servings = item.total_stock_in_servings
    print(f"{item.sku:12} | Full: {item.current_full_units:6} | "
          f"Partial: {item.current_partial_units:10.2f} | "
          f"Total servings: {total_servings:10.2f}")

print("\n✓ Low stock data is available!")
print(f"  API endpoint should return {low_stock.count()} items")
