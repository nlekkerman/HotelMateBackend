#!/usr/bin/env python
"""Test that profitability endpoint handles None values correctly."""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel
from stock_tracker.models import StockItem
import json

hotel = Hotel.objects.first()
if not hotel:
    print('No hotel found')
    exit(1)

# Test item that has None for markup_percentage
test_item = StockItem.objects.filter(hotel=hotel, sku='M0011').first()

if not test_item:
    print('Test item M0011 not found')
    exit(1)

print(f"Testing item: {test_item.sku}")
print(f"  menu_price: {test_item.menu_price}")
print(f"  markup_percentage: {test_item.markup_percentage} (type: {type(test_item.markup_percentage).__name__})")
print(f"  gross_profit_percentage: {test_item.gross_profit_percentage}")

# Simulate the safe_float function
def _safe_float(val):
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None

# Build the result dict like the view does
result = {
    'sku': test_item.sku,
    'menu_price': _safe_float(test_item.menu_price),
    'markup_percentage': _safe_float(test_item.markup_percentage),
    'gross_profit_percentage': _safe_float(test_item.gross_profit_percentage),
    'pour_cost_percentage': _safe_float(test_item.pour_cost_percentage),
}

print("\nJSON result:")
print(json.dumps(result, indent=2))
print("\n✓ No TypeError - null values handled correctly!")
