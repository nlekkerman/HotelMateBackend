"""
Re-populate October stocktake to recalculate opening_qty for BULK_JUICES.

This will update October's opening stock to use September's closing values:
- M0042: 43 bottles
- M0210: 43 bottles
- M11: 138 bottles
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake

print("=" * 80)
print("RE-POPULATE OCTOBER STOCKTAKE")
print("=" * 80)

october = Stocktake.objects.filter(
    period_start__year=2025,
    period_start__month=10
).first()

if not october:
    print("\n❌ October not found!")
    exit()

print(f"\nFound: {october}")
print(f"Period: {october.period_start} to {october.period_end}")

items_to_check = ['M0042', 'M0210', 'M11']

print("\n" + "-" * 80)
print("CURRENT OCTOBER OPENING STOCK:")
print("-" * 80)

for sku in items_to_check:
    line = october.lines.filter(item__sku=sku).first()
    if line:
        print(f"{line.item.sku}: opening_qty={line.opening_qty}")

response = input("\nRe-populate October? (yes/no): ").strip().lower()

if response != 'yes':
    print("\n❌ Cancelled.")
    exit()

print("\n" + "=" * 80)
print("UPDATING OPENING QTY...")
print("=" * 80)

# Get September stocktake
september = Stocktake.objects.filter(
    period_start__year=2025,
    period_start__month=9
).first()

if not september:
    print("❌ September not found!")
    exit()

# Update each item's opening_qty from September's closing
for sku in items_to_check:
    sept_line = september.lines.filter(item__sku=sku).first()
    oct_line = october.lines.filter(item__sku=sku).first()
    
    if sept_line and oct_line:
        # September closing = October opening
        sept_closing = sept_line.counted_qty
        oct_line.opening_qty = sept_closing
        oct_line.save(update_fields=['opening_qty'])
        
        print(f"✅ {sku}: opening_qty updated to {sept_closing}")

print("\n✅ October opening stock updated!")

print("\n" + "-" * 80)
print("NEW OCTOBER OPENING STOCK:")
print("-" * 80)

for sku in items_to_check:
    line = october.lines.filter(item__sku=sku).first()
    if line:
        print(f"{line.item.sku}: opening_qty={line.opening_qty} "
              f"(display: {line.opening_qty} bottles)")

print("\n" + "=" * 80)
print("DONE! October now has correct opening stock from September closing.")
