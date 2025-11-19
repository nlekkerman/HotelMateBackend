#!/usr/bin/env python
"""Check actual database values for M0006"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine

# Get the syrup line
line = StocktakeLine.objects.filter(
    stocktake__id=45,
    item__sku='M0006'
).first()

if line:
    print(f"\nDATABASE VALUES for {line.item.name} (SKU: {line.item.sku})")
    print("=" * 80)
    print(f"counted_full_units (DB):    {line.counted_full_units}")
    print(f"counted_partial_units (DB): {line.counted_partial_units}")
    print(f"")
    print(f"counted_qty (calculated):   {line.counted_qty}")
    print(f"expected_qty (calculated):  {line.expected_qty}")
    print(f"variance_qty (calculated):  {line.variance_qty}")
    print(f"")
    print(f"Item UOM: {line.item.uom}")
    print(f"Item Subcategory: {line.item.subcategory}")
else:
    print("Line not found!")
