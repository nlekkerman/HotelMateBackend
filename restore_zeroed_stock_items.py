"""
Restore stock item data that was accidentally zeroed.
Uses backup JSON files to restore values.
"""
import os
import django
import json
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, Stocktake, StocktakeLine
from hotel.models import Hotel


def restore_from_september_closing_json():
    """Restore StockItem data from september_closing_stock.json"""
    
    json_file = 'september_closing_stock.json'
    
    if not os.path.exists(json_file):
        print(f"❌ ERROR: {json_file} not found!")
        return
    
    print(f"\n{'='*80}")
    print(f"RESTORING STOCK ITEMS FROM SEPTEMBER CLOSING STOCK BACKUP")
    print(f"Source: {json_file}")
    print(f"{'='*80}\n")
    
    # Load backup data
    with open(json_file, 'r') as f:
        backup_data = json.load(f)
    
    print(f"Loaded {len(backup_data)} items from backup\n")
    
    hotel = Hotel.objects.first()
    
    restored_count = 0
    not_found_count = 0
    already_has_data_count = 0
    
    for sku, data in backup_data.items():
        try:
            item = StockItem.objects.get(hotel=hotel, sku=sku)
            
            # Check if item is already zeroed (needs restoration)
            is_zeroed = (
                item.current_full_units == Decimal('0') and 
                item.current_partial_units == Decimal('0')
            )
            
            if is_zeroed:
                # Restore the values from backup
                # Note: The JSON has counted values which are in partial units
                item.current_full_units = Decimal(data.get('counted_full_units', '0.00'))
                item.current_partial_units = Decimal(data.get('counted_partial_units', '0.00'))
                item.save()
                
                restored_count += 1
                print(f"✓ Restored {sku}: {item.current_full_units} full, {item.current_partial_units} partial")
            else:
                already_has_data_count += 1
                if already_has_data_count <= 5:
                    print(f"⚬ Skipped {sku}: Already has data ({item.current_full_units} full, {item.current_partial_units} partial)")
                    
        except StockItem.DoesNotExist:
            not_found_count += 1
            if not_found_count <= 5:
                print(f"⚠ Item not found: {sku}")
    
    print(f"\n{'='*80}")
    print(f"RESTORATION COMPLETE")
    print(f"{'='*80}")
    print(f"✓ Restored: {restored_count} items")
    print(f"⚬ Skipped (has data): {already_has_data_count} items")
    print(f"⚠ Not found: {not_found_count} items")
    print(f"{'='*80}\n")


def restore_from_stocktake_line(stocktake_id=None):
    """Restore StockItem data from a specific stocktake's closing stock"""
    
    if not stocktake_id:
        print("\n📋 Available Stocktakes:")
        print("-" * 80)
        stocktakes = Stocktake.objects.all().order_by('-period_start')
        for st in stocktakes[:10]:
            print(f"ID: {st.id:3d} | {st.period_start} to {st.period_end} | Status: {st.status}")
        print("-" * 80)
        stocktake_id = input("\nEnter Stocktake ID to restore from: ")
    
    try:
        stocktake = Stocktake.objects.get(id=stocktake_id)
    except Stocktake.DoesNotExist:
        print(f"❌ ERROR: Stocktake ID {stocktake_id} not found!")
        return
    
    print(f"\n{'='*80}")
    print(f"RESTORING STOCK ITEMS FROM STOCKTAKE")
    print(f"Stocktake ID: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"Status: {stocktake.status}")
    print(f"{'='*80}\n")
    
    lines = stocktake.lines.all().select_related('item')
    print(f"Processing {lines.count()} stocktake lines...\n")
    
    restored_count = 0
    skipped_count = 0
    
    for line in lines:
        item = line.item
        
        # Check if item is zeroed
        is_zeroed = (
            item.current_full_units == Decimal('0') and 
            item.current_partial_units == Decimal('0')
        )
        
        if is_zeroed:
            # Restore from the stocktake line's counted values
            item.current_full_units = line.counted_full_units
            item.current_partial_units = line.counted_partial_units
            item.save()
            
            restored_count += 1
            if restored_count % 20 == 0:
                print(f"Restored {restored_count} items...")
        else:
            skipped_count += 1
    
    print(f"\n{'='*80}")
    print(f"RESTORATION COMPLETE")
    print(f"{'='*80}")
    print(f"✓ Restored: {restored_count} items")
    print(f"⚬ Skipped (has data): {skipped_count} items")
    print(f"{'='*80}\n")


def list_zeroed_items():
    """List all stock items that are currently zeroed"""
    
    hotel = Hotel.objects.first()
    zeroed_items = StockItem.objects.filter(
        hotel=hotel,
        current_full_units=Decimal('0'),
        current_partial_units=Decimal('0'),
        active=True
    ).select_related('category')
    
    print(f"\n{'='*80}")
    print(f"ZEROED STOCK ITEMS")
    print(f"{'='*80}\n")
    
    if zeroed_items.count() == 0:
        print("✓ No zeroed items found!\n")
        return
    
    print(f"Found {zeroed_items.count()} zeroed items:\n")
    
    by_category = {}
    for item in zeroed_items:
        cat = item.category.code
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    for cat_code in sorted(by_category.keys()):
        items = by_category[cat_code]
        print(f"\n{cat_code} - {items[0].category.name} ({len(items)} items)")
        print("-" * 80)
        for item in items[:10]:  # Show first 10
            print(f"  {item.sku:<10} {item.name}")
        if len(items) > 10:
            print(f"  ... and {len(items) - 10} more")
    
    print(f"\n{'='*80}\n")


def main():
    """Main menu"""
    
    while True:
        print("\n" + "="*80)
        print("STOCK ITEM RESTORATION MENU")
        print("="*80)
        print("\n1. List zeroed items")
        print("2. Restore from September closing stock JSON")
        print("3. Restore from specific stocktake")
        print("4. Exit")
        print("\n" + "="*80)
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            list_zeroed_items()
        elif choice == '2':
            confirm = input("\n⚠️  This will restore zeroed items from september_closing_stock.json. Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                restore_from_september_closing_json()
        elif choice == '3':
            restore_from_stocktake_line()
        elif choice == '4':
            print("\nExiting...\n")
            break
        else:
            print("\n❌ Invalid choice. Please select 1-4.")


if __name__ == '__main__':
    main()
