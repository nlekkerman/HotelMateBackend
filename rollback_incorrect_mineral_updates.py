"""
Rollback incorrect mineral name updates from the first script execution.
These SKUs were updated with wrong names because the original list had incorrect mappings.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

# Rollback incorrect updates - restore original names
rollback_updates = [
    ("M0008", "Mixer Lemon Juice 700ML"),
    ("M0009", "Mixer Lime Juice 700ML"),
    ("M0012", "Teisseire Bubble Gum"),
    ("M0013", "Split Coke 330ML"),
    ("M0014", "Monin Ginger Syrup"),
    ("M0040", "Split Coke"),
]

print("=" * 60)
print("ROLLING BACK INCORRECT MINERAL UPDATES")
print("=" * 60)

success_count = 0
error_count = 0

for sku, correct_name in rollback_updates:
    try:
        item = StockItem.objects.get(sku=sku)
        old_name = item.name
        item.name = correct_name
        item.save()
        print(f"✓ {sku}: Reverted from '{old_name}' back to '{correct_name}'")
        success_count += 1
    except StockItem.DoesNotExist:
        print(f"✗ {sku}: NOT FOUND - {correct_name}")
        error_count += 1
    except Exception as e:
        print(f"✗ {sku}: ERROR - {e}")
        error_count += 1

print("\n" + "=" * 60)
print(f"ROLLBACK COMPLETE: {success_count} reverted, {error_count} errors")
print("=" * 60)
