"""
Remove all numbers from stock item names
Example: "Heineken 500ml" → "Heineken ml"
Example: "Coca Cola 2L" → "Coca Cola L"
"""
import os
import sys
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem


def remove_numbers_from_names(dry_run=True):
    """
    Remove all numeric digits from stock item names
    
    Args:
        dry_run: If True, only show what would change without saving
    """
    print("=" * 60)
    print("REMOVE NUMBERS FROM PRODUCT NAMES")
    print("=" * 60)
    print()
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be saved")
        print()
    
    items = StockItem.objects.all()
    total = items.count()
    changed_count = 0
    
    print(f"Found {total} stock items")
    print()
    
    changes = []
    
    for item in items:
        original_name = item.name
        # Remove all digits from the name
        new_name = re.sub(r'\d+', '', original_name)
        # Clean up extra spaces
        new_name = re.sub(r'\s+', ' ', new_name).strip()
        
        if new_name != original_name:
            changed_count += 1
            changes.append({
                'id': item.id,
                'old': original_name,
                'new': new_name,
                'item': item
            })
            
            status = "WOULD CHANGE" if dry_run else "CHANGED"
            print(f"{status}: '{original_name}' → '{new_name}'")
    
    print()
    print(f"Items to change: {changed_count}/{total}")
    print()
    
    if not dry_run and changed_count > 0:
        confirm = input(f"Save {changed_count} changes? (yes/no): ")
        if confirm.lower() == 'yes':
            for change in changes:
                change['item'].name = change['new']
                change['item'].save()
            print(f"✅ Saved {changed_count} changes")
        else:
            print("❌ Cancelled - no changes saved")
    elif dry_run and changed_count > 0:
        print("To apply changes, run:")
        print("  python remove_numbers_from_product_names.py --apply")
    else:
        print("No changes needed")


if __name__ == "__main__":
    # Check for --apply flag
    apply = '--apply' in sys.argv
    remove_numbers_from_names(dry_run=not apply)
