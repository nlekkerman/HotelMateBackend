"""
List all beer products in the database
Shows ID, name, category, and unit of measurement
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem


def list_all_beers():
    """List all beer products"""
    print("=" * 80)
    print("ALL BEER PRODUCTS")
    print("=" * 80)
    print()
    
    # Find beers by category
    beers = StockItem.objects.filter(category__name__icontains='beer').order_by('name')
    
    if not beers.exists():
        # Try alternative category names
        beers = StockItem.objects.filter(
            category__name__icontains='draught'
        ).order_by('name') | StockItem.objects.filter(
            category__name__icontains='lager'
        ).order_by('name') | StockItem.objects.filter(
            category__name__icontains='ale'
        ).order_by('name')
    
    if not beers.exists():
        print("No beer products found")
        print("\nTrying to list all categories:")
        from stock_tracker.models import Category
        categories = Category.objects.all()
        for cat in categories:
            print(f"  - {cat.name}")
        return
    
    total = beers.count()
    print(f"Found {total} beer products")
    print()
    
    # Group by category
    by_category = {}
    for beer in beers:
        cat_name = beer.category.name if beer.category else "Uncategorized"
        if cat_name not in by_category:
            by_category[cat_name] = []
        by_category[cat_name].append(beer)
    
    # Print by category
    for cat_name, items in sorted(by_category.items()):
        print(f"\n📦 {cat_name.upper()} ({len(items)} items)")
        print("-" * 80)
        
        for beer in items:
            uom = beer.unit_of_measurement or "N/A"
            print(f"  ID: {beer.id:4d} | {beer.name:40s} | UOM: {uom}")
    
    print()
    print("=" * 80)
    print(f"Total: {total} beer products")
    print("=" * 80)


if __name__ == "__main__":
    list_all_beers()
