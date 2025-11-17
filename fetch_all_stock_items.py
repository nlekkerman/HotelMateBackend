import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

def fetch_all_stock_items():
    """Fetch all stock items with their categories and subcategories"""
    
    stock_items = StockItem.objects.all().select_related(
        'hotel', 'category'
    ).order_by('category__name', 'subcategory', 'name')
    
    print(f"\n{'='*100}")
    print(f"TOTAL STOCK ITEMS: {stock_items.count()}")
    print(f"{'='*100}\n")
    
    current_category = None
    current_subcategory = None
    category_count = 0
    
    for item in stock_items:
        # Print category header when it changes
        if current_category != item.category:
            if current_category is not None:
                print(f"\n{'-'*100}\n")
            current_category = item.category
            category_count = stock_items.filter(category=current_category).count()
            print(f"\n{'#'*100}")
            cat_name = item.category.name if item.category else 'NO CATEGORY'
            cat_code = item.category.code if item.category else 'N/A'
            print(f"CATEGORY: {cat_name} (Code: {cat_code}) - {category_count} items")
            print(f"HOTEL: {item.hotel.name}")
            print(f"{'#'*100}\n")
            current_subcategory = None
        
        # Print subcategory header when it changes
        if current_subcategory != item.subcategory:
            current_subcategory = item.subcategory
            subcategory_count = stock_items.filter(
                category=current_category,
                subcategory=current_subcategory
            ).count()
            subcat_display = item.subcategory if item.subcategory else 'NO SUBCATEGORY'
            print(f"\n  >> SUBCATEGORY: {subcat_display} - {subcategory_count} items\n")
        
        # Print item details
        print(f"    • ID: {item.id:4d} | {item.name}")
        print(f"      SKU: {item.sku} | Size: {item.size} | UoM: {item.uom}")
        print(f"      Unit Cost: €{item.unit_cost}")
    
    print(f"\n{'='*100}")
    print(f"END OF STOCK ITEMS LIST")
    print(f"{'='*100}\n")
    
    # Summary by category
    print("\n" + "="*100)
    print("SUMMARY BY CATEGORY:")
    print("="*100)
    
    from django.db.models import Count
    categories = StockItem.objects.values(
        'category__code', 'category__name'
    ).annotate(
        count=Count('id')
    ).order_by('category__name')
    
    for cat in categories:
        cat_name = cat['category__name'] or 'NO CATEGORY'
        cat_code = cat['category__code'] or 'N/A'
        print(f"  {cat_name} (Code: {cat_code}): {cat['count']} items")
    
    print("\n" + "="*100)
    print("SUMMARY BY SUBCATEGORY:")
    print("="*100)
    
    subcategories = StockItem.objects.values(
        'category__name', 'subcategory'
    ).annotate(
        count=Count('id')
    ).order_by('category__name', 'subcategory')
    
    for subcat in subcategories:
        cat_name = subcat['category__name'] or 'NO CATEGORY'
        subcat_name = subcat['subcategory'] or 'NO SUBCATEGORY'
        print(f"  {cat_name} > {subcat_name}: {subcat['count']} items")

if __name__ == '__main__':
    fetch_all_stock_items()
