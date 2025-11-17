import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem


def save_stock_items_to_json():
    """Save each stock item to a separate JSON file"""
    
    # Create output directory
    output_dir = 'stock_items_json'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    # Fetch all stock items
    stock_items = StockItem.objects.all().select_related(
        'hotel', 'category'
    ).order_by('category__name', 'subcategory', 'name')
    
    print(f"\nTotal stock items: {stock_items.count()}\n")
    
    # Process each item
    for item in stock_items:
        # Create filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '_') else '_' 
                           for c in item.name)
        filename = f"{item.id:04d}_{item.sku}_{safe_name}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Create item data dictionary
        item_data = {
            'id': item.id,
            'sku': item.sku,
            'name': item.name,
            'hotel': {
                'id': item.hotel.id,
                'name': item.hotel.name
            },
            'category': {
                'code': item.category.code,
                'name': item.category.name
            },
            'subcategory': item.subcategory,
            'size': item.size,
            'size_value': str(item.size_value),
            'size_unit': item.size_unit,
            'uom': str(item.uom),
            'unit_cost': str(item.unit_cost),
            'current_full_units': str(item.current_full_units),
            'current_partial_units': str(item.current_partial_units),
            'par_level': str(item.par_level) if item.par_level else None,
            'menu_price': str(item.menu_price) if item.menu_price else None,
        }
        
        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(item_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved: {filename}")
    
    print(f"\n{'='*80}")
    print(f"COMPLETED: {stock_items.count()} JSON files saved to '{output_dir}' directory")
    print(f"{'='*80}")
    
    # Create summary by category
    summary_file = os.path.join(output_dir, '_SUMMARY.json')
    
    from django.db.models import Count
    categories = StockItem.objects.values(
        'category__code', 'category__name'
    ).annotate(
        count=Count('id')
    ).order_by('category__name')
    
    summary_data = {
        'total_items': stock_items.count(),
        'by_category': []
    }
    
    for cat in categories:
        cat_code = cat['category__code'] or 'N/A'
        cat_name = cat['category__name'] or 'NO CATEGORY'
        summary_data['by_category'].append({
            'code': cat_code,
            'name': cat_name,
            'count': cat['count']
        })
    
    # Add subcategory breakdown for Minerals
    minerals_items = StockItem.objects.filter(
        category__code='M'
    ).values('subcategory').annotate(
        count=Count('id')
    ).order_by('subcategory')
    
    summary_data['minerals_subcategories'] = []
    for subcat in minerals_items:
        summary_data['minerals_subcategories'].append({
            'subcategory': subcat['subcategory'] or 'NO SUBCATEGORY',
            'count': subcat['count']
        })
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSummary saved to: {summary_file}")


if __name__ == '__main__':
    save_stock_items_to_json()
