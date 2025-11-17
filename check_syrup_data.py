"""
Check syrup stocktake line data in February
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, Stocktake
from decimal import Decimal

# Get February stocktake
february = Stocktake.objects.filter(
    hotel_id=2,
    period__month=2,
    period__year=2025
).first()

if not february:
    print("❌ No February stocktake found")
else:
    print(f"📋 Stocktake #{february.id} - {february.period.name}")
    print("=" * 80)
    
    # Get syrup lines
    syrup_lines = StocktakeLine.objects.filter(
        stocktake=february,
        item__subcategory='SYRUPS'
    ).select_related('item')[:3]  # Just first 3 for testing
    
    print("\nSYRUP STOCKTAKE LINES:")
    print("=" * 80)
    
    for line in syrup_lines:
        print(f"\n📦 {line.item.name}")
        print(f"   SKU: {line.item.sku}")
        print(f"   Size: {line.item.size}")
        print(f"   UOM: {line.item.uom} ml")
        print(f"   Category: {line.item.category_id}")
        print(f"   Subcategory: {line.item.subcategory}")
        print(f"\n   COUNTED VALUES:")
        print(f"   - counted_full_units: {line.counted_full_units}")
        print(f"   - counted_partial_units: {line.counted_partial_units}")
        print(f"   - counted_qty (servings): {line.counted_qty}")
        print(f"\n   OPENING VALUES:")
        print(f"   - opening_qty: {line.opening_qty}")
        print(f"\n   STOCK ITEM CURRENT VALUES:")
        print(f"   - current_full_units: {line.item.current_full_units}")
        print(f"   - current_partial_units: {line.item.current_partial_units}")
        print(f"   - total_stock_in_servings: {line.item.total_stock_in_servings}")
