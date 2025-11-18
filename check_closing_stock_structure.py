"""
Check how closing stock is stored for different categories
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from decimal import Decimal

# Get September (previous closed period)
september = StockPeriod.objects.filter(hotel_id=2, year=2025, month=9).first()

if not september:
    print("No September period found")
    exit()

print("=" * 100)
print(f"SEPTEMBER 2025 CLOSING STOCK STRUCTURE")
print("=" * 100)
print(f"Period: {september.period_name}")
print(f"Status: {'CLOSED' if september.is_closed else 'OPEN'}")

# Check each category
categories = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer', 
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals'
}

for cat_code, cat_name in categories.items():
    snapshots = StockSnapshot.objects.filter(
        period=september,
        item__category_id=cat_code
    ).select_related('item')[:3]
    
    if snapshots.exists():
        print(f"\n{'='*100}")
        print(f"{cat_code} - {cat_name}")
        print(f"{'='*100}")
        
        for snap in snapshots:
            print(f"\n{snap.item.sku} - {snap.item.name}")
            print(f"  Size: {snap.item.size} | UOM: {snap.item.uom}")
            print(f"  Subcategory: {snap.item.subcategory or 'N/A'}")
            print(f"  closing_full_units: {snap.closing_full_units}")
            print(f"  closing_partial_units: {snap.closing_partial_units}")
            print(f"  total_servings: {snap.total_servings:.4f}")
            
            # Show what would be displayed as opening for next period
            display_full = snap.calculate_opening_display_full(snap.total_servings)
            display_partial = snap.calculate_opening_display_partial(snap.total_servings)
            print(f"  ➜ Would display as opening: {display_full} full + {display_partial:.2f} partial")

print("\n" + "="*100)
print("KEY QUESTION: How should closing stock be stored?")
print("="*100)
print("Current observation:")
print("- closing_full_units = 0 for most items")
print("- closing_partial_units = actual count (bottles, pints, etc)")
print("- total_servings = calculated value")
