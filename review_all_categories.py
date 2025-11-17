"""
Complete overview of all stock categories and subcategories
with their current UOM settings for review
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockCategory
from django.db.models import Count
from collections import defaultdict

print("=" * 120)
print("COMPLETE STOCK CATEGORIES & SUBCATEGORIES REVIEW")
print("=" * 120)

# Get all categories
categories = StockCategory.objects.all().order_by('code')

for category in categories:
    items = StockItem.objects.filter(category=category)
    
    if items.count() == 0:
        continue
    
    print(f"\n{'#' * 120}")
    print(f"CATEGORY: {category.code} - {category.name}")
    print(f"Total Items: {items.count()}")
    print(f"{'#' * 120}")
    
    # Group by subcategory
    subcategories = items.values_list('subcategory', flat=True).distinct()
    
    for subcat in subcategories:
        subcat_items = items.filter(subcategory=subcat)
        subcat_display = subcat if subcat else "NO SUBCATEGORY"
        
        print(f"\n  {'=' * 110}")
        print(f"  SUBCATEGORY: {subcat_display} ({subcat_items.count()} items)")
        print(f"  {'=' * 110}")
        
        # Get UOM distribution
        uom_groups = defaultdict(list)
        for item in subcat_items[:10]:  # Show first 10 examples
            uom_groups[item.uom].append(item)
        
        # Show examples
        for item in subcat_items[:10]:
            stock_display = f"{item.current_full_units} + {item.current_partial_units}"
            print(f"    {item.sku:10s} | {item.name[:50]:50s}")
            print(f"               Size: {item.size:15s} | UOM: {item.uom:8.2f} | Stock: {stock_display}")
        
        if subcat_items.count() > 10:
            print(f"    ... and {subcat_items.count() - 10} more items")
        
        # Show UOM distribution
        print("\n    UOM Distribution:")
        uom_summary = subcat_items.values('uom').annotate(
            count=Count('id')
        ).order_by('uom')
        
        for uom_data in uom_summary:
            print(f"      UOM {uom_data['uom']:8.2f}: {uom_data['count']} items")

print("\n" + "=" * 120)
print("QUESTIONS TO CLARIFY FOR EACH CATEGORY/SUBCATEGORY:")
print("=" * 120)
print("""
For each category/subcategory above, please clarify:

1. DRAUGHT (D) - Kegs + Pints
   - Current: UOM = pints per keg
   - Is this correct? ✓ or needs change?

2. BOTTLED BEER (B) - Cases + Bottles  
   - Current: UOM = bottles per case (usually 12 or 24)
   - Is this correct? ✓ or needs change?

3. SPIRITS (S) - Bottles + Fractional
   - Current: UOM = shots per bottle
   - Is this correct? ✓ or needs change?

4. WINE (W) - Bottles + Fractional
   - Current: UOM = glasses per bottle
   - Is this correct? ✓ or needs change?

5. MINERALS (M):
   a) SOFT_DRINKS - Cases + Bottles (splits, schweppes, etc.)
      - Current: UOM = 12 bottles per case
      - Is this correct? ✓ or needs change?
   
   b) SYRUPS - Individual bottles (Monin, mixers)
      - Current: UOM = bottle size in ml (700 or 1000)
      - Input: Single decimal (e.g., 10.5 bottles)
      - Is this correct? ✓ or needs change?
   
   c) JUICES - Cases + Bottles + ml
      - Current: UOM = bottle size in ml
      - Is this correct? ✓ or needs change?
   
   d) CORDIALS - Cases + Bottles
      - Current: UOM = 12 bottles per case
      - Is this correct? ✓ or needs change?
   
   e) BIB (Bag-in-Box) - Boxes + Liters
      - Current: UOM = 18 liters per box
      - Is this correct? ✓ or needs change?
   
   f) BULK_JUICES - Individual bottles
      - Current: UOM = 1 (individual)
      - Is this correct? ✓ or needs change?

Please review and tell me what needs to be changed!
""")
