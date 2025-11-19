import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

def fetch_all_stockitems_uom():
    """Fetch all stock items and log their UOM"""
    stock_items = StockItem.objects.all().order_by('category', 'name')
    
    print(f"\nTotal Stock Items: {stock_items.count()}\n")
    print("=" * 100)
    
    current_category = None
    for item in stock_items:
        if current_category != item.category:
            current_category = item.category
            print(f"\n{'=' * 100}")
            print(f"CATEGORY: {item.category}")
            print(f"{'=' * 100}")
        
        print(f"ID: {item.id:4d} | Name: {item.name:50s} | UOM: {str(item.uom):15s} | Subcategory: {item.subcategory or 'N/A'}")
    
    print("\n" + "=" * 100)
    print("\nSummary by UOM:")
    print("=" * 100)
    
    uom_summary = {}
    for item in stock_items:
        uom = str(item.uom)
        if uom not in uom_summary:
            uom_summary[uom] = []
        uom_summary[uom].append(f"{item.name} ({item.category})")
    
    for uom, items in sorted(uom_summary.items()):
        print(f"\n{uom}: {len(items)} items")
        for item_name in items[:5]:  # Show first 5 items
            print(f"  - {item_name}")
        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")

if __name__ == '__main__':
    fetch_all_stockitems_uom()
